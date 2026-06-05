const BOARD_URL = "https://raw.githubusercontent.com/jason7newstar-max/warroom/main/BOARD.md";
const COMMITS_URL = "https://api.github.com/repos/jason7newstar-max/warroom/commits?per_page=18";

const agentRoot = document.querySelector("#agents");
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
  IA10: { id: "IA10", initials: "IA", avatar: "ia10.jpg", role: "Supervisor / COO", engine: "Claude Code", machine: "studio iMac" },
  Karen: { id: "Karen", initials: "KA", avatar: "karen.jpg", role: "Reasoning / review", engine: "Claude Code", machine: "home MacBook Air" },
  Mini: { id: "Mini", initials: "MI", avatar: "mini.jpg", role: "Implementation", engine: "OpenAI Codex", machine: "home MacBook Air" },
  Dali: { id: "Dali", initials: "DA", avatar: "dali.png", role: "Implementation", engine: "OpenAI Codex", machine: "studio iMac" }
};

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

function renderAgents(agents) {
  agentRoot.innerHTML = agents
    .map(
      (agent, index) => `
        <article class="agent-card tilt-${index + 1}">
          <div class="agent-topline">
            <span>${escapeHtml(agent.role)}</span>
            <span>${agent.online ? "online" : "offline"}</span>
          </div>
          <div class="avatar">
            <img src="/avatars/${escapeHtml(agent.avatar)}" alt="" onerror="this.remove()" />
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
      `
    )
    .join("");
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

async function refresh() {
  try {
    let data;
    try {
      data = await loadRemoteState();
    } catch (remoteError) {
      data = await loadLocalFallback();
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
