#!/usr/bin/env python3
"""Generate the photography site (scrocco) — photojournalist edition.

Design language (VII / Addario informed): warm paper ground, stories
titled by place, hero image first, photographs presented as full-width
statements with occasional two-up rows for pacing, story text
interleaved between image groups. Each story carries a palette
extracted from its own photographs (palettes.json).

Structure on disk:
    img/<story>/*.jpg        — web photos (folder per story)
    img/<story>/cover.jpg    — optional explicit cover/hero
    img/<story>/story.txt    — optional text: plain paragraphs separated
                               by blank lines. First paragraph = the dek
                               under the title; the rest interleave
                               between image groups.
    palettes.json            — from extract_palettes.js
    editions.json            — curated print editions (see prints below)

Generates: index.html, <story>.html per story, prints.html.
Run:  python3 photography/build_gallery.py
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
IMG = HERE / "img"

DEFAULT_PAL = {"accent": "hsl(30, 8%, 32%)", "tint": "#f7f6f3",
               "hairline": "#e5e2db"}

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Photography by John Santerre, shooting as scrocco.">
<style>
  :root {{
    --paper: {paper};
    --ink: #1c1b18;
    --dim: #8a867c;
    --hair: {hairline};
    --accent: {accent};
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: var(--paper); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  a {{ color: inherit; text-decoration: none; }}
  header {{
    display: flex; align-items: baseline; gap: 20px;
    padding: 26px 4vw 22px;
    border-bottom: 1px solid var(--hair);
  }}
  .mark {{ font-size: 15px; letter-spacing: 0.34em; text-transform: lowercase; font-weight: 400; }}
  .mark b {{ font-weight: 700; }}
  header .right {{ margin-left: auto; display: flex; gap: 22px; font-size: 12.5px; color: var(--dim); letter-spacing: 0.06em; }}
  header .right a:hover {{ color: var(--ink); }}
  footer {{
    padding: 5vh 4vw 8vh; border-top: 1px solid var(--hair);
    display: flex; flex-wrap: wrap; gap: 12px 24px; font-size: 12.5px; color: var(--dim); letter-spacing: 0.06em;
  }}
  footer a:hover {{ color: var(--ink); }}
  footer .copy {{ margin-left: auto; }}
{extra_css}
</style>
</head>
<body>

<header>
  <a class="mark" href="/photography/"><b>scrocco</b></a>
  <span class="right">
    <a href="/photography/prints.html">prints</a>
    <a href="https://www.instagram.com/scrocco/">instagram</a>
    <a href="/">john santerre — the academic side</a>
  </span>
</header>
"""

FOOT = """
<footer>
  <a href="/photography/prints.html">prints</a>
  <a href="https://www.instagram.com/scrocco/">@scrocco</a>
  <a href="mailto:john.santerre.ai@gmail.com">email</a>
  <span class="copy">© 2026 John Santerre</span>
</footer>
{script}
</body>
</html>
"""

INDEX_CSS = """
  .stories {
    padding: 7vh 4vw 10vh;
    display: grid; gap: 40px 34px;
    grid-template-columns: repeat(auto-fit, minmax(min(460px, 100%), 1fr));
  }
  .tile { display: block; }
  .tile .frame { overflow: hidden; background: #fff; border: 1px solid var(--hair); }
  .tile img {
    width: 100%; aspect-ratio: 3 / 2; object-fit: cover; display: block;
    transition: transform 700ms ease;
  }
  .tile:hover img { transform: scale(1.025); }
  .tile .label { display: flex; align-items: baseline; gap: 14px; padding: 14px 2px 0; }
  .tile .name {
    font-size: 13.5px; letter-spacing: 0.26em; text-transform: uppercase;
    font-weight: 650; color: var(--tile-accent, var(--accent));
  }
  .tile .count { font-size: 12px; color: var(--dim); letter-spacing: 0.08em; }
"""

STORY_CSS = """
  .story { max-width: 1120px; margin: 0 auto; padding: 0 4vw; }
  .story-head { padding: 8vh 0 4vh; }
  .story-head h1 {
    font-weight: 650; font-size: clamp(1.3rem, 2.6vw, 1.9rem);
    letter-spacing: 0.3em; text-transform: uppercase; color: var(--accent);
  }
  .story-head .dek {
    margin-top: 18px; max-width: 62ch;
    font-family: Georgia, "Times New Roman", serif;
    font-size: clamp(1.05rem, 1.7vw, 1.25rem); line-height: 1.65; color: #33312c;
  }
  .story-head .meta { margin-top: 14px; font-size: 12px; color: var(--dim); letter-spacing: 0.1em; }
  .story-head .back { color: var(--dim); font-size: 12.5px; letter-spacing: 0.06em; }
  .story-head .back:hover { color: var(--ink); }

  .ph { margin: 0 0 26px; cursor: zoom-in; }
  .ph img { width: 100%; display: block; background: #fff; border: 1px solid var(--hair); padding: 8px; }
  .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; margin-bottom: 26px; }
  .row2 .ph { margin: 0; }
  @media (max-width: 700px) { .row2 { grid-template-columns: 1fr; gap: 0; } .row2 .ph { margin-bottom: 26px; } }

  .prose {
    max-width: 62ch; margin: 7vh auto 7vh;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.12rem; line-height: 1.75; color: #2c2a25;
  }
  .prose p + p { margin-top: 1.1em; }
  .endmark { text-align: center; color: var(--dim); font-size: 18px; padding: 3vh 0 9vh; }

  #lb {
    position: fixed; inset: 0; z-index: 50; display: none;
    background: color-mix(in srgb, var(--paper) 90%, #000 3%);
    backdrop-filter: blur(6px);
    align-items: center; justify-content: center;
  }
  #lb.open { display: flex; }
  #lb img {
    max-width: 93vw; max-height: 89vh; display: block;
    background: #fff; padding: 10px; border: 1px solid var(--hair);
    box-shadow: 0 30px 80px -30px rgba(0,0,0,0.35);
  }
  #lb button { position: fixed; background: none; border: none; cursor: pointer;
    color: var(--ink); font-size: 30px; padding: 18px; opacity: 0.55; }
  #lb button:hover { opacity: 1; }
  #lb .close { top: 12px; right: 16px; }
  #lb .prev { left: 8px; top: 50%; transform: translateY(-50%); }
  #lb .next { right: 8px; top: 50%; transform: translateY(-50%); }
"""

LIGHTBOX = """
<div id="lb">
  <button class="close" aria-label="Close">×</button>
  <button class="prev" aria-label="Previous">‹</button>
  <button class="next" aria-label="Next">›</button>
  <img alt="">
</div>
<script>
  const imgs = [...document.querySelectorAll('.ph img')];
  const lb = document.getElementById('lb');
  const lbImg = lb.querySelector('img');
  let cur = -1;
  function show(i) {
    cur = (i + imgs.length) % imgs.length;
    lbImg.src = imgs[cur].src;
    lb.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function hide() { lb.classList.remove('open'); document.body.style.overflow = ''; }
  imgs.forEach((img, i) => img.closest('.ph').addEventListener('click', () => show(i)));
  lb.querySelector('.close').addEventListener('click', hide);
  lb.querySelector('.prev').addEventListener('click', (e) => { e.stopPropagation(); show(cur - 1); });
  lb.querySelector('.next').addEventListener('click', (e) => { e.stopPropagation(); show(cur + 1); });
  lb.addEventListener('click', (e) => { if (e.target === lb) hide(); });
  document.addEventListener('keydown', (e) => {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') hide();
    if (e.key === 'ArrowLeft') show(cur - 1);
    if (e.key === 'ArrowRight') show(cur + 1);
  });
</script>
"""

PRINTS_CSS = """
  .intro { max-width: 1120px; margin: 0 auto; padding: 8vh 4vw 4vh; }
  .intro h1 {
    font-weight: 650; font-size: clamp(1.3rem, 2.6vw, 1.9rem);
    letter-spacing: 0.3em; text-transform: uppercase; color: var(--accent);
  }
  .intro p {
    margin-top: 18px; max-width: 58ch;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 1.08rem; line-height: 1.7; color: #33312c;
  }
  .editions { max-width: 1120px; margin: 0 auto; padding: 2vh 4vw 10vh; }
  .edition {
    display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
    gap: 40px; align-items: start;
    padding: 6vh 0; border-top: 1px solid var(--hair);
  }
  .edition:first-child { border-top: none; }
  @media (max-width: 760px) { .edition { grid-template-columns: 1fr; } }
  .edition img { width: 100%; display: block; background: #fff; border: 1px solid var(--hair); padding: 8px; }
  .edition h2 { font-size: 1.05rem; letter-spacing: 0.18em; text-transform: uppercase; font-weight: 650; }
  .edition .ed-meta { margin-top: 10px; font-size: 12.5px; color: var(--dim); letter-spacing: 0.08em; }
  .edition table { margin-top: 22px; border-collapse: collapse; width: 100%; max-width: 340px; }
  .edition td { padding: 9px 0; border-bottom: 1px solid var(--hair); font-size: 14px; }
  .edition td:last-child { text-align: right; font-variant-numeric: tabular-nums; }
  .edition .acquire {
    display: inline-block; margin-top: 26px; padding: 11px 22px;
    border: 1px solid var(--ink); font-size: 12.5px; letter-spacing: 0.14em;
    text-transform: uppercase;
  }
  .edition .acquire:hover { background: var(--ink); color: var(--paper); }
  .forthcoming {
    max-width: 58ch; margin: 4vh auto 14vh; padding: 0 4vw;
    font-family: Georgia, serif; font-size: 1.05rem; line-height: 1.7; color: var(--dim);
  }
"""


def story_title(name):
    return name.replace("-", " / ").replace("_", " ").title().replace(" / ", " / ")


def load_json(name, default):
    p = HERE / name
    return json.loads(p.read_text()) if p.exists() else default


def read_story_text(album_dir):
    p = album_dir / "story.txt"
    if not p.exists():
        return None, []
    paras = [x.strip() for x in p.read_text(encoding="utf-8").split("\n\n") if x.strip()]
    return (paras[0], paras[1:]) if paras else (None, [])


def main():
    palettes = load_json("palettes.json", {})
    editions = load_json("editions.json", [])

    stories = []
    for d in sorted(p for p in IMG.iterdir() if p.is_dir()):
        photos = sorted(p.name for p in d.iterdir()
                        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
        if not photos:
            continue
        cover = "cover.jpg" if "cover.jpg" in photos else photos[0]
        dek, paras = read_story_text(d)
        stories.append((d.name, photos, cover, dek, paras))

    # --- index ---
    tiles = "\n".join(
        f'  <a class="tile" href="{name}.html" style="--tile-accent: '
        f'{palettes.get(name, DEFAULT_PAL)["accent"]}">'
        f'<span class="frame"><img src="img/{name}/{cover}" alt="{story_title(name)}"></span>'
        f'<span class="label"><span class="name">{story_title(name)}</span>'
        f'<span class="count">{len(photos)} photographs</span></span></a>'
        for name, photos, cover, dek, paras in stories
    )
    index = (
        HEAD.format(title="scrocco — photographs", extra_css=INDEX_CSS,
                    paper="#f7f6f3", hairline="#e5e2db", accent=DEFAULT_PAL["accent"])
        + f'\n<main class="stories">\n{tiles}\n</main>\n'
        + FOOT.format(script="")
    )
    (HERE / "index.html").write_text(index, encoding="utf-8")

    # --- story pages: hero, then rhythm [full, 2up] with prose interleaved ---
    for name, photos, cover, dek, paras in stories:
        pal = palettes.get(name, DEFAULT_PAL)
        rest = [p for p in photos if p != cover and p != "cover.jpg"]

        def fig(p):
            return (f'<figure class="ph"><img loading="lazy" '
                    f'src="img/{name}/{p}" alt=""></figure>')

        # group photos: alternating single / pair
        groups, i, toggle = [], 0, True
        while i < len(rest):
            if toggle or i == len(rest) - 1:
                groups.append(fig(rest[i])); i += 1
            else:
                groups.append(f'<div class="row2">{fig(rest[i])}{fig(rest[i+1])}</div>')
                i += 2
            toggle = not toggle

        # interleave prose paragraphs roughly evenly between groups
        blocks = []
        if paras and groups:
            step = max(1, round(len(groups) / (len(paras) + 1)))
            pi = 0
            for gi, g in enumerate(groups):
                blocks.append(g)
                if pi < len(paras) and (gi + 1) % step == 0:
                    blocks.append(f'<div class="prose"><p>{paras[pi]}</p></div>')
                    pi += 1
            for p in paras[pi:]:
                blocks.append(f'<div class="prose"><p>{p}</p></div>')
        else:
            blocks = groups

        dek_html = f'<p class="dek">{dek}</p>' if dek else ""
        page = (
            HEAD.format(title=f"{story_title(name)} — scrocco",
                        extra_css=STORY_CSS, paper=pal["tint"],
                        hairline=pal["hairline"], accent=pal["accent"])
            + f"""
<article class="story">
  <div class="story-head">
    <a class="back" href="/photography/">← stories</a>
    <h1>{story_title(name)}</h1>
    {dek_html}
    <div class="meta">{len(photos)} photographs · click any image to view large</div>
  </div>

  <figure class="ph"><img src="img/{name}/{cover}" alt=""></figure>

{chr(10).join(blocks)}

  <div class="endmark">◦</div>
</article>
"""
            + FOOT.format(script=LIGHTBOX)
        )
        (HERE / f"{name}.html").write_text(page, encoding="utf-8")

    # --- prints: curated editions only ---
    if editions:
        rows = []
        for e in editions:
            sizes = "\n".join(
                f'      <tr><td>{dim}</td><td>{price}</td></tr>'
                for dim, price in e.get("sizes", [])
            )
            subject = f'Acquire — {e["title"]}'.replace(" ", "%20")
            rows.append(f"""
  <div class="edition">
    <img src="img/{e['file']}" alt="{e['title']}">
    <div>
      <h2>{e['title']}</h2>
      <div class="ed-meta">Edition of {e['edition']} · archival pigment print · signed and numbered</div>
      <table>
{sizes}
      </table>
      <a class="acquire" href="mailto:john.santerre.ai@gmail.com?subject={subject}">Acquire</a>
    </div>
  </div>""")
        body = f'\n<main class="editions">{"".join(rows)}\n</main>\n'
    else:
        body = ('\n<p class="forthcoming">The first editions are being selected now. '
                'For early inquiries, <a href="mailto:john.santerre.ai@gmail.com?subject=Print%20editions" '
                'style="border-bottom:1px solid var(--hair)">write to me</a>.</p>\n')

    prints = (
        HEAD.format(title="Prints — scrocco", extra_css=PRINTS_CSS,
                    paper="#f7f6f3", hairline="#e5e2db", accent=DEFAULT_PAL["accent"])
        + """
<section class="intro">
  <h1>Prints</h1>
  <p>A small number of photographs, released as limited editions —
     archival pigment prints, signed and numbered. When an edition is
     gone, it is gone.</p>
</section>
"""
        + body
        + FOOT.format(script="")
    )
    (HERE / "prints.html").write_text(prints, encoding="utf-8")

    print(f"built: index + {len(stories)} stories + prints "
          f"({len(editions)} editions{' — forthcoming state' if not editions else ''})")


if __name__ == "__main__":
    main()
