/* T-035 JARVIS console — DATA LAYER (model-agnostic plumbing).
 * No LLM, no auth: reads the PUBLIC war-room repo. The dazzling UI layer (built
 * after the Claude upgrade) just calls these and renders. Keep this stable.
 *
 *   WarRoomData.tasks()    -> Promise<[{id,title,status,owner,statusEmoji}]>
 *   WarRoomData.commits()  -> Promise<[{sha,author,message,date}]>
 *   WarRoomData.poll(onData, ms=20000) -> starts a refresh loop, returns stop()
 *
 * Plus the UI<->Hue hook CONTRACT (the bridge polls these globals):
 *   window.jarvisColors()      -> [[r,g,b], ...]   dominant accent colors right now
 *   window.jarvisAudioLevel()  -> 0..1             current core reactive level
 *   window.setCoreLevel(0..1)                       UI sets the core's level
 *   window.setCoreState('idle'|'listening'|'speaking'|'working')
 */
(function (global) {
  const OWNER = "jason7newstar-max", REPO = "warroom";
  const RAW_BOARD = `https://raw.githubusercontent.com/${OWNER}/${REPO}/main/BOARD.md`;
  const COMMITS_API = `https://api.github.com/repos/${OWNER}/${REPO}/commits?per_page=12`;

  const STATUS_EMOJI = { "🟢":"done","🟡":"in-progress","🟣":"review","🔵":"todo","🔴":"blocked","⚪":"idea" };

  async function tasks() {
    const md = await fetch(RAW_BOARD, { cache: "no-store" }).then(r => r.text());
    const out = [];
    // parse the ACTIVE TASKS markdown table rows: | id | task | owner | mode | status | branch | updated |
    for (const line of md.split("\n")) {
      const m = line.match(/^\|\s*(T-\d+)\s*\|(.+)$/);
      if (!m) continue;
      const cells = line.split("|").map(c => c.trim());
      // cells[0]="" , 1=id, 2=task, 3=owner, 4=mode, 5=status, 6=branch, 7=updated
      const id = cells[1], title = (cells[2] || "").replace(/\*\*/g, ""),
            owner = cells[3] || "", statusCell = cells[5] || "";
      let statusEmoji = "", status = "";
      for (const e of Object.keys(STATUS_EMOJI)) if (statusCell.includes(e)) { statusEmoji = e; status = STATUS_EMOJI[e]; break; }
      out.push({ id, title: title.slice(0, 90), owner, status, statusEmoji,
                 rawStatus: statusCell });
    }
    return out;
  }

  async function commits() {
    const j = await fetch(COMMITS_API, { cache: "no-store" }).then(r => r.json());
    if (!Array.isArray(j)) return [];
    return j.map(c => ({
      sha: c.sha.slice(0, 7),
      author: (c.commit.author && c.commit.author.name) || "?",
      message: c.commit.message.split("\n")[0].slice(0, 80),
      date: c.commit.author && c.commit.author.date,
    }));
  }

  function poll(onData, ms = 20000) {
    let alive = true;
    async function tick() {
      if (!alive) return;
      try {
        const [t, c] = await Promise.all([tasks(), commits()]);
        onData({ tasks: t, commits: c, at: Date.now() });
      } catch (e) { console.warn("[WarRoomData] fetch failed", e); }
      if (alive) setTimeout(tick, ms);
    }
    tick();
    return () => { alive = false; };
  }

  global.WarRoomData = { tasks, commits, poll };

  // --- default Hue-hook stubs so the bridge never crashes before the UI wires real ones ---
  if (!global.jarvisColors) global.jarvisColors = () => [[34, 211, 238], [216, 180, 109]]; // cyan + gold
  if (!global.jarvisAudioLevel) global.jarvisAudioLevel = () => 0;
  if (!global.setCoreLevel) global.setCoreLevel = (_v) => {};
  if (!global.setCoreState) global.setCoreState = (_s) => {};
})(window);
