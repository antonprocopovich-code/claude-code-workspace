#!/usr/bin/env python3
"""Generate 1080x1080 PNG covers for Instagram Highlights — v2 Dark Gold design.

Pallete: brendbuk-v3 — #1C1917 bg, #CA8A04 gold accent, Cormorant Garamond + Libre Baskerville.
Topics: aligned with 7 pillars of personal brand.
"""

import subprocess, os

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

covers = [
    (1, "◐", "МОЙ ПУТЬ",    "дно · тьма · служение",             "мой-путь"),
    (2, "∞",  "БЛИЗОСТЬ",   "священное · тело · пара",            "близость"),
    (3, "◑",  "ПОЛЯРНОСТЬ", "притяжение · мужское · женское",     "полярность"),
    (4, "≋",  "ЭНЕРГОВОЛНА","тело · подсознание · практика",      "энерговолна"),
    (5, "◇",  "ЖЕНЩИНА",    "природа · притяжение · суть",        "женщина"),
    (6, "◉",  "СЕМЬЯ",      "сохранить · защитить · выстроить",   "семья"),
    (7, "△",  "ОБЩИНЫ",     "свои люди · земля · движение",       "общины"),
    (8, "◈",  "ОТЗЫВЫ",     "пары · мужчины · трансформация",     "отзывы"),
]

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Libre+Baskerville:ital@1&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:1080px;height:1080px;overflow:hidden;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}
body{{
  background:
    radial-gradient(circle at 50% 42%, rgba(202,138,4,0.10) 0%, rgba(202,138,4,0.0) 62%),
    #1C1917;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  font-family:'Cormorant Garamond', Georgia, 'Times New Roman', serif;
  position:relative;
}}
.corner{{position:absolute;width:40px;height:40px;}}
.tl{{top:40px;left:40px;border-top:1px solid #292524;border-left:1px solid #292524;}}
.tr{{top:40px;right:40px;border-top:1px solid #292524;border-right:1px solid #292524;}}
.bl{{bottom:40px;left:40px;border-bottom:1px solid #292524;border-left:1px solid #292524;}}
.br{{bottom:40px;right:40px;border-bottom:1px solid #292524;border-right:1px solid #292524;}}
.symbol{{
  font-size:220px;line-height:1;
  color:#CA8A04;
  text-shadow:0 0 80px rgba(202,138,4,0.30),0 0 40px rgba(202,138,4,0.15);
  margin-bottom:32px;
}}
.divider{{width:60px;height:1px;background:rgba(202,138,4,0.70);margin-bottom:32px;}}
.title{{
  font-family:'Cormorant Garamond', Georgia, serif;
  font-weight:700;font-size:58px;
  letter-spacing:0.28em;text-transform:uppercase;
  color:#F2EDE6;margin-bottom:20px;
  padding-left:0.28em;
}}
.subtitle{{
  font-family:'Libre Baskerville','Times New Roman',serif;font-style:italic;
  font-size:19px;color:#A8A29E;letter-spacing:0.12em;
}}
</style>
</head>
<body>
  <span class="corner tl"></span>
  <span class="corner tr"></span>
  <span class="corner bl"></span>
  <span class="corner br"></span>
  <div class="symbol">{sym}</div>
  <div class="divider"></div>
  <div class="title">{title}</div>
  <div class="subtitle">{sub}</div>
</body>
</html>
"""

for (num, sym, title, sub, slug) in covers:
    html_path = os.path.join(OUT_DIR, f"cover-{num}.html")
    png_path  = os.path.join(OUT_DIR, f"cover-{num:02d}-{slug}.png")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(sym=sym, title=title, sub=sub))

    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1080,1080",
        f"--screenshot={png_path}",
        f"file://{html_path}",
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    ok = os.path.exists(png_path) and os.path.getsize(png_path) > 10000
    status = "✓" if ok else "✗ FAILED"
    size = f"{os.path.getsize(png_path)//1024}KB" if ok else ""
    print(f"{status}  cover-{num:02d}  {title:<14}  {size}")
    os.remove(html_path)

print("\nDone. PNGs saved to:", OUT_DIR)
