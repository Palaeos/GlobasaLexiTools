// libstdc++'s std::sort, for the wasm build (force-included into the files that sort
// values with ties: lttoolbox state.cc, apertium-lex-tools lrx_processor.cc).
//
// std::sort is not stable. With more than 16 elements, equal elements come out in an
// order that depends on the library's introsort: libstdc++ (the native Linux build the
// pairs were developed and checked with) and libc++ (Emscripten) differ. lt-proc's
// State::NFinals sorts all analyses by weight, so a German adjective with 40 equally
// weighted readings came out in another order, and a later first-reading choice changed
// a translation (deu-glb UDHR: "kulturali haki" vs native "kulturali Kanan").
// This is the libstdc++ algorithm (bits/stl_algo.h, stl_heap.h; unchanged since GCC 4.x),
// so the wasm tools reproduce the native order exactly.
#pragma once
#include <algorithm>
#include <deque>
#include <forward_list>
#include <functional>
#include <iostream>
#include <list>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace gnu_compat {

constexpr long kThreshold = 16;

template <class D> inline D lg(D n) {
  D k = 0;
  for (; n > 1; n >>= 1) ++k;
  return k;
}

template <class It, class C>
void g_push_heap(It first, long hole, long top, typename std::iterator_traits<It>::value_type value, C& comp) {
  long parent = (hole - 1) / 2;
  while (hole > top && comp(*(first + parent), value)) {
    *(first + hole) = std::move(*(first + parent));
    hole = parent;
    parent = (hole - 1) / 2;
  }
  *(first + hole) = std::move(value);
}

template <class It, class C>
void g_adjust_heap(It first, long hole, long len, typename std::iterator_traits<It>::value_type value, C& comp) {
  const long top = hole;
  long child = hole;
  while (child < (len - 1) / 2) {
    child = 2 * (child + 1);
    if (comp(*(first + child), *(first + (child - 1)))) child--;
    *(first + hole) = std::move(*(first + child));
    hole = child;
  }
  if ((len & 1) == 0 && child == (len - 2) / 2) {
    child = 2 * (child + 1);
    *(first + hole) = std::move(*(first + (child - 1)));
    hole = child - 1;
  }
  g_push_heap(first, hole, top, std::move(value), comp);
}

template <class It, class C> void g_make_heap(It first, It last, C& comp) {
  const long len = last - first;
  if (len < 2) return;
  long parent = (len - 2) / 2;
  while (true) {
    auto value = std::move(*(first + parent));
    g_adjust_heap(first, parent, len, std::move(value), comp);
    if (parent == 0) return;
    parent--;
  }
}

template <class It, class C> void g_pop_heap(It first, It last, It result, C& comp) {
  auto value = std::move(*result);
  *result = std::move(*first);
  g_adjust_heap(first, 0L, long(last - first), std::move(value), comp);
}

template <class It, class C> void g_partial_sort(It first, It middle, It last, C& comp) {
  g_make_heap(first, middle, comp);
  for (It i = middle; i < last; ++i)
    if (comp(*i, *first)) g_pop_heap(first, middle, i, comp);
  while (middle - first > 1) {
    --middle;
    g_pop_heap(first, middle, middle, comp);
  }
}

template <class It, class C> void g_move_median_to_first(It result, It a, It b, It c, C& comp) {
  if (comp(*a, *b)) {
    if (comp(*b, *c)) std::iter_swap(result, b);
    else if (comp(*a, *c)) std::iter_swap(result, c);
    else std::iter_swap(result, a);
  } else if (comp(*a, *c)) std::iter_swap(result, a);
  else if (comp(*b, *c)) std::iter_swap(result, c);
  else std::iter_swap(result, b);
}

template <class It, class C> It g_unguarded_partition(It first, It last, It pivot, C& comp) {
  while (true) {
    while (comp(*first, *pivot)) ++first;
    --last;
    while (comp(*pivot, *last)) --last;
    if (!(first < last)) return first;
    std::iter_swap(first, last);
    ++first;
  }
}

template <class It, class C> void g_introsort_loop(It first, It last, long depth, C& comp) {
  while (last - first > kThreshold) {
    if (depth == 0) {
      g_partial_sort(first, last, last, comp);
      return;
    }
    --depth;
    It mid = first + (last - first) / 2;
    g_move_median_to_first(first, first + 1, mid, last - 1, comp);
    It cut = g_unguarded_partition(first + 1, last, first, comp);
    g_introsort_loop(cut, last, depth, comp);
    last = cut;
  }
}

template <class It, class C> void g_unguarded_linear_insert(It last, C& comp) {
  auto val = std::move(*last);
  It next = last;
  --next;
  while (comp(val, *next)) {
    *last = std::move(*next);
    last = next;
    --next;
  }
  *last = std::move(val);
}

template <class It, class C> void g_insertion_sort(It first, It last, C& comp) {
  if (first == last) return;
  for (It i = first + 1; i != last; ++i) {
    if (comp(*i, *first)) {
      auto val = std::move(*i);
      std::move_backward(first, i, i + 1);
      *first = std::move(val);
    } else {
      g_unguarded_linear_insert(i, comp);
    }
  }
}

template <class It, class C> void g_final_insertion_sort(It first, It last, C& comp) {
  if (last - first > kThreshold) {
    g_insertion_sort(first, first + kThreshold, comp);
    for (It i = first + kThreshold; i != last; ++i) g_unguarded_linear_insert(i, comp);
  } else {
    g_insertion_sort(first, last, comp);
  }
}

}  // namespace gnu_compat

namespace std {
template <class It, class C> void gnu_compat_sort(It first, It last, C comp) {
  if (first != last) {
    gnu_compat::g_introsort_loop(first, last, gnu_compat::lg(long(last - first)) * 2, comp);
    gnu_compat::g_final_insertion_sort(first, last, comp);
  }
}
template <class It> void gnu_compat_sort(It first, It last) {
  std::less<> less;
  gnu_compat_sort(first, last, less);
}
}  // namespace std
using std::gnu_compat_sort;

// Every later "sort" token in the file (calls, and member sort() declarations and calls,
// renamed consistently) becomes gnu_compat_sort; the standard headers above are done.
#define sort gnu_compat_sort
