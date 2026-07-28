#!/usr/bin/env python3
"""Build the PRIVATE local archive browser inside photos-inbox/ (gitignored).

Home page (archive.html):
  - the UNSORTED inbox photos as a grid up top (these need organizing —
    drag them into folders in Finder)
  - below, the albums as compact cover tiles only — click into an album

Album pages (archive-<name>.html): the album's photos with lightbox.

JPG/PNG rendered; RAW files stored alongside are counted, never shown.
Run after any reorganizing:  python3 photography/build_archive.py
(or double-click photos-inbox/Refresh Archive.command)
"""

import html
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
INBOX = HERE.parent / "photos-inbox"
PUBLISHED = {p.name for p in (HERE / "img").iterdir() if p.is_dir()}
SHOW = (".jpg", ".jpeg", ".png", ".webp")
RAW = (".cr2", ".raf", ".arw", ".dng", ".nef", ".orf", ".rw2")

STYLE = """
  :root { --paper:#f7f6f3; --ink:#1c1b18; --dim:#8a867c; --hair:#e5e2db; --accent:#7C2530; }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--paper); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",Helvetica,Arial,sans-serif; }
  a { color:inherit; text-decoration:none; }
  header { display:flex; align-items:baseline; gap:14px; padding:22px 3vw 16px;
    border-bottom:1px solid var(--hair); position:sticky; top:0; background:var(--paper); z-index:5; }
  .mark { font-size:15px; letter-spacing:0.34em; font-weight:700; }
  .private-badge { font-size:10.5px; letter-spacing:0.2em; color:#fff; background:var(--accent);
    padding:3px 9px; border-radius:3px; text-transform:uppercase; }
  header .note { margin-left:auto; font-size:12px; color:var(--dim); }
  header .back { font-size:12.5px; color:var(--dim); }
  header .back:hover { color:var(--ink); }
  h2.sec { font-size:12.5px; letter-spacing:0.28em; text-transform:uppercase; color:var(--dim);
    padding:4vh 3vw 14px; }
  /* Row-major grid: reads left→right then next row (chronology stays
     readable). Uniform thumb cells; lightbox shows the full frame. */
  .grid { display:grid; grid-template-columns:repeat(5, 1fr); gap:10px; padding:0 3vw 3vh; }
  @media (max-width:1400px){ .grid{grid-template-columns:repeat(4,1fr);} }
  @media (max-width:1000px){ .grid{grid-template-columns:repeat(3,1fr);} }
  @media (max-width:640px){ .grid{grid-template-columns:repeat(2,1fr);} }
  figure { margin:0; background:#fff; border:1px solid var(--hair);
    padding:4px; cursor:zoom-in; }
  figure img { width:100%; aspect-ratio:3/2; object-fit:cover; display:block; }
  figcaption { font-size:9.5px; color:var(--dim); padding:3px 2px 1px; overflow:hidden;
    text-overflow:ellipsis; white-space:nowrap; }
  .albums { display:grid; gap:16px; padding:0 3vw 8vh;
    grid-template-columns:repeat(auto-fill, minmax(210px, 1fr)); }
  .alb { background:#fff; border:1px solid var(--hair); padding:6px; }
  .alb img { width:100%; aspect-ratio:4/3; object-fit:cover; display:block; }
  .alb .row { display:flex; align-items:baseline; gap:8px; padding:8px 3px 3px; }
  .alb .name { font-size:11.5px; letter-spacing:0.16em; text-transform:uppercase; font-weight:650; }
  .alb .n { margin-left:auto; font-size:10.5px; color:var(--dim); }
  .tag { font-size:9px; letter-spacing:0.1em; text-transform:uppercase; padding:1px 6px;
    border-radius:3px; border:1px solid var(--hair); color:var(--dim); }
  .tag.pub { color:#2e6b45; border-color:#bcd8c6; }
  .empty { padding:2vh 3vw 4vh; color:var(--dim); font-size:13.5px; }
  .sortbar { display:flex; gap:8px; align-items:baseline; padding:14px 3vw 0;
    font-size:11.5px; color:var(--dim); }
  .sortbar button { font-size:11px; padding:3px 10px; border:1px solid var(--hair);
    background:none; border-radius:99px; cursor:pointer; color:var(--dim); letter-spacing:0.06em; }
  .sortbar button.on { border-color:var(--ink); color:var(--ink); }
  .cap-date { float:right; opacity:0.75; }
  #lb { position:fixed; inset:0; z-index:50; display:none; background:rgba(247,246,243,0.95);
    align-items:center; justify-content:center; }
  #lb.open { display:flex; }
  #lb img { max-width:94vw; max-height:88vh; background:#fff; padding:8px; border:1px solid var(--hair); }
  #lb .name { position:fixed; bottom:14px; left:0; right:0; text-align:center; font-size:12px; color:var(--dim); }
  #lb button { position:fixed; background:none; border:none; cursor:pointer; font-size:30px;
    padding:16px; opacity:0.5; color:var(--ink); }
  #lb button:hover { opacity:1; }
  #lb .close { top:8px; right:12px; } #lb .prev { left:6px; top:50%; } #lb .next { right:6px; top:50%; }
"""

LIGHTBOX = """
<div class="sortbar"><span>sort:</span>
  <button data-mode="date" class="on">date captured</button>
  <button data-mode="name">filename</button>
</div>
<div id="lb">
  <button class="close">×</button><button class="prev">‹</button><button class="next">›</button>
  <img alt=""><div class="name"></div>
</div>
<script>
  // sort every grid by capture date (default) or filename
  function applySort(mode) {
    document.querySelectorAll('.grid').forEach(g => {
      [...g.children]
        .sort((a, b) => mode === 'date'
          ? (a.dataset.date || '9').localeCompare(b.dataset.date || '9')
          : (a.dataset.name || '').localeCompare(b.dataset.name || ''))
        .forEach(el => g.appendChild(el));
    });
    document.querySelectorAll('.sortbar button').forEach(b =>
      b.classList.toggle('on', b.dataset.mode === mode));
    rebind();
  }
  document.querySelectorAll('.sortbar button').forEach(b =>
    b.addEventListener('click', () => applySort(b.dataset.mode)));

  let figs = [];
  const lb = document.getElementById('lb');
  const lbImg = lb.querySelector('img');
  const lbName = lb.querySelector('.name');
  let cur = -1;
  function show(i) {
    if (!figs.length) return;
    cur = (i + figs.length) % figs.length;
    const img = figs[cur].querySelector('img');
    lbImg.src = img.src;
    lbName.textContent = decodeURIComponent(img.src.split('/').pop());
    lb.classList.add('open'); document.body.style.overflow = 'hidden';
  }
  function hide() { lb.classList.remove('open'); document.body.style.overflow = ''; }
  function rebind() {
    figs = [...document.querySelectorAll('figure')];
    figs.forEach((f, i) => { f.onclick = () => show(i); });
  }
  applySort('date');
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
"""


def page(title, header_extra, body):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<header>
  <a class="mark" href="archive.html">archive</a>
  <span class="private-badge">private — local only</span>
  {header_extra}
</header>
{body}
{LIGHTBOX}
</body>
</html>
"""


def capture_dates():
    """relpath -> ISO capture datetime (EXIF, falling back to mtime)."""
    try:
        out = subprocess.run(
            ["node", str(HERE / "scan_dates.js")],
            capture_output=True, text=True, timeout=600, check=True)
        return json.loads(out.stdout)
    except Exception:
        return {}


DATES = {}


def figs_html(files, prefix):
    return "\n".join(
        f'  <figure data-date="{DATES.get(prefix + f, "")}" data-name="{html.escape(f)}">'
        f'<img loading="lazy" src="{prefix}{html.escape(f)}" alt="">'
        f'<figcaption>{html.escape(f)}'
        f'<span class="cap-date">{DATES.get(prefix + f, "")[:10]}</span></figcaption></figure>'
        for f in files
    )


def walk_albums():
    """Every directory (any depth, skipping voice/) with its DIRECT files.
    Album id = relative path; nested dirs are their own albums."""
    out = []
    def rec(d):
        rel = str(d.relative_to(INBOX))
        files = sorted(p.name for p in d.iterdir()
                       if p.is_file() and p.suffix.lower() in SHOW)
        raws = sum(1 for p in d.iterdir()
                   if p.is_file() and p.suffix.lower() in RAW)
        subs = sorted(p for p in d.iterdir() if p.is_dir())
        out.append((rel, files, raws, len(subs)))
        for s_ in subs:
            rec(s_)
    for d in sorted(p for p in INBOX.iterdir() if p.is_dir()):
        if d.name == "voice":
            continue
        rec(d)
    return out


def slug(rel):
    return rel.replace("/", "--").replace(" ", "_")


def main():
    global DATES
    DATES = capture_dates()
    albums = walk_albums()

    loose = sorted(p.name for p in INBOX.iterdir()
                   if p.is_file() and p.suffix.lower() in SHOW)
    loose_raw = sum(1 for p in INBOX.iterdir()
                    if p.is_file() and p.suffix.lower() in RAW)

    # --- home: unsorted grid + album tiles ---
    if loose:
        unsorted_html = (f'<h2 class="sec">Unsorted — {len(loose)} to organize'
                         f'{f" · {loose_raw} RAW" if loose_raw else ""}</h2>\n'
                         f'<div class="grid">\n{figs_html(loose, "")}\n</div>')
    else:
        unsorted_html = '<p class="empty">Inbox clear — nothing unsorted.</p>'

    tiles = []
    for rel, files, raws, nsubs in albums:
        if not files and not raws and not nsubs:
            continue
        cover = files[0] if files else None
        cover_html = (f'<img loading="lazy" src="{rel}/{html.escape(cover)}" alt="">'
                      if cover else '<span style="display:block;aspect-ratio:4/3;background:var(--paper)"></span>')
        tag = ('<span class="tag pub">published</span>'
               if rel in PUBLISHED else '<span class="tag">private</span>')
        bits = [str(len(files))] if files else []
        if raws: bits.append(f'+{raws} raw')
        if nsubs: bits.append(f'{nsubs} sub')
        tiles.append(
            f'<a class="alb" href="archive-{slug(rel)}.html">{cover_html}'
            f'<span class="row"><span class="name">{html.escape(rel)}</span>'
            f'{tag}<span class="n">{" · ".join(bits)}</span></span></a>'
        )
    albums_html = ('<h2 class="sec">Albums</h2>\n<div class="albums">\n'
                   + "\n".join(tiles) + "\n</div>")

    total = len(loose) + sum(len(f) for _, f, _, _ in albums)
    raw_total = loose_raw + sum(r for _, _, r, _ in albums)
    home = page("Archive — private",
                f'<span class="note">{total} photographs · {raw_total} RAW stored</span>',
                unsorted_html + "\n" + albums_html)
    (INBOX / "archive.html").write_text(home, encoding="utf-8")

    # --- album pages (nested dirs get their own pages + sub links) ---
    for rel, files, raws, nsubs in albums:
        subs = [a for a in albums if a[0].startswith(rel + "/")
                and a[0].count("/") == rel.count("/") + 1]
        sub_html = ""
        if subs:
            sub_tiles = "".join(
                f'<a class="alb" href="archive-{slug(r)}.html">'
                + (f'<img loading="lazy" src="{r}/{html.escape(f2[0])}" alt="">' if f2 else "")
                + f'<span class="row"><span class="name">{html.escape(r.split("/")[-1])}</span>'
                  f'<span class="n">{len(f2)}{f" +{rw} raw" if rw else ""}</span></span></a>'
                for r, f2, rw, _ in subs)
            sub_html = f'<div class="albums" style="padding-top:2vh">{sub_tiles}</div>'
        body = f'<h2 class="sec">{html.escape(rel)} — {len(files)} photographs' \
               f'{f" · {raws} RAW stored" if raws else ""}</h2>\n' + sub_html
        if files:
            body += f'\n<div class="grid">\n{figs_html(files, f"{rel}/")}\n</div>'
        elif not subs:
            body = f'<p class="empty">{html.escape(rel)} — no viewable photos' \
                   f'{f" ({raws} RAW stored)" if raws else ""}.</p>'
        p = page(f"{rel} — archive",
                 '<a class="back" href="archive.html">← all albums</a>',
                 body)
        (INBOX / f"archive-{slug(rel)}.html").write_text(p, encoding="utf-8")

    print(f"archive rebuilt: home ({len(loose)} unsorted) + {len(albums)} album pages")


if __name__ == "__main__":
    main()
