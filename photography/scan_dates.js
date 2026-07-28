// Emit {relpath: iso-datetime} for every image in photos-inbox (used by
// build_archive.py to enable sort-by-capture-date).
const exifr = require('/Users/john/Dropbox/___AntiGravity/PhotoApp/server/node_modules/exifr');
const fs = require('fs');
const path = require('path');
const INBOX = path.join(__dirname, '..', 'photos-inbox');
const exts = /\.(jpe?g|png)$/i;
(async () => {
  const out = {};
  async function walk(dir, rel) {
    for (const f of fs.readdirSync(dir)) {
      const full = path.join(dir, f);
      const r = rel ? rel + '/' + f : f;
      const st = fs.statSync(full);
      if (st.isDirectory()) { if (f !== 'voice') await walk(full, r); continue; }
      if (!exts.test(f)) continue;
      try {
        const d = await exifr.parse(full, ['DateTimeOriginal', 'CreateDate']);
        const dt = d?.DateTimeOriginal || d?.CreateDate;
        out[r] = dt ? dt.toISOString() : st.mtime.toISOString();
      } catch { out[r] = st.mtime.toISOString(); }
    }
  }
  await walk(INBOX, '');
  console.log(JSON.stringify(out));
})();
