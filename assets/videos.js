/* Technology Information — the Tutorials pages. Nothing comes from YouTube until the visitor presses play;
   chapters start the video at their time; release times show in the visitor's own time zone. */
(function () {
  "use strict";

  /* YouTube's caption codes for our two Chinese tracks */
  var CC = { "zh-CN": "zh-Hans", "zh-TW": "zh-Hant" };

  function lang() { return document.documentElement.lang || "en"; }

  function load(box, start) {
    var l = lang(), cc = CC[l] || l;
    var q = "autoplay=1&rel=0&playsinline=1&hl=" + cc;
    if (l !== "en") q += "&cc_load_policy=1&cc_lang_pref=" + cc;
    if (start) q += "&start=" + start;
    var f = document.createElement("iframe");
    /* youtube.com, not youtube-nocookie.com: without the visitor's YouTube sign-in the privacy-mode player
       asks people on shared or office networks to sign in to prove they are not a bot (seen 2026-10-27) */
    f.src = "https://www.youtube.com/embed/" + box.getAttribute("data-yt") + "?" + q;
    f.title = box.getAttribute("data-title") || "YouTube";
    f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
    f.allowFullscreen = true;
    f.referrerPolicy = "strict-origin-when-cross-origin";
    box.textContent = "";
    box.appendChild(f);
    box.classList.add("on");
  }

  var box = document.querySelector(".vplayer");
  if (box) {
    box.querySelector(".vplay").addEventListener("click", function () { load(box, 0); });
    document.querySelectorAll("[data-t]").forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        load(box, parseInt(a.getAttribute("data-t"), 10));
        box.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
  }

  /* <time data-at> → the visitor's clock; site.js rewrites the text on a language change, so redo it then */
  function times() {
    var l = lang();
    document.querySelectorAll("time[data-at]").forEach(function (t) {
      var opt = t.getAttribute("data-fmt") === "clock"
        ? { hour: "numeric", minute: "2-digit" }
        : { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" };
      try { t.textContent = new Intl.DateTimeFormat(l, opt).format(new Date(t.getAttribute("data-at"))); } catch (e) {}
    });
  }
  times();
  if ("MutationObserver" in window) {
    new MutationObserver(times).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  }
})();
