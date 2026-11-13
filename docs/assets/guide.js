/* ATLAS guide: the live project run, the 3D stack, tabs, copy buttons, motion control. No dependencies. */
(function () {
  "use strict";
  var root = document.documentElement;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var paused = reduce;
  var $ = function (id) { return document.getElementById(id); };

  /* ── motion control: one button pauses everything that moves ── */
  var motionBtn = $("motion");
  function setPaused(p) {
    paused = p;
    root.classList.toggle("paused", p);
    if (motionBtn) { motionBtn.textContent = p ? "Play motion" : "Pause motion"; motionBtn.setAttribute("aria-pressed", String(p)); }
    var play = $("play");
    if (play) { play.textContent = p ? "Play" : "Pause"; play.setAttribute("aria-pressed", String(!p)); }
  }
  if (motionBtn) motionBtn.addEventListener("click", function () { setPaused(!paused); });

  /* ── the 3D stack leans a few degrees toward the pointer ── */
  var scene = $("scene"), stack = $("stack");
  if (scene && stack && !reduce && window.matchMedia("(pointer: fine)").matches) {
    var tx = 0, ty = 0, cx = 0, cy = 0, raf = 0;
    var tick = function () {
      cx += (tx - cx) * 0.07; cy += (ty - cy) * 0.07;
      stack.style.setProperty("--rz", (cx * 9).toFixed(2) + "deg");
      stack.style.setProperty("--rx", (-cy * 6).toFixed(2) + "deg");
      raf = Math.abs(tx - cx) + Math.abs(ty - cy) > 0.002 ? requestAnimationFrame(tick) : 0;
    };
    window.addEventListener("pointermove", function (e) {
      if (paused) return;
      tx = e.clientX / window.innerWidth - 0.5; ty = e.clientY / window.innerHeight - 0.5;
      if (!raf) raf = requestAnimationFrame(tick);
    }, { passive: true });
  }

  /* ── Atlas ticker in the hero ── */
  var watch = $("watch");
  var ticks = [
    "3 new commits on WP-04-order-form",
    "pull request #12 merged → WP-07 done",
    "CI green on main",
    "G4 passed for phase 1 (5 checks)",
    "plan is 1 requirement behind the design",
    "nothing needs you right now"
  ];
  var ti = 0;
  function nextTick() {
    if (!watch || paused) return;
    watch.textContent = ticks[ti % ticks.length]; ti++;
  }
  if (watch) { if (reduce) watch.textContent = ticks[1]; else { setTimeout(nextTick, 1800); setInterval(nextTick, 3200); } }

  /* ── the project run ── */
  var STAGES = ["define", "design", "plan", "build", "test", "handover"];
  var frames = [
    { s: 0, g: 0, state: "run", cmd: "/atlas new Bakery Orders",
      say: "Atlas creates the project and asks for the client, the size and the code repository.",
      next: "Add the client's files, then run /alice.", ev: ["atlas", "project.created", "PRJ-0001 Bakery Orders"] },
    { s: 0, g: 0, state: "run", cmd: "/alice",
      say: "Alice reads three meeting transcripts and two documents. She asks you four things she will not guess.",
      need: ["4 questions from Alice about the meetings"], next: "Answer Alice; send the proposal to the client.",
      ev: ["alice", "doc.version", "PRD v0.1 — 23 requirements"] },
    { s: 0, g: 1, state: "done", cmd: "record sign-off",
      say: "The client approves the proposal. Atlas snapshots the exact documents, and check G1 passes by itself.",
      next: "Run /stark (design).", ev: ["atlas", "gate.passed", "G1 passed (5 checks)"] },
    { s: 1, g: 2, state: "done", cmd: "/atlas go",
      say: "Stark designs the system and proposes a level of scrutiny for each module. You confirm them in one command.",
      next: "Run /jarvis (plan).", ev: ["atlas", "rigour.set", "M2 Payments → Critical"] },
    { s: 2, g: 3, state: "done", cmd: "/atlas go",
      say: "Jarvis turns the design into two phases and fourteen work packages. The blueprint lands in your repository.",
      next: "Build phase P1: 8 work packages open.", ev: ["jarvis", "doc.version", "PLAN v1.0 — 14 work packages"] },
    { s: 3, g: 3, state: "run", cmd: "git push",
      say: "You build. A teammate merges the checkout branch. Nobody updates a board.",
      phase: "P1 — 5/8 work packages done", next: "Build phase P1: 3 work packages open.",
      ev: ["atlas", "wp.inferred", "WP-07 → done (pull request #12 merged)"] },
    { s: 3, g: 4, state: "done", cmd: "atlas status",
      say: "Atlas reads the new commits, moves the work packages, and runs check G4 once the phase is built.",
      phase: "P1 — 8/8 work packages done", need: ["WP-03 (Critical) looks done — confirm once reviewed"],
      next: "Run /sentinel P1.", ev: ["atlas", "gate.passed", "G4/P1 passed (5 checks)"] },
    { s: 4, g: 5, state: "done", cmd: "/atlas go",
      say: "Sentinel writes the tests from the acceptance criteria. The client signs the acceptance script, and phase 1 ships.",
      phase: "P1 — released", next: "Build phase P2.", ev: ["atlas", "phase.released", "P1 released"] },
    { s: 5, g: 5, state: "done", cmd: "/alice handover",
      say: "Alice writes the handover pack as a PDF. The log holds every decision, sign-off and release.",
      phase: "all phases released", next: "Project complete.", ev: ["alice", "stage.finished", "Handover pack written"] }
  ];
  var track = $("track"), cmdEl = $("cmd"), sayEl = $("say"), statusEl = $("status"), logEl = $("log"), countEl = $("count");
  var fi = 0, seq = 1, timer = 0;
  var hash = function () { return Math.floor(Math.random() * 65535).toString(16).padStart(4, "0"); };
  function esc(t) { return t.replace(/&/g, "&amp;").replace(/</g, "&lt;"); }

  function render(i, quiet) {
    var f = frames[i];
    if (!track) return;
    var stations = track.querySelectorAll(".station");
    stations.forEach(function (el, n) {
      el.classList.toggle("on", n === f.s);
      el.classList.toggle("past", n < f.s);
      el.setAttribute("aria-selected", String(n === f.s));
      var gate = el.querySelector(".gate");
      if (gate) gate.classList.toggle("ok", n < f.g);
    });
    track.style.setProperty("--p", (f.s * 100 / STAGES.length).toFixed(2));
    cmdEl.textContent = f.cmd;
    sayEl.textContent = f.say;
    countEl.textContent = (i + 1) + " / " + frames.length;
    var line = STAGES.map(function (st, n) {
      var mark = n < f.s || (n === f.s && f.state === "done") ? '<span class="g">✓</span>' : n === f.s ? '<span class="r">…</span>' : '<span class="k">·</span>';
      return st + " " + mark;
    }).join(' <span class="k">·</span> ');
    var out = '<span class="k">PRJ-0001 — Bakery Orders  (Small)</span>\nStages: ' + line + "\n";
    if (f.phase) out += "Current phase: " + esc(f.phase) + "\n";
    out += f.need ? 'Needs attention:\n<span class="r">  - ' + f.need.map(esc).join("\n  - ") + "</span>\n" : '<span class="k">Needs attention: nothing.</span>\n';
    out += "Next: " + esc(f.next);
    statusEl.innerHTML = out;
    if (!quiet) {
      var row = document.createElement("div");
      row.innerHTML = "<em>#" + String(seq++).padStart(2, "0") + " " + hash() + "</em>  <b>" + f.ev[0] + "</b>  " + f.ev[1] + "  " + esc(f.ev[2]);
      logEl.appendChild(row);
      while (logEl.children.length > 4) logEl.removeChild(logEl.firstChild);
    }
  }
  function advance() { fi = (fi + 1) % frames.length; if (fi === 0) { seq = 1; logEl.innerHTML = ""; } render(fi); }
  function schedule() { clearInterval(timer); timer = setInterval(function () { if (!paused && inView) advance(); }, 3600); }

  var inView = false;
  if (track) {
    render(0);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) { inView = es[0].isIntersecting; }, { threshold: 0.25 }).observe(track.parentNode);
    } else { inView = true; }
    schedule();
    $("step").addEventListener("click", function () { advance(); schedule(); });
    $("play").addEventListener("click", function () { setPaused(!paused); });
    track.querySelectorAll(".station").forEach(function (el) {
      el.addEventListener("click", function () {
        var s = Number(el.getAttribute("data-s"));
        for (var n = frames.length - 1; n >= 0; n--) { if (frames[n].s === s) { fi = n; break; } }
        render(fi); schedule();
      });
    });
  }
  setPaused(paused);

  /* ── install tabs (arrow keys move between them) ── */
  document.querySelectorAll(".tabs").forEach(function (list) {
    var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
    function pick(tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", String(on)); t.tabIndex = on ? 0 : -1;
        document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
      });
    }
    tabs.forEach(function (tab, n) {
      tab.addEventListener("click", function () { pick(tab); });
      tab.addEventListener("keydown", function (e) {
        var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        var t = tabs[(n + d + tabs.length) % tabs.length]; pick(t); t.focus(); e.preventDefault();
      });
    });
  });

  /* ── copy buttons on code blocks ── */
  document.querySelectorAll("pre.code").forEach(function (pre) {
    var b = document.createElement("button");
    b.className = "copy-btn"; b.type = "button"; b.textContent = "Copy";
    b.setAttribute("aria-label", "Copy the commands");
    b.addEventListener("click", function () {
      var text = pre.querySelector("code").innerText.replace(/\s+#.*$/gm, "");
      var done = function (ok) { b.textContent = ok ? "Copied" : "Select and copy"; setTimeout(function () { b.textContent = "Copy"; }, 1600); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
      else done(false);
    });
    pre.appendChild(b);
  });
})();
