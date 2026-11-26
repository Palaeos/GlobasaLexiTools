//! Chu-Liu-Edmonds maximum spanning tree with exactly one root arc: a literal port of
//! stanza/models/common/chuliu_edmonds.py (stanza 1.15), the decoder stanza's depparse runs in
//! Python for every sentence. Every step follows the numpy original so the trees are identical:
//! argmax keeps the first maximum, Tarjan finds the cycles in the same order and the last one
//! is contracted first, element-wise arithmetic is in the same order, and the cycle score is
//! summed with numpy's pairwise summation.
use numpy::{PyArray1, PyReadonlyArray2};
use pyo3::exceptions::PyAssertionError;
use pyo3::prelude::*;

/// Dense row-major square matrix.
#[derive(Clone)]
struct Mat {
    n: usize,
    v: Vec<f64>,
}

impl Mat {
    fn get(&self, r: usize, c: usize) -> f64 {
        self.v[r * self.n + c]
    }
    fn set(&mut self, r: usize, c: usize, x: f64) {
        self.v[r * self.n + c] = x;
    }
}

/// numpy's pairwise summation (pairwise_sum_DOUBLE, blocks of 8, PW_BLOCKSIZE 128), as used by
/// ndarray.sum() on a contiguous float64 array (starting from 0.0).
fn pairwise_sum(a: &[f64]) -> f64 {
    let n = a.len();
    if n < 8 {
        let mut res = 0.0;
        for &x in a {
            res += x;
        }
        res
    } else if n <= 128 {
        let mut r = [a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7]];
        let mut i = 8;
        while i < n - (n % 8) {
            for j in 0..8 {
                r[j] += a[i + j];
            }
            i += 8;
        }
        let mut res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
        while i < n {
            res += a[i];
            i += 1;
        }
        res
    } else {
        let mut n2 = n / 2;
        n2 -= n2 % 8;
        pairwise_sum(&a[..n2]) + pairwise_sum(&a[n2..])
    }
}

/// np.argmax over a row: the first index of the maximum (no NaN: checked on entry).
fn argmax(xs: impl Iterator<Item = f64>) -> usize {
    let mut best = f64::NEG_INFINITY;
    let mut bi = 0;
    for (i, x) in xs.enumerate() {
        if i == 0 || x > best {
            best = x;
            bi = i;
        }
    }
    bi
}

fn prepare_scores(s: &mut Mat) {
    for i in 0..s.n {
        s.set(i, i, f64::NEG_INFINITY);
    }
    for j in 0..s.n {
        s.set(0, j, f64::NEG_INFINITY);
    }
    s.set(0, 0, 0.0);
}

fn heads(s: &Mat) -> Vec<usize> {
    (0..s.n).map(|i| argmax((0..s.n).map(|j| s.get(i, j)))).collect()
}

/// Tarjan's strongly connected components on the dependents graph (i -> j when tree[j] == i),
/// iteratively, visiting dependents in ascending order: the cycles (> 1 node) as boolean masks,
/// in the order the original finds them.
fn tarjan(tree: &[usize]) -> Vec<Vec<bool>> {
    let n = tree.len();
    let mut dependents: Vec<Vec<usize>> = vec![Vec::new(); n];
    for (j, &h) in tree.iter().enumerate() {
        dependents[h].push(j);
    }
    let mut indices = vec![-1i64; n];
    let mut lowlinks = vec![-1i64; n];
    let mut onstack = vec![false; n];
    let mut stack: Vec<usize> = Vec::new();
    let mut counter = 0i64;
    let mut cycles = Vec::new();
    for start in 0..n {
        if indices[start] != -1 {
            continue;
        }
        // (node, next dependent position, dependent just visited)
        let mut call_stack: Vec<(usize, Option<usize>, usize)> = vec![(start, None, 0)];
        while let Some((i, pos, j_prev)) = call_stack.pop() {
            let mut k = match pos {
                None => {
                    counter += 1;
                    indices[i] = counter - 1;
                    lowlinks[i] = counter - 1;
                    stack.push(i);
                    onstack[i] = true;
                    0
                }
                Some(p) => {
                    lowlinks[i] = lowlinks[i].min(lowlinks[j_prev]);
                    p
                }
            };
            let mut descended = false;
            while k < dependents[i].len() {
                let j = dependents[i][k];
                k += 1;
                if indices[j] == -1 {
                    call_stack.push((i, Some(k), j));
                    call_stack.push((j, None, 0));
                    descended = true;
                    break;
                } else if onstack[j] {
                    lowlinks[i] = lowlinks[i].min(indices[j]);
                }
            }
            if !descended && lowlinks[i] == indices[i] {
                let mut cycle = vec![false; n];
                while *stack.last().unwrap() != i {
                    let j = stack.pop().unwrap();
                    onstack[j] = false;
                    cycle[j] = true;
                }
                stack.pop();
                onstack[i] = false;
                cycle[i] = true;
                if cycle.iter().filter(|&&c| c).count() > 1 {
                    cycles.push(cycle);
                }
            }
        }
    }
    cycles
}

struct Contraction {
    tree: Vec<usize>,
    cycle_locs: Vec<usize>,
    noncycle_locs: Vec<usize>,
    metanode_heads: Vec<usize>,
    metanode_deps: Vec<usize>,
}

/// process_cycle: the subproblem with one cycle contracted into a metanode (last row/column).
fn process_cycle(tree: &[usize], cycle: &[bool], s: &Mat) -> (Mat, Contraction) {
    let cycle_locs: Vec<usize> = (0..s.n).filter(|&i| cycle[i]).collect();
    let noncycle_locs: Vec<usize> = (0..s.n).filter(|&i| !cycle[i]).collect();
    let cycle_scores: Vec<f64> = cycle_locs.iter().map(|&c| s.get(c, tree[c])).collect();
    let cycle_score = pairwise_sum(&cycle_scores);
    let (nc, nn) = (cycle_locs.len(), noncycle_locs.len());
    // metanode_head_scores[ci][nj] = scores[cycle[ci], noncycle[nj]] - cycle_scores[ci] + cycle_score
    let head_score = |ci: usize, nj: usize| s.get(cycle_locs[ci], noncycle_locs[nj]) - cycle_scores[ci] + cycle_score;
    let dep_score = |ni: usize, cj: usize| s.get(noncycle_locs[ni], cycle_locs[cj]);
    let metanode_heads: Vec<usize> = (0..nn).map(|nj| argmax((0..nc).map(|ci| head_score(ci, nj)))).collect();
    let metanode_deps: Vec<usize> = (0..nn).map(|ni| argmax((0..nc).map(|cj| dep_score(ni, cj)))).collect();
    let m = nn + 1;
    let mut sub = Mat { n: m, v: vec![0.0; m * m] };
    for (a, &r) in noncycle_locs.iter().enumerate() {
        for (b, &c) in noncycle_locs.iter().enumerate() {
            sub.set(a, b, s.get(r, c));
        }
    }
    for nj in 0..nn {
        sub.set(nn, nj, head_score(metanode_heads[nj], nj));
    }
    for ni in 0..nn {
        sub.set(ni, nn, dep_score(ni, metanode_deps[ni]));
    }
    (sub, Contraction { tree: tree.to_vec(), cycle_locs, noncycle_locs, metanode_heads, metanode_deps })
}

fn expand_contracted_tree(c: &Contraction, contracted_tree: &[usize]) -> Vec<usize> {
    let cycle_head = contracted_tree[contracted_tree.len() - 1];
    let contracted = &contracted_tree[..contracted_tree.len() - 1];
    let mut new_tree = vec![usize::MAX; c.tree.len()];
    for (k, &h) in contracted.iter().enumerate() {
        if h < contracted.len() {
            new_tree[c.noncycle_locs[k]] = c.noncycle_locs[h];
        } else {
            new_tree[c.noncycle_locs[k]] = c.cycle_locs[c.metanode_deps[k]];
        }
    }
    for &cl in &c.cycle_locs {
        new_tree[cl] = c.tree[cl];
    }
    let cycle_root = c.metanode_heads[cycle_head];
    new_tree[c.cycle_locs[cycle_root]] = c.noncycle_locs[cycle_head];
    new_tree
}

fn chuliu_edmonds(mut s: Mat) -> Vec<usize> {
    let mut stack: Vec<Contraction> = Vec::new();
    prepare_scores(&mut s);
    let mut tree = heads(&s);
    let mut cycles = tarjan(&tree);
    while let Some(cycle) = cycles.pop() {
        let (sub, contraction) = process_cycle(&tree, &cycle, &s);
        stack.push(contraction);
        s = sub;
        prepare_scores(&mut s);
        tree = heads(&s);
        cycles = tarjan(&tree);
    }
    while let Some(c) = stack.pop() {
        tree = expand_contracted_tree(&c, &tree);
    }
    tree
}

/// chuliu_edmonds_one_root(scores): scores[x][y] = score of y as the head of x (square, float).
/// Returns the heads as an int64 array, or None when the scores hold a NaN (the caller then
/// uses stanza's function, whose argmax treats NaN differently).
#[pyfunction]
pub fn chuliu_edmonds_one_root<'py>(py: Python<'py>, scores: PyReadonlyArray2<'py, f64>)
                                    -> PyResult<Option<Bound<'py, PyArray1<i64>>>> {
    let a = scores.as_array();
    let (r, c) = a.dim();
    if r != c || r == 0 {
        return Ok(None);
    }
    let mut v: Vec<f64> = Vec::with_capacity(r * r);
    for x in a.iter() {
        if x.is_nan() {
            return Ok(None);
        }
        v.push(*x);
    }
    let finite_min = v.iter().copied().filter(|x| x.is_finite()).fold(f64::INFINITY, f64::min);
    if !finite_min.is_finite() {
        return Ok(None);    // no finite score: let stanza raise its own error
    }
    let shift = finite_min * r as f64;
    for i in 0..r {
        v[i * r] += shift;
    }
    let tree = py.allow_threads(|| chuliu_edmonds(Mat { n: r, v }));
    let roots = tree[1..].iter().filter(|&&h| h == 0).count();
    if roots != 1 {
        return Err(PyAssertionError::new_err(
            "Rescaling by the lowest score should have prevented using multiple root edges"));
    }
    let out: Vec<i64> = tree.into_iter().map(|h| h as i64).collect();
    Ok(Some(PyArray1::from_vec(py, out)))
}
