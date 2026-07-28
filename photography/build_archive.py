#!/usr/bin/env python3
"""Build the PRIVATE local archive browser: photos-inbox/archive.html.

This page lives inside photos-inbox/ (gitignored) so it can never reach
GitHub. Open it directly from disk — it references the original files
with relative paths, so it works fully offline from this Mac (or any
machine with the Dropbox folder).

What it shows:
  - every folder in photos-inbox/ as an album (marked PUBLISHED if a
    matching story exists in photography/img/, else PRIVATE)
  - loose files at the inbox root as "Inbox — unsorted"
  - JPG/PNG only are rendered; RAW files (CR2/RAF/ARW/DNG/NEF) are
    stored alongside and counted, never displayed

Run after ingesting photos:  python3 photography/build_archive.py
"""

import html
from pathlib import Path

HERE = Path(__file__).parent
INBOX = HERE.parent / "photos-inbox"
PUBLISHED = {p.name for p in (HERE / "img").iterdir() if p.is_dir()}

SHOW = (".jpg", ".jpeg", ".png", ".webp")
RAW = (".cr2", ".raf", ".arw", ".dng", ".nef", ".orf", ".rw2")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Archive — private</title>
<style>
  :root { --paper:#f7f6f3; --ink:#1c1b18; --dim:#8a867c; --hair:#e5e2db; --accent:#7C2530; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--paper); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Helvetica,Arial,sans-serif; }
  header { display:flex; align-items:baseline; gap:16px; padding:24px 4vw 18px;
    border-bottom:1px solid var(--hair); position:sticky; top:0; background:var(--paper); z-index:5; }
  .mark { font-size:15px; letter-spacing:0.34em; font-weight:700; }
  .private-badge { font-size:10.5px; letter-spacing:0.2em; color:#fff; background:var(--accent);
    padding:3px 9px; border-radius:3px; text-transform:uppercase; }
  header .note { margin-left:auto; font-size:12px; color:var(--dim); }
  nav.toc { display:flex; flex-wrap:wrap; gap:8px 18px; padding:16px 4vw; font-size:12.5px;
    border-bottom:1px solid var(--hair); }
  nav.toc a { color:var(--dim); text-decoration:none; letter-spacing:0.06em; }
  nav.toc a:hover { color:var(--ink); }
  section { padding: 4vh 4vw 2vh; }
  .album-head { display:flex; align-items:baseline; gap:14px; margin-bottom:16px; }
  .album-head h2 { font-size:13px; letter-spacing:0.28em; text-transform:uppercase; font-weight:650; }
  .tag { font-size:10px; letter-spacing:0.14em; text-transform:uppercase; padding:2px 8px;
    border-radius:3px; border:1px solid var(--hair); color:var(--dim); }
  .tag.pub { color:#2e6b45; border-color:#bcd8c6; }
  .tag.priv { color:var(--accent); border-color:#e0c8cb; }
  .meta { font-size:11.5px; color:var(--dim); letter-spacing:0.06em; }
  .grid { columns:5; column-gap:10px; }
  @media (max-width:1400px){ .grid{columns:4;} }
  @media (max-width:1000px){ .grid{columns:3;} }
  @media (max-width:640px){ .grid{columns:2;} }
  figure { break-inside:avoid; margin:0 0 10px; background:#fff; border:1px solid var(--hair);
    padding:4px; cursor:zoom-in; }
  figure img { width:100%; display:block; }
  figcaption { font-size:9.5px; color:var(--dim); padding:3px 2px 1px; overflow:hidden;
    text-overflow:ellipsis; white-space:nowrap; }
  #lb { position:fixed; inset:0; z-index:50; display:none; background:rgba(247,246,243,0.94);
    align-items:center; justify-content:center; }
  #lb.open { display:flex; }
  #lb img { max-width:94vw; max-height:90vh; background:#fff; padding:8px; border:1px solid var(--hair); }
  #lb .name { position:fixed; bottom:14px; left:0; right:0; text-align:center; font-size:12px; color:var(--dim); }
  #lb button { position:fixed; background:none; border:none; cursor:pointer; font-size:30px;
    padding:16px; opacity:0.5; color:var(--ink); }
  #lb button:hover { opacity:1; }
  #lb .close { top:8px; right:12px; } #lb .prev { left:6px; top:50%; } #lb .next { right:6px; top:50%; }
</style>
</head>
<body>
<header>
  <span class="mark">archive</span>
  <span class="private-badge">private — local only</span>
  <span class="note">__COUNTS__</span>
</header>
<nav class="toc">__TOC__</nav>
__SECTIONS__
<div id="lb">
  <button class="close">×</button><button class="prev">‹</button><button class="next">›</button>
  <img alt=""><div class="name"></div>
</div>
<script>
  const figs = [...document.querySelectorAll('figure')];
  const lb = document.getElementById('lb');
  const lbImg = lb.querySelector('img');
  const lbName = lb.querySelector('.name');
  let cur = -1;
  function show(i) {
    cur = (i + figs.length) % figs.length;
    const img = figs[cur].querySelector('img');
    lbImg.src = img.src;
    lbName.textContent = decodeURIComponent(img.src.split('/').slice(-2).join(' / '));
    lb.classList.add('open'); document.body.style.overflow = 'hidden';
  }
  function hide() { lb.classList.remove('open'); document.body.style.overflow = ''; }
  figs.forEach((f, i) => f.addEventListener('click', () => show(i)));
  lb.querySelector('.close').addEventListener('click', hide);
  lb.querySelector('.prev').addEventListener('click', e => { e.stopPropagation(); show(cur - 1); });
  lb.querySelector('.next').addEventListener('click', e => { e.stopPropagation(); show(cur + 1); });
  lb.addEventListener('click', e => { if (e.target === lb) hide(); });
  document.addEventListener('keydown', e => {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') hide();
    if (e.key === 'ArrowLeft') show(cur - 1);
    if (e.key === 'ArrowRight') show(cur + 1);
  });
</script>
</body>
</html>
"""


def section(anchor, title, tag, files, raw_count, prefix):
    figs = "\n".join(
        f'  <figure><img loading="lazy" src="{prefix}{html.escape(f)}" alt="">'
        f'<figcaption>{html.escape(f)}</figcaption></figure>'
        for f in files
    )
    raw_note = f" · {raw_count} RAW stored (not shown)" if raw_count else ""
    return f"""
<section id="{anchor}">
  <div class="album-head">
    <h2>{html.escape(title)}</h2>
    <span class="tag {'pub' if tag == 'published' else 'priv'}">{tag}</span>
    <span class="meta">{len(files)} shown{raw_note}</span>
  </div>
  <div class="grid">
{figs}
  </div>
</section>"""


def main():
    sections, toc, total, raw_total = [], [], 0, 0

    loose = sorted(p.name for p in INBOX.iterdir()
                   if p.is_file() and p.suffix.lower() in SHOW)
    loose_raw = sum(1 for p in INBOX.iterdir()
                    if p.is_file() and p.suffix.lower() in RAW)
    if loose or loose_raw:
        sections.append(section("inbox", "Inbox — unsorted", "private",
                                loose, loose_raw, ""))
        toc.append('<a href="#inbox">inbox</a>')
        total += len(loose); raw_total += loose_raw

    for d in sorted(p for p in INBOX.iterdir() if p.is_dir()):
        files = sorted(p.name for p in d.iterdir() if p.suffix.lower() in SHOW)
        raws = sum(1 for p in d.iterdir() if p.suffix.lower() in RAW)
        if not files and not raws:
            continue
        tag = "published" if d.name in PUBLISHED else "private"
        title = d.name.replace("-", " ").title()
        sections.append(section(d.name, title, tag, files, raws, f"{d.name}/"))
        toc.append(f'<a href="#{d.name}">{d.name}</a>')
        total += len(files); raw_total += raws

    page = (PAGE
            .replace("__COUNTS__", f"{total} photographs · {raw_total} RAW files stored")
            .replace("__TOC__", "\n".join(toc))
            .replace("__SECTIONS__", "\n".join(sections)))
    out = INBOX / "archive.html"
    out.write_text(page, encoding="utf-8")
    print(f"archive.html written: {total} shown, {raw_total} raw, "
          f"{len(sections)} sections -> {out}")


if __name__ == "__main__":
    main()
