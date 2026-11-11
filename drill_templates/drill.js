/* Globasa drill cards: a card per TARGET, a fresh round of items per review.
 *
 * Anki schedules the cards, so a target the learner keeps missing comes back
 * sooner: that is the adaptivity, and it syncs like any card. What the learner
 * sees must not reveal which card is up, so every card of a family has the
 * same front and every round mixes target items with others:
 *
 *   Pool field (JSON, written by DrillDeckMaker.py):
 *     {"t": [target items], "o": [items of the other targets]}
 *   A round runs until the learner answers STREAK target items in a row
 *   CLEANLY (right, first listen, not slow), or until MAX_TARGETS target items
 *   (user, 2026-11-11: a short round when the skill is there, a long one when
 *   it is not). Items are drawn one at a time; "other" items are mixed in at
 *   about 2 for every 3 targets, at random, so the card cannot be identified.
 *   (A card with no other targets yet -- a single speaker -- is all t.)
 *   After a miss the next item is a fresh one of the same shape (same list), so
 *   a mistake is followed at once by another try at the same rule or contrast.
 *   The suggested rating comes from how the streak was reached (see rating()).
 *
 * Kinds (item.k), each a renderer below:
 *   "stress"  word on screen; tap the stressed vowel.
 *             {w, s: index of the stressed vowel, why, src, shape, g?, hint?}
 *   "listen"  a recording plays; tap the spelling heard among 3.
 *             {w: spelling, a: media file, f: [[foil, contrast], ...] in the item's
 *              contrast group, x: [...] in other groups, src: speaker, shape, g?}
 *             Per showing: one foil from f (the contrast tested) and one more
 *             from the rest of f and x.
 *   "dictate" a recording plays; type what was heard (keyboard use).
 *             {w, a, src, shape: contrast group, g?}
 *
 * Front and back are rendered separately (on some clients in separate pages),
 * so the round is handed to the back through sessionStorage, with a window
 * variable as a second channel. When neither survives the flip, the back says
 * so: the front was already a complete drill.
 *
 * This file is inlined into the card templates. Anki reads double curly braces
 * as field references, so this file must never contain two opening or two
 * closing braces in a row; DrillDeckMaker.py refuses to build if it does.
 * Kept to ES5 for old Android webviews.
 */
(function () {
  var STREAK = 3;          // clean target answers in a row that end the round
  var MAX_TARGETS = 10;    // target items at most, streak or not
  var OTHER_PER_TARGET = 2 / 3;   // "other" items per target item, on average
  var OTHER_CHANCE = 0.4;  // chance of an "other" item next while under that share
  var STORE_KEY = "globasaDrillRound";
  var MAX_AGE_MS = 30 * 60 * 1000;
  var IDLE_MS = 20000;   // slower than this: most likely interrupted, not timed
  var VOWELS = "aeiou";

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }

  function button(cls, text, onClick) {
    var b = el("button", cls, text);
    b.setAttribute("type", "button");
    b.addEventListener("click", function (ev) { if (ev && ev.stopPropagation) ev.stopPropagation(); onClick(); });
    return b;
  }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function shuffle(a) {
    for (var j = a.length - 1; j > 0; j--) {
      var r = Math.floor(Math.random() * (j + 1));
      var t = a[j]; a[j] = a[r]; a[r] = t;
    }
    return a;
  }

  /* k indices of list with distinct words, skipping those in `used`, words in
   * `words` (already in the round: one clip can sit in both lists under two
   * contrasts, and hearing it twice would give the second answer away) and, if
   * given, items of another shape. */
  function draw(list, k, used, shape, words) {
    var idx = [];
    for (var i = 0; i < list.length; i++) {
      if (used[i]) continue;
      if (shape && list[i].shape !== shape) continue;
      idx.push(i);
    }
    shuffle(idx);
    var out = [], seen = {};
    for (var w in (words || {})) seen[w] = true;
    for (var j = 0; j < idx.length && out.length < k; j++) {
      var word = list[idx[j]].w;
      if (seen[word]) continue;
      seen[word] = true;
      out.push(idx[j]);
    }
    return out;
  }

  function wordsIn(pool, picks) {
    var words = {};
    for (var i = 0; i < picks.length; i++) words[pool[picks[i].l][picks[i].i].w] = true;
    return words;
  }

  function save(round) {
    window.__globasaDrillRound = round;
    try { sessionStorage.setItem(STORE_KEY, JSON.stringify(round)); } catch (e) { /* storage blocked */ }
  }

  function load(skill) {
    var round = null;
    try {
      var raw = sessionStorage.getItem(STORE_KEY);
      if (raw) round = JSON.parse(raw);
    } catch (e) { round = null; }
    if (!round) round = window.__globasaDrillRound || null;
    if (!round || round.skill !== skill) return null;
    if (Date.now() - round.t > MAX_AGE_MS) return null;
    return round;
  }

  /* {t: [...], o: [...]}; a plain array (older packages) counts as all target. */
  function readPool(root) {
    var node = root.querySelector(".drill-pool");
    var data;
    try { data = JSON.parse(node.textContent); } catch (e) { return null; }
    if (Object.prototype.toString.call(data) === "[object Array]") return { t: data, o: [] };
    if (!data || !data.t) return null;
    return { t: data.t, o: data.o || [] };
  }

  function itemOf(pool, pick) {
    return pool[pick.l][pick.i];
  }

  function countList(picks, list) {
    var n = 0;
    for (var i = 0; i < picks.length; i++) if (picks[i].l === list) n += 1;
    return n;
  }

  function usedIn(picks, list) {
    var used = {};
    for (var i = 0; i < picks.length; i++) if (picks[i].l === list) used[picks[i].i] = true;
    return used;
  }

  function seconds(ms) {
    return (Math.round(ms / 100) / 10).toFixed(1) + " s";
  }

  function letterCount(w) {
    return String(w).replace(/[^a-z]/g, "").length;
  }

  function playClip(file) {
    try {
      var a = new Audio(file);
      var p = a.play();
      if (p && p.catch) p.catch(function () { /* autoplay refused: the play button stays */ });
      return a;
    } catch (e) { return null; }
  }

  /* ---- kinds ----
   * render(item, area, ctx): builds the question, returns its answer buttons
   *   (each with data-v). ctx.answer(value) answers; ctx.timing is the clock.
   * correct(item): the right value.  speed(item, ms, replays): fast/steady/slow.
   * explain(item, answer, shown): the reason line after answering.
   * show(item): the item as listed on the back.  source(item): its origin. */

  var KINDS = {};

  /* Speed limits of every kind grow with the length of the word in letters
   * (spaces of a phrase not counted): a longer word takes longer to read, hear
   * or type. Stricter since 2026-11-11 (user); a 6-letter word gets about
   * two thirds of the earlier time. Tune after real use; the back shows every time. */
  var STRESS_FAST_BASE_MS = 500, STRESS_FAST_PER_LETTER_MS = 150;     // harita: fast <= 1.4 s
  var STRESS_SLOW_BASE_MS = 1000, STRESS_SLOW_PER_LETTER_MS = 275;    //         slow > 2.65 s

  KINDS.stress = {
    render: function (item, area, ctx) {
      if (item.hint && item.src !== "made-up") area.appendChild(el("div", "drill-hint", item.hint));
      var word = el("div", "drill-word");
      var buttons = [];
      for (var i = 0; i < item.w.length; i++) {
        var ch = item.w.charAt(i);
        if (VOWELS.indexOf(ch) >= 0) {
          var b = button("drill-letter drill-vowel", ch, (function (index) {
            return function () { ctx.answer(index); };
          })(i));
          b.setAttribute("data-v", String(i));
          buttons.push(b);
          word.appendChild(b);
        } else {
          word.appendChild(el("span", "drill-letter", ch));
        }
      }
      area.appendChild(word);
      return buttons;
    },
    value: function (b) { return Number(b.getAttribute("data-v")); },
    correct: function (item) { return item.s; },
    speed: function (item, ms) {
      var n = letterCount(item.w);
      if (ms <= STRESS_FAST_BASE_MS + STRESS_FAST_PER_LETTER_MS * n) return "fast";
      if (ms > STRESS_SLOW_BASE_MS + STRESS_SLOW_PER_LETTER_MS * n) return "slow";
      return "steady";
    },
    explain: function (item) { return item.why; },
    show: function (item) {
      var span = el("span", "drill-word drill-word-done");
      for (var i = 0; i < item.w.length; i++) {
        span.appendChild(el("span", i === item.s ? "drill-letter stressed" : "drill-letter", item.w.charAt(i)));
      }
      return span;
    },
    source: function (item) {
      if (item.src === "made-up") return "made-up word (it follows the Globasa sound rules)";
      if (item.src === "built") return "built by rule: " + item.hint + " (not in the dictionary)";
      return item.g ? item.w + ": " + item.g : item.w;
    }
  };

  /* Listening is timed from the END of the first playback (the clip's own
   * length is not the learner's time; an answer during playback counts as 0).
   * Limits grow with length: the three choices take longer to read. */
  var LISTEN_FAST_BASE_MS = 400, LISTEN_FAST_PER_LETTER_MS = 100;     // harita: fast <= 1.0 s
  var LISTEN_SLOW_BASE_MS = 800, LISTEN_SLOW_PER_LETTER_MS = 200;     //         slow > 2.0 s
  var LISTEN_FOILS = 2;

  KINDS.listen = {
    render: function (item, area, ctx) {
      var audio = null;
      var played = false;
      function play() {
        if (played) ctx.replays += 1;
        played = true;
        audio = playClip(item.a);
        if (audio && audio.addEventListener) {
          audio.addEventListener("ended", function () { ctx.heard(); });
          audio.addEventListener("error", function () { ctx.heard(); });
        } else {
          ctx.heard();
        }
      }
      ctx.replay = play;
      ctx.playButton = area.appendChild(button("drill-play", "▶ Listen again · counts as a miss", play));
      var own = shuffle(item.f.slice());
      var foils = own.slice(0, 1);
      var rest = shuffle(own.slice(1).concat(item.x || []));
      for (var r = 0; foils.length < LISTEN_FOILS && r < rest.length; r++) {
        if (rest[r][0] !== foils[0][0]) foils.push(rest[r]);
      }
      var options = [item.w];
      for (var i = 0; i < foils.length; i++) options.push(foils[i][0]);
      shuffle(options);
      ctx.shown = foils;
      var row = el("div", "drill-options");
      var buttons = [];
      for (var j = 0; j < options.length; j++) {
        var b = button("drill-option", options[j], (function (v) {
          return function () { ctx.answer(v); };
        })(options[j]));
        b.setAttribute("data-v", options[j]);
        buttons.push(b);
        row.appendChild(b);
      }
      area.appendChild(row);
      play();
      return buttons;
    },
    value: function (b) { return b.getAttribute("data-v"); },
    correct: function (item) { return item.w; },
    speed: function (item, ms, replays) {
      var n = letterCount(item.w);
      if (ms > LISTEN_SLOW_BASE_MS + LISTEN_SLOW_PER_LETTER_MS * n) return "slow";
      if (ms <= LISTEN_FAST_BASE_MS + LISTEN_FAST_PER_LETTER_MS * n && !replays) return "fast";
      return "steady";
    },
    explain: function (item, answer, shown) {
      var list = shown || item.f;
      if (answer !== item.w) {
        var all = item.f.concat(item.x || []);
        for (var i = 0; i < all.length; i++) {
          if (all[i][0] === answer) return "heard " + item.w + ", not " + answer + ": " + all[i][1];
        }
        return "heard " + item.w + ", not " + answer;
      }
      var parts = [];
      for (var j = 0; j < list.length; j++) parts.push(list[j][0] + " (" + list[j][1] + ")");
      return "heard " + item.w + (parts.length ? "; the others were " + parts.join(", ") : "");
    },
    show: function (item) {
      var span = el("span", "drill-word drill-word-done");
      span.appendChild(button("drill-play-small", "▶", function () { playClip(item.a); }));
      span.appendChild(el("span", "", " " + item.w));
      return span;
    },
    source: function (item) {
      return "recorded by " + item.src + (item.g ? " · " + item.w + ": " + item.g : "");
    }
  };

  /* Dictation (typed; meant for a keyboard): the clip plays, the learner types
   * what was heard, Enter checks. Any difference is a mistake; the back aligns
   * the typing with the word letter by letter and names each sound confused.
   * Timed from the end of the first playback to Enter, with limits that grow
   * with the length of the word (typing takes longer than tapping). In the
   * answer box Enter checks and ↑ plays the clip again, so typed n and p stay
   * letters; once checked, the usual keys apply. */
  var DICTATE_FAST_BASE_MS = 700, DICTATE_FAST_PER_LETTER_MS = 200;    // harita: fast <= 1.9 s
  var DICTATE_SLOW_BASE_MS = 1800, DICTATE_SLOW_PER_LETTER_MS = 400;   //         slow > 4.2 s

  var SOUNDS = {
    a: "a [a]", e: "e [e]", i: "i [i]", o: "o [o]", u: "u [u]",
    b: "b", c: "c [tʃ] (ch)", d: "d", f: "f", g: "g [g] (hard)", h: "h", j: "j [dʒ] (j in jam)",
    k: "k", l: "l [l]", m: "m", n: "n", p: "p", r: "r [ɾ] (tapped)", s: "s [s]", t: "t",
    v: "v", w: "w", x: "x [ʃ] (sh)", y: "y", z: "z [z]"
  };

  function soundOf(ch) {
    return SOUNDS[ch] || ch;
  }

  function normalizeTyped(text) {
    return String(text || "").toLowerCase().replace(/\s+/g, " ").replace(/^ | $/g, "");
  }

  /* Letter alignment of typed against right (edit distance):
   * [{op: "same"|"sub"|"miss"|"extra", r: right letter, t: typed letter}] */
  function align(right, typed) {
    var n = right.length, m = typed.length, d = [], i, j;
    for (i = 0; i <= n; i++) { d.push([]); for (j = 0; j <= m; j++) d[i].push(i === 0 ? j : (j === 0 ? i : 0)); }
    for (i = 1; i <= n; i++) {
      for (j = 1; j <= m; j++) {
        var cost = right.charAt(i - 1) === typed.charAt(j - 1) ? 0 : 1;
        d[i][j] = Math.min(d[i - 1][j - 1] + cost, d[i - 1][j] + 1, d[i][j - 1] + 1);
      }
    }
    var ops = [];
    i = n; j = m;
    while (i > 0 || j > 0) {
      if (i > 0 && j > 0 && d[i][j] === d[i - 1][j - 1] + (right.charAt(i - 1) === typed.charAt(j - 1) ? 0 : 1)) {
        ops.unshift({ op: right.charAt(i - 1) === typed.charAt(j - 1) ? "same" : "sub", r: right.charAt(i - 1), t: typed.charAt(j - 1) });
        i -= 1; j -= 1;
      } else if (i > 0 && d[i][j] === d[i - 1][j] + 1) {
        ops.unshift({ op: "miss", r: right.charAt(i - 1), t: "" });
        i -= 1;
      } else {
        ops.unshift({ op: "extra", r: "", t: typed.charAt(j - 1) });
        j -= 1;
      }
    }
    return ops;
  }

  function diffView(right, typed) {
    var box = el("div", "drill-diff");
    var ops = align(right, typed);
    var rRow = el("div", "drill-diff-row");
    var tRow = el("div", "drill-diff-row");
    rRow.appendChild(el("span", "drill-diff-label", "heard"));
    tRow.appendChild(el("span", "drill-diff-label", "typed"));
    for (var i = 0; i < ops.length; i++) {
      var o = ops[i];
      rRow.appendChild(el("span", "drill-diff-ch " + o.op, o.r === " " ? "·" : (o.r || "·")));
      tRow.appendChild(el("span", "drill-diff-ch " + o.op, o.t === " " ? "·" : (o.t || "·")));
    }
    box.appendChild(rRow);
    box.appendChild(tRow);
    return box;
  }

  KINDS.dictate = {
    render: function (item, area, ctx) {
      var played = false;
      function play() {
        if (played) ctx.replays += 1;
        played = true;
        var audio = playClip(item.a);
        if (audio && audio.addEventListener) {
          audio.addEventListener("ended", function () { ctx.heard(); });
          audio.addEventListener("error", function () { ctx.heard(); });
        } else {
          ctx.heard();
        }
      }
      ctx.replay = play;
      ctx.playButton = area.appendChild(button("drill-play", "▶ Listen again (↑) · counts as a miss", play));
      var row = el("div", "drill-typed-row");
      var input = el("input", "drill-typed");
      input.setAttribute("type", "text");
      input.setAttribute("autocomplete", "off");
      input.setAttribute("autocapitalize", "off");
      input.setAttribute("autocorrect", "off");
      input.setAttribute("spellcheck", "false");
      input.setAttribute("aria-label", "Type what you hear");
      function check() { if (!input.disabled) ctx.answer(normalizeTyped(input.value)); }
      input.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter") { if (ev.preventDefault) ev.preventDefault(); if (ev.stopPropagation) ev.stopPropagation(); check(); }
        else if (ev.key === "ArrowUp") { if (ev.preventDefault) ev.preventDefault(); play(); }
      });
      row.appendChild(input);
      row.appendChild(button("drill-check", "Check", check));
      area.appendChild(row);
      ctx.onAnswered = function () { input.disabled = true; if (input.blur) input.blur(); };
      ctx.typeInto = function (text) { input.value = text; };   // for tests
      play();
      setTimeout(function () { if (input.focus) input.focus(); }, 0);
      return [];
    },
    value: function () { return null; },
    correct: function (item) { return item.w; },
    speed: function (item, ms, replays) {
      var n = letterCount(item.w);
      if (ms > DICTATE_SLOW_BASE_MS + DICTATE_SLOW_PER_LETTER_MS * n) return "slow";
      if (ms <= DICTATE_FAST_BASE_MS + DICTATE_FAST_PER_LETTER_MS * n && !replays) return "fast";
      return "steady";
    },
    explain: function (item, answer) {
      if (answer === item.w) return "heard " + item.w;
      if (!answer) return "nothing typed; heard " + item.w;
      var ops = align(item.w, answer);
      var parts = [];
      for (var i = 0; i < ops.length; i++) {
        var o = ops[i];
        if (o.op === "sub") parts.push(soundOf(o.r) + ", you typed " + soundOf(o.t));
        else if (o.op === "miss") parts.push(o.r === " " ? "a word break was missed" : soundOf(o.r) + " was missed");
        else if (o.op === "extra") parts.push(o.t === " " ? "no word break there" : "no " + soundOf(o.t) + " there");
      }
      return "heard " + item.w + ": " + parts.join("; ");
    },
    detail: function (item, answer) {
      return answer === item.w ? null : diffView(item.w, answer || "");
    },
    show: function (item) { return KINDS.listen.show(item); },
    source: function (item) { return KINDS.listen.source(item); }
  };

  function kindOf(item) {
    return KINDS[item.k] || KINDS.stress;
  }

  function isCorrect(item, answer) {
    return answer === kindOf(item).correct(item);
  }

  /* The goal of the listening drills is understanding a recording WITHOUT
   * rewinding it, so a replay before answering is a miss even when the answer
   * is right ("needed a second listen"): it counts against the rating and is
   * followed by a retry like any miss. Replays after answering are free. Only
   * recordings can be replayed, so this never touches the stress drill. */
  function passed(item, answer, replays) {
    return isCorrect(item, answer) && !replays;
  }

  function verdict(item, answer, replays) {
    if (!isCorrect(item, answer)) return { cls: "bad", sym: "✗", text: "" };
    if (replays) return { cls: "bad", sym: "↻", text: "right, but after a second listen: counts as a miss" };
    return { cls: "ok", sym: "✓", text: "" };
  }

  function speed(item, ms, replays) {
    if (ms === undefined || ms === null || ms > IDLE_MS) return "unknown";
    return kindOf(item).speed(item, ms, replays || 0);
  }

  /* The round so far, replayed from its answers -- the single source for when
   * the round ends (front) and for the rating (back). A target answer is clean
   * when right, at the first listen and not slow; a miss or a slow answer ends
   * the streak; an answer over IDLE_MS (an interruption) neither adds to it nor
   * ends it. Other items never touch the streak. */
  function progress(pool, round) {
    var p = { targets: 0, streak: 0, reached: false, right: 0, mistakes: 0, relistens: 0,
              slow: 0, fast: 0, unknown: 0, passes: 0, answered: 0, done: false };
    var times = round.times || [];
    var replays = round.replays || [];
    for (var i = 0; i < round.picks.length && i < round.answers.length; i++) {
      var item = itemOf(pool, round.picks[i]);
      var ok = isCorrect(item, round.answers[i]);
      var pass = ok && !replays[i];
      p.answered += 1;
      if (pass) p.passes += 1;
      if (round.picks[i].l !== "t") continue;
      p.targets += 1;
      if (!ok) { p.mistakes += 1; p.streak = 0; continue; }
      if (!pass) { p.mistakes += 1; p.relistens += 1; p.streak = 0; continue; }
      p.right += 1;
      var sp = speed(item, times[i], replays[i]);
      if (sp === "slow") { p.slow += 1; p.streak = 0; continue; }
      if (sp === "unknown") { p.unknown += 1; continue; }
      if (sp === "fast") p.fast += 1;
      p.streak += 1;
      if (p.streak >= STREAK) p.reached = true;
    }
    p.done = p.reached || p.targets >= MAX_TARGETS || !!round.exhausted;
    return p;
  }

  function missText(p) {
    var wrong = p.mistakes - p.relistens, parts = [];
    if (wrong) parts.push(wrong === 1 ? "1 mistake" : wrong + " mistakes");
    if (p.relistens) parts.push(p.relistens === 1 ? "1 second listen" : p.relistens + " second listens");
    if (p.slow) parts.push(p.slow === 1 ? "1 slow answer" : p.slow + " slow answers");
    return parts.join(", ");
  }

  /* How the streak was reached -> suggested rating and the reason for it.
   *   streak, no misses, every answer fast   Easy
   *   streak, no misses (none slow)          Good
   *   streak after misses or slow answers    Hard
   *   no streak within MAX_TARGETS           Again
   * A second listen counts as a miss; a slow answer breaks the streak. */
  function rating(p) {
    var inRow = STREAK + " in a row";
    if (!p.reached) {
      if (p.targets >= MAX_TARGETS) return { r: "Again", why: "no " + inRow + " in " + MAX_TARGETS + " items" };
      return { r: "Again", why: "round not finished" };
    }
    if (p.mistakes || p.slow) return { r: "Hard", why: inRow + " after " + missText(p) };
    if (p.fast === p.right - p.unknown) return { r: "Easy", why: inRow + ", no misses, every answer fast" };
    return { r: "Good", why: inRow + ", no misses" };
  }

  /* ---- front ---- */

  function front(root) {
    var skill = root.getAttribute("data-skill");
    var stage = root.querySelector(".drill-stage");
    var pool = readPool(root);
    if (!pool || !pool.t.length) {
      stage.appendChild(el("p", "drill-error", "This drill has no items (the Pool field is empty or not valid JSON)."));
      return;
    }
    var round = { skill: skill, picks: [], answers: [], times: [], replays: [], shown: [], t: Date.now() };
    var pos = 0;
    var missed = null;   // {l, shape} of the last miss: the next item retries it

    /* The next item: after a miss, a fresh one of the same shape from the same
     * list; otherwise an "other" item now and then (while under its share), else
     * a target. Never a word already in the round. A missed "other" item is
     * retried only while others are under their share, so misses on items that
     * do not count cannot stretch the round. */
    function nextPick() {
      var targets = 0, others = 0;
      for (var i = 0; i < round.picks.length; i++) {
        if (round.picks[i].l === "t") targets += 1; else others += 1;
      }
      var words = wordsIn(pool, round.picks);
      var room = others < Math.ceil((targets + 1) * OTHER_PER_TARGET);
      if (missed && missed.l === "o" && !room) missed = null;
      if (missed) {
        var again = draw(pool[missed.l], 1, usedIn(round.picks, missed.l), missed.shape, words);
        var list = missed.l;
        missed = null;
        if (again.length) return { l: list, i: again[0], retry: true };
      }
      var order = pool.o.length && room && Math.random() < OTHER_CHANCE ? ["o", "t"] : ["t", "o"];
      for (var k = 0; k < order.length; k++) {
        if (order[k] === "o" && !pool.o.length) continue;
        var fresh = draw(pool[order[k]], 1, usedIn(round.picks, order[k]), null, words);
        if (fresh.length) return { l: order[k], i: fresh[0] };
      }
      return null;
    }

    function show() {
      clear(stage);
      if (progress(pool, round).done) return summary();
      var pick = nextPick();
      if (!pick) { round.exhausted = true; save(round); return summary(); }
      round.picks.push(pick);
      save(round);
      var item = itemOf(pool, pick);
      var kind = kindOf(item);
      var ctx = { replays: 0, shown: null, replay: null, origin: Date.now(), heardOnce: false };
      ctx.heard = function () { if (!ctx.heardOnce) { ctx.heardOnce = true; ctx.origin = Date.now(); } };
      // No total: the round ends on a streak, and counting it would show which items count.
      stage.appendChild(el("div", "drill-counter", "item " + (pos + 1)));
      var area = el("div", "drill-question");
      stage.appendChild(area);
      var feedback = el("div", "drill-feedback");
      stage.appendChild(feedback);

      ctx.answer = function (value) {
        if (round.answers.length > pos) return;
        round.answers.push(value);
        round.times.push(Math.max(0, Date.now() - ctx.origin));
        round.replays.push(ctx.replays);
        round.shown.push(ctx.shown);
        var pass = passed(item, value, ctx.replays);
        var done = progress(pool, round).done;
        if (!pass && !done) missed = { l: pick.l, shape: item.shape };
        save(round);
        var retryLikely = missed && (missed.l === "t" || round.picks.length < 2 ||
          countList(round.picks, "o") < Math.ceil((countList(round.picks, "t") + 1) * OTHER_PER_TARGET));
        var right = kind.correct(item);
        for (var j = 0; j < buttons.length; j++) {
          var v = kind.value(buttons[j]);
          buttons[j].disabled = true;
          if (v === right) buttons[j].className += " correct";
          else if (v === value) buttons[j].className += " wrong";
        }
        if (ctx.onAnswered) ctx.onAnswered();
        if (ctx.playButton) ctx.playButton.textContent = "▶ Listen again";   // free from now on
        var vd = verdict(item, value, ctx.replays);
        feedback.appendChild(el("div", "drill-verdict " + vd.cls, vd.sym));
        if (vd.text) feedback.appendChild(el("div", "drill-relisten", vd.text));
        var detail = kind.detail ? kind.detail(item, value) : null;
        if (detail) feedback.appendChild(detail);
        feedback.appendChild(el("div", "drill-why", kind.explain(item, value, ctx.shown)));
        feedback.appendChild(el("div", "drill-source", kind.source(item)));
        if (retryLikely) feedback.appendChild(el("div", "drill-retry", "Next: another one of this kind."));
        feedback.appendChild(button("drill-next", done ? "Finish" : "Next →", advance));
      };

      var buttons = kind.render(item, area, ctx);

      function advance() {
        if (round.answers.length <= pos) return;
        pos += 1;
        show();
      }

      window.__globasaDrillKeys = {
        pick: function (n) { if (n >= 1 && n <= buttons.length) ctx.answer(kind.value(buttons[n - 1])); },
        next: advance,
        replay: function () { if (ctx.replay) ctx.replay(); }
      };
    }

    function summary() {
      window.__globasaDrillKeys = null;
      var p = progress(pool, round);
      stage.appendChild(el("div", "drill-score", p.reached ? STREAK + " in a row" : "no streak yet"));
      stage.appendChild(el("div", "drill-suggest", "Show the answer to rate: suggested " + rating(p).r + "."));
    }

    show();
  }

  /* ---- back ---- */

  function resultItem(pool, round, i) {
    var item = itemOf(pool, round.picks[i]);
    var kind = kindOf(item);
    var answered = i < round.answers.length;
    var times = round.times || [];
    var replays = round.replays || [];
    var ok = answered && passed(item, round.answers[i], replays[i]);
    var vd = answered ? verdict(item, round.answers[i], replays[i]) : { cls: "bad", sym: "–", text: "" };
    var li = el("li", ok ? "ok" : "bad");
    li.appendChild(el("span", "drill-verdict " + vd.cls, vd.sym));
    li.appendChild(kind.show(item));
    if (answered && times[i] !== undefined) {
      var sp = speed(item, times[i], replays[i]);
      // Speed is only judged on right answers; a wrong one shows its time alone.
      var label = ok && sp !== "steady" ? seconds(times[i]) + " · " + (sp === "unknown" ? "not timed (paused)" : sp) : seconds(times[i]);
      li.appendChild(el("span", "drill-time" + (ok ? " " + sp : ""), label));
    }
    if (replays[i]) li.appendChild(el("span", "drill-tag bad", replays[i] === 1 ? "second listen" : "listened " + (replays[i] + 1) + " times"));
    if (round.picks[i].retry) li.appendChild(el("span", "drill-tag", "retry"));
    if (answered && kind.detail) {
      var detail = kind.detail(item, round.answers[i]);
      if (detail) li.appendChild(detail);
    }
    if (answered) li.appendChild(el("div", "drill-why", kind.explain(item, round.answers[i], (round.shown || [])[i])));
    li.appendChild(el("div", "drill-source", kind.source(item)));
    return li;
  }

  function back(root) {
    window.__globasaDrillKeys = null;
    var skill = root.getAttribute("data-skill");
    var out = root.querySelector(".drill-summary");
    var pool = readPool(root);
    var round = load(skill);
    if (!pool || !round) {
      out.appendChild(el("p", "drill-note", "This Anki app did not pass the round to the answer side. Rate the card on how the round went on the front."));
      return;
    }
    var p = progress(pool, round);
    var rt = rating(p);
    out.appendChild(el("div", "drill-score", p.reached
      ? STREAK + " in a row after " + p.targets + (p.targets === 1 ? " item" : " items")
      : "no " + STREAK + " in a row (" + p.targets + (p.targets === 1 ? " item" : " items") + ")"));
    out.appendChild(el("div", "drill-suggest", "Suggested rating: " + rt.r + " (" + rt.why + ")"));
    var counted = el("ol", "drill-results");
    var also = el("ol", "drill-results");
    for (var i = 0; i < round.picks.length && i < round.answers.length; i++) {
      (round.picks[i].l === "t" ? counted : also).appendChild(resultItem(pool, round, i));
    }
    out.appendChild(el("div", "drill-section", "Counted for the rating"));
    out.appendChild(counted);
    if (also.firstChild) {
      out.appendChild(el("div", "drill-section", "Also in this round"));
      out.appendChild(also);
    }
  }

  /* Number keys pick the n-th answer button, p plays the recording again,
   * n or → goes on. Only while a front is showing: the back clears the hook, so
   * Anki's own 1-4 rating keys are untouched. (Anki's r replays [sound:] tags
   * only; these clips play from script, hence p.) */
  if (!window.__globasaDrillKeyListener) {
    window.__globasaDrillKeyListener = true;
    document.addEventListener("keydown", function (ev) {
      var k = window.__globasaDrillKeys;
      if (!k || !document.querySelector(".drill-stage")) return;
      // Typing in a dictation box: its own handler takes Enter and ↑; letters stay letters.
      var tag = ev.target && ev.target.tagName ? String(ev.target.tagName).toUpperCase() : "";
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (ev.key >= "1" && ev.key <= "9") { k.pick(Number(ev.key)); }
      else if (ev.key === "n" || ev.key === "ArrowRight") { k.next(); }
      else if (ev.key === "p") { k.replay(); }
    });
  }

  window.GlobasaDrill = { front: front, back: back, rating: rating, progress: progress, speed: speed, readPool: readPool,
                          align: align, normalizeTyped: normalizeTyped };
})();
