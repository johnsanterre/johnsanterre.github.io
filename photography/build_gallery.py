#!/usr/bin/env python3
"""Generate the photography site: album-tile front page + one gallery
page per album.

Structure on disk:
    img/<album>/*.jpg      — web-optimized photos (one folder per album)
    img/<album>/cover.jpg  — optional; otherwise the first photo is the cover

Generates:
    index.html             — de.MO-style album tiles (cover + name + count)
    <album>.html           — dark masonry gallery for that album

Run after adding/removing photos or albums:
    python3 photography/build_gallery.py
"""

from pathlib import Path

HERE = Path(__file__).parent
IMG = HERE / "img"

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Street photography by John Santerre, shooting as scrocco.">
<style>
  :root {{
    --bg: #0b0b0c;
    --ink: #e6e4df;
    --dim: #8a8880;
    --hair: #232326;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: var(--bg); color: var(--ink);
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
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
    display: flex; gap: 24px; font-size: 12.5px; color: var(--dim); letter-spacing: 0.06em;
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
    <a href="https://www.instagram.com/scrocco/">instagram</a>
    <a href="/">john santerre — the academic side</a>
  </span>
</header>
"""

FOOT = """
<footer>
  <a href="https://www.instagram.com/scrocco/">@scrocco</a>
  <a href="mailto:john.santerre.ai@gmail.com">email</a>
  <span class="copy">© 2026 John Santerre</span>
</footer>
{script}
</body>
</html>
"""

INDEX_CSS = """
  .intro { padding: 9vh 4vw 6vh; }
  .intro h1 {
    font-weight: 300; font-size: clamp(1.3rem, 2.6vw, 1.9rem);
    letter-spacing: 0.01em; max-width: 34ch; line-height: 1.45;
  }
  .intro h1 span { color: var(--dim); }
  .albums {
    padding: 0 4vw 10vh;
    display: grid; gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(min(440px, 100%), 1fr));
  }
  .tile { position: relative; display: block; overflow: hidden; background: #101012; }
  .tile img {
    width: 100%; aspect-ratio: 3 / 2; object-fit: cover; display: block;
    transition: transform 600ms ease, opacity 400ms ease;
  }
  .tile:hover img { transform: scale(1.03); }
  .tile .label {
    position: absolute; left: 0; right: 0; bottom: 0;
    padding: 40px 22px 18px;
    background: linear-gradient(transparent, rgba(0,0,0,0.72));
    display: flex; align-items: baseline; gap: 14px;
  }
  .tile .name {
    font-size: 15px; letter-spacing: 0.26em; text-transform: uppercase; font-weight: 600;
  }
  .tile .count { font-size: 12px; color: #bdbab2; letter-spacing: 0.08em; }
"""

GALLERY_CSS = """
  .intro { padding: 7vh 4vw 5vh; display: flex; align-items: baseline; gap: 20px; }
  .intro h1 {
    font-weight: 300; font-size: clamp(1.4rem, 3vw, 2.1rem);
    letter-spacing: 0.22em; text-transform: uppercase;
  }
  .intro .count { color: var(--dim); font-size: 13px; letter-spacing: 0.08em; }
  .intro .back { margin-left: auto; color: var(--dim); font-size: 12.5px; letter-spacing: 0.06em; }
  .intro .back:hover { color: var(--ink); }
  .gallery { padding: 0 4vw 10vh; columns: 3; column-gap: 14px; }
  @media (max-width: 1000px) { .gallery { columns: 2; } }
  @media (max-width: 620px)  { .gallery { columns: 1; } }
  .gallery figure { break-inside: avoid; margin: 0 0 14px; background: #101012; overflow: hidden; }
  .gallery img {
    width: 100%; display: block; opacity: 0;
    transition: opacity 500ms ease, transform 400ms ease;
  }
  .gallery img.in { opacity: 1; }
  .gallery figure:hover img { transform: scale(1.015); }
"""

FADE_SCRIPT = """
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
  document.querySelectorAll('.gallery img').forEach(i => io.observe(i));
</script>
"""


def album_title(name):
    return name.replace("-", " ").replace("_", " ").title()


def main():
    albums = []
    for d in sorted(p for p in IMG.iterdir() if p.is_dir()):
        photos = sorted(p.name for p in d.iterdir()
                        if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
        if not photos:
            continue
        cover = "cover.jpg" if "cover.jpg" in photos else photos[0]
        albums.append((d.name, photos, cover))

    # --- front page: album tiles ---
    tiles = "\n".join(
        f'  <a class="tile" href="{name}.html">'
        f'<img src="img/{name}/{cover}" alt="{album_title(name)} album cover">'
        f'<span class="label"><span class="name">{album_title(name)}</span>'
        f'<span class="count">{len(photos)} photographs</span></span></a>'
        for name, photos, cover in albums
    )
    index = (
        HEAD.format(title="scrocco — photographs", extra_css=INDEX_CSS)
        + f"""
<section class="intro">
  <h1>Streets, walls, and what people leave on them.
      <span>Photographs by John Santerre.</span></h1>
</section>

<main class="albums">
{tiles}
</main>
"""
        + FOOT.format(script="")
    )
    (HERE / "index.html").write_text(index, encoding="utf-8")

    # --- per-album gallery pages ---
    for name, photos, cover in albums:
        figures = "\n".join(
            f'  <figure><img loading="lazy" src="img/{name}/{p}" alt=""></figure>'
            for p in photos if p != "cover.jpg"
        )
        page = (
            HEAD.format(title=f"{album_title(name)} — scrocco", extra_css=GALLERY_CSS)
            + f"""
<section class="intro">
  <h1>{album_title(name)}</h1>
  <span class="count">{len(photos)} photographs</span>
  <a class="back" href="/photography/">← all albums</a>
</section>

<main class="gallery">
{figures}
</main>
"""
            + FOOT.format(script=FADE_SCRIPT)
        )
        (HERE / f"{name}.html").write_text(page, encoding="utf-8")

    print(f"built: index + {len(albums)} album page(s):",
          ", ".join(a[0] for a in albums))


if __name__ == "__main__":
    main()
