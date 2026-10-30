#!/usr/bin/env python3
"""Builds the Tutorials section from videos/_data/<series>.json: the overview page /videos/, a page per episode
in each of the seven languages, assets/videos-strings.js and videos/sitemap.xml.

An episode goes up only once YouTube says it is public (oEmbed answers 200; a scheduled video answers 401/403).
What went up stays up: a failed check changes nothing. Runs on the Mac and in the daily GitHub workflow.

  python3 tools/build_videos.py            # ask YouTube about episodes not up yet, then build
  python3 tools/build_videos.py --offline  # build from videos/_data/status.json only
"""
import argparse
import datetime as dt
import html
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "videos/_data"
STATUS = DATA / "status.json"
BASE = "https://techinfo-apps.github.io/"
CHANNEL = "https://www.youtube.com/@TechInForFree"
BEIJING = dt.timezone(dt.timedelta(hours=8))

LANGS = ["en", "zh-CN", "zh-TW", "ja", "ko", "es", "fr"]
HREFLANG = {"en": "en", "zh-CN": "zh-Hans", "zh-TW": "zh-Hant", "ja": "ja", "ko": "ko", "es": "es", "fr": "fr"}
SLUG = {l: "" if l == "en" else l.lower() + "/" for l in LANGS}
ZH_NUM = "零一二三四五六七八九十"

# Text of the Tutorials pages. {time} becomes a <time> the visitor sees in their own time zone (assets/videos.js).
# The slogan “no ads, ever” is about our apps; the videos may carry YouTube ads one day, so these pages never use it.
UI = {
"en": {
 "title": "Free tutorials — Technology Information", "h": "Free tutorials.",
 "lead": "How computers really work, built up one step at a time. Every picture is computed by code; the narration is an AI voice.",
 "desc": "Free video tutorials from Technology Information: how computers really work, from a single switch to a whole CPU.",
 "season": "Season {n}", "progress": "{n} of {total} episodes out", "daily": "A new episode every day at {time}.",
 "done": "All {total} episodes are out.", "next": "Episode {n} comes out {time}", "soon": "Episode {n} is coming soon",
 "ep": "Episode {n}", "min": "{m} min", "new": "New", "watch": "Watch on YouTube", "sub": "Subscribe on YouTube",
 "season_yt": "Whole season on YouTube", "play": "Play", "loads": "Pressing play loads the video from YouTube.",
 "chapters": "Chapters", "transcript": "Transcript", "prev": "Previous", "nextep": "Next", "all": "All episodes",
},
"zh-CN": {
 "title": "免费教程 — Technology Information", "h": "免费教程。",
 "lead": "电脑到底是怎么工作的，一步一步搭起来讲。每个画面都是代码算出来的，旁白是 AI 配音。",
 "desc": "Technology Information 的免费视频教程：电脑到底是怎么工作的，从一个开关讲到整颗 CPU。",
 "season": "第{zh}季", "progress": "已更新 {n} / {total} 集", "daily": "每天 {time} 更新一集。",
 "done": "全部 {total} 集已经出齐。", "next": "第 {n} 集 {time} 上线", "soon": "第 {n} 集很快上线",
 "ep": "第 {n} 集", "min": "{m} 分钟", "new": "新", "watch": "在 YouTube 上看", "sub": "在 YouTube 上订阅",
 "season_yt": "在 YouTube 上看整季", "play": "播放", "loads": "按下播放后，视频从 YouTube 加载。",
 "chapters": "章节", "transcript": "文字稿", "prev": "上一集", "nextep": "下一集", "all": "全部视频",
},
"zh-TW": {
 "title": "免費教學 — Technology Information", "h": "免費教學。",
 "lead": "電腦到底是怎麼運作的，一步一步搭起來講。每個畫面都是程式算出來的，旁白是 AI 配音。",
 "desc": "Technology Information 的免費影片教學：電腦到底是怎麼運作的，從一個開關講到整顆 CPU。",
 "season": "第{zh}季", "progress": "已更新 {n} / {total} 集", "daily": "每天 {time} 更新一集。",
 "done": "全部 {total} 集已經出齊。", "next": "第 {n} 集 {time} 上線", "soon": "第 {n} 集很快上線",
 "ep": "第 {n} 集", "min": "{m} 分鐘", "new": "新", "watch": "在 YouTube 上看", "sub": "在 YouTube 上訂閱",
 "season_yt": "在 YouTube 上看整季", "play": "播放", "loads": "按下播放後，影片從 YouTube 載入。",
 "chapters": "章節", "transcript": "文字稿", "prev": "上一集", "nextep": "下一集", "all": "全部影片",
},
"ja": {
 "title": "無料チュートリアル — Technology Information", "h": "無料チュートリアル。",
 "lead": "コンピューターが本当はどう動いているのかを、一歩ずつ組み立てながら解説します。画面はすべてコードで計算して描き、ナレーションはAI音声です。",
 "desc": "Technology Informationの無料動画チュートリアル。スイッチ1つからCPUまで、コンピューターが本当はどう動いているのかを解説します。",
 "season": "シーズン{n}", "progress": "全{total}話のうち{n}話を公開中", "daily": "毎日 {time} に新しい回を公開します。",
 "done": "全{total}話、公開しました。", "next": "第{n}話は {time} に公開", "soon": "第{n}話はまもなく公開",
 "ep": "第{n}話", "min": "{m}分", "new": "新着", "watch": "YouTubeで見る", "sub": "YouTubeでチャンネル登録",
 "season_yt": "YouTubeでシーズン全体を見る", "play": "再生", "loads": "再生を押すと、動画をYouTubeから読み込みます。",
 "chapters": "チャプター", "transcript": "ナレーション全文", "prev": "前の回", "nextep": "次の回", "all": "すべての回",
},
"ko": {
 "title": "무료 강좌 — Technology Information", "h": "무료 강좌.",
 "lead": "컴퓨터가 실제로 어떻게 동작하는지, 한 단계씩 쌓아 올리며 설명합니다. 모든 화면은 코드로 계산해 그렸고, 내레이션은 AI 음성입니다.",
 "desc": "Technology Information의 무료 영상 강좌: 스위치 하나에서 CPU까지, 컴퓨터가 실제로 어떻게 동작하는지 설명합니다.",
 "season": "시즌 {n}", "progress": "전체 {total}편 중 {n}편 공개", "daily": "매일 {time}에 새 편이 올라옵니다.",
 "done": "{total}편이 모두 공개되었습니다.", "next": "{n}편은 {time}에 공개", "soon": "{n}편이 곧 공개됩니다",
 "ep": "{n}편", "min": "{m}분", "new": "새 편", "watch": "YouTube에서 보기", "sub": "YouTube에서 구독",
 "season_yt": "YouTube에서 시즌 전체 보기", "play": "재생", "loads": "재생을 누르면 YouTube에서 영상을 불러옵니다.",
 "chapters": "챕터", "transcript": "전체 대본", "prev": "이전 편", "nextep": "다음 편", "all": "전체 목록",
},
"es": {
 "title": "Tutoriales gratis — Technology Information", "h": "Tutoriales gratis.",
 "lead": "Cómo funcionan de verdad las computadoras, paso a paso. Cada imagen la calcula el código; la narración es una voz de IA.",
 "desc": "Tutoriales en video gratis de Technology Information: cómo funcionan de verdad las computadoras, de un interruptor a una CPU.",
 "season": "Temporada {n}", "progress": "{n} de {total} episodios publicados", "daily": "Un episodio nuevo cada día a las {time}.",
 "done": "Ya están los {total} episodios.", "next": "El episodio {n} sale el {time}", "soon": "El episodio {n} sale pronto",
 "ep": "Episodio {n}", "min": "{m} min", "new": "Nuevo", "watch": "Ver en YouTube", "sub": "Suscribirse en YouTube",
 "season_yt": "Toda la temporada en YouTube", "play": "Reproducir", "loads": "Al pulsar reproducir, el video se carga desde YouTube.",
 "chapters": "Capítulos", "transcript": "Transcripción", "prev": "Anterior", "nextep": "Siguiente", "all": "Todos los episodios",
},
"fr": {
 "title": "Tutoriels gratuits — Technology Information", "h": "Tutoriels gratuits.",
 "lead": "Comment un ordinateur fonctionne vraiment, construit pas à pas. Chaque image est calculée par le code ; la narration est une voix d'IA.",
 "desc": "Tutoriels vidéo gratuits de Technology Information : comment un ordinateur fonctionne vraiment, d'un interrupteur à un processeur.",
 "season": "Saison {n}", "progress": "{n} épisodes sur {total} en ligne", "daily": "Un nouvel épisode chaque jour à {time}.",
 "done": "Les {total} épisodes sont en ligne.", "next": "L'épisode {n} sort le {time}", "soon": "L'épisode {n} arrive bientôt",
 "ep": "Épisode {n}", "min": "{m} min", "new": "Nouveau", "watch": "Regarder sur YouTube", "sub": "S'abonner sur YouTube",
 "season_yt": "Toute la saison sur YouTube", "play": "Lire", "loads": "En appuyant sur lecture, la vidéo se charge depuis YouTube.",
 "chapters": "Chapitres", "transcript": "Transcription", "prev": "Précédent", "nextep": "Suivant", "all": "Tous les épisodes",
},
}

E = html.escape
PLAY_SVG = '<svg viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z"/></svg>'


def fmt(lang, key, **kw):
    if "n" in kw:
        kw.setdefault("zh", ZH_NUM[kw["n"]] if kw["n"] <= 10 else str(kw["n"]))
    return UI[lang][key].format(**kw)


def time_tag(at, kind):
    """A <time> that videos.js rewrites in the visitor's time zone; without script it reads in Beijing time."""
    d = dt.datetime.fromisoformat(at).astimezone(BEIJING)
    text = d.strftime("%H:%M") if kind == "clock" else d.strftime("%m-%d %H:%M")
    return f'<time datetime="{E(at)}" data-at="{E(at)}" data-fmt="{kind}">{text} (UTC+8)</time>'


def clock(sec):
    return f"{sec // 60}:{sec % 60:02d}"


def is_public(video_id):
    url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://youtu.be/{video_id}")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=15) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 404):
            return False
        return None
    except Exception:
        return None


# ---------- shared page parts ----------

def nav(root):
    return f"""<header class="nav">
  <div class="wrap">
    <a class="brand" href="{root}">Technology Information</a>
    <nav class="links">
      <a href="{root}unitctrl/" data-i18n="nav.unitctrl">UnitCtrl</a>
      <a href="{root}broomy/" data-i18n="nav.broomy">Broomy</a>
      <a href="{root}#unitplayer" data-i18n="nav.unitplayer">UnitPlayer</a>
      <a href="{root}aiban/" data-i18n="nav.aiban">AI Ban Simulator</a>
      <a href="{root}videos/" data-i18n="nav.videos">Tutorials</a>
    </nav>
    <label class="lang">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9M12 3c-2.5 2.7-3.8 5.7-3.8 9s1.3 6.3 3.8 9"/></svg>
      <select class="lang-pick" aria-label="Language">
        <option value="en" lang="en">English</option>
        <option value="zh-CN" lang="zh-CN">简体中文</option>
        <option value="zh-TW" lang="zh-TW">繁體中文</option>
        <option value="ja" lang="ja">日本語</option>
        <option value="ko" lang="ko">한국어</option>
        <option value="es" lang="es">Español</option>
        <option value="fr" lang="fr">Français</option>
      </select>
    </label>
  </div>
</header>"""


def foot(root, scripts):
    tags = "\n".join(f'<script src="{root}assets/{s}"></script>' for s in scripts)
    return f"""<footer class="foot">
  <div class="wrap">
    <span class="social">
      <a class="ico" href="{CHANNEL}" rel="noopener" aria-label="YouTube" title="YouTube"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31.3 31.3 0 0 0 0 12a31.3 31.3 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31.3 31.3 0 0 0 24 12a31.3 31.3 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z"/></svg></a>
      <a class="ico" href="https://x.com/TechInfoApps" rel="noopener" aria-label="X" title="X"><svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>
      <a class="ico" href="mailto:techinfor404@gmail.com" data-i18n-attr="aria-label:foot.contact" aria-label="Contact" title="techinfor404@gmail.com"><svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 6.5 8.5 6.5 8.5-6.5"/></svg></a>
    </span>
    <button class="coffee-link" type="button" data-open="coffee"><img src="{root}assets/img/coffee-cup.png" alt="" width="18" height="18"><span data-i18n="coffee.link">Buy the Developer a Coffee…</span></button>
    <span class="copy">© 2026 Technology Information</span>
  </div>
</footer>

<dialog id="coffee" class="coffee" aria-labelledby="coffee-h">
  <form method="dialog" class="x"><button data-i18n-attr="aria-label:coffee.close" aria-label="Close">×</button></form>
  <img class="cup" src="{root}assets/img/coffee-cup.png" alt="" width="64" height="64">
  <h3 id="coffee-h" data-i18n="coffee.h">Buy the Developer a Coffee</h3>
  <p data-i18n="coffee.p1">Entirely up to you: it works the same either way.</p>
  <p data-i18n="coffee.p2">Every cup turns into the next update.</p>
  <div class="codes">
    <figure><img src="{root}assets/img/donate/wechat.webp" alt="WeChat Pay QR code" width="398" height="540" loading="lazy"><figcaption data-i18n="coffee.wechat">WeChat Pay</figcaption></figure>
    <figure><img src="{root}assets/img/donate/alipay.webp" alt="Alipay QR code" width="360" height="540" loading="lazy"><figcaption data-i18n="coffee.alipay">Alipay</figcaption></figure>
    <figure><img src="{root}assets/img/donate/paypal.webp" alt="PayPal QR code" width="454" height="540" loading="lazy"><figcaption data-i18n="coffee.paypal">PayPal</figcaption></figure>
  </div>
</dialog>

{tags}
</body>
</html>
"""


def head(lang, root, title, desc, url, extra=""):
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#000000">
<link rel="icon" href="{root}assets/img/favicon-64.png">
<link rel="stylesheet" href="{root}assets/site.css">
{extra}</head>"""


# ---------- the overview page ----------

def series_block(series, up, strings, root):
    """One season's block on the overview page (and its texts in `strings`)."""
    sid, total = series["id"], series["total"]
    eps = series["episodes"]
    shown = [e for e in eps if e["id"] in up]
    nxt = next((e for e in eps if e["id"] not in up), None)
    now = dt.datetime.now(dt.timezone.utc)
    daily_at = (dt.datetime.now(BEIJING).strftime("%Y-%m-%d") + f"T{series['daily']}:00+08:00")
    for l in LANGS:
        s = strings[l]
        s[f"vid.{sid}.name"] = series["name"][l]
        s[f"vid.{sid}.season"] = fmt(l, "season", n=series["season"])
        s[f"vid.{sid}.progress"] = fmt(l, "progress", n=len(shown), total=total)
        s[f"vid.{sid}.when"] = (fmt(l, "daily", time=time_tag(daily_at, "clock")) if nxt else fmt(l, "done", total=total))
        for e in eps:
            s[f"vid.ep.{e['n']}"] = fmt(l, "ep", n=e["n"])
        for e in shown:
            s[f"vid.{sid}.{e['n']}"] = e["lang"][l]["title"]
            s[f"vid.{sid}.{e['n']}.d"] = fmt(l, "min", m=max(1, round(e["duration"] / 60)))
        if nxt:
            due = dt.datetime.fromisoformat(nxt["at"]) > now
            s[f"vid.{sid}.next"] = (fmt(l, "next", n=nxt["n"], time=time_tag(nxt["at"], "when")) if due
                                    else fmt(l, "soon", n=nxt["n"]))

    en = strings["en"]
    cards = []
    for e in shown:
        n, nn = e["n"], f"{e['n']:02d}"
        badge = f'<span class="new" data-i18n="vid.new">{E(en["vid.new"])}</span>' if e is shown[-1] and nxt else ""
        cards.append(f"""      <a class="ep-card" href="{sid}/{nn}/" data-lang-href="videos/{sid}/{nn}/">
        <span class="thumb"><img src="{root}assets/img/videos/{sid}-{nn}.webp" alt="" width="960" height="540" loading="lazy">{badge}<span class="dur" data-i18n="vid.{sid}.{n}.d">{E(en[f"vid.{sid}.{n}.d"])}</span></span>
        <span class="n" data-i18n="vid.ep.{n}">{E(en[f"vid.ep.{n}"])}</span>
        <b data-i18n="vid.{sid}.{n}">{E(en[f"vid.{sid}.{n}"])}</b>
      </a>""")
    if nxt:
        cards.append(f"""      <div class="ep-card soon">
        <span class="thumb"><span data-i18n="vid.ep.{nxt['n']}">{E(en[f"vid.ep.{nxt['n']}"])}</span></span>
        <span class="n" data-i18n="vid.{sid}.next">{en[f"vid.{sid}.next"]}</span>
      </div>""")
    cards = "\n".join(cards)

    return f"""  <section class="vid-series dark">
    <div class="wrap">
      <div class="series-head">
        <div>
          <p class="eyebrow" data-i18n="vid.{sid}.season">{E(en[f"vid.{sid}.season"])}</p>
          <h2 class="h-2" data-i18n="vid.{sid}.name">{E(en[f"vid.{sid}.name"])}</h2>
          <p class="series-meta"><span data-i18n="vid.{sid}.progress">{E(en[f"vid.{sid}.progress"])}</span> · <span data-i18n="vid.{sid}.when">{en[f"vid.{sid}.when"]}</span></p>
        </div>
        <div class="btns">
          <a class="btn ghost" href="https://www.youtube.com/playlist?list={series['playlist']}" rel="noopener" data-i18n="vid.season_yt">{E(en["vid.season_yt"])}</a>
          <a class="btn ghost" href="{CHANNEL}?sub_confirmation=1" rel="noopener" data-i18n="vid.sub">{E(en["vid.sub"])}</a>
        </div>
      </div>
      <div class="ep-cards">
{cards}
      </div>
    </div>
  </section>"""


def overview(all_series, up, strings):
    """/videos/: the intro, then one block per season, in the order of all_series. Returns the page's address."""
    root = "../"
    for l in LANGS:
        s = strings[l]
        s["vid.title"], s["vid.h"], s["vid.lead"] = UI[l]["title"], UI[l]["h"], UI[l]["lead"]
        s["vid.watch"], s["vid.sub"], s["vid.season_yt"] = UI[l]["watch"], UI[l]["sub"], UI[l]["season_yt"]
        s["vid.new"] = UI[l]["new"]
    blocks = "\n\n".join(series_block(series, up, strings, root) for series in all_series)
    en = strings["en"]

    page = head("en", root, en["vid.title"], UI["en"]["desc"], BASE + "videos/") + f"""
<body data-root="{root}" data-title-key="vid.title">

{nav(root)}

<main>
  <section class="vid-hero dark">
    <div class="wrap center reveal">
      <h1 class="h-1"><span class="grad" data-i18n="vid.h">{E(en["vid.h"])}</span></h1>
      <p class="lead" data-i18n="vid.lead">{E(en["vid.lead"])}</p>
    </div>
  </section>

{blocks}
</main>

""" + foot(root, ["strings.js", "videos-strings.js", "site.js", "videos.js"])
    (ROOT / "videos/index.html").write_text(page, encoding="utf-8")
    return BASE + "videos/"


# ---------- an episode page, in one language ----------

def episode(series, e, l, up):
    sid, n, nn = series["id"], e["n"], f"{e['n']:02d}"
    eps = series["episodes"]
    t, u = e["lang"][l], UI[l]
    root = "../../../" + ("../" if SLUG[l] else "")
    sdir = "../../" if SLUG[l] else "../"  # from this page up to the season's folder (the other languages sit one folder deeper)
    url = f"{BASE}videos/{sid}/{nn}/{SLUG[l]}"
    cover = f"{BASE}assets/img/videos/{sid}-{nn}.webp"
    name = series["name"][l]
    title = f"{t['title']} — {name} #{n}"
    desc = " ".join(t["intro"])
    # data-href: the same page in another language, relative, so the language menu works on any host
    rel = {x: ("../" if SLUG[l] else "./") + SLUG[x] for x in LANGS}
    alts = "".join(f'<link rel="alternate" hreflang="{HREFLANG[x]}" href="{BASE}videos/{sid}/{nn}/{SLUG[x]}" data-lang="{x}" data-href="{rel[x]}">\n'
                   for x in LANGS)
    alts += f'<link rel="alternate" hreflang="x-default" href="{BASE}videos/{sid}/{nn}/">\n'
    ld = {"@context": "https://schema.org", "@type": "VideoObject", "name": t["title"], "description": desc,
          "thumbnailUrl": [cover], "uploadDate": e["at"], "duration": f"PT{e['duration'] // 60}M{e['duration'] % 60}S",
          "embedUrl": f"https://www.youtube.com/embed/{e['id']}", "inLanguage": "en",
          "publisher": {"@type": "Organization", "name": "Technology Information", "url": BASE}}
    extra = (alts + f'<meta property="og:type" content="video.other">\n<meta property="og:title" content="{E(title)}">\n'
             f'<meta property="og:description" content="{E(desc)}">\n<meta property="og:image" content="{cover}">\n'
             f'<meta property="og:url" content="{url}">\n'
             f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n')

    intro = "<br>".join(E(x) for x in t["intro"])
    text = "\n".join(f"        <p>{E(p)}</p>" for p in t["transcript"])
    chapters = "\n".join(
        f'        <li><a href="https://youtu.be/{e["id"]}?t={s}" data-t="{s}" rel="noopener"><span class="t">{clock(s)}</span>{E(label)}</a></li>'
        for s, label in t["chapters"])
    close = f'\n        <p class="ep-close">{E(t["close"])}</p>' if t["close"] else ""

    def pg(other, cls, label):
        if other is None:
            return ""
        on = f"{other['n']:02d}"
        if other["id"] in up:
            return (f'<a class="ep-pg {cls}" href="{sdir}{on}/{SLUG[l]}"><span>{E(label)} · {E(fmt(l, "ep", n=other["n"]))}</span>'
                    f'<b>{E(other["lang"][l]["title"])}</b></a>')
        due = dt.datetime.fromisoformat(other["at"]) > dt.datetime.now(dt.timezone.utc)
        when = fmt(l, "next", n=other["n"], time=time_tag(other["at"], "when")) if due else fmt(l, "soon", n=other["n"])
        return f'<div class="ep-pg {cls} soon"><span>{E(label)}</span><b>{when}</b></div>'

    i = eps.index(e)
    prev_pg = pg(eps[i - 1] if i > 0 else None, "prev", u["prev"])
    next_pg = pg(eps[i + 1] if i + 1 < len(eps) else None, "next", u["nextep"])

    page = head(l, root, title, desc, url, extra) + f"""
<body data-root="{root}" data-page-lang="{l}">

{nav(root)}

<main>
  <section class="ep dark">
    <div class="wrap">
      <p class="ep-crumb"><a href="{root}videos/">{E(u["all"])}</a> · {E(name)} · {E(fmt(l, "ep", n=n))}</p>
      <h1 class="ep-title">{E(t["title"])}</h1>
      <div class="vplayer" data-yt="{e["id"]}" data-title="{E(t["title"])}">
        <button type="button" class="vplay" aria-label="{E(u["play"])}: {E(t["title"])}">
          <img src="{root}assets/img/videos/{sid}-{nn}.webp" alt="" width="960" height="540">
          <span class="vplay-ico" aria-hidden="true">{PLAY_SVG}</span>
        </button>
      </div>
      <p class="vnote">{E(u["loads"])}</p>
      <div class="ep-actions">
        <a class="btn" href="https://youtu.be/{e["id"]}" rel="noopener">{E(u["watch"])}</a>
        <a class="btn ghost" href="{CHANNEL}?sub_confirmation=1" rel="noopener">{E(u["sub"])}</a>
      </div>
    </div>
  </section>

  <section class="ep-body">
    <div class="wrap">
      <p class="ep-intro">{intro}</p>
      <p class="ep-ai">{E(t["note"])}</p>
    </div>
    <div class="wrap ep-grid">
      <aside class="ep-side">
        <h2 class="ep-h">{E(u["chapters"])}</h2>
        <ol class="chapters">
{chapters}
        </ol>
      </aside>
      <article class="ep-main">
        <h2 class="ep-h">{E(u["transcript"])}</h2>
        <div class="ep-text">
{text}
        </div>{close}
      </article>
    </div>
    <nav class="wrap ep-pager">{prev_pg}{next_pg}</nav>
  </section>
</main>

""" + foot(root, ["strings.js", "site.js", "videos.js"])
    out = ROOT / f"videos/{sid}/{nn}/{SLUG[l]}index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return url


def sitemap(groups):
    """groups: lists of the same page in each language (hreflang alternates); /videos/ alone."""
    rows = []
    for urls in groups:
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{HREFLANG[l]}" href="{u}"/>' for l, u in urls.items()) if len(urls) > 1 else ""
        for u in urls.values():
            rows.append(f"  <url><loc>{u}</loc>{alts}</url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")
    (ROOT / "videos/sitemap.xml").write_text(xml, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="don't ask YouTube; use status.json as it is")
    offline = ap.parse_args().offline
    status = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.exists() else {}
    # The overview lists the seasons in order, whatever the file names are.
    all_series = sorted((json.loads(p.read_text(encoding="utf-8")) for p in DATA.glob("*.json") if p != STATUS),
                        key=lambda s: (s["season"], s["id"]))

    if not offline:
        today = dt.datetime.now(BEIJING).strftime("%Y-%m-%d")
        for s in all_series:
            for e in s["episodes"]:
                if e["id"] not in status and is_public(e["id"]):
                    status[e["id"]] = today
                    print(f"up: {s['id']} #{e['n']} {e['id']}")
        STATUS.write_text(json.dumps(status, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    up = set(status)

    strings = {l: {} for l in LANGS}
    groups = []
    if all_series:
        groups.append({"en": overview(all_series, up, strings)})
    for s in all_series:
        for e in s["episodes"]:
            if e["id"] in up:
                groups.append({l: episode(s, e, l, up) for l in LANGS})
    js = ("/* Generated by tools/build_videos.py: the Tutorials pages' text. Merged into TI_STRINGS before site.js runs. */\n"
          "(function (V) { var T = window.TI_STRINGS = window.TI_STRINGS || {};\n"
          "  for (var l in V) { T[l] = T[l] || {}; for (var k in V[l]) T[l][k] = V[l][k]; }\n"
          "})(" + json.dumps(strings, ensure_ascii=False, indent=0) + ");\n")
    (ROOT / "assets/videos-strings.js").write_text(js, encoding="utf-8")
    sitemap(groups)
    print(f"built: {sum(len(g) for g in groups)} pages, {len(up)} episodes up")


if __name__ == "__main__":
    main()
