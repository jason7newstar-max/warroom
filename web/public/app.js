const BOARD_URL = "https://raw.githubusercontent.com/jason7newstar-max/warroom/main/BOARD.md";
const COMMITS_URL = "https://api.github.com/repos/jason7newstar-max/warroom/commits?per_page=18";
const TREE_URL = "https://api.github.com/repos/jason7newstar-max/warroom/git/trees/main?recursive=1";
const RAW_BASE = "https://raw.githubusercontent.com/jason7newstar-max/warroom/main/";

const NOW_URL = "/api/now";

const agentRoot = document.querySelector("#agents");
const outputsRoot = document.querySelector("#outputs");
const liveRoot = document.querySelector("#live");
const tasksRoot = document.querySelector("#tasks");
const activityRoot = document.querySelector("#activity");
const decisionsRoot = document.querySelector("#decisions");
const signal = document.querySelector("#signal");
const lastUpdated = document.querySelector("#last-updated");
const taskCount = document.querySelector("#task-count");
const decisionCount = document.querySelector("#decision-count");
const activitySource = document.querySelector("#activity-source");
const worldviewDeck = document.querySelector("#worldview-deck");
const worldviewSolo = document.querySelector("#worldview-solo");

const AGENT_META = {
  IA10: { id: "IA10", initials: "IA", avatar: "ia10_work1.png", role: "Supervisor / COO", engine: "Claude Code", machine: "Opus 4.8",
          frames: ["ia10_work1.png","ia10_work2.png","ia10_work3.png","ia10_work4.png","ia10_alt1.png","ia10_alt2.png","ia10_alt3.png","ia10_alt4.png"] },
  Karen: { id: "Karen", initials: "KA", avatar: "karen_work1.png", role: "Reasoning / review", engine: "Claude Code", machine: "Opus 4.8",
          frames: ["karen_work1.png","karen_work2.png","karen_work3.png","karen_work4.png"] },
  Mini: { id: "Mini", initials: "MI", avatar: "mini_work1.png", role: "Implementation", engine: "OpenAI Codex", machine: "GPT-5.5",
          frames: ["mini_work1.png","mini_work2.png","mini_work3.png","mini_work4.png"] },
  Dali: { id: "Dali", initials: "DA", avatar: "dali.png", role: "Implementation", engine: "OpenAI Codex", machine: "GPT-5.5",
          frames: ["dali.png"] }
};

function pickStart(meta) {
  const f = meta && meta.frames && meta.frames.length ? meta.frames : [meta.avatar];
  return f[Math.floor(Math.random() * f.length)];
}

const WORLDVIEW = [
  {
    id: "one-ten",
    name: "ONE TEN",
    number: "01",
    avatar: "wentian.jpg",
    line: "Carbon intent, final judgment."
  },
  {
    id: "ia10",
    name: "IA10",
    number: "02",
    avatar: "ia10.jpg",
    line: "Architecture, review, decisions."
  },
  {
    id: "karen",
    name: "Karen",
    number: "03",
    avatar: "karen.jpg",
    line: "Reasoning, research, documentation."
  },
  {
    id: "mini",
    name: "Mini",
    number: "04",
    avatar: "mini.jpg",
    line: "Compact execution and tool work."
  }
];

let activeWorldview = 0;

const statusClass = (value) => {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("blocked")) return "blocked";
  if (normalized.includes("progress") || normalized.includes("review")) return "working";
  if (normalized.includes("done")) return "done";
  if (normalized.includes("todo")) return "todo";
  return "idle";
};

const escapeHtml = (value) =>
  String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

function stripMd(value) {
  return String(value || "")
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    .trim();
}

function parseTable(markdown, heading) {
  const start = markdown.indexOf(heading);
  if (start === -1) return [];
  const lines = markdown.slice(start).split(/\r?\n/);
  const tableLines = [];
  let inTable = false;

  for (const line of lines) {
    if (line.trim().startsWith("|")) {
      tableLines.push(line.trim());
      inTable = true;
    } else if (inTable) {
      break;
    }
  }

  if (tableLines.length < 3) return [];
  const headers = tableLines[0].split("|").slice(1, -1).map(stripMd);
  return tableLines.slice(2).map((line) => {
    const cells = line.split("|").slice(1, -1).map(stripMd);
    return Object.fromEntries(headers.map((header, index) => [header, cells[index] || ""]));
  });
}

function renderWorldview() {
  const active = WORLDVIEW[activeWorldview];
  worldviewSolo.innerHTML = `
    <img src="/avatars/${escapeHtml(active.avatar)}" alt="" />
    <div class="solo-scrim"></div>
    <div class="solo-content">
      <span>${escapeHtml(active.number)}</span>
      <h2>${escapeHtml(active.name)}</h2>
      <p>${escapeHtml(active.line)}</p>
    </div>
  `;

  if (!worldviewDeck.children.length) {
    worldviewDeck.innerHTML = WORLDVIEW.map(
      (card, index) => `
        <button class="deck-card worldview-card" type="button" data-index="${index}" aria-pressed="false">
          <img src="/avatars/${escapeHtml(card.avatar)}" alt="" />
          <span>${escapeHtml(card.number)}</span>
          <strong>${escapeHtml(card.name)}</strong>
        </button>
      `
    ).join("");
  }

  [...worldviewDeck.querySelectorAll(".worldview-card")].forEach((card, index) => {
    const selected = index === activeWorldview;
    card.classList.toggle("selected", selected);
    card.setAttribute("aria-pressed", String(selected));
  });
}

function parseAgents(markdown, tasks) {
  const rollCallStart = markdown.indexOf("### 🟢 ROLL CALL");
  const rollCallEnd = markdown.indexOf("---", rollCallStart);
  const rollCall = rollCallStart === -1
    ? ""
    : markdown.slice(rollCallStart, rollCallEnd === -1 ? undefined : rollCallEnd);
  const agentTaskMap = tasks.reduce((map, task) => {
    const owners = String(task.Owner || "").split(",").map((owner) => owner.trim()).filter(Boolean);
    for (const owner of owners) {
      if (!AGENT_META[owner]) continue;
      if (!map[owner]) map[owner] = [];
      map[owner].push(task);
    }
    return map;
  }, {});

  return Object.entries(AGENT_META).map(([name, meta]) => {
    const rollCallLine = rollCall.split(/\r?\n/).find((entry) => entry.includes(`**${name}**`)) || "";
    const ownedTasks = agentTaskMap[name] || [];
    const workingTask = ownedTasks.find((task) => /in-progress|review/i.test(task.Status));
    const blockedTask = ownedTasks.find((task) => /blocked/i.test(task.Status));
    const lastTask = ownedTasks[ownedTasks.length - 1];
    const status = workingTask ? "working" : blockedTask ? "blocked" : "idle";

    return {
      name,
      ...meta,
      status,
      online: /✅/.test(rollCallLine),
      currentTask: (workingTask || blockedTask || lastTask || {}).ID || "standing by",
      taskCount: ownedTasks.length
    };
  });
}

function parseBoard(markdown) {
  const updatedMatch = markdown.match(/Last updated:\s*(.+)/);
  const tasks = parseTable(markdown, "## 🔥 ACTIVE TASKS").map((task) => ({
    ID: task.ID,
    Task: task.Task,
    Owner: task.Owner,
    Mode: task.Mode,
    Status: task.Status,
    Branch: task.Branch,
    Updated: task.Updated
  }));
  const decisions = parseTable(markdown, "## ✅ DECISION LOG");

  return {
    lastUpdated: updatedMatch ? stripMd(updatedMatch[1]) : "unknown",
    agents: parseAgents(markdown, tasks),
    tasks,
    decisions
  };
}

function parseCommits(commits) {
  return commits.map((item) => ({
    hash: String(item.sha || "").slice(0, 7),
    author: item.commit?.author?.name || item.author?.login || "unknown",
    date: item.commit?.author?.date || item.commit?.committer?.date || new Date().toISOString(),
    subject: item.commit?.message?.split("\n")[0] || "commit"
  }));
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${url} returned HTTP ${response.status}`);
  return response.json();
}

async function fetchText(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`${url} returned HTTP ${response.status}`);
  return response.text();
}

async function loadRemoteState() {
  const [markdown, commits] = await Promise.all([
    fetchText(BOARD_URL),
    fetchJson(COMMITS_URL)
  ]);

  return {
    generatedAt: new Date().toISOString(),
    source: "github",
    board: parseBoard(markdown),
    activity: parseCommits(commits)
  };
}

async function loadLocalFallback() {
  const response = await fetch("/api/state", { cache: "no-store" });
  if (!response.ok) throw new Error(`Local fallback returned HTTP ${response.status}`);
  return { ...(await response.json()), source: "local fallback" };
}

let avatarTimer = null;

function renderAgents(agents) {
  agentRoot.innerHTML = agents
    .map((agent, index) => {
      const meta = AGENT_META[agent.id] || AGENT_META[agent.name] || {};
      const aid = meta.id || agent.id || agent.name || "";
      const start = pickStart(meta) || agent.avatar;
      return `
        <article class="agent-card tilt-${index + 1}">
          <div class="agent-topline">
            <span>${escapeHtml(agent.role)}</span>
            <span>${agent.online ? "online" : "offline"}</span>
          </div>
          <div class="avatar">
            <img data-agent="${escapeHtml(aid)}" src="/avatars/${escapeHtml(start)}" style="transition:opacity .5s ease" alt="" onerror="this.remove()" />
            <span>${escapeHtml(agent.initials)}</span>
          </div>
          <div>
            <h2>${escapeHtml(agent.name)}</h2>
            <p>${escapeHtml(agent.engine)} · ${escapeHtml(agent.machine)}</p>
          </div>
          <div class="agent-meta">
            <span class="pill ${agent.status}">${escapeHtml(agent.status)}</span>
            <span>${escapeHtml(agent.currentTask)}</span>
          </div>
        </article>
      `;
    })
    .join("");
  cycleAvatars();
}

// Gently CYCLE each work-panel avatar through its storyboard frames — a soft
// crossfade every few seconds (no hard flash), staggered so they don't all flip
// at once. Chairman picked "rotate, don't make me choose".
function cycleAvatars() {
  if (avatarTimer) clearInterval(avatarTimer);
  const imgs = Array.from(agentRoot.querySelectorAll("img[data-agent]"));
  avatarTimer = setInterval(() => {
    imgs.forEach((img, i) => {
      const meta = AGENT_META[img.dataset.agent];
      const frames = meta && meta.frames ? meta.frames : null;
      if (!frames || frames.length < 2) return;
      setTimeout(() => {
        const cur = (img.getAttribute("src") || "").split("/").pop();
        let next = cur;
        for (let n = 0; n < 6 && next === cur; n++) next = frames[Math.floor(Math.random() * frames.length)];
        img.style.opacity = "0";
        setTimeout(() => { img.src = "/avatars/" + next; img.style.opacity = "1"; }, 500);
      }, i * 600);
    });
  }, 5200);
}

function renderTasks(tasks) {
  taskCount.textContent = `${tasks.length} tasks`;
  tasksRoot.innerHTML = tasks
    .map(
      (task) => `
        <article class="task-row ${statusClass(task.Status)}">
          <div class="task-id">${escapeHtml(task.ID)}</div>
          <div class="task-main">
            <h3>${escapeHtml(task.Task)}</h3>
            <p>${escapeHtml(task.Owner)} · ${escapeHtml(task.Mode)} · ${escapeHtml(task.Branch)}</p>
          </div>
          <div class="task-status">${escapeHtml(task.Status)}</div>
        </article>
      `
    )
    .join("");
}

function renderActivity(items) {
  activityRoot.innerHTML = items
    .slice(0, 10)
    .map(
      (item) => `
        <article class="activity-row">
          <span class="hash">${escapeHtml(item.hash)}</span>
          <div>
            <h3>${escapeHtml(item.subject)}</h3>
            <p>${escapeHtml(item.author)} · ${new Date(item.date).toLocaleString()}</p>
          </div>
        </article>
      `
    )
    .join("");
}

function renderDecisions(decisions) {
  decisionCount.textContent = `${decisions.length} logged`;
  decisionsRoot.innerHTML = decisions
    .slice(0, 6)
    .map(
      (decision) => `
        <article class="decision-row">
          <strong>${escapeHtml(decision.Date)}</strong>
          <span>${escapeHtml(decision.Decision)}</span>
        </article>
      `
    )
    .join("");
}

// OUTPUTS gallery — what the agents actually PRODUCED. One GitHub tree call,
// pure client-side (no LLM/token): list every image committed under tasks/, show
// the newest as thumbnails. Click → full image on raw.githubusercontent.
async function loadOutputs() {
  if (!outputsRoot) return;
  try {
    const res = await fetch(TREE_URL);
    if (!res.ok) throw new Error("tree " + res.status);
    const tree = (await res.json()).tree || [];
    const imgs = tree
      .filter((t) => t.type === "blob"
        && t.path.startsWith("tasks/")
        && /\.(png|jpe?g|webp)$/i.test(t.path)
        && !/_posesheet/i.test(t.path))
      .sort((a, b) => b.path.localeCompare(a.path)) // higher T-number / later path first
      .slice(0, 14);
    if (!imgs.length) { outputsRoot.innerHTML = '<p class="outputs-empty">No agent image outputs yet.</p>'; return; }
    outputsRoot.innerHTML = imgs
      .map((t) => {
        const raw = RAW_BASE + t.path.split("/").map(encodeURIComponent).join("/");
        const file = t.path.split("/").pop();
        const task = (t.path.match(/tasks\/(T-\d+)/) || [])[1] || "";
        return `<a class="output-card" href="${raw}" target="_blank" rel="noopener" title="${escapeHtml(t.path)}">
            <img loading="lazy" src="${raw}" alt="" onerror="this.closest('.output-card').remove()" />
            <span>${escapeHtml(task)}${task ? " · " : ""}${escapeHtml(file)}</span>
          </a>`;
      })
      .join("");
  } catch (e) {
    outputsRoot.innerHTML = '<p class="outputs-empty">Outputs unavailable (GitHub rate limit?).</p>';
  }
}

// LIVE strip — "who's on what NOW". The listener writes live/now.json the moment
// it dispatches/wakes an agent; we poll it (cache-busted). An agent shows ● working
// if its dispatch was < 10 min ago, else it has gone quiet. Zero LLM/token.
function timeAgo(ts) {
  const s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  if (s < 60) return s + "s ago";
  if (s < 3600) return Math.floor(s / 60) + "m ago";
  return Math.floor(s / 3600) + "h ago";
}
async function loadLive() {
  if (!liveRoot) return;
  try {
    const res = await fetch(NOW_URL + "?t=" + Date.now());
    if (!res.ok) throw new Error("now " + res.status);
    const data = await res.json();
    const agents = data.agents || {};
    const rows = Object.keys(agents)
      .map((k) => ({ agent: k, ...agents[k] }))
      .sort((a, b) => (b.ts || 0) - (a.ts || 0));
    if (!rows.length) { liveRoot.innerHTML = '<p class="live-empty">Idle — no agent dispatched recently.</p>'; return; }
    const now = Date.now() / 1000;
    liveRoot.innerHTML = rows
      .map((r) => {
        const working = (now - (r.ts || 0)) < 600;
        return `<div class="live-row ${working ? "on" : "off"}">
            <span class="live-dot"></span>
            <strong>${escapeHtml(r.agent)}</strong>
            <span class="live-task">${escapeHtml(r.task || "")}</span>
            <span class="live-when">${escapeHtml(timeAgo(r.ts || 0))}</span>
          </div>`;
      })
      .join("");
  } catch (e) {
    liveRoot.innerHTML = '<p class="live-empty">Live status unavailable.</p>';
  }
}

async function refresh() {
  loadOutputs();
  loadLive();
  try {
    let data;
    try {
      data = await loadLocalFallback();
    } catch (localError) {
      data = await loadRemoteState();
    }

    renderAgents(data.board.agents);
    renderTasks(data.board.tasks);
    renderActivity(data.activity);
    renderDecisions(data.board.decisions);
    lastUpdated.textContent = `Board ${data.board.lastUpdated}`;
    activitySource.textContent = data.source === "github" ? "GitHub API" : "Local fallback";
    signal.textContent = `${data.source} · ${new Date(data.generatedAt).toLocaleTimeString()}`;
    signal.className = "signal live";
  } catch (error) {
    signal.textContent = "offline";
    signal.className = "signal offline";
    lastUpdated.textContent = "Could not reach GitHub or the local fallback.";
  }
}

worldviewDeck.addEventListener("click", (event) => {
  const card = event.target.closest(".worldview-card");
  if (!card) return;
  activeWorldview = Number(card.dataset.index || 0);
  renderWorldview();
});

renderWorldview();
refresh();
setInterval(refresh, 30000);
