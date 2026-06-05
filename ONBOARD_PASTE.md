# 📋 Paste this to each agent to join the War Room

Copy the block below into **Dali**, **Karen**, and **Mini** (one each).
Replace `<YOUR-ID>` with that agent's id: `Dali` / `Karen` / `Mini`.
For Air agents, clone under `~/claude-work` (Karen) or `~/codex-work` (Mini).

---

You're joining a multi-agent "War Room." Do this now:

1. Clone the shared board (skip if already cloned; then `cd` in and `git pull`):
   ```
   git clone https://github.com/jason7newstar-max/warroom.git ~/<workspace>/warroom
   cd ~/<workspace>/warroom
   ```
   (Dali → `~/codex-work/warroom`; Karen → `~/claude-work/warroom`; Mini → `~/codex-work/warroom`)

2. Read **RULES.md** (governance — no voting, one owner per task, proposer executes, solo/pipeline/parallel modes) and the current **BOARD.md**.

3. Add yourself to the roster: edit `AGENTS.md` only if your row is missing, then in `BOARD.md` you don't need to add a task yet — just confirm you can push:
   ```
   git pull
   # (make any small edit only if needed)
   git -c user.name="<YOUR-ID>" -c user.email="warroom@pinla.local" commit --allow-empty -m "[<YOUR-ID>] online: read RULES + BOARD, standing by"
   git push
   ```

4. From now on: **pull before you act, push after.** Claim tasks by setting yourself as Owner in `BOARD.md`. The Supervisor is **IA10** (assigns work-orders, the human Wentian is the final decider).

Report back: "✅ <YOUR-ID> online."
