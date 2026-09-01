import json
from pathlib import Path
from typing import Iterable, List, Dict, Any


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "mcts_analytics.html"
DATA_DIR = BASE_DIR / "mcts_data"


def load_traces() -> List[Dict[str, Any]]:
    traces: List[Dict[str, Any]] = []
    seen_files = set()
    if not DATA_DIR.exists():
        return traces

    for path in sorted(DATA_DIR.glob("mcts_trace_*.json")):
        resolved = path.resolve()
        if resolved in seen_files:
            continue
        seen_files.add(resolved)
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        traces.append(
            {
                "file_name": path.name,
                "file_path": str(path),
                "payload": payload,
            }
        )
    return traces


def _escape_backticks(text: str) -> str:
    return text.replace("`", "\\`")


def build_html(traces: List[Dict[str, Any]]) -> str:
    data_json = json.dumps(traces)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MCTS Analytics</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --panel: #ffffff;
      --line: #d8dee8;
      --ink: #0f172a;
      --muted: #5b6472;
      --accent: #2457ff;
    }}
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    .wrap {{ padding: 24px; }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    .meta {{ color: var(--muted); margin: 8px 0 18px; line-height: 1.5; }}
    .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
    .tabbtn {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--ink);
      border-radius: 8px;
      padding: 10px 14px;
      cursor: pointer;
    }}
    .tabbtn.active {{ background: var(--ink); color: white; border-color: var(--ink); }}
    .tab {{ display: none; }}
    .tab.active {{ display: block; }}
    .grid.cards {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-bottom: 18px; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }}
    .value {{ font-size: 22px; font-weight: 700; margin: 4px 0 6px; }}
    .small {{ color: var(--muted); font-size: 13px; line-height: 1.5; }}
    .controls {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}
    select, button.action {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 10px 12px;
      font: inherit;
      color: var(--ink);
    }}
    button.action {{ cursor: pointer; }}
    button.action.primary {{ background: var(--ink); color: white; border-color: var(--ink); }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      margin-bottom: 14px;
    }}
    .two-col {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }}
    pre {{
      white-space: pre;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      overflow-x: auto;
      margin: 0;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    details {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      margin: 8px 0;
      padding: 8px 10px;
    }}
    details summary {{
      cursor: pointer;
      list-style: none;
      font-weight: 700;
    }}
    details summary::-webkit-details-marker {{ display: none; }}
    .tree-node {{ margin-left: 18px; }}
    .tree-meta {{ color: var(--muted); font-size: 13px; margin: 6px 0 10px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>MCTS Analytics</h1>
    <div class="meta">Every trace file is a game. The navigator tab lets you step through turns; the tree tab shows the state-action tree with collapsible branches for branch-wise analysis.</div>

    <div class="tabs">
      <button class="tabbtn active" data-tab="navigator">Navigator</button>
      <button class="tabbtn" data-tab="tree">Tree Explorer</button>
    </div>

    <section id="navigator" class="tab active">
      <div class="grid cards" id="overviewCards"></div>
      <div class="controls">
        <select id="gameSelect"></select>
        <select id="turnSelect"></select>
        <button class="action" id="prevTurn">Previous Turn</button>
        <button class="action" id="nextTurn">Next Turn</button>
        <button class="action primary" id="openTree">Open Tree Tab</button>
      </div>
      <div class="panel" id="turnSummary"></div>
      <div class="two-col">
        <div class="panel">
          <h3>Board Before</h3>
          <pre id="boardBefore"></pre>
        </div>
        <div class="panel">
          <h3>Board After</h3>
          <pre id="boardAfter"></pre>
        </div>
      </div>
      <div class="panel">
        <h3>Root Child Values</h3>
        <div id="childTable"></div>
      </div>
    </section>

    <section id="tree" class="tab">
      <div class="controls">
        <select id="treeGameSelect"></select>
        <select id="treeTurnSelect"></select>
      </div>
      <div class="panel">
        <h3>State-Action Tree</h3>
        <div id="treeContainer"></div>
      </div>
    </section>
  </div>

  <script>
    const DATA = {_escape_backticks(data_json)};
    const COLORS = ['#2457ff', '#e11d48', '#059669', '#7c3aed', '#d97706'];
    const tabs = Array.from(document.querySelectorAll('.tabbtn'));
    const panels = Array.from(document.querySelectorAll('.tab'));
    const gameSelect = document.getElementById('gameSelect');
    const turnSelect = document.getElementById('turnSelect');
    const treeGameSelect = document.getElementById('treeGameSelect');
    const treeTurnSelect = document.getElementById('treeTurnSelect');
    const prevTurn = document.getElementById('prevTurn');
    const nextTurn = document.getElementById('nextTurn');
    const openTree = document.getElementById('openTree');
    let activeGameIndex = 0;
    let activeTurnIndex = 0;
    let activeTreeGameIndex = 0;
    let activeTreeTurnIndex = 0;

    function switchTab(name) {{
      tabs.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === name));
      panels.forEach(panel => panel.classList.toggle('active', panel.id === name));
      if (name === 'tree') {{
        renderTree();
      }}
    }}

    tabs.forEach(btn => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));
    openTree.addEventListener('click', () => switchTab('tree'));

    function setSelectOptions(select, items, selectedIndex) {{
      select.innerHTML = items.map((item, index) => `<option value="${{index}}">${{item}}</option>`).join('');
      select.value = String(selectedIndex);
    }}

    function boardToHtml(text) {{
      return text || '';
    }}

    function currentGame() {{
      return DATA[activeGameIndex];
    }}

    function currentTurn() {{
      const game = currentGame();
      return game && game.payload.trace[activeTurnIndex];
    }}

    function renderOverview() {{
      const totalGames = DATA.length;
      const totalTurns = DATA.reduce((sum, entry) => sum + entry.payload.trace.length, 0);
      const avgTurns = totalGames ? (totalTurns / totalGames).toFixed(2) : '0.00';
      const maxChildren = DATA.reduce((max, entry) => {{
        return Math.max(max, ...entry.payload.trace.map(turn => (turn.children || []).length));
      }}, 0);
      document.getElementById('overviewCards').innerHTML = `
        <div class="card"><div class="label">Trace Files</div><div class="value">${{totalGames}}</div></div>
        <div class="card"><div class="label">Total Turns</div><div class="value">${{totalTurns}}</div></div>
        <div class="card"><div class="label">Average Turns / Game</div><div class="value">${{avgTurns}}</div></div>
        <div class="card"><div class="label">Max Root Children</div><div class="value">${{maxChildren}}</div></div>
      `;
    }}

    function renderGameSelectors() {{
      const gameLabels = DATA.map((entry, index) => `${{index + 1}}. ${{entry.file_name}}`);
      setSelectOptions(gameSelect, gameLabels, activeGameIndex);
      setSelectOptions(treeGameSelect, gameLabels, activeTreeGameIndex);
    }}

    function renderTurnSelectors() {{
      const game = currentGame();
      const turns = game ? game.payload.trace.map(turn => `Turn ${{turn.turn_index}}`) : [];
      const treeGame = DATA[activeTreeGameIndex];
      const treeTurns = treeGame ? treeGame.payload.trace.map(turn => `Turn ${{turn.turn_index}}`) : [];
      setSelectOptions(turnSelect, turns, activeTurnIndex);
      setSelectOptions(treeTurnSelect, treeTurns, activeTreeTurnIndex);
    }}

    function renderChildTable(turn) {{
      const rows = (turn.children || []).map(child => `
        <tr>
          <td>${{JSON.stringify(child.action)}}</td>
          <td>${{child.visits}}</td>
          <td>${{Number(child.total_value).toFixed(2)}}</td>
          <td>${{Number(child.average_value).toFixed(2)}}</td>
        </tr>
      `).join('');
      return `
        <table>
          <thead><tr><th>Action</th><th>Visits</th><th>Total Value</th><th>Average Value</th></tr></thead>
          <tbody>${{rows || '<tr><td colspan="4">No child statistics recorded.</td></tr>'}}</tbody>
        </table>
      `;
    }}

    function renderNavigator() {{
      const turn = currentTurn();
      if (!turn) return;
      const game = currentGame();
      document.getElementById('turnSummary').innerHTML = `
        <h3>${{game.file_name}}</h3>
        <div class="small">Agent: ${{game.payload.agent_name}} | Simulations per move: ${{game.payload.simulation_count}}</div>
        <div class="small">Turn ${{turn.turn_index}} | Root player: ${{turn.root_player}} | Best action: ${{JSON.stringify(turn.chosen_action)}} | Value: ${{turn.chosen_action_value ?? 'n/a'}}</div>
      `;
      document.getElementById('boardBefore').textContent = turn.board_before_text || '';
      document.getElementById('boardAfter').textContent = turn.board_after_text || '';
      document.getElementById('childTable').innerHTML = renderChildTable(turn);
    }}

    function renderNode(node, actionLabel = 'Root') {{
      const header = `${{actionLabel}} | visits: ${{node.visits}} | total: ${{Number(node.total_value).toFixed(2)}} | avg: ${{Number(node.average_value).toFixed(2)}} | player to move: ${{node.player_to_move}}`;
      const children = (node.children || []).map((child, index) => renderNode(child.node, `Action ${{JSON.stringify(child.action)}}`)).join('');
      const board = `<pre>${{node.board_text || ''}}</pre>`;
      return `
        <details>
          <summary>${{header}}</summary>
          <div class="tree-node">
            <div class="tree-meta">Board state for this node</div>
            ${{board}}
            ${{children}}
          </div>
        </details>
      `;
    }}

    function renderTree() {{
      const entry = DATA[activeTreeGameIndex];
      if (!entry) return;
      const turn = entry.payload.trace[activeTreeTurnIndex];
      if (!turn) return;
      document.getElementById('treeContainer').innerHTML = `
        <div class="small" style="margin-bottom:12px;">${{entry.file_name}} | Turn ${{turn.turn_index}} | Root player: ${{turn.root_player}} | Chosen action: ${{JSON.stringify(turn.chosen_action)}}</div>
        ${{renderNode(turn.tree)}}
      `;
    }}

    gameSelect.addEventListener('change', () => {{
      activeGameIndex = Number(gameSelect.value);
      activeTurnIndex = 0;
      renderTurnSelectors();
      renderNavigator();
    }});

    turnSelect.addEventListener('change', () => {{
      activeTurnIndex = Number(turnSelect.value);
      renderNavigator();
    }});

    treeGameSelect.addEventListener('change', () => {{
      activeTreeGameIndex = Number(treeGameSelect.value);
      activeTreeTurnIndex = 0;
      renderTurnSelectors();
      renderTree();
    }});

    treeTurnSelect.addEventListener('change', () => {{
      activeTreeTurnIndex = Number(treeTurnSelect.value);
      renderTree();
    }});

    prevTurn.addEventListener('click', () => {{
      activeTurnIndex = Math.max(0, activeTurnIndex - 1);
      turnSelect.value = String(activeTurnIndex);
      renderNavigator();
    }});

    nextTurn.addEventListener('click', () => {{
      const game = currentGame();
      if (!game) return;
      activeTurnIndex = Math.min(game.payload.trace.length - 1, activeTurnIndex + 1);
      turnSelect.value = String(activeTurnIndex);
      renderNavigator();
    }});

    renderOverview();
    renderGameSelectors();
    renderTurnSelectors();
    renderNavigator();
  </script>
</body>
</html>
"""


def generate_mcts_analytics_html(output_path: Path = OUTPUT_PATH) -> Path:
    traces = load_traces()
    output_path.write_text(build_html(traces), encoding="utf-8")
    return output_path


def main():
    output = generate_mcts_analytics_html()
    print(f"Wrote MCTS analytics to {output}")


if __name__ == "__main__":
    main()
