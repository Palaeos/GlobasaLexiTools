// Chu-Liu-Edmonds maximum spanning tree with exactly one root arc, for the in-browser parser:
// a literal port of rust/globasa_fast/src/mst.rs, itself a port of stanza's
// models/common/chuliu_edmonds.py (stanza 1.15). Every step follows the numpy original so the
// trees are identical: argmax keeps the first maximum, Tarjan finds the cycles in the same order
// and the last one is contracted first, arithmetic is element-wise in the same order (float64),
// and the cycle score uses numpy's pairwise summation. Checked by web/test/mst_check.mjs against
// stanza's trees on the exporter's score matrices.
//
// chuliuEdmondsOneRoot(scores, n): scores = Float64Array (or Float32Array, widened) n x n,
// row-major, scores[x * n + y] = score of y as the head of x; row/column 0 is ROOT.
// Returns the heads (Int32Array, tree[0] = 0).

function pairwiseSum(a, lo, hi) {
  const n = hi - lo;
  if (n < 8) {
    let res = 0.0;
    for (let i = lo; i < hi; i++) res += a[i];
    return res;
  }
  if (n <= 128) {
    const r = [a[lo], a[lo + 1], a[lo + 2], a[lo + 3], a[lo + 4], a[lo + 5], a[lo + 6], a[lo + 7]];
    let i = 8;
    for (; i < n - (n % 8); i += 8) for (let j = 0; j < 8; j++) r[j] += a[lo + i + j];
    let res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
    for (; i < n; i++) res += a[lo + i];
    return res;
  }
  let n2 = Math.floor(n / 2);
  n2 -= n2 % 8;
  return pairwiseSum(a, lo, lo + n2) + pairwiseSum(a, lo + n2, hi);
}

function argmax(len, f) {
  let best = -Infinity, bi = 0;
  for (let i = 0; i < len; i++) {
    const x = f(i);
    if (i === 0 || x > best) { best = x; bi = i; }
  }
  return bi;
}

function prepareScores(s, n) {
  for (let i = 0; i < n; i++) s[i * n + i] = -Infinity;
  for (let j = 0; j < n; j++) s[j] = -Infinity;
  s[0] = 0.0;
}

function heads(s, n) {
  const t = new Array(n);
  for (let i = 0; i < n; i++) t[i] = argmax(n, (j) => s[i * n + j]);
  return t;
}

// Tarjan's SCCs on the dependents graph (i -> j when tree[j] == i), iterative, dependents in
// ascending order: the cycles (> 1 node) as boolean masks, in the original's order.
function tarjan(tree) {
  const n = tree.length;
  const dependents = Array.from({ length: n }, () => []);
  tree.forEach((h, j) => dependents[h].push(j));
  const indices = new Array(n).fill(-1), lowlinks = new Array(n).fill(-1), onstack = new Array(n).fill(false);
  const stack = [], cycles = [];
  let counter = 0;
  for (let start = 0; start < n; start++) {
    if (indices[start] !== -1) continue;
    const callStack = [[start, null, 0]];         // (node, next dependent position, dependent just visited)
    while (callStack.length) {
      const [i, pos, jPrev] = callStack.pop();
      let k;
      if (pos === null) {
        counter += 1;
        indices[i] = counter - 1;
        lowlinks[i] = counter - 1;
        stack.push(i);
        onstack[i] = true;
        k = 0;
      } else {
        lowlinks[i] = Math.min(lowlinks[i], lowlinks[jPrev]);
        k = pos;
      }
      let descended = false;
      while (k < dependents[i].length) {
        const j = dependents[i][k];
        k += 1;
        if (indices[j] === -1) {
          callStack.push([i, k, j]);
          callStack.push([j, null, 0]);
          descended = true;
          break;
        } else if (onstack[j]) {
          lowlinks[i] = Math.min(lowlinks[i], indices[j]);
        }
      }
      if (!descended && lowlinks[i] === indices[i]) {
        const cycle = new Array(n).fill(false);
        while (stack[stack.length - 1] !== i) {
          const j = stack.pop();
          onstack[j] = false;
          cycle[j] = true;
        }
        stack.pop();
        onstack[i] = false;
        cycle[i] = true;
        if (cycle.filter(Boolean).length > 1) cycles.push(cycle);
      }
    }
  }
  return cycles;
}

// The subproblem with one cycle contracted into a metanode (last row/column).
function processCycle(tree, cycle, s, n) {
  const cycleLocs = [], noncycleLocs = [];
  for (let i = 0; i < n; i++) (cycle[i] ? cycleLocs : noncycleLocs).push(i);
  const cycleScores = Float64Array.from(cycleLocs, (c) => s[c * n + tree[c]]);
  const cycleScore = pairwiseSum(cycleScores, 0, cycleScores.length);
  const nc = cycleLocs.length, nn = noncycleLocs.length;
  const headScore = (ci, nj) => s[cycleLocs[ci] * n + noncycleLocs[nj]] - cycleScores[ci] + cycleScore;
  const depScore = (ni, cj) => s[noncycleLocs[ni] * n + cycleLocs[cj]];
  const metanodeHeads = Array.from({ length: nn }, (_, nj) => argmax(nc, (ci) => headScore(ci, nj)));
  const metanodeDeps = Array.from({ length: nn }, (_, ni) => argmax(nc, (cj) => depScore(ni, cj)));
  const m = nn + 1, sub = new Float64Array(m * m);
  for (let a = 0; a < nn; a++) for (let b = 0; b < nn; b++) sub[a * m + b] = s[noncycleLocs[a] * n + noncycleLocs[b]];
  for (let nj = 0; nj < nn; nj++) sub[nn * m + nj] = headScore(metanodeHeads[nj], nj);
  for (let ni = 0; ni < nn; ni++) sub[ni * m + nn] = depScore(ni, metanodeDeps[ni]);
  return [sub, m, { tree: tree.slice(), cycleLocs, noncycleLocs, metanodeHeads, metanodeDeps }];
}

function expandContractedTree(c, contractedTree) {
  const cycleHead = contractedTree[contractedTree.length - 1];
  const contracted = contractedTree.slice(0, -1);
  const newTree = new Array(c.tree.length).fill(-1);
  contracted.forEach((h, k) => {
    newTree[c.noncycleLocs[k]] = h < contracted.length ? c.noncycleLocs[h] : c.cycleLocs[c.metanodeDeps[k]];
  });
  for (const cl of c.cycleLocs) newTree[cl] = c.tree[cl];
  const cycleRoot = c.metanodeHeads[cycleHead];
  newTree[c.cycleLocs[cycleRoot]] = c.noncycleLocs[cycleHead];
  return newTree;
}

function chuliuEdmonds(s, n) {
  const contractions = [];
  prepareScores(s, n);
  let tree = heads(s, n);
  let cycles = tarjan(tree);
  while (cycles.length) {
    const cycle = cycles.pop();
    const [sub, m, contraction] = processCycle(tree, cycle, s, n);
    contractions.push(contraction);
    s = sub;
    n = m;
    prepareScores(s, n);
    tree = heads(s, n);
    cycles = tarjan(tree);
  }
  while (contractions.length) tree = expandContractedTree(contractions.pop(), tree);
  return tree;
}

export function chuliuEdmondsOneRoot(scores, n) {
  const v = Float64Array.from(scores);          // a copy: the caller's scores stay as they were
  if (v.length !== n * n || n === 0) throw new Error("mst: scores must be n x n");
  let finiteMin = Infinity;
  for (const x of v) {
    if (Number.isNaN(x)) throw new Error("mst: NaN score");
    if (Number.isFinite(x) && x < finiteMin) finiteMin = x;
  }
  if (!Number.isFinite(finiteMin)) throw new Error("mst: no finite score");
  const shift = finiteMin * n;
  for (let i = 0; i < n; i++) v[i * n] += shift;
  const tree = chuliuEdmonds(v, n);
  if (tree.slice(1).filter((h) => h === 0).length !== 1)
    throw new Error("Rescaling by the lowest score should have prevented using multiple root edges");
  return Int32Array.from(tree);
}
