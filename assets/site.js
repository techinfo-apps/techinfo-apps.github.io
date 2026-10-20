/* Technology Information — language switch, scroll scenes, reveal on scroll.
   No trackers, no cookies. The chosen language is kept in localStorage only (it may be unavailable). */
(function () {
  "use strict";

  var LANGS = ["en", "zh-CN", "zh-TW", "ja"];
  var T = window.TI_STRINGS || {};
  var root = document.body.getAttribute("data-root") || "";

  function pickLang() {
    var saved = null;
    try { saved = localStorage.getItem("ti-lang"); } catch (e) {}
    if (saved && LANGS.indexOf(saved) >= 0) return saved;
    var want = (navigator.languages && navigator.languages[0]) || navigator.language || "en";
    want = want.toLowerCase();
    if (want.indexOf("zh") === 0) {
      return /tw|hk|mo|hant/.test(want) ? "zh-TW" : "zh-CN";
    }
    if (want.indexOf("ja") === 0) return "ja";
    return "en";
  }

  function apply(lang) {
    var dict = T[lang] || T.en || {};
    var en = T.en || {};
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var k = el.getAttribute("data-i18n");
      var v = dict[k] != null ? dict[k] : en[k];
      if (v != null) el.innerHTML = v; // our own strings only
    });
    document.querySelectorAll("[data-i18n-attr]").forEach(function (el) {
      el.getAttribute("data-i18n-attr").split(";").forEach(function (pair) {
        var p = pair.split(":"), v = dict[p[1]] != null ? dict[p[1]] : en[p[1]];
        if (v != null) el.setAttribute(p[0], v);
      });
    });
    document.querySelectorAll("[data-img]").forEach(function (el) {
      el.src = root + "assets/img/" + el.getAttribute("data-img") + "-" + lang + ".webp";
    });
    var tk = document.body.getAttribute("data-title-key");
    var title = tk && (dict[tk] != null ? dict[tk] : en[tk]);
    if (title) document.title = title;
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.setAttribute("aria-pressed", b.getAttribute("data-lang") === lang ? "true" : "false");
    });
  }

  var current = pickLang();
  apply(current);
  document.querySelectorAll(".lang button").forEach(function (b) {
    b.addEventListener("click", function () {
      current = b.getAttribute("data-lang");
      try { localStorage.setItem("ti-lang", current); } catch (e) {}
      apply(current);
    });
  });

  /* gallery tabs */
  document.querySelectorAll(".tabs").forEach(function (tabs) {
    var sec = tabs.closest("section");
    tabs.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        var i = parseInt(b.getAttribute("data-tab"), 10);
        tabs.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-selected", x === b ? "true" : "false"); });
        sec.querySelectorAll(".g").forEach(function (g, k) { g.classList.toggle("on", k === i); });
        sec.querySelectorAll(".gal-cap .c").forEach(function (c, k) { c.classList.toggle("on", k === i); });
      });
    });
  });

  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* reveal on scroll */
  var revealed = document.querySelectorAll(".reveal, .rise, .combo");
  if (reduce || !("IntersectionObserver" in window)) {
    revealed.forEach(function (el) { el.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.18 });
    revealed.forEach(function (el) { io.observe(el); });
  }

  /* scroll scenes: --p goes 0..1 while the scene's sticky stage is pinned.
     data-steps="0.2,0.45,0.7" turns --p into data-step 0..3 for step-by-step scenes. */
  var scenes = Array.prototype.slice.call(document.querySelectorAll("[data-scene]"));
  if (reduce) {
    scenes.forEach(function (s) {
      var th = s.getAttribute("data-steps");
      if (th) s.setAttribute("data-step", String(th.split(",").length));
      s.querySelectorAll("[data-step-item]").forEach(function (li) { li.classList.add("on"); });
    });
    return;
  }
  var ticking = false;
  function update() {
    ticking = false;
    var vh = window.innerHeight;
    scenes.forEach(function (s) {
      var r = s.getBoundingClientRect();
      var total = s.offsetHeight - vh;
      if (total <= 0) return;
      var p = Math.min(1, Math.max(0, -r.top / total));
      s.style.setProperty("--p", p.toFixed(4));
      var th = s.getAttribute("data-steps");
      if (th) {
        var step = 0;
        th.split(",").forEach(function (t) { if (p >= parseFloat(t)) step++; });
        if (s.getAttribute("data-step") !== String(step)) {
          s.setAttribute("data-step", String(step));
          s.querySelectorAll("[data-step-item]").forEach(function (li) {
            li.classList.toggle("on", parseInt(li.getAttribute("data-step-item"), 10) <= step);
          });
        }
      }
    });
  }
  function onScroll() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }
  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll);
  update();
})();
