# 📡 War Room Telegram channel — per-machine setup

The shared group is **"oneten company"** via bot **@ONETENLINEBOT**.
The bot token is a secret → it does NOT live in this (public) repo. Each machine holds it locally.

## One-time, on each machine:
Create `~/.warroom/env` (perms 600) with:
```
WARROOM_BOT_TOKEN=<the @ONETENLINEBOT token from BotFather>
WARROOM_CHAT_ID=-5165312302
```
```
mkdir -p ~/.warroom && chmod 700 ~/.warroom
# put the two lines above into ~/.warroom/env, then:
chmod 600 ~/.warroom/env
```

## Posting to the room
Any agent posts a line with its id prefix:
```
~/claude-work/warroom/bin/warroom-say "[Mini] claiming T-002, starting the implementation"
```
(or add `bin/` to PATH and just `warroom-say "..."`)

Use it to: announce online, claim a task, hand off ("done, @Karen your turn"), ask, escalate.
**Durable state still goes on BOARD.md** — the group is the live feed, the board is the record.
