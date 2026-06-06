import fs from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const root = new URL(".", import.meta.url).pathname;

const cafes = [
  {
    slug: "cafe-erzulie",
    sources: ["source-01.jpg", "source-02.jpg", "source-03.jpg"],
    modulate: { brightness: 1.08, saturation: 1.28, hue: 5 },
    tint: { r: 255, g: 160, b: 72, a: 0.16 },
    glow: { r: 254, g: 66, b: 128, a: 0.13 },
  },
  {
    slug: "abbotsford-road",
    sources: ["source-01.webp", "source-02.jpg", "source-03.jpg"],
    modulate: { brightness: 0.82, saturation: 0.74, hue: 0 },
    tint: { r: 22, g: 24, b: 22, a: 0.18 },
    glow: { r: 205, g: 214, b: 202, a: 0.09 },
  },
  {
    slug: "devocion",
    sources: ["source-01.jpg", "source-02.jpg", "source-03.png"],
    modulate: { brightness: 0.98, saturation: 1.2, hue: 28 },
    tint: { r: 22, g: 80, b: 43, a: 0.16 },
    glow: { r: 155, g: 204, b: 119, a: 0.16 },
  },
];

function svgOverlay(width, height, cafe) {
  const { tint, glow } = cafe;
  return Buffer.from(`
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="g" cx="22%" cy="15%" r="72%">
          <stop offset="0" stop-color="rgba(${glow.r},${glow.g},${glow.b},${glow.a})"/>
          <stop offset="0.46" stop-color="rgba(${glow.r},${glow.g},${glow.b},0)"/>
        </radialGradient>
        <linearGradient id="v" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0" stop-color="rgba(${tint.r},${tint.g},${tint.b},${tint.a})"/>
          <stop offset="0.55" stop-color="rgba(0,0,0,0)"/>
          <stop offset="1" stop-color="rgba(0,0,0,0.24)"/>
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" fill="url(#g)"/>
      <rect width="100%" height="100%" fill="url(#v)"/>
      <rect x="18" y="18" width="${width - 36}" height="${height - 36}" rx="18" fill="none" stroke="rgba(255,255,255,0.18)" stroke-width="2"/>
    </svg>
  `);
}

async function render(cafe) {
  const dir = path.join(root, cafe.slug, "assets");
  await Promise.all(
    cafe.sources.map(async (source, index) => {
      const width = index === 0 ? 1500 : 980;
      const height = index === 0 ? 1100 : 1220;
      const inFile = path.join(dir, source);
      const outFile = path.join(dir, `makeover-0${index + 1}.jpg`);
      await sharp(inFile)
        .rotate()
        .resize(width, height, { fit: "cover", position: "attention" })
        .modulate(cafe.modulate)
        .linear(1.06, -8)
        .sharpen({ sigma: 0.7, m1: 1.2, m2: 1.8 })
        .composite([{ input: svgOverlay(width, height, cafe), blend: "over" }])
        .jpeg({ quality: 89, progressive: true })
        .toFile(outFile);
    })
  );
}

await Promise.all(cafes.map(render));
