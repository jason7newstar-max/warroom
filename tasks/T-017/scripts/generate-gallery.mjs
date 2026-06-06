import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const site = path.join(root, "site");

const W = 1672;
const H = 941;

const products = [
  {
    id: "alani",
    input: "alani-nu-variety.png",
    scale: 0.57,
    x: 350,
    y: 245,
    scenes: [
      ["gallery/alani-scene-02.png", "turquoise", "#35f1db", "#ff3d8e", 0],
      ["gallery/alani-scene-03.png", "afterglow", "#ff5b7a", "#ffe35c", 1],
    ],
  },
  {
    id: "cherry",
    input: "celsius-cherry-cola.png",
    scale: 0.58,
    x: 640,
    y: 120,
    scenes: [
      ["gallery/celsius-cherry-cola-scene-02.png", "cola", "#f03a73", "#2be4ff", 2],
      ["gallery/celsius-cherry-cola-scene-03.png", "backbar", "#ff2f66", "#ffd166", 3],
    ],
  },
  {
    id: "blue",
    input: "celsius-blue-crush.png",
    scale: 0.72,
    x: 590,
    y: 150,
    scenes: [
      ["gallery/celsius-blue-crush-scene-02.png", "blue", "#16d9ff", "#f0fbff", 4],
      ["gallery/celsius-blue-crush-scene-03.png", "laser", "#00b7ff", "#ff3bbd", 5],
    ],
  },
];

function bgSvg(label, a, b, variant) {
  const lineA = 130 + variant * 23;
  const lineB = 760 - variant * 31;
  return `
  <svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <radialGradient id="g1" cx="30%" cy="10%" r="70%">
        <stop offset="0%" stop-color="${a}" stop-opacity=".34"/>
        <stop offset="38%" stop-color="#121522" stop-opacity=".62"/>
        <stop offset="100%" stop-color="#05070c"/>
      </radialGradient>
      <radialGradient id="g2" cx="82%" cy="18%" r="54%">
        <stop offset="0%" stop-color="${b}" stop-opacity=".34"/>
        <stop offset="52%" stop-color="#0a0d15" stop-opacity=".44"/>
        <stop offset="100%" stop-color="#05070c" stop-opacity="0"/>
      </radialGradient>
      <linearGradient id="floor" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="#0a1018" stop-opacity=".08"/>
        <stop offset="62%" stop-color="#111827" stop-opacity=".74"/>
        <stop offset="100%" stop-color="#020308"/>
      </linearGradient>
      <filter id="blur"><feGaussianBlur stdDeviation="18"/></filter>
      <filter id="soft"><feGaussianBlur stdDeviation="7"/></filter>
    </defs>
    <rect width="100%" height="100%" fill="#05070c"/>
    <rect width="100%" height="100%" fill="url(#g1)"/>
    <rect width="100%" height="100%" fill="url(#g2)"/>
    <g opacity=".34" filter="url(#blur)">
      <circle cx="${220 + variant * 70}" cy="180" r="80" fill="${a}"/>
      <circle cx="${1360 - variant * 35}" cy="260" r="96" fill="${b}"/>
      <circle cx="${760 + variant * 18}" cy="105" r="44" fill="#ffffff"/>
    </g>
    <g opacity=".25" stroke-width="4" stroke-linecap="round" filter="url(#soft)">
      <path d="M-80 ${lineA} C 320 ${lineA - 90}, 520 ${lineA + 80}, 980 ${lineA - 20} S 1460 ${lineA - 120}, 1760 ${lineA - 40}" stroke="${a}" fill="none"/>
      <path d="M-120 ${lineB} C 320 ${lineB - 180}, 670 ${lineB + 20}, 1030 ${lineB - 90} S 1460 ${lineB - 20}, 1780 ${lineB - 150}" stroke="${b}" fill="none"/>
    </g>
    <rect y="596" width="100%" height="345" fill="url(#floor)"/>
    <path d="M0 640 C 260 604, 430 622, 610 650 C 800 680, 1010 655, 1230 620 C 1410 592, 1540 612, 1672 632 L1672 941 L0 941 Z" fill="#111827" opacity=".56"/>
    <g opacity=".22">
      <line x1="0" y1="725" x2="1672" y2="648" stroke="#ffffff" stroke-opacity=".2"/>
      <line x1="0" y1="812" x2="1672" y2="745" stroke="${a}" stroke-opacity=".18"/>
      <line x1="0" y1="894" x2="1672" y2="846" stroke="${b}" stroke-opacity=".18"/>
    </g>
    <rect width="100%" height="100%" fill="#000" opacity=".18"/>
    <text x="66" y="874" font-family="Arial, Helvetica, sans-serif" font-size="15" letter-spacing="6" fill="#ffffff" opacity=".26">${label.toUpperCase()} / REAL PRODUCT</text>
  </svg>`;
}

async function main() {
  for (const product of products) {
    const input = path.join(site, "assets/products", product.input);
    const meta = await sharp(input).metadata();
    const width = Math.round(meta.width * product.scale);
    const height = Math.round(meta.height * product.scale);
    const can = await sharp(input).resize(width, height).png().toBuffer();
    for (const [out, label, a, b, variant] of product.scenes) {
      const bg = await sharp(Buffer.from(bgSvg(label, a, b, variant))).png().toBuffer();
      await sharp(bg)
        .composite([
          { input: can, left: product.x, top: product.y },
        ])
        .png({ compressionLevel: 9 })
        .toFile(path.join(site, "assets", out));
    }
  }
}

await main();
