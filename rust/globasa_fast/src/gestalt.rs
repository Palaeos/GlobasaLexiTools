//! difflib.SequenceMatcher (Ratcliff-Obershelp "gestalt" matching) with isjunk=None and
//! autojunk=False, on the characters of two strings: a line-by-line port of CPython 3.10's
//! find_longest_match / get_matching_blocks / ratio / quick_ratio / real_quick_ratio, so the
//! blocks and ratios are identical to difflib's. best_matches is the hot loop of
//! edition_variants.variants (char-level matching of sentences), run over A in parallel.
use std::collections::HashMap;

use pyo3::prelude::*;
use rayon::prelude::*;

/// b's per-character index lists (difflib's b2j), each in ascending order.
struct Chained {
    b: Vec<u32>,
    b2j: HashMap<u32, Vec<usize>>,
    counts: HashMap<u32, i64>,
}

impl Chained {
    fn new(s: &str) -> Self {
        let b: Vec<u32> = s.chars().map(|c| c as u32).collect();
        let mut b2j: HashMap<u32, Vec<usize>> = HashMap::new();
        let mut counts: HashMap<u32, i64> = HashMap::new();
        for (i, &e) in b.iter().enumerate() {
            b2j.entry(e).or_default().push(i);
            *counts.entry(e).or_insert(0) += 1;
        }
        Chained { b, b2j, counts }
    }
}

fn chars(s: &str) -> Vec<u32> {
    s.chars().map(|c| c as u32).collect()
}

fn calculate_ratio(matches: usize, length: usize) -> f64 {
    if length > 0 {
        2.0 * matches as f64 / length as f64
    } else {
        1.0
    }
}

/// find_longest_match(alo, ahi, blo, bhi) -> (i, j, k). j2len is kept in two arrays indexed
/// by j + 1 with the touched entries cleared, instead of difflib's dicts (same values).
fn find_longest_match(a: &[u32], cb: &Chained, alo: usize, ahi: usize, blo: usize, bhi: usize,
                      j2len: &mut Vec<usize>, newj2len: &mut Vec<usize>,
                      touched: &mut Vec<usize>, newtouched: &mut Vec<usize>) -> (usize, usize, usize) {
    let b = &cb.b;
    let (mut besti, mut bestj, mut bestsize) = (alo, blo, 0usize);
    for &t in touched.iter() {
        j2len[t] = 0;
    }
    touched.clear();
    for i in alo..ahi {
        newtouched.clear();
        if let Some(js) = cb.b2j.get(&a[i]) {
            for &j in js {
                if j < blo {
                    continue;
                }
                if j >= bhi {
                    break;
                }
                // j2len[j] in difflib is stored at index j + 1 here, so j2len.get(j-1) is j2len[j]
                let k = j2len[j] + 1;
                newj2len[j + 1] = k;
                newtouched.push(j + 1);
                if k > bestsize {
                    besti = i + 1 - k;
                    bestj = j + 1 - k;
                    bestsize = k;
                }
            }
        }
        for &t in touched.iter() {
            j2len[t] = 0;
        }
        std::mem::swap(j2len, newj2len);
        std::mem::swap(touched, newtouched);
    }
    // no junk: only the "not isbjunk" extensions can apply (and with no popular elements they
    // never do; kept for fidelity)
    while besti > alo && bestj > blo && a[besti - 1] == b[bestj - 1] {
        besti -= 1;
        bestj -= 1;
        bestsize += 1;
    }
    while besti + bestsize < ahi && bestj + bestsize < bhi && a[besti + bestsize] == b[bestj + bestsize] {
        bestsize += 1;
    }
    (besti, bestj, bestsize)
}

/// get_matching_blocks(), including the final (la, lb, 0).
fn matching_blocks_of(a: &[u32], cb: &Chained) -> Vec<(usize, usize, usize)> {
    let (la, lb) = (a.len(), cb.b.len());
    let mut j2len = vec![0usize; lb + 2];
    let mut newj2len = vec![0usize; lb + 2];
    let (mut touched, mut newtouched) = (Vec::new(), Vec::new());
    let mut queue = vec![(0usize, la, 0usize, lb)];
    let mut blocks = Vec::new();
    while let Some((alo, ahi, blo, bhi)) = queue.pop() {
        let (i, j, k) = find_longest_match(a, cb, alo, ahi, blo, bhi, &mut j2len, &mut newj2len,
                                           &mut touched, &mut newtouched);
        if k > 0 {
            blocks.push((i, j, k));
            if alo < i && blo < j {
                queue.push((alo, i, blo, j));
            }
            if i + k < ahi && j + k < bhi {
                queue.push((i + k, ahi, j + k, bhi));
            }
        }
    }
    blocks.sort();
    let (mut i1, mut j1, mut k1) = (0usize, 0usize, 0usize);
    let mut out = Vec::with_capacity(blocks.len() + 1);
    for (i2, j2, k2) in blocks {
        if i1 + k1 == i2 && j1 + k1 == j2 {
            k1 += k2;
        } else {
            if k1 > 0 {
                out.push((i1, j1, k1));
            }
            i1 = i2;
            j1 = j2;
            k1 = k2;
        }
    }
    if k1 > 0 {
        out.push((i1, j1, k1));
    }
    out.push((la, lb, 0));
    out
}

fn ratio_of(a: &[u32], cb: &Chained) -> f64 {
    let matches: usize = matching_blocks_of(a, cb).iter().map(|t| t.2).sum();
    calculate_ratio(matches, a.len() + cb.b.len())
}

fn quick_ratio_of(a: &[u32], cb: &Chained) -> f64 {
    let mut avail: HashMap<u32, i64> = HashMap::new();
    let mut matches = 0usize;
    for e in a {
        let numb = match avail.get(e) {
            Some(&n) => n,
            None => *cb.counts.get(e).unwrap_or(&0),
        };
        avail.insert(*e, numb - 1);
        if numb > 0 {
            matches += 1;
        }
    }
    calculate_ratio(matches, a.len() + cb.b.len())
}

fn real_quick_ratio_of(la: usize, lb: usize) -> f64 {
    calculate_ratio(la.min(lb), la + lb)
}

#[pyfunction]
pub fn ratio(a: &str, b: &str) -> f64 {
    ratio_of(&chars(a), &Chained::new(b))
}

#[pyfunction]
pub fn quick_ratio(a: &str, b: &str) -> f64 {
    quick_ratio_of(&chars(a), &Chained::new(b))
}

#[pyfunction]
pub fn real_quick_ratio(a: &str, b: &str) -> f64 {
    real_quick_ratio_of(a.chars().count(), b.chars().count())
}

/// [(i, j, size), ...] as difflib's get_matching_blocks() (plain tuples).
#[pyfunction]
pub fn matching_blocks(a: &str, b: &str) -> Vec<(usize, usize, usize)> {
    matching_blocks_of(&chars(a), &Chained::new(b))
}

/// For each sentence A[i]: (ratio, j) of the first B[j] with the highest ratio among
/// B[max(0, c - window) : c + window], c = int(i * len(B) / len(A)), skipping pairs whose
/// real_quick_ratio or quick_ratio is below min_ratio; (0.0, -1) when none qualifies.
/// This is the candidate search of edition_variants.variants, unchanged.
#[pyfunction]
pub fn best_matches(py: Python<'_>, a_list: Vec<String>, b_list: Vec<String>, window: usize,
                    min_ratio: f64) -> Vec<(f64, i64)> {
    py.allow_threads(|| {
        let bs: Vec<Chained> = b_list.par_iter().map(|s| Chained::new(s)).collect();
        let (la, lb) = (a_list.len(), b_list.len());
        a_list
            .par_iter()
            .enumerate()
            .map(|(i, a)| {
                let av = chars(a);
                let c = ((i * lb) as f64 / la as f64) as usize;
                let lo = c.saturating_sub(window);
                let hi = (c + window).min(lb);
                let mut best = (0.0f64, -1i64);
                for j in lo..hi.max(lo) {
                    let cb = &bs[j];
                    if real_quick_ratio_of(av.len(), cb.b.len()) < min_ratio
                        || quick_ratio_of(&av, cb) < min_ratio
                    {
                        continue;
                    }
                    let r = ratio_of(&av, cb);
                    if r > best.0 {
                        best = (r, j as i64);
                    }
                }
                best
            })
            .collect()
    })
}
