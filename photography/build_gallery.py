#!/usr/bin/env python3
"""Generate the photography site (scrocco): album index, album
galleries, and the prints page.

Design: light "paper" ground (de.MO-style sophistication), with a
palette PER ALBUM extracted from its own photographs (palettes.json,
produced by extract_palettes.js) — album pages carry a whisper of
their own tint; accents and hairlines follow.

Structure on disk:
    img/<album>/*.jpg      — web-optimized photos (one folder per album)
    img/<album>/cover.jpg  — optional; else first photo is the cover
    palettes.json          — per-album colors (run extract_palettes.js
                             after adding albums)

Generates:
    index.html   — album tiles (cover, name, count, album accent)
    <album>.html — gallery with click-to-zoom lightbox (prev/next/esc)
    prints.html  — print sales: every photograph, inquire via email

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
<meta name="description" content="Street photography by John Santerre, shooting as scrocco.">
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
  .albums {
    padding: 7vh 4vw 10vh;
    display: grid; gap: 34px;
    grid-template-columns: repeat(auto-fit, minmax(min(460px, 100%), 1fr));
  }
  .tile { display: block; }
  .tile .frame {
    overflow: hidden; background: #fff;
    border: 1px solid var(--hair);
  }
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

GALLERY_CSS = """
  .intro { padding: 7vh 4vw 4vh; display: flex; align-items: baseline; gap: 18px; }
  .intro h1 {
    font-weight: 650; font-size: clamp(1.1rem, 2.2vw, 1.5rem);
    letter-spacing: 0.26em; text-transform: uppercase; color: var(--accent);
  }
  .intro .count { color: var(--dim); font-size: 13px; letter-spacing: 0.08em; }
  .intro .back { margin-left: auto; color: var(--dim); font-size: 12.5px; letter-spacing: 0.06em; }
  .intro .back:hover { color: var(--ink); }
  .gallery { padding: 0 4vw 10vh; columns: 3; column-gap: 18px; }
  @media (max-width: 1000px) { .gallery { columns: 2; } }
  @media (max-width: 620px)  { .gallery { columns: 1; } }
  .gallery figure {
    break-inside: avoid; margin: 0 0 18px; background: #fff;
    border: 1px solid var(--hair); padding: 8px; cursor: zoom-in;
  }
  .gallery img { width: 100%; display: block; opacity: 0; transition: opacity 500ms ease; }
  .gallery img.in { opacity: 1; }

  /* lightbox */
  #lb {
    position: fixed; inset: 0; z-index: 50; display: none;
    background: color-mix(in srgb, var(--paper) 88%, #000 4%);
    backdrop-filter: blur(6px);
    align-items: center; justify-content: center;
  }
  #lb.open { display: flex; }
  #lb img {
    max-width: 92vw; max-height: 88vh; display: block;
    background: #fff; padding: 10px; border: 1px solid var(--hair);
    box-shadow: 0 30px 80px -30px rgba(0,0,0,0.35);
  }
  #lb button {
    position: fixed; background: none; border: none; cursor: pointer;
    color: var(--ink); font-size: 30px; padding: 18px; opacity: 0.55;
  }
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
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      const img = e.target;
      if (img.complete) img.classList.add('in');
      else img.addEventListener('load', () => img.classList.add('in'), { once: true });
      io.unobserve(img);
    }
  }, { rootMargin: '200px' });
  const imgs = [...document.querySelectorAll('.gallery img')];
  imgs.forEach(i => io.observe(i));

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
  imgs.forEach((img, i) => img.closest('figure').addEventListener('click', () => show(i)));
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
  .intro { padding: 7vh 4vw 3vh; max-width: 70ch; }
  .intro h1 {
    font-weight: 650; font-size: clamp(1.1rem, 2.2vw, 1.5rem);
    letter-spacing: 0.26em; text-transform: uppercase; color: var(--accent);
  }
  .intro p { margin-top: 16px; color: #444; font-size: 1.02rem; line-height: 1.6; }
  .intro p.small { font-size: 0.88rem; color: var(--dim); }
  .album-head {
    padding: 5vh 4vw 14px; font-size: 12px; letter-spacing: 0.3em;
    text-transform: uppercase; color: var(--dim);
  }
  .gallery { padding: 0 4vw 4vh; columns: 4; column-gap: 14px; }
  @media (max-width: 1100px) { .gallery { columns: 3; } }
  @media (max-width: 800px)  { .gallery { columns: 2; } }
  .gallery figure {
    break-inside: avoid; margin: 0 0 14px; background: #fff;
    border: 1px solid var(--hair); padding: 6px;
  }
  .gallery img { width: 100%; display: block; }
  .gallery figcaption {
    display: flex; align-items: baseline; gap: 8px;
    padding: 8px 4px 4px; font-size: 11.5px; color: var(--dim);
  }
  .gallery figcaption a {
    margin-left: auto; color: var(--accent); letter-spacing: 0.06em;
    border-bottom: 1px solid var(--hair);
  }
  .gallery figcaption a:hover { border-color: var(--accent); }
"""


def album_title(name):
    return name.replace("-", " ").replace("_", " ").title()


def load_palettes():
    p = HERE / "palettes.json"
    return json.loads(p.read_text()) if p.exists() else {}


def main():
    palettes = load_palettes()
    albums = []
    for d in sorted(p for p in IMG.iterdir() if p.is_dir()):
        photos = sorted(p.name for p in d.iterdir()
                        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
        if not photos:
            continue
        cover = "cover.jpg" if "cover.jpg" in photos else photos[0]
        albums.append((d.name, photos, cover))

    # --- index: album tiles on neutral paper, each label in its album accent ---
    tiles = "\n".join(
        f'  <a class="tile" href="{name}.html" style="--tile-accent: '
        f'{palettes.get(name, DEFAULT_PAL)["accent"]}">'
        f'<span class="frame"><img src="img/{name}/{cover}" alt="{album_title(name)} album cover"></span>'
        f'<span class="label"><span class="name">{album_title(name)}</span>'
        f'<span class="count">{len(photos)} photographs</span></span></a>'
        for name, photos, cover in albums
    )
    index = (
        HEAD.format(title="scrocco — photographs", extra_css=INDEX_CSS,
                    paper="#f7f6f3", hairline="#e5e2db",
                    accent=DEFAULT_PAL["accent"])
        + f"""
<main class="albums">
{tiles}
</main>
"""
        + FOOT.format(script="")
    )
    (HERE / "index.html").write_text(index, encoding="utf-8")

    # --- per-album galleries in the album's own palette, with lightbox ---
    for name, photos, cover in albums:
        pal = palettes.get(name, DEFAULT_PAL)
        figures = "\n".join(
            f'  <figure><img loading="lazy" src="img/{name}/{p}" alt=""></figure>'
            for p in photos if p != "cover.jpg"
        )
        page = (
            HEAD.format(title=f"{album_title(name)} — scrocco",
                        extra_css=GALLERY_CSS, paper=pal["tint"],
                        hairline=pal["hairline"], accent=pal["accent"])
            + f"""
<section class="intro">
  <h1>{album_title(name)}</h1>
  <span class="count">{len(photos)} photographs · click any image to view large</span>
  <a class="back" href="/photography/">← all albums</a>
</section>

<main class="gallery">
{figures}
</main>
"""
            + FOOT.format(script=LIGHTBOX)
        )
        (HERE / f"{name}.html").write_text(page, encoding="utf-8")

    # --- prints page: every photograph, inquire by email ---
    sections = []
    for name, photos, cover in albums:
        figs = []
        for p in photos:
            if p == "cover.jpg":
                continue
            pid = f"{name}/{p}"
            subject = f"Print inquiry — {pid}"
            figs.append(
                f'  <figure><img loading="lazy" src="img/{name}/{p}" alt="">'
                f'<figcaption><span>{p.rsplit(".",1)[0]}</span>'
                f'<a href="mailto:john.santerre.ai@gmail.com?subject={subject.replace(" ", "%20")}">'
                f'inquire</a></figcaption></figure>'
            )
        sections.append(
            f'<div class="album-head">{album_title(name)}</div>\n'
            f'<main class="gallery">\n' + "\n".join(figs) + "\n</main>"
        )
    prints = (
        HEAD.format(title="Prints — scrocco", extra_css=PRINTS_CSS,
                    paper="#f7f6f3", hairline="#e5e2db",
                    accent=DEFAULT_PAL["accent"])
        + """
<section class="intro">
  <h1>Prints</h1>
  <p>Every photograph here is available as an archival pigment print,
     produced to order and signed. Tell me which image and the size
     you're imagining — I'll reply with options and pricing.</p>
  <p class="small">Editions are small. Framing available on request.</p>
</section>
"""
        + "\n".join(sections)
        + FOOT.format(script="")
    )
    (HERE / "prints.html").write_text(prints, encoding="utf-8")

    print(f"built: index + {len(albums)} album page(s) + prints:",
          ", ".join(a[0] for a in albums))


if __name__ == "__main__":
    main()
