# 文天 VOICE — capability report (Karen, for Code-100 #26)

**Status: READY.** I can render text→文天-voice mp3 on the home MacBook Air.

## What it actually is (honest)
- **Service:** MiniMax T2A (`speech-02-hd`), endpoint `https://api.minimax.io/v1/t2a_v2`.
- **Voice id:** `male-qn-wenrun` — a MiniMax **stock** voice (温润 male) used as 文天's
  CANONICAL voice across all PA1 episodes (101 uses). It is **not** an ElevenLabs clone of
  the user's real recorded voice — it's a consistent stock voice that = "文天" by convention.
  (An `ELEVENLABS_API_KEY` exists on this machine but the 文天 pipeline does NOT use it.)
- **Key:** `MINIMAX_API_KEY` (in `~/.zshrc`, NOT in repo).

## Recipe (one command)
```bash
source ~/.zshrc   # loads MINIMAX_API_KEY
/opt/homebrew/bin/python3.11 /Users/t/workdir/yasagami-hf-test/tts_minimax.py \
  "male-qn-wenrun" "中文旁白文本" out.mp3 1.0 1.0 ""
#  args: voice_id  text  output.mp3  speed  vol  emotion(opt: happy/sad/..)  lang(opt cn/en)
```
Auto text-normalize runs (2→两, ONETEN→ONE TEN, etc). For broadcast loudness, post-process:
`ffmpeg -y -i out.mp3 -af "loudnorm=I=-18:LRA=7:TP=-1.5" out_norm.mp3`

## Reference samples (existing 文天 renders)
`/Users/t/workdir/pa1-ep11b/build/voice/d1_wentian.mp3` (and d8_wentian_norm.mp3, plus
pa1-ep05/ep33/special-wwdc 的 *_wentian.mp3).

## For #26 (~30字 / ~11s)
Speed 1.0 fits ~11s for ~30 Chinese chars. **Standing by — send final approved text, I render
mp3 + loudnorm version. Not generating anything yet.**
