#!/usr/bin/env python3
"""Regenerate the photography gallery from img/.

Scans photography/img/ for web images, reads their dimensions, and
rewrites the gallery grid inside index.html between the GALLERY:BEGIN /
GALLERY:END markers. Run after adding or removing photos:

    python3 photography/build_gallery.py
"""

import re
import struct
from pathlib import Path

HERE = Path(__file__).parent
IMG = HERE / "img"
PAGE = HERE / "index.html"


def jpeg_size(path):
    with open(path, "rb") as f:
        data = f.read(64 * 1024)
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        seg_len = struct.unpack(">H", data[i + 2:i + 4])[0]
        i += 2 + seg_len
    return None


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", head[16:24])
        return w, h
    return None


def main():
    # Each subfolder of img/ is an album; loose files form an untitled set.
    sections = []
    albums = sorted(d for d in IMG.iterdir() if d.is_dir())
    for album in albums:
        tiles = []
        for p in sorted(album.iterdir()):
            if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                continue
            tiles.append(
                f'    <figure><img loading="lazy" '
                f'src="img/{album.name}/{p.name}" alt=""></figure>'
            )
        if tiles:
            title = album.name.replace("-", " ").replace("_", " ").title()
            sections.append(
                f'  <h2 class="album">{title}</h2>\n  <div class="album-grid">\n'
                + "\n".join(tiles) + "\n  </div>"
            )
    block = "\n".join(sections) if sections else '    <p class="empty">Prints arriving.</p>'
    html = PAGE.read_text(encoding="utf-8")
    html = re.sub(
        r"(<!-- GALLERY:BEGIN -->).*?(<!-- GALLERY:END -->)",
        lambda m: m.group(1) + "\n" + block + "\n" + m.group(2),
        html, flags=re.S,
    )
    PAGE.write_text(html, encoding="utf-8")
    print(f"gallery rebuilt: {len(tiles)} photos")


if __name__ == "__main__":
    main()
