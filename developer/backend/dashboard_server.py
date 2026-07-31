import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


STATE_FILE = Path("runtime_state.json")
HOST = "127.0.0.1"
PORT = 8000


DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Classroom Edge AI Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef3f8;
      --panel: #ffffff;
      --ink: #142033;
      --muted: #647184;
      --line: #d7e0ea;
      --blue: #1468c8;
      --green: #16845b;
      --amber: #b36b00;
      --red: #c93333;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
    }

    .shell {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0;
    }

    header {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-end;
      margin-bottom: 20px;
    }

    h1 {
      margin: 0;
      font-size: 28px;
      line-height: 1.15;
    }

    .status {
      min-width: 160px;
      text-align: right;
      color: var(--muted);
      font-size: 14px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      min-height: 128px;
    }

    .panel.wide {
      grid-column: span 2;
    }

    .label {
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 12px;
    }

    .value {
      font-size: 34px;
      font-weight: 700;
      line-height: 1.1;
    }

    .sub {
      color: var(--muted);
      font-size: 14px;
      margin-top: 10px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 112px;
      min-height: 44px;
      border-radius: 999px;
      padding: 0 18px;
      color: white;
      background: var(--green);
      font-size: 18px;
      font-weight: 700;
    }

    .pill.medium {
      background: var(--amber);
    }

    .pill.high {
      background: var(--red);
    }

    .pill.off {
      background: #536173;
    }

    .timeline {
      display: grid;
      gap: 8px;
      max-height: 260px;
      overflow: auto;
    }

    .row {
      display: grid;
      grid-template-columns: 150px 100px 80px 90px 1fr;
      gap: 10px;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid var(--line);
      font-size: 14px;
    }

    .row:last-child {
      border-bottom: 0;
    }

    .empty {
      color: var(--muted);
      padding: 24px 0;
    }

    @media (max-width: 820px) {
      header {
        align-items: flex-start;
        flex-direction: column;
      }

      .status {
        text-align: left;
      }

      .grid {
        grid-template-columns: 1fr;
      }

      .panel.wide {
        grid-column: auto;
      }

      .row {
        grid-template-columns: 1fr 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <h1>Smart Classroom Edge AI Dashboard</h1>
        <div class="sub">Live state from the local edge backend</div>
      </div>
      <div class="status" id="connection">Waiting for backend state</div>
    </header>

    <section class="grid">
      <article class="panel">
        <div class="label">Occupancy Level</div>
        <div id="occupancy" class="pill off">--</div>
        <div class="sub" id="timestamp">No timestamp yet</div>
      </article>

      <article class="panel">
        <div class="label">Detected People</div>
        <div class="value" id="people">--</div>
        <div class="sub">Count from YOLO person detections</div>
      </article>

      <article class="panel">
        <div class="label">AC State</div>
        <div class="value" id="ac">--</div>
        <div class="sub" id="last-change">Last change: --</div>
      </article>

      <article class="panel">
        <div class="label">Temperature</div>
        <div class="value" id="temp">--</div>
        <div class="sub">Software AC simulation</div>
      </article>

      <article class="panel wide">
        <div class="label">Total AC Running Time</div>
        <div class="value" id="runtime">0s</div>
        <div class="sub">Accumulates while AC is ON</div>
      </article>

      <article class="panel wide">
        <div class="label">Latest Backend Frame</div>
        <div class="value" id="frame">--</div>
        <div class="sub">Updated from runtime_state.json</div>
      </article>

      <article class="panel wide">
        <div class="label">Occupancy Timeline</div>
        <div class="timeline" id="timeline">
          <div class="empty">Timeline will appear when edge_demo.py starts writing state.</div>
        </div>
      </article>
    </section>
  </main>

  <script>
    const history = [];
    let lastFrame = null;

    function secondsLabel(value) {
      const seconds = Math.floor(Number(value || 0));
      const minutes = Math.floor(seconds / 60);
      const rest = seconds % 60;
      if (minutes === 0) return `${rest}s`;
      return `${minutes}m ${rest}s`;
    }

    function setOccupancy(level) {
      const el = document.getElementById("occupancy");
      el.textContent = level || "--";
      el.className = "pill";
      if (level === "HIGH") el.classList.add("high");
      else if (level === "MEDIUM") el.classList.add("medium");
      else if (level === "LOW") el.classList.add("off");
      else el.classList.add("off");
    }

    function renderTimeline() {
      const el = document.getElementById("timeline");
      if (!history.length) {
        el.innerHTML = '<div class="empty">Timeline will appear when edge_demo.py starts writing state.</div>';
        return;
      }

      el.innerHTML = history.slice(-30).reverse().map(item => `
        <div class="row">
          <div>${item.timestamp || "--"}</div>
          <div>${item.occupancy || "--"}</div>
          <div>${item.person_count ?? "--"} people</div>
          <div>AC ${item.ac_state || "--"}</div>
          <div>${item.temperature_c ? item.temperature_c + " C" : "No cooling"}</div>
        </div>
      `).join("");
    }

    function updateDashboard(state) {
      document.getElementById("connection").textContent = "Connected to local backend";
      document.getElementById("people").textContent = state.person_count ?? "--";
      document.getElementById("ac").textContent = state.ac_state || "--";
      document.getElementById("temp").textContent = state.temperature_c ? `${state.temperature_c} C` : "--";
      document.getElementById("runtime").textContent = secondsLabel(state.ac_runtime_seconds);
      document.getElementById("frame").textContent = state.frame ?? "--";
      document.getElementById("timestamp").textContent = state.timestamp || "No timestamp yet";
      document.getElementById("last-change").textContent = `Last change: ${state.last_ac_change || "--"}`;
      setOccupancy(state.occupancy);

      if (state.frame !== lastFrame) {
        history.push(state);
        lastFrame = state.frame;
        renderTimeline();
      }
    }

    async function poll() {
      try {
        const response = await fetch("/api/state", { cache: "no-store" });
        if (!response.ok) throw new Error("State unavailable");
        const state = await response.json();
        updateDashboard(state);
      } catch (error) {
        document.getElementById("connection").textContent = "Waiting for runtime_state.json";
      }
    }

    setInterval(poll, 1000);
    poll();
  </script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
            return

        if path == "/api/state":
            if not STATE_FILE.exists():
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "runtime_state.json not found"}).encode("utf-8"))
                return

            try:
                state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.send_response(503)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "state file is being updated"}).encode("utf-8"))
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(json.dumps(state).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    print(f"Dashboard running at http://{HOST}:{PORT}")
    print("Start edge_demo.py in another terminal to update runtime_state.json.")
    server.serve_forever()


if __name__ == "__main__":
    main()
