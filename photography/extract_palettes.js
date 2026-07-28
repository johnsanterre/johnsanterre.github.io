// Extract a per-album palette from the photographs themselves.
// For each album: average the dominant color of every photo (via sharp
// stats), then derive a family: accent (deep, usable on paper), tint
// (near-white wash), hairline. Writes palettes.json for build_gallery.py.
const sharp = require('/Users/john/Dropbox/___AntiGravity/PhotoApp/server/node_modules/sharp');
const fs = require('fs');
const path = require('path');
const IMG = path.join(__dirname, 'img');

function rgbToHsl(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0; const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    if (max === r) h = ((g - b) / d + (g < b ? 6 : 0));
    else if (max === g) h = (b - r) / d + 2;
    else h = (r - g) / d + 4;
    h *= 60;
  }
  return [h, s * 100, l * 100];
}

(async () => {
  const out = {};
  for (const album of fs.readdirSync(IMG).filter(d => fs.statSync(path.join(IMG, d)).isDirectory())) {
    const files = fs.readdirSync(path.join(IMG, album)).filter(f => /\.(jpe?g|png|webp)$/i.test(f));
    let sx = 0, sy = 0, weight = 0; // average hue as vector; weight by saturation
    let satSum = 0, lSum = 0, n = 0;
    for (const f of files) {
      const { dominant } = await sharp(path.join(IMG, album, f)).stats();
      const [h, s, l] = rgbToHsl(dominant.r, dominant.g, dominant.b);
      const rad = h * Math.PI / 180;
      sx += Math.cos(rad) * s; sy += Math.sin(rad) * s;
      satSum += s; lSum += l; n++;
    }
    const hue = ((Math.atan2(sy, sx) * 180 / Math.PI) + 360) % 360;
    const sat = satSum / n, lig = lSum / n;
    out[album] = {
      hue: Math.round(hue),
      accent:  `hsl(${Math.round(hue)}, ${Math.round(Math.min(46, Math.max(30, sat * 1.4)))}%, 34%)`,
      tint:    `hsl(${Math.round(hue)}, 26%, 96.5%)`,
      hairline:`hsl(${Math.round(hue)}, 18%, 87%)`,
      note: `avg sat ${sat.toFixed(0)} lum ${lig.toFixed(0)} over ${n} photos`,
    };
  }
  fs.writeFileSync(path.join(__dirname, 'palettes.json'), JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
})();
