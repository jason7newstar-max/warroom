const agentRoot = document.querySelector("#agents");
const tasksRoot = document.querySelector("#tasks");
const activityRoot = document.querySelector("#activity");
const decisionsRoot = document.querySelector("#decisions");
const signal = document.querySelector("#signal");
const lastUpdated = document.querySelector("#last-updated");
const taskCount = document.querySelector("#task-count");
const decisionCount = document.querySelector("#decision-count");

const statusClass = (value) => {
  const normalized = value.toLowerCase();
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

function renderAgents(agents) {
  agentRoot.innerHTML = agents
    .map(
      (agent, index) => `
        <article class="agent-card tilt-${index + 1}">
          <div class="avatar">${escapeHtml(agent.name.slice(0, 2).toUpperCase())}</div>
          <div>
            <h2>${escapeHtml(agent.name)}</h2>
            <p>${escapeHtml(agent.engine)}</p>
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
  taskCount.textContent = String(tasks.length);
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
  decisionCount.textContent = String(decisions.length);
  decisionsRoot.innerHTML = decisions
    .slice(0, 5)
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
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    renderAgents(data.board.agents);
    renderTasks(data.board.tasks);
    renderActivity(data.activity);
    renderDecisions(data.board.decisions);
    lastUpdated.textContent = `Board ${data.board.lastUpdated}`;
    signal.textContent = `live · ${new Date(data.generatedAt).toLocaleTimeString()}`;
    signal.className = "signal live";
  } catch (error) {
    signal.textContent = "offline";
    signal.className = "signal offline";
  }
}

refresh();
setInterval(refresh, 10000);
