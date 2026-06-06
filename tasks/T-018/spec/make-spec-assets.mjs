import fs from "fs";
import path from "path";
import sharp from "sharp";

const ROOT = new URL(".", import.meta.url).pathname;

const brands = {
  gorgie: {
    name: "GORGIE",
    mark: "GORGIE",
    line: "made for GORGIE on spec",
    tone: "bright feminine energy, clean product accuracy, glossy daytime studio",
    bg: ["#fff3f8", "#f8ffda", "#f5ddff"],
    ink: "#351f62",
    accent: "#ef4f9a",
    files: ["source-01.avif", "source-02.png", "source-03.png", "source-04.avif"],
  },
  bloom: {
    name: "Bloom Nutrition",
    mark: "Bloom",
    line: "made for Bloom Nutrition on spec",
    tone: "fresh vibrant citrus, wellness retail polish, bright social-ready color",
    bg: ["#fff6d8", "#ffedf3", "#dff7d1"],
    ink: "#174f34",
    accent: "#ff4f8d",
    files: ["source-01.jpg", "source-02.png", "source-03.png", "source-04.jpg"],
  },
};

function svgOverlay({ brand, i, width, height }) {
  const [a, b, c] = brand.bg;
  const alpha = i % 2 ? 0.58 : 0.46;
  return Buffer.from(`
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="${a}" stop-opacity="${alpha}"/>
          <stop offset=".52" stop-color="${b}" stop-opacity=".18"/>
          <stop offset="1" stop-color="${c}" stop-opacity="${alpha}"/>
        </linearGradient>
        <radialGradient id="r" cx=".78" cy=".18" r=".65">
          <stop offset="0" stop-color="${brand.accent}" stop-opacity=".25"/>
          <stop offset=".55" stop-color="#ffffff" stop-opacity=".04"/>
          <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <rect width="${width}" height="${height}" fill="url(#g)" opacity=".55"/>
      <rect width="${width}" height="${height}" fill="url(#r)"/>
      <circle cx="${width * 0.14}" cy="${height * 0.18}" r="${width * 0.055}" fill="#fff" opacity=".48"/>
      <circle cx="${width * 0.88}" cy="${height * 0.82}" r="${width * 0.12}" fill="${brand.accent}" opacity=".10"/>
      <path d="M${width * 0.03},${height * 0.78} C${width * 0.26},${height * 0.68} ${width * 0.44},${height * 0.92} ${width * 0.68},${height * 0.76} S${width * 0.92},${height * 0.62} ${width},${height * 0.68}" fill="none" stroke="#fff" stroke-width="10" opacity=".32"/>
    </svg>
  `);
}

async function makeImage(brandKey, brand, file, index) {
  const source = path.join(ROOT, brandKey, "source", file);
  const out = path.join(ROOT, brandKey, "assets", `makeover-${String(index + 1).padStart(2, "0")}.jpg`);
  const width = 1440;
  const height = 1080;
  const sourceFrame = await sharp(source)
    .rotate()
    .resize(width, height, { fit: "contain", background: { r: 255, g: 255, b: 255, alpha: 0 } })
    .modulate({
      brightness: brandKey === "gorgie" ? 1.06 : 1.04,
      saturation: brandKey === "gorgie" ? 1.18 : 1.22,
    })
    .linear(1.04, -4)
    .png()
    .toBuffer();

  const base = Buffer.from(`
    <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="${brand.bg[0]}"/>
          <stop offset=".58" stop-color="#ffffff"/>
          <stop offset="1" stop-color="${brand.bg[2]}"/>
        </linearGradient>
      </defs>
      <rect width="${width}" height="${height}" fill="url(#bg)"/>
      <circle cx="${width * 0.88}" cy="${height * 0.12}" r="${width * 0.22}" fill="${brand.accent}" opacity=".13"/>
      <circle cx="${width * 0.12}" cy="${height * 0.84}" r="${width * 0.18}" fill="${brand.bg[1]}" opacity=".75"/>
    </svg>
  `);

  await sharp(base)
    .composite([
      { input: sourceFrame, blend: "over" },
      { input: svgOverlay({ brand, i: index, width, height }), blend: "soft-light" },
      {
        input: Buffer.from(`
          <svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
            <rect x="26" y="26" width="${width - 52}" height="${height - 52}" rx="34" fill="none" stroke="#ffffff" stroke-width="2" opacity=".64"/>
            <rect width="${width}" height="${height}" fill="none"/>
          </svg>
        `),
        blend: "over",
      },
    ])
    .sharpen({ sigma: 0.8, m1: 0.8, m2: 1.8 })
    .jpeg({ quality: 88, mozjpeg: true })
    .toFile(out);
}

function htmlFor(key, brand) {
  const shots = [1, 2, 3].map((n) => `assets/makeover-0${n}.jpg`);
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${brand.name} Spec Preview</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body class="${key}">
  <main class="shell">
    <section class="hero">
      <div class="brand">
        <p class="kicker">private creative preview</p>
        <h1>${brand.mark}</h1>
        <p class="tone">${brand.tone}</p>
      </div>
      <div class="gallery" aria-label="${brand.name} spec makeover gallery">
        ${shots.map((src, i) => `<figure class="shot shot-${i + 1}"><img src="${src}" alt="${brand.name} cinematic spec makeover ${i + 1}"></figure>`).join("\n        ")}
      </div>
      <p class="spec-line">${brand.line}</p>
    </section>
  </main>
</body>
</html>
`;
}

const css = `*{box-sizing:border-box}html,body{margin:0;min-height:100%;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--bg)}body{overflow-x:hidden}.shell{min-height:100svh;display:grid;place-items:center;padding:24px}.hero{width:min(1180px,100%);min-height:min(760px,calc(100svh - 48px));display:grid;grid-template-columns:minmax(260px,.86fr) 1.34fr;grid-template-rows:1fr auto;gap:28px;align-items:center;position:relative}.brand{padding:12px 0 52px}.kicker{margin:0 0 18px;text-transform:uppercase;font-size:12px;font-weight:800;letter-spacing:.12em}.brand h1{margin:0;font-size:clamp(58px,10vw,132px);line-height:.86;letter-spacing:0;text-transform:uppercase}.tone{max-width:390px;margin:24px 0 0;font-size:18px;line-height:1.35;font-weight:650}.gallery{display:grid;grid-template-columns:1.05fr .78fr;grid-template-rows:1fr 1fr;gap:14px;align-items:stretch}.shot{margin:0;overflow:hidden;border-radius:8px;box-shadow:0 28px 70px rgba(35,22,28,.18);background:#fff}.shot img{width:100%;height:100%;display:block;object-fit:cover}.shot-1{grid-row:1/3;min-height:580px}.shot-2,.shot-3{min-height:284px}.spec-line{grid-column:1/3;margin:0;padding-top:6px;font-size:15px;font-weight:850;text-transform:uppercase;letter-spacing:.08em}.gorgie{--bg:radial-gradient(circle at 88% 12%,#f5ddff 0 19%,transparent 38%),linear-gradient(135deg,#fff3f8 0%,#fbffe2 55%,#f4e9ff 100%);--ink:#351f62}.bloom{--bg:radial-gradient(circle at 88% 12%,#dff7d1 0 18%,transparent 38%),linear-gradient(135deg,#fff4cc 0%,#ffe9f0 48%,#e9f8d8 100%);--ink:#174f34}.bloom .shot{box-shadow:0 28px 70px rgba(23,79,52,.17)}@media(max-width:820px){.shell{padding:16px}.hero{min-height:auto;grid-template-columns:1fr;grid-template-rows:auto;gap:18px}.brand{padding:10px 0}.brand h1{font-size:clamp(54px,18vw,86px)}.tone{font-size:16px;margin-top:16px}.gallery{grid-template-columns:1fr;grid-template-rows:none}.shot-1{grid-row:auto;min-height:390px}.shot-2,.shot-3{min-height:280px}.spec-line{grid-column:auto;font-size:12px;line-height:1.35}}`;

for (const [key, brand] of Object.entries(brands)) {
  fs.mkdirSync(path.join(ROOT, key, "assets"), { recursive: true });
  fs.writeFileSync(path.join(ROOT, key, "styles.css"), css);
  fs.writeFileSync(path.join(ROOT, key, "index.html"), htmlFor(key, brand));
  fs.writeFileSync(path.join(ROOT, key, "vercel.json"), JSON.stringify({ cleanUrls: true }, null, 2) + "\n");
  for (const [i, file] of brand.files.entries()) {
    await makeImage(key, brand, file, i);
  }
}
