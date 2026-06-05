const http = require("http");
const fs = require("fs");
const path = require("path");
const { execFile } = require("child_process");

const WEB_ROOT = __dirname;
const REPO_ROOT = path.resolve(WEB_ROOT, "..");
const PUBLIC_ROOT = path.join(WEB_ROOT, "public");
const PORT = Number(process.env.PORT || 4173);
const BOARD_URL = "https://raw.githubusercontent.com/jason7newstar-max/warroom/main/BOARD.md";
const COMMITS_URL = "https://api.github.com/repos/jason7newstar-max/warroom/commits?per_page=18";

const AGENT_META = {
  IA10: { id: "IA10", initials: "IA", role: "Supervisor / COO", engine: "Claude Code", machine: "studio iMac" },
  Dali: { id: "Dali", initials: "DA", role: "Worker", engine: "OpenAI Codex", machine: "studio iMac" },
  Karen: { id: "Karen", initials: "KA", role: "Worker", engine: "Claude Code", machine: "home MacBook Air" },
  Mini: { id: "Mini", initials: "MI", role: "Worker", engine: "OpenAI Codex", machine: "home MacBook Air" }
};

function readBoard() {
  return fs.readFileSync(path.join(REPO_ROOT, "BOARD.md"), "utf8");
}

async function fetchBoard() {
  const response = await fetch(BOARD_URL, { cache: "no-store" });
  if (!response.ok) throw new Error(`BOARD.md HTTP ${response.status}`);
  return response.text();
}

function stripMd(value) {
  return value
    .replace(/\*\*/g, "")
    .replace(/`/g, "")
    .replace(/\[(.*?)\]\(.*?\)/g, "$1")
    .trim();
}

function parseTable(markdown, heading) {
  const start = markdown.indexOf(heading);
  if (start === -1) return [];
  const tail = markdown.slice(start);
  const lines = tail.split(/\r?\n/);
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

function parseAgents(markdown, tasks) {
  const rollCallStart = markdown.indexOf("### 🟢 ROLL CALL");
  const rollCallEnd = markdown.indexOf("---", rollCallStart);
  const rollCall = rollCallStart === -1
    ? ""
    : markdown.slice(rollCallStart, rollCallEnd === -1 ? undefined : rollCallEnd);
  const agentTaskMap = tasks.reduce((map, task) => {
    const owners = task.Owner.split(",").map((owner) => owner.trim()).filter(Boolean);
    for (const owner of owners) {
      if (!AGENT_META[owner]) continue;
      if (new RegExp(`${owner}\\s+done`, "i").test(task.Task)) continue;
      if (!map[owner]) map[owner] = [];
      map[owner].push(task);
    }
    return map;
  }, {});

  return Object.entries(AGENT_META).map(([name, meta]) => {
    const line = markdown.split(/\r?\n/).find((entry) => entry.includes(`**${name}**`)) || "";
    const rollCallLine = rollCall.split(/\r?\n/).find((entry) => entry.includes(`**${name}**`)) || "";
    const ownedTasks = agentTaskMap[name] || [];
    const workingTask = ownedTasks.find((task) => /in-progress|review/i.test(task.Status));
    const blockedTask = ownedTasks.find((task) => /blocked/i.test(task.Status));
    const status = workingTask ? "working" : blockedTask ? "blocked" : "idle";

    return {
      name,
      ...meta,
      status,
      online: /✅/.test(rollCallLine || line),
      currentTask: (workingTask || blockedTask || ownedTasks[ownedTasks.length - 1] || {}).ID || "standing by",
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

function getGitLog() {
  return new Promise((resolve) => {
    execFile(
      "git",
      ["log", "--date=iso-strict", "--pretty=format:%h%x09%an%x09%ad%x09%s", "-18"],
      { cwd: REPO_ROOT },
      (error, stdout) => {
        if (error) {
          resolve([]);
          return;
        }
        resolve(
          stdout
            .split(/\r?\n/)
            .filter(Boolean)
            .map((line) => {
              const [hash, author, date, ...subjectParts] = line.split("\t");
              return { hash, author, date, subject: subjectParts.join("\t") };
            })
        );
      }
    );
  });
}

async function getGitHubCommits() {
  const response = await fetch(COMMITS_URL, { cache: "no-store" });
  if (!response.ok) throw new Error(`commits HTTP ${response.status}`);
  const commits = await response.json();
  return commits.map((item) => ({
    hash: String(item.sha || "").slice(0, 7),
    author: item.commit?.author?.name || item.author?.login || "unknown",
    date: item.commit?.author?.date || item.commit?.committer?.date || new Date().toISOString(),
    subject: item.commit?.message?.split("\n")[0] || "commit"
  }));
}

function sendJson(res, payload) {
  res.writeHead(200, {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store"
  });
  res.end(JSON.stringify(payload));
}

function sendFile(res, requestPath) {
  const cleanPath = requestPath === "/" ? "/index.html" : requestPath;
  const filePath = path.normalize(path.join(PUBLIC_ROOT, cleanPath));
  if (!filePath.startsWith(PUBLIC_ROOT)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }

  fs.readFile(filePath, (error, data) => {
    if (error) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }

    const ext = path.extname(filePath);
    const types = {
      ".html": "text/html; charset=utf-8",
      ".css": "text/css; charset=utf-8",
      ".js": "application/javascript; charset=utf-8",
      ".svg": "image/svg+xml",
      ".png": "image/png",
      ".jpg": "image/jpeg",
      ".jpeg": "image/jpeg",
      ".webp": "image/webp"
    };
    res.writeHead(200, { "content-type": types[ext] || "application/octet-stream" });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  if (url.pathname === "/api/state") {
    try {
      const [markdown, activity] = await Promise.all([fetchBoard(), getGitHubCommits()]);
      sendJson(res, {
        generatedAt: new Date().toISOString(),
        source: "github",
        board: parseBoard(markdown),
        activity
      });
    } catch (error) {
      const board = parseBoard(readBoard());
      const activity = await getGitLog();
      sendJson(res, {
        generatedAt: new Date().toISOString(),
        source: "local fallback",
        board,
        activity
      });
    }
    return;
  }
  sendFile(res, url.pathname);
});

server.listen(PORT, () => {
  console.log(`War-room web listening on http://localhost:${PORT}`);
});
