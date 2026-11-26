//! Weighted global alignment of Globasa-letter forms: a port of `align()` in
//! word_selection/align.py. The substitution costs arrive as a table over an ASCII alphabet,
//! computed in Python from the cost function (sub_cost, sino_sub_cost, ...), so the phonetic
//! classes are defined once, in Python. The order of the additions and of the comparisons
//! follows the Python code, which gives bit-identical costs and the same traceback.
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

const UNKNOWN: u8 = u8::MAX;

/// Position classes of `_positions`: vowel, coda, ambiguous (before a glide), onset.
#[derive(Clone, Copy, PartialEq)]
enum Pos {
    Vowel,
    Coda,
    Glide,
    Onset,
}

fn is_vowel(c: u8) -> bool {
    matches!(c, b'a' | b'e' | b'i' | b'o' | b'u')
}

fn positions(s: &[u8]) -> Vec<Pos> {
    (0..s.len())
        .map(|k| {
            let ch = s[k];
            let nxt = s.get(k + 1).copied();
            if is_vowel(ch) {
                Pos::Vowel
            } else {
                match nxt {
                    None => Pos::Coda,
                    Some(n) if !is_vowel(n) && n != b'y' && n != b'w' => Pos::Coda,
                    Some(b'y') | Some(b'w') => Pos::Glide,
                    Some(_) => Pos::Onset,
                }
            }
        })
        .collect()
}

/// `_sino_coda(s, k)`: is s[k] a coda consonant that a Sino-xenic reading may lack?
fn sino_coda(s: &[u8], k: usize) -> bool {
    if let Some(&n) = s.get(k + 1) {
        if matches!(n, b'a' | b'e' | b'i' | b'o' | b'u' | b'y') {
            return false;
        }
    }
    matches!(s[k], b't' | b'k' | b'p') || (s[k] == b'g' && k > 0 && s[k - 1] == b'n')
}

/// One configuration of the Python `align(a, b, sub=..., coda=..., nasal_pos=..., edge_gap=...)`.
#[pyclass(frozen, module = "globasa_fast")]
pub struct Aligner {
    index: [u8; 128],
    k: usize,
    table: Vec<f64>,
    gap: f64,
    edge_gap: f64,
    coda_gap: f64,
    nasal_pos: f64,
    sino_coda: bool,
}

#[derive(Clone, Copy, PartialEq)]
enum Op {
    Diag,
    Up,
    Left,
}

impl Aligner {
    /// Letters as alphabet indices; None if a letter is outside the alphabet (the Python
    /// wrapper checks first and uses the Python code then).
    fn encode<'s>(&self, s: &'s str) -> Option<&'s [u8]> {
        let b = s.as_bytes();
        if b.iter().all(|&c| c < 128 && self.index[c as usize] != UNKNOWN) {
            Some(b)
        } else {
            None
        }
    }

    fn sub(&self, x: u8, y: u8) -> f64 {
        self.table[self.index[x as usize] as usize * self.k + self.index[y as usize] as usize]
    }

    fn coda(&self, s: &[u8], k: usize) -> bool {
        self.sino_coda && sino_coda(s, k)
    }

    /// The DP table D (row-major, (n+1) x (m+1)) and, when wanted, the traceback ops.
    fn fill(&self, a: &[u8], b: &[u8], with_ops: bool) -> (Vec<f64>, Vec<Op>) {
        let (n, m) = (a.len(), b.len());
        let w = m + 1;
        let mut d = vec![0.0f64; (n + 1) * w];
        let mut ops = if with_ops { vec![Op::Diag; (n + 1) * w] } else { Vec::new() };
        let edge_or_coda = self.edge_gap.min(self.coda_gap);
        for i in 1..=n {
            let g = if self.coda(a, i - 1) { edge_or_coda } else { self.edge_gap };
            d[i * w] = d[(i - 1) * w] + g;
            if with_ops {
                ops[i * w] = Op::Up;
            }
        }
        for j in 1..=m {
            let g = if self.coda(b, j - 1) { edge_or_coda } else { self.edge_gap };
            d[j] = d[j - 1] + g;
            if with_ops {
                ops[j] = Op::Left;
            }
        }
        let use_nasal = self.nasal_pos != 0.0;
        let (pa, pb) = if use_nasal { (positions(a), positions(b)) } else { (Vec::new(), Vec::new()) };
        for i in 1..=n {
            let x = a[i - 1];
            let coda_a = self.coda(a, i - 1);
            for j in 1..=m {
                let y = b[j - 1];
                let mut c = self.sub(x, y);
                if use_nasal && matches!(x, b'm' | b'n') && matches!(y, b'm' | b'n') {
                    let (p, q) = (pa[i - 1], pb[j - 1]);
                    if (p == Pos::Coda && q == Pos::Onset) || (p == Pos::Onset && q == Pos::Coda) {
                        c += self.nasal_pos;
                    }
                }
                let mut best = d[(i - 1) * w + (j - 1)] + c;
                let mut op = Op::Diag;
                let mut gu = if j == m { self.edge_gap } else { self.gap };
                let mut gl = if i == n { self.edge_gap } else { self.gap };
                if self.sino_coda {
                    if coda_a {
                        gu = gu.min(self.coda_gap);
                    }
                    if self.coda(b, j - 1) {
                        gl = gl.min(self.coda_gap);
                    }
                }
                let up = d[(i - 1) * w + j] + gu;
                let left = d[i * w + (j - 1)] + gl;
                if up < best {
                    best = up;
                    op = Op::Up;
                }
                if left < best {
                    best = left;
                    op = Op::Left;
                }
                d[i * w + j] = best;
                if with_ops {
                    ops[i * w + j] = op;
                }
            }
        }
        (d, ops)
    }

    fn cost_bytes(&self, a: &[u8], b: &[u8]) -> f64 {
        let (d, _) = self.fill(a, b, false);
        d[a.len() * (b.len() + 1) + b.len()]
    }
}

#[pymethods]
impl Aligner {
    /// alphabet: ASCII letters the table covers; table: len(alphabet)**2 costs, row-major,
    /// table[i*k+j] = sub(alphabet[i], alphabet[j]); coda: "" (none) or "sino" (_sino_coda).
    #[new]
    #[pyo3(signature = (alphabet, table, gap, edge_gap, coda_gap, nasal_pos, coda))]
    fn new(alphabet: &str, table: Vec<f64>, gap: f64, edge_gap: f64, coda_gap: f64, nasal_pos: f64,
           coda: &str) -> PyResult<Self> {
        let letters = alphabet.as_bytes();
        let k = letters.len();
        if !alphabet.is_ascii() || k == 0 || k >= UNKNOWN as usize {
            return Err(PyValueError::new_err("alphabet must be 1-254 ASCII letters"));
        }
        if table.len() != k * k {
            return Err(PyValueError::new_err("table must have len(alphabet)**2 entries"));
        }
        let sino_coda = match coda {
            "" => false,
            "sino" => true,
            _ => return Err(PyValueError::new_err("coda must be '' or 'sino'")),
        };
        let mut index = [UNKNOWN; 128];
        for (i, &c) in letters.iter().enumerate() {
            index[c as usize] = i as u8;
        }
        Ok(Aligner { index, k, table, gap, edge_gap, coda_gap, nasal_pos, sino_coda })
    }

    /// True if every letter of s is in the alphabet.
    fn covers(&self, s: &str) -> bool {
        self.encode(s).is_some()
    }

    /// (cost, [(x, y), ...]) with '-' for gaps, as the Python align().
    fn align(&self, a: &str, b: &str) -> PyResult<(f64, Vec<(char, char)>)> {
        let (x, y) = self.both(a, b)?;
        let (d, ops) = self.fill(x, y, true);
        let (n, m) = (x.len(), y.len());
        let w = m + 1;
        let mut pairs = Vec::with_capacity(n + m);
        let (mut i, mut j) = (n, m);
        while i > 0 || j > 0 {
            match ops[i * w + j] {
                Op::Diag => {
                    pairs.push((x[i - 1] as char, y[j - 1] as char));
                    i -= 1;
                    j -= 1;
                }
                Op::Up => {
                    pairs.push((x[i - 1] as char, '-'));
                    i -= 1;
                }
                Op::Left => {
                    pairs.push(('-', y[j - 1] as char));
                    j -= 1;
                }
            }
        }
        pairs.reverse();
        Ok((d[n * w + m], pairs))
    }

    /// The alignment cost only (align(a, b)[0]).
    fn cost(&self, a: &str, b: &str) -> PyResult<f64> {
        let (x, y) = self.both(a, b)?;
        Ok(self.cost_bytes(x, y))
    }

    /// min over x in xs, y in ys of cost(x, y) / max(len(x), len(y), 1) (sino_distance).
    fn min_norm_cost(&self, xs: Vec<String>, ys: Vec<String>) -> PyResult<f64> {
        let mut best = f64::INFINITY;
        for x in &xs {
            for y in &ys {
                let (a, b) = self.both(x, y)?;
                let c = self.cost_bytes(a, b) / (a.len().max(b.len()).max(1) as f64);
                if c < best {
                    best = c;
                }
            }
        }
        if xs.is_empty() || ys.is_empty() {
            return Err(PyValueError::new_err("min_norm_cost of an empty set"));
        }
        Ok(best)
    }
}

impl Aligner {
    fn both<'s>(&self, a: &'s str, b: &'s str) -> PyResult<(&'s [u8], &'s [u8])> {
        match (self.encode(a), self.encode(b)) {
            (Some(x), Some(y)) => Ok((x, y)),
            _ => Err(PyValueError::new_err("letter outside the alphabet")),
        }
    }
}
