#!/usr/bin/env bash
# ONE TEN QUANT ARENA — NEON promo video builder (Karen / T-036)
# Pipeline: ImageMagick neon poster frames  ->  ffmpeg ken-burns + crossfade + BGM
# Visual base: tasks/T-036/neon_refs/{neon_cyan,neon_magenta,neon_red}.png
# No external APIs — fully local. Vertical 1080x1920 (Douyin).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
REF="$ROOT/../neon_refs"
F="$ROOT/frames"
OUT="$ROOT/quant_arena_neon_v1.mp4"
mkdir -p "$F"

W=1080; H=1920
HEI="/System/Library/Fonts/STHeiti Medium.ttc"     # CJK headline
HEL="/System/Library/Fonts/STHeiti Light.ttc"      # CJK light
CYAN="#22E6FF"; MAG="#FF35D2"; RED="#FF4040"; WHT="#EAFBFF"; AMB="#FFB020"; DIM="#8FB8C8"

# neon_text <outfile> <color> <pointsize> <font> <text...>
# renders glowing text on transparent canvas, auto-sized
neon_text(){ local out="$1" col="$2" ps="$3" fnt="$4"; shift 4; local txt="$*"
  magick -background none -fill "$col" -font "$fnt" -pointsize "$ps" \
         -interline-spacing 14 -gravity center label:"$txt" "/tmp/_t.png"
  magick \( "/tmp/_t.png" -blur 0x16 \) \( "/tmp/_t.png" -blur 0x6 \) "/tmp/_t.png" \
         -background none -layers flatten "$out"; }

# mkpanel <out> <w> <h> : translucent dark rounded panel for text legibility
mkpanel(){ magick -size "$2"x"$3" xc:none -fill "rgba(2,12,20,0.58)" \
  -draw "roundrectangle 0,0,$(($2-1)),$(($3-1)),40,40" -blur 0x1 "$1"; }

# bg_frame <ref.png> <out.png>  : cover-fill blurred backdrop + sharp planet band + legibility grads
bg_frame(){ local ref="$1" out="$2"
  magick "$ref" -resize ${W}x${H}^ -gravity center -extent ${W}x${H} -blur 0x22 -modulate 48 "/tmp/_bg.png"
  magick "$ref" -resize ${W}x "/tmp/_fg.png"
  magick -size ${W}x720 gradient:black-none "/tmp/_gt.png"
  magick -size ${W}x820 gradient:none-black "/tmp/_gb.png"
  magick "/tmp/_bg.png" \
    "/tmp/_fg.png" -gravity center -geometry +0-30 -composite \
    "/tmp/_gt.png" -gravity north -composite \
    "/tmp/_gb.png" -gravity south -composite \
    "$out"; }

echo "[1/3] building neon poster frames…"

# ---- S1 HOOK ----
bg_frame "$REF/neon_cyan.png" "$F/s1.png"
neon_text "/tmp/h.png" "$WHT" 96 "$HEI" "6 个 AI · 各 \$1000"
neon_text "/tmp/s.png" "$CYAN" 52 "$HEL" "美股期权 · 真实行情 · 打擂台一周"
neon_text "/tmp/b.png" "$AMB" 64 "$HEI" "谁,赚得多?"
magick "$F/s1.png" \
  "/tmp/h.png" -gravity north -geometry +0+220 -composite \
  "/tmp/s.png" -gravity north -geometry +0+360 -composite \
  "/tmp/b.png" -gravity south -geometry +0+360 -composite "$F/s1.png"

# ---- S2 SLOGAN ----
bg_frame "$REF/neon_magenta.png" "$F/s2.png"
neon_text "/tmp/h.png" "$DIM" 64 "$HEL" "这不是 3D 模型"
neon_text "/tmp/b.png" "$MAG" 92 "$HEI" "每个像素\n都是实时数据"
magick "$F/s2.png" \
  "/tmp/h.png" -gravity north -geometry +0+240 -composite \
  "/tmp/b.png" -gravity south -geometry +0+340 -composite "$F/s2.png"

# ---- S3 SOLAR SYSTEM ----
bg_frame "$REF/neon_cyan.png" "$F/s3.png"
neon_text "/tmp/h.png" "$CYAN" 84 "$HEI" "实时 3D 太阳系"
neon_text "/tmp/s.png" "$WHT" 50 "$HEL" "太阳 = 大盘   行星 = AI 交易员"
neon_text "/tmp/b.png" "$DIM" 44 "$HEL" "涨 → 蓝白耀眼     跌 → 暗红"
magick "$F/s3.png" \
  "/tmp/h.png" -gravity north -geometry +0+210 -composite \
  "/tmp/s.png" -gravity north -geometry +0+340 -composite \
  "/tmp/b.png" -gravity south -geometry +0+330 -composite "$F/s3.png"

# ---- S4 LEGEND ----
bg_frame "$REF/neon_magenta.png" "$F/s4.png"
neon_text "/tmp/h.png" "$MAG" 76 "$HEI" "每个像素都是数据"
neon_text "/tmp/b.png" "$WHT" 50 "$HEL" \
  "环宽 = 资金量\n亮暗 = 当日盈亏\n转速 = 仓位轻重\n彗尾 = 持仓中\n涟漪 = 刚成交\n★ = 领跑者"
mkpanel "/tmp/pan.png" 820 760
magick "$F/s4.png" \
  "/tmp/pan.png" -gravity center -geometry +0+90 -composite \
  "/tmp/h.png" -gravity north -geometry +0+200 -composite \
  "/tmp/b.png" -gravity center -geometry +0+120 -composite "$F/s4.png"

# ---- S5 DAY1 BOARD ----
bg_frame "$REF/neon_cyan.png" "$F/s5.png"
neon_text "/tmp/h.png" "$CYAN" 70 "$HEI" "DAY 1 · 大盘暴力反弹"
neon_text "/tmp/l1.png" "$AMB" 58 "$HEI" "★ Mini      +\$88   领跑"
neon_text "/tmp/l2.png" "$RED" 58 "$HEI" "Karen      +\$50   看涨命中"
neon_text "/tmp/l3.png" "$DIM" 50 "$HEL" "GPT · Gemini · Fable … 混战中"
neon_text "/tmp/l4.png" "$DIM" 58 "$HEL" "Dali       −\$177   垫底"
mkpanel "/tmp/pan.png" 1000 560
magick "$F/s5.png" \
  "/tmp/pan.png" -gravity center -geometry +0+30 -composite \
  "/tmp/h.png"  -gravity north  -geometry +0+210 -composite \
  "/tmp/l1.png" -gravity center -geometry +0-150 -composite \
  "/tmp/l2.png" -gravity center -geometry +0-30  -composite \
  "/tmp/l3.png" -gravity center -geometry +0+85  -composite \
  "/tmp/l4.png" -gravity center -geometry +0+200 -composite "$F/s5.png"

# ---- S6 KAREN HIGHLIGHT ----
bg_frame "$REF/neon_red.png" "$F/s6.png"
neon_text "/tmp/h.png" "$WHT" 60 "$HEL" "本场作者 · Claude 交易员"
neon_text "/tmp/n.png" "$RED" 132 "$HEI" "Karen +\$50"
neon_text "/tmp/b.png" "$AMB" 56 "$HEI" "全场唯一看涨 · 当天验证"
magick "$F/s6.png" \
  "/tmp/h.png" -gravity north -geometry +0+200 -composite \
  "/tmp/n.png" -gravity center -geometry +0-40 -composite \
  "/tmp/b.png" -gravity south -geometry +0+380 -composite "$F/s6.png"

# ---- S7 CTA ----
bg_frame "$REF/neon_magenta.png" "$F/s7.png"
neon_text "/tmp/h.png" "$WHT"  92 "$HEI" "ONE TEN\nQUANT ARENA"
neon_text "/tmp/u.png" "$CYAN" 46 "$HEL" "quant-dash-sable.vercel.app/pro"
neon_text "/tmp/p.png" "$MAG"  64 "$HEI" "\$19 / 月 · 实时擂台直播"
neon_text "/tmp/t.png" "$DIM"  42 "$HEL" "抖音「Claude Code 挑战 100 个项目」第 35 期"
mkpanel "/tmp/pan.png" 1000 280
magick "$F/s7.png" \
  "/tmp/pan.png" -gravity center -geometry +0+115 -composite \
  "/tmp/h.png" -gravity north  -geometry +0+260 -composite \
  "/tmp/u.png" -gravity center -geometry +0+60  -composite \
  "/tmp/p.png" -gravity center -geometry +0+170 -composite \
  "/tmp/t.png" -gravity south  -geometry +0+260 -composite "$F/s7.png"

echo "[2/3] animating + crossfading (ffmpeg)…"
# Per-shot durations (seconds)
D=(4.2 4.6 4.6 5.4 5.2 4.8 5.2)
XF=0.6   # crossfade
FPS=30
clips=()
for i in 1 2 3 4 5 6 7; do
  d=${D[$((i-1))]}
  # ken-burns slow zoom-in; pad duration by XF so xfade overlap doesn't shorten total
  dd=$(awk "BEGIN{print $d + $XF}")
  frames=$(awk "BEGIN{printf \"%d\", $dd * $FPS}")
  ffmpeg -y -loglevel error -loop 1 -i "$F/s$i.png" \
    -vf "scale=${W}*1.06:-1,zoompan=z='min(zoom+0.0006,1.10)':d=$frames:s=${W}x${H}:fps=$FPS,format=yuv420p" \
    -t "$dd" -r $FPS "$F/clip$i.mp4"
  clips+=("$F/clip$i.mp4")
done

# chain xfades
prev="${clips[0]}"
acc=$(awk "BEGIN{print ${D[0]} + $XF}")
for i in 2 3 4 5 6 7; do
  off=$(awk "BEGIN{print $acc - $XF}")
  out="$F/xf$i.mp4"
  ffmpeg -y -loglevel error -i "$prev" -i "${clips[$((i-1))]}" \
    -filter_complex "[0][1]xfade=transition=fade:duration=$XF:offset=$off,format=yuv420p" \
    "$out"
  prev="$out"
  acc=$(awk "BEGIN{print $acc + ${D[$((i-1))]}}")
done
cp "$prev" "$F/_video_noaudio.mp4"

echo "[3/3] BGM (synth pad) + mux…"
TOTAL=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$F/_video_noaudio.mp4")
# dark synth bed: low drone + soft pulse, faded
ffmpeg -y -loglevel error \
  -f lavfi -i "sine=frequency=55:sample_rate=44100" \
  -f lavfi -i "sine=frequency=110:sample_rate=44100" \
  -f lavfi -i "sine=frequency=220:sample_rate=44100" \
  -t "$TOTAL" -filter_complex \
  "[0]volume=0.30[a];[1]volume=0.16[b];[2]volume=0.06,tremolo=f=2:d=0.7[c];[a][b][c]amix=inputs=3,lowpass=f=600,afade=t=in:st=0:d=1.5,afade=t=out:st=$(awk "BEGIN{print $TOTAL-1.8}"):d=1.8[out]" \
  -map "[out]" -ar 44100 -ac 2 "$F/_bgm.wav"

ffmpeg -y -loglevel error -i "$F/_video_noaudio.mp4" -i "$F/_bgm.wav" \
  -c:v libx264 -pix_fmt yuv420p -profile:v high -crf 19 -preset medium \
  -c:a aac -b:a 160k -shortest -movflags +faststart "$OUT"

echo "DONE -> $OUT"
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 "$OUT"
