import { cpSync, existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { execFileSync } from "node:child_process";
import { homedir } from "node:os";

const root = resolve(new URL("../..", import.meta.url).pathname);
const task = join(root, "tasks", "T-014");
const tempRoot = join(task, ".render-t014");
const downloads = join(homedir(), "Downloads");
const bgm = join(task, "assets", "chrome_riddle_bgm.mp3");

const videos = [
  {
    id: "01",
    product: "Alani Nu Beach Blend",
    image: "alani_scene_v2.png",
    accent: "#22f3ff",
    accent2: "#ff2cbf",
    template: "scanline",
    top: "Last set energy, stocked for sunrise",
    bottom: "Bright tropical cans for the night shift",
    cta: "Tap to grab yours",
  },
  {
    id: "02",
    product: "Celsius Cherry Cola",
    image: "celsius_cherrycola_scene_v2.png",
    accent: "#ff2d7f",
    accent2: "#20d9ff",
    template: "shutter",
    top: "Cherry cola sparkle after dark",
    bottom: "Cold, crisp energy for the next venue",
    cta: "Tap to grab yours",
  },
  {
    id: "03",
    product: "Celsius Blue Crush",
    image: "celsius_bluecrush_scene_v2.png",
    accent: "#10d7ff",
    accent2: "#ff45d6",
    template: "pulse",
    top: "Blue crush for the midnight run",
    bottom: "Zero sugar energy with club-light chill",
    cta: "Tap for Blue Crush",
  },
  {
    id: "04",
    product: "Alani Nu Beach Blend",
    image: "alani_scene_v2.png",
    accent: "#ff3abf",
    accent2: "#65fff2",
    template: "ribbons",
    top: "Festival bag, cooler, afterparty",
    bottom: "Three bright flavors built for long nights",
    cta: "Tap for festival fuel",
  },
  {
    id: "05",
    product: "Celsius Cherry Cola",
    image: "celsius_cherrycola_scene_v2.png",
    accent: "#ff184f",
    accent2: "#2ff7ff",
    template: "strobe",
    top: "When the lights come back up",
    bottom: "Cherry cola energy keeps the plan moving",
    cta: "Tap to shop now",
  },
];

function html(v) {
  const safeTop = 250;
  const bottomCaption = 1310;
  const ctaTop = 1454;
  const ctaHeight = 78;
  const lines = v.top.length > 28 ? v.top.replace(", ", ",<br />") : v.top;
  const scriptByTemplate = {
    scanline: `
      tl.from("#scene",{scale:1.015,x:-14,y:6,duration:12,ease:"none"},0).to("#scene",{scale:1.09,x:18,y:-8,duration:12,ease:"none"},0)
        .to("#scan",{opacity:.58,x:1580,duration:1.05,ease:"power2.inOut",repeat:5,repeatDelay:1.15},.8)
        .to(".laser",{opacity:.58,x:180,duration:1.65,yoyo:true,repeat:6,ease:"sine.inOut",stagger:.22},1.0);`,
    shutter: `
      tl.from("#scene",{scale:1.08,x:16,duration:12,ease:"none"},0).to("#scene",{scale:1.025,x:-18,y:4,duration:12,ease:"none"},0)
        .from(".slat",{scaleX:0,opacity:0,duration:.42,ease:"power3.out",stagger:.05,transformOrigin:"left center"},.15)
        .to(".slat",{x:90,opacity:.28,duration:1.1,yoyo:true,repeat:8,ease:"sine.inOut",stagger:.06},1.0);`,
    pulse: `
      tl.from("#scene",{scale:1.045,y:8,duration:12,ease:"none"},0).to("#scene",{scale:1.12,y:-10,duration:12,ease:"none"},0)
        .to("#halo",{opacity:.72,scale:1.08,duration:.55,yoyo:true,repeat:11,repeatDelay:.48,ease:"sine.inOut"},1.0)
        .to(".dot",{opacity:.9,scale:1.9,duration:.24,yoyo:true,repeat:14,repeatDelay:.45,stagger:.16,ease:"sine.inOut"},1.2);`,
    ribbons: `
      tl.from("#scene",{scale:1.02,x:10,duration:12,ease:"none"},0).to("#scene",{scale:1.095,x:-18,y:-6,duration:12,ease:"none"},0)
        .from(".ribbon",{opacity:0,x:-360,duration:.7,ease:"power3.out",stagger:.12},.65)
        .to(".ribbon",{x:360,opacity:.5,duration:1.45,yoyo:true,repeat:6,ease:"sine.inOut",stagger:.18},1.1);`,
    strobe: `
      tl.from("#scene",{scale:1.075,x:-10,duration:12,ease:"none"},0).to("#scene",{scale:1.025,x:16,y:-4,duration:12,ease:"none"},0)
        .to("#flash",{opacity:.28,duration:.08,yoyo:true,repeat:20,repeatDelay:.38,ease:"steps(1)"},1.1)
        .to(".laser",{opacity:.62,x:220,duration:.95,yoyo:true,repeat:10,ease:"power1.inOut",stagger:.12},.9);`,
  };
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#030407;font-family:Inter,"Helvetica Neue",Arial,sans-serif}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:radial-gradient(circle at 18% 16%,${v.accent}30,transparent 30%),radial-gradient(circle at 84% 86%,${v.accent2}2e,transparent 34%),linear-gradient(180deg,#05060c 0%,#111320 44%,#070811 100%)}
.clip{position:absolute;will-change:transform,opacity,filter}.band{left:0;width:1080px;overflow:hidden}.band:before{content:"";position:absolute;inset:-60px;background:linear-gradient(110deg,transparent 0%,rgba(255,255,255,.08) 46%,transparent 58%),repeating-linear-gradient(90deg,rgba(255,255,255,.032) 0 1px,transparent 1px 42px);opacity:.55;filter:blur(1px)}
#top-band{top:0;height:656px}#bottom-band{top:1264px;height:656px}
#image-wrap{left:0;top:656px;width:1080px;height:608px;overflow:hidden;border-top:2px solid rgba(255,255,255,.18);border-bottom:2px solid rgba(255,255,255,.18);box-shadow:0 0 64px ${v.accent}28,0 0 90px ${v.accent2}28;background:#090a10}
#scene{left:0;top:0;width:1080px;height:608px;object-fit:cover;transform-origin:52% 66%}
#image-glow{inset:0;background:radial-gradient(circle at 50% 62%,transparent 34%,rgba(0,0,0,.28) 100%),linear-gradient(90deg,rgba(0,0,0,.28),transparent 18%,transparent 82%,rgba(0,0,0,.28));pointer-events:none}
#scan{left:-270px;top:0;width:230px;height:1920px;transform:skewX(-16deg);background:linear-gradient(90deg,transparent,rgba(255,255,255,.22),transparent);filter:blur(28px);opacity:0}
.laser{width:1380px;height:7px;left:-190px;border-radius:999px;filter:blur(3px);opacity:0}.laser.a{top:318px;background:${v.accent};box-shadow:0 0 38px ${v.accent};transform:rotate(-14deg)}.laser.b{top:1585px;background:${v.accent2};box-shadow:0 0 42px ${v.accent2};transform:rotate(12deg)}
.copy{left:68px;right:68px;color:#fff;text-align:center;text-shadow:0 8px 28px rgba(0,0,0,.88),0 0 32px ${v.accent}38}
#top-caption{top:${safeTop}px;font-size:60px;line-height:1.06;font-weight:950;letter-spacing:0;text-transform:uppercase}
#top-kicker{top:474px;font-size:28px;font-weight:850;letter-spacing:6px;color:${v.accent};text-transform:uppercase}
#bottom-caption{top:${bottomCaption}px;font-size:46px;line-height:1.12;font-weight:920;letter-spacing:0}
#bottom-cta{left:190px;right:190px;top:${ctaTop}px;height:${ctaHeight}px;display:flex;align-items:center;justify-content:center;border:2px solid rgba(255,255,255,.76);border-radius:8px;background:rgba(5,6,11,.74);color:#fff;font-size:30px;font-weight:950;letter-spacing:3px;text-transform:uppercase;text-shadow:0 3px 18px rgba(0,0,0,.95);box-shadow:0 0 42px ${v.accent2}54,inset 0 0 34px ${v.accent}33}
.slat{left:-30px;width:1140px;height:78px;background:linear-gradient(90deg,transparent,${v.accent}55,transparent);filter:blur(2px);opacity:.34}.slat.s1{top:190px}.slat.s2{top:360px}.slat.s3{top:1410px}.slat.s4{top:1580px}
#halo{left:86px;top:704px;width:908px;height:520px;border:2px solid ${v.accent}66;border-radius:50%;filter:blur(10px);opacity:.15}.dot{width:12px;height:12px;border-radius:50%;background:#fff;box-shadow:0 0 22px #fff,0 0 38px ${v.accent};opacity:0}.d1{left:158px;top:438px}.d2{left:862px;top:1430px}.d3{left:760px;top:1662px}
.ribbon{left:-260px;width:1600px;height:11px;border-radius:999px;filter:blur(3px);opacity:.45;background:${v.accent};box-shadow:0 0 30px ${v.accent}}.r1{top:290px;transform:rotate(-18deg)}.r2{top:1522px;transform:rotate(15deg);background:${v.accent2};box-shadow:0 0 30px ${v.accent2}}#flash{inset:0;background:#fff;opacity:0;mix-blend-mode:screen;pointer-events:none}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="12" data-width="1080" data-height="1920">
<div id="top-band" class="clip band" data-start="0" data-duration="12" data-track-index="1"></div>
<div id="bottom-band" class="clip band" data-start="0" data-duration="12" data-track-index="2"></div>
<div id="image-wrap" class="clip" data-start="0" data-duration="12" data-track-index="3"><img id="scene" class="clip" src="assets/images/${v.image}" data-layout-allow-overflow data-start="0" data-duration="12" data-track-index="4" alt="" /><div id="image-glow" class="clip" data-start="0" data-duration="12" data-track-index="5"></div></div>
<div id="scan" class="clip" data-start=".7" data-duration="10.5" data-track-index="6"></div><div id="laser-a" class="clip laser a" data-start=".6" data-duration="11" data-track-index="7"></div><div id="laser-b" class="clip laser b" data-start=".9" data-duration="10.8" data-track-index="8"></div><div id="slat-1" class="clip slat s1" data-start=".1" data-duration="11.5" data-track-index="9"></div><div id="slat-2" class="clip slat s2" data-start=".1" data-duration="11.5" data-track-index="10"></div><div id="slat-3" class="clip slat s3" data-start=".1" data-duration="11.5" data-track-index="11"></div><div id="slat-4" class="clip slat s4" data-start=".1" data-duration="11.5" data-track-index="12"></div><div id="halo" class="clip" data-start=".4" data-duration="11.2" data-track-index="13"></div><div id="dot-1" class="clip dot d1" data-start="1" data-duration="10" data-track-index="14"></div><div id="dot-2" class="clip dot d2" data-start="1.2" data-duration="10" data-track-index="15"></div><div id="dot-3" class="clip dot d3" data-start="1.4" data-duration="10" data-track-index="16"></div><div id="ribbon-1" class="clip ribbon r1" data-start=".4" data-duration="11.1" data-track-index="17"></div><div id="ribbon-2" class="clip ribbon r2" data-start=".6" data-duration="11" data-track-index="18"></div><div id="flash" class="clip" data-start=".8" data-duration="10.8" data-track-index="19"></div>
<div id="top-caption" class="clip copy" data-start=".2" data-duration="11.4" data-track-index="20">${lines}</div>
<div id="top-kicker" class="clip copy" data-start=".55" data-duration="11" data-track-index="21">${v.product}</div>
<div id="bottom-caption" class="clip copy" data-start=".45" data-duration="11.2" data-track-index="22">${v.bottom}</div>
<div id="bottom-cta" class="clip copy" data-start=".8" data-duration="10.9" data-track-index="23">${v.cta}</div>
</div>
<script>
window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});
tl.from("#image-wrap",{opacity:0,scale:.985,duration:.6,ease:"power2.out"},.05)
  .from("#top-caption",{opacity:0,y:-42,duration:.62,ease:"power3.out"},.24)
  .from("#top-kicker",{opacity:0,y:24,duration:.46,ease:"power2.out"},.68)
  .from("#bottom-caption",{opacity:0,y:42,duration:.62,ease:"power3.out"},.42)
  .from("#bottom-cta",{opacity:0,y:44,scale:.94,duration:.58,ease:"back.out(1.7)"},.88)
  .to("#bottom-cta",{scale:1.03,duration:.34,ease:"sine.inOut",yoyo:true,repeat:7,repeatDelay:.88},2.0)
  .to("#top-band",{x:18,duration:5.6,ease:"sine.inOut",yoyo:true,repeat:1},0)
  .to("#bottom-band",{x:-20,duration:5.3,ease:"sine.inOut",yoyo:true,repeat:1},.2);
${scriptByTemplate[v.template]}
tl.to(["#top-caption","#top-kicker","#bottom-caption","#bottom-cta"],{opacity:0,duration:.45,ease:"power2.in"},11.45);
window.__timelines.main=tl;
</script>
</body>
</html>`;
}

rmSync(tempRoot, { recursive: true, force: true });
mkdirSync(tempRoot, { recursive: true });
mkdirSync(downloads, { recursive: true });

for (const v of videos) {
  const dir = join(tempRoot, `T014_v2_${v.id}`);
  const imgDir = join(dir, "assets", "images");
  mkdirSync(imgDir, { recursive: true });
  cpSync(join(task, "output", v.image), join(imgDir, v.image));
  writeFileSync(join(dir, "index.html"), html(v));
  writeFileSync(join(dir, "hyperframes.json"), JSON.stringify({
    $schema: "https://hyperframes.heygen.com/schema/hyperframes.json",
    registry: "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
    paths: { blocks: "compositions", components: "compositions/components", assets: "assets" },
  }, null, 2));
  writeFileSync(join(dir, "meta.json"), JSON.stringify({ id: `T014_v2_${v.id}`, name: `T014 v2 ${v.id}` }, null, 2));
  writeFileSync(join(dir, "package.json"), JSON.stringify({ private: true, type: "module" }, null, 2));

  const silent = join(tempRoot, `T014_v2_${v.id}.silent.mp4`);
  const final = join(downloads, `T014_v2_${v.id}.mp4`);
  execFileSync("npx", ["--yes", "hyperframes@0.6.28", "render", "-o", silent], { cwd: dir, stdio: "inherit" });
  execFileSync("ffmpeg", [
    "-y", "-i", silent, "-stream_loop", "-1", "-i", bgm,
    "-t", "12", "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", final,
  ], { stdio: "inherit" });
  if (!existsSync(final)) throw new Error(`Missing ${final}`);
}

const frames = videos.flatMap((v) => {
  const final = join(downloads, `T014_v2_${v.id}.mp4`);
  const frame = join(tempRoot, `T014_v2_${v.id}.png`);
  execFileSync("ffmpeg", ["-y", "-ss", "5.5", "-i", final, "-frames:v", "1", "-vf", "scale=216:384", frame], { stdio: "ignore" });
  return [frame];
});

const sheet = join(task, "output", "_batch_frames.png");
execFileSync("ffmpeg", [
  "-y", ...frames.flatMap((f) => ["-i", f]),
  "-filter_complex", `hstack=inputs=${frames.length}`,
  "-frames:v", "1", "-update", "1",
  sheet,
], { stdio: "inherit" });

console.log(`Rendered ${videos.length} videos to ${downloads}`);
console.log(`Contact sheet: ${sheet}`);
