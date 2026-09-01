import json
from pathlib import Path
from typing import Any, Dict, List


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "td_analytics.html"
DATA_DIR = BASE_DIR / "td_data"


def load_traces() -> List[Dict[str, Any]]:
    traces: List[Dict[str, Any]] = []
    if not DATA_DIR.exists():
        return traces

    for path in sorted(DATA_DIR.glob("td_trace_*.json")):
        with path.open("r", encoding="utf-8") as trace_file:
            payload = json.load(trace_file)
        traces.append(
            {
                "file_name": path.name,
                "file_path": str(path),
                "payload": payload,
            }
        )
    return traces


def build_html(traces: List[Dict[str, Any]]) -> str:
    data_json = json.dumps(traces)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TD Analytics</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --panel: #ffffff;
      --line: #d8dee8;
      --ink: #0f172a;
      --muted: #5b6472;
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
    .grid {{ display: grid; gap: 12px; }}
    .cards {{ grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-bottom: 18px; }}
    .card, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .panel {{ margin-bottom: 14px; }}
    .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }}
    .value {{ font-size: 22px; font-weight: 700; margin: 4px 0 6px; }}
    .small {{ color: var(--muted); font-size: 13px; line-height: 1.5; }}
    .controls {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }}
    select {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 10px 12px;
      font: inherit;
      color: var(--ink);
    }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    pre {{
      white-space: pre;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      overflow-x: auto;
      margin: 0;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>TD Analytics</h1>
    <div class="meta">Trace files capture each TD agent's selected actions, Q-values at decision time, and per-episode learning updates.</div>

    <div class="grid cards" id="overviewCards"></div>
    <div class="controls">
      <select id="traceSelect"></select>
      <select id="moveSelect"></select>
    </div>
    <div class="panel" id="traceSummary"></div>
    <div class="grid cards">
      <div class="panel">
        <h3>Board Before Move</h3>
        <pre id="boardBefore"></pre>
      </div>
      <div class="panel">
        <h3>Top Learned Q-values</h3>
        <div id="topQTable"></div>
      </div>
    </div>
    <div class="panel">
      <h3>Action Values At Move</h3>
      <div id="actionValueTable"></div>
    </div>
    <div class="panel">
      <h3>Learning Updates</h3>
      <div id="learningTable"></div>
    </div>
  </div>

  <script>
    const DATA = {data_json};
    const traceSelect = document.getElementById('traceSelect');
    const moveSelect = document.getElementById('moveSelect');
    let activeTraceIndex = 0;
    let activeMoveIndex = 0;

    function boardToText(board) {{
      if (!board) return '';
      return [
        '-------------',
        ...board.flatMap(row => [
          row.map(cell => ` ${{cell || ' '}} `).join('|'),
          '---|---|---'
        ])
      ].join('\\n');
    }}

    function renderOverview() {{
      const totalMoves = DATA.reduce((sum, entry) => sum + entry.payload.action_trace.length, 0);
      const totalUpdates = DATA.reduce((sum, entry) => sum + entry.payload.learning_trace.length, 0);
      const agents = new Set(DATA.map(entry => entry.payload.agent_name));
      document.getElementById('overviewCards').innerHTML = `
        <div class="card"><div class="label">Trace Files</div><div class="value">${{DATA.length}}</div></div>
        <div class="card"><div class="label">TD Agents</div><div class="value">${{agents.size}}</div></div>
        <div class="card"><div class="label">Recorded Moves</div><div class="value">${{totalMoves}}</div></div>
        <div class="card"><div class="label">Learning Updates</div><div class="value">${{totalUpdates}}</div></div>
      `;
    }}

    function setOptions(select, labels, selectedIndex) {{
      select.innerHTML = labels.map((label, index) => `<option value="${{index}}">${{label}}</option>`).join('');
      select.value = String(selectedIndex);
    }}

    function renderSelectors() {{
      setOptions(traceSelect, DATA.map((entry, index) => `${{index + 1}}. ${{entry.file_name}}`), activeTraceIndex);
      const trace = DATA[activeTraceIndex];
      const moves = trace ? trace.payload.action_trace.map(move => `Turn ${{move.turn_index}}: ${{JSON.stringify(move.chosen_action)}}`) : [];
      setOptions(moveSelect, moves, Math.min(activeMoveIndex, Math.max(moves.length - 1, 0)));
    }}

    function table(headers, rows, emptyText) {{
      const head = headers.map(header => `<th>${{header}}</th>`).join('');
      const body = rows.length
        ? rows.map(row => `<tr>${{row.map(cell => `<td>${{cell}}</td>`).join('')}}</tr>`).join('')
        : `<tr><td colspan="${{headers.length}}">${{emptyText}}</td></tr>`;
      return `<table><thead><tr>${{head}}</tr></thead><tbody>${{body}}</tbody></table>`;
    }}

    function renderTrace() {{
      const trace = DATA[activeTraceIndex];
      if (!trace) return;
      const payload = trace.payload;
      const move = payload.action_trace[activeMoveIndex] || payload.action_trace[0];
      document.getElementById('traceSummary').innerHTML = `
        <h2>${{payload.agent_name}} / ${{payload.algorithm}}</h2>
        <div class="small">alpha=${{payload.alpha}}, gamma=${{payload.gamma}}, epsilon=${{Number(payload.epsilon).toFixed(4)}}, q-table states/actions=${{payload.q_table_size}}</div>
        <div class="small">File: ${{trace.file_name}}</div>
      `;
      document.getElementById('boardBefore').textContent = boardToText(move && move.board_before);
      document.getElementById('actionValueTable').innerHTML = table(
        ['Action', 'Q-value'],
        (move ? move.action_values : []).map(item => [JSON.stringify(item.action), Number(item.q_value).toFixed(4)]),
        'No action values recorded.'
      );
      document.getElementById('learningTable').innerHTML = table(
        ['Action', 'Reward', 'Old Value', 'Target', 'New Value', 'Done'],
        payload.learning_trace.map(item => [
          JSON.stringify(item.action),
          Number(item.reward).toFixed(2),
          Number(item.old_value).toFixed(4),
          Number(item.target).toFixed(4),
          Number(item.new_value).toFixed(4),
          item.done ? 'yes' : 'no'
        ]),
        'No learning updates recorded.'
      );
      document.getElementById('topQTable').innerHTML = table(
        ['Action', 'Q-value'],
        payload.top_q_values.map(item => [JSON.stringify(item.action), Number(item.q_value).toFixed(4)]),
        'No Q-values learned yet.'
      );
    }}

    traceSelect.addEventListener('change', event => {{
      activeTraceIndex = Number(event.target.value);
      activeMoveIndex = 0;
      renderSelectors();
      renderTrace();
    }});

    moveSelect.addEventListener('change', event => {{
      activeMoveIndex = Number(event.target.value);
      renderTrace();
    }});

    renderOverview();
    renderSelectors();
    renderTrace();
  </script>
</body>
</html>
"""


def generate_td_analytics_html(output_path: Path = OUTPUT_PATH):
    output_path.write_text(build_html(load_traces()), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    print(generate_td_analytics_html())
