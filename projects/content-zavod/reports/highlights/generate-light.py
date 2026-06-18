#!/usr/bin/env python3
"""Generate 1080x1080 PNG covers — light version (white bg, black text)."""

import subprocess, os

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "light")
os.makedirs(OUT_DIR, exist_ok=True)

covers = [
    (1, "◐", "МОЙ ПУТЬ",     "дно → трансформация → служение"),
    (2, "◉", "ОТЗЫВЫ",        "что менялось у пар и мужчин"),
    (3, "≋", "ИНСТРУМЕНТЫ",   "Энерговолна · тело · подсознание"),
    (4, "●", "ДЕПРЕССИЯ",     "путь через тьму изнутри"),
    (5, "◇", "РАЗВОД",        "12 лет · разрушение · возрождение"),
    (6, "∞", "СЕМЬЯ",         "близость · полярность · союз"),
    (7, "△", "ТЕЛО",          "секс как духовный путь"),
    (8, "◈", "ОБО МНЕ",       "кто я и зачем я здесь"),
]

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;700&family=Lora:ital@1&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:1080px;height:1080px;overflow:hidden;-webkit-print-color-adjust:exact;print-color-adjust:exact;}}
body{{
  background:#FFFFFF;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  font-family:'Inter',sans-serif;
  position:relative;
}}
.corner{{position:absolute;width:36px;height:36px;}}
.tl{{top:36px;left:36px;border-top:1px solid #D0C8C0;border-left:1px solid #D0C8C0;}}
.tr{{top:36px;right:36px;border-top:1px solid #D0C8C0;border-right:1px solid #D0C8C0;}}
.bl{{bottom:36px;left:36px;border-bottom:1px solid #D0C8C0;border-left:1px solid #D0C8C0;}}
.br{{bottom:36px;right:36px;border-bottom:1px solid #D0C8C0;border-right:1px solid #D0C8C0;}}
.symbol{{
  font-size:240px;line-height:1;
  color:#1A1512;
  margin-bottom:28px;
}}
.divider{{width:80px;height:2px;background:#1A1512;margin-bottom:28px;}}
.title{{
  font-weight:700;font-size:56px;
  letter-spacing:0.3em;text-transform:uppercase;
  color:#0F0D0B;margin-bottom:18px;
}}
.subtitle{{
  font-family:'Lora',serif;font-style:italic;
  font-size:22px;color:#7a706a;letter-spacing:0.15em;
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

for (num, sym, title, sub) in covers:
    html_path = os.path.join(OUT_DIR, f"cover-{num}.html")
    png_path  = os.path.join(OUT_DIR, f"cover-{num:02d}-{title.lower().replace(' ','-')}.png")

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
    subprocess.run(cmd, capture_output=True)
    ok = os.path.exists(png_path) and os.path.getsize(png_path) > 10000
    status = "✓" if ok else "✗ FAILED"
    size = f"{os.path.getsize(png_path)//1024}KB" if ok else ""
    print(f"{status}  cover-{num:02d}  {title:<14}  {size}")
    os.remove(html_path)

print("\nDone. PNGs saved to:", OUT_DIR)
