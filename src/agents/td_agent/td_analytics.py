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
      --bg: #f3f5f9;
      --panel: #ffffff;
      --line: #d8dee8;
      --ink: #0f172a;
      --muted: #5b6472;
      --accent: #0f766e;
      --accent-soft: #ccfbf1;
      --warn: #92400e;
      --warn-soft: #fef3c7;
      --danger: #991b1b;
      --danger-soft: #fee2e2;
      --good: #166534;
      --good-soft: #dcfce7;
    }}
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    .wrap {{ padding: 24px; max-width: 1440px; margin: 0 auto; }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    .meta {{ color: var(--muted); margin: 8px 0 18px; line-height: 1.5; }}
    .grid {{ display: grid; gap: 12px; }}
    .cards {{ grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); margin-bottom: 18px; }}
    .card, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
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
    .control-label {{ display: grid; gap: 6px; font-size: 13px; color: var(--muted); }}
    select {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 10px;
      padding: 10px 12px;
      font: inherit;
      color: var(--ink);
    }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    tr.selected-row td {{ background: #ecfeff; }}
    pre {{
      white-space: pre;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      overflow-x: auto;
      margin: 0;
    }}
    .hero {{
      display: grid;
      gap: 10px;
      margin-bottom: 16px;
      padding: 18px;
      border-radius: 16px;
      background: linear-gradient(135deg, #ffffff 0%, #ecfeff 45%, #f8fafc 100%);
      border: 1px solid #cbd5e1;
    }}
    .hero-title {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      background: #e2e8f0;
      color: #0f172a;
    }}
    .chip.good {{ background: var(--good-soft); color: var(--good); }}
    .chip.bad {{ background: var(--danger-soft); color: var(--danger); }}
    .chip.neutral {{ background: #e2e8f0; color: #334155; }}
    .chip.accent {{ background: var(--accent-soft); color: var(--accent); }}
    .inline-stats {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 6px;
    }}
    .two-up {{
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    }}
    .three-up {{
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }}
    .callout {{
      margin-top: 10px;
      padding: 12px;
      border-radius: 10px;
      background: #f8fafc;
      border: 1px solid var(--line);
      line-height: 1.5;
    }}
    .formula {{
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 13px;
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      overflow-x: auto;
    }}
    .info-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }}
    .info-button {{
      width: 24px;
      height: 24px;
      border-radius: 999px;
      border: 1px solid #94a3b8;
      background: #fff;
      color: #334155;
      font-weight: 700;
      cursor: pointer;
    }}
    .info-box {{
      display: none;
      margin-top: 8px;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid #bfdbfe;
      background: #eff6ff;
      color: #1e3a8a;
      line-height: 1.5;
    }}
    .info-box.open {{ display: block; }}
    .board-caption {{
      margin-top: 8px;
      font-size: 13px;
      color: var(--muted);
      line-height: 1.5;
    }}
    .empty-state {{
      color: var(--muted);
      font-style: italic;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>TD Analytics</h1>
    <div class="meta">This view links one selected move to the board the agent saw, the move it actually played, the board after the move, and the TD update that was applied after the game ended.</div>

    <div class="grid cards" id="overviewCards"></div>
    <div class="controls">
      <label class="control-label">Trace file
        <select id="traceSelect"></select>
      </label>
      <label class="control-label">Agent move inside this game
        <select id="moveSelect"></select>
      </label>
    </div>
    <div class="hero" id="traceSummary"></div>
    <div class="grid cards three-up">
      <div class="panel">
        <div class="info-row">
          <h3>Selected Move</h3>
          <button class="info-button" data-info-target="selectedMoveInfo" type="button">i</button>
        </div>
        <div id="selectedMoveSummary"></div>
        <div id="selectedMoveInfo" class="info-box">This section answers “what did the agent actually do here?” It shows the chosen action, whether it explored or exploited, and whether that move later ended in a win, loss, or draw for this agent.</div>
      </div>
      <div class="panel">
        <h3>Board Before Move</h3>
        <pre id="boardBefore"></pre>
        <div class="board-caption" id="boardBeforeCaption"></div>
      </div>
      <div class="panel">
        <h3>Board After Move</h3>
        <pre id="boardAfter"></pre>
        <div class="board-caption" id="boardAfterCaption"></div>
      </div>
    </div>
    <div class="panel">
      <div class="info-row">
        <h3>Action Values At Move</h3>
        <button class="info-button" data-info-target="actionValuesInfo" type="button">i</button>
      </div>
      <div id="actionValuesInfo" class="info-box">These are the Q-values for each legal action in the selected state, before the chosen move was made. A zero here usually means the state-action pair has not learned a preference yet, not that the logging is broken.</div>
      <div id="actionValueTable"></div>
    </div>
    <div class="panel">
      <div class="info-row">
        <h3>Learning Update For Selected Move</h3>
        <button class="info-button" data-info-target="updateInfo" type="button">i</button>
      </div>
      <div id="updateInfo" class="info-box">Q-learning bootstraps from the best next action value in the next state. SARSA bootstraps from the next action the same agent actually took. Only the agent's own turns are updated here.</div>
      <div id="selectedUpdate"></div>
    </div>
    <div class="panel">
      <h3>Move Update Timeline</h3>
      <div id="learningTable"></div>
    </div>
    <div class="panel">
      <div class="info-row">
        <h3>Strongest Learned Q-table Entries</h3>
        <button class="info-button" data-info-target="topQInfo" type="button">i</button>
      </div>
      <div id="topQInfo" class="info-box">These values are cumulative across training up to this trace file. They are not “the best moves from only this one game.” Positive values suggest actions the agent expects to help; negative values suggest actions it learned to avoid.</div>
      <div id="topQTable"></div>
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

    function boardFromStateKey(stateKey) {{
      if (!Array.isArray(stateKey) || stateKey.length !== 9) return null;
      const cells = stateKey.map(cell => cell === '-' ? null : cell);
      return [cells.slice(0, 3), cells.slice(3, 6), cells.slice(6, 9)];
    }}

    function inferMarker(boardBefore, boardAfter, chosenAction) {{
      if (boardAfter && chosenAction) {{
        const [row, col] = chosenAction;
        return boardAfter?.[row]?.[col] || null;
      }}
      const flat = (boardBefore || []).flat();
      const xCount = flat.filter(cell => cell === 'X').length;
      const oCount = flat.filter(cell => cell === 'O').length;
      return xCount <= oCount ? 'X' : 'O';
    }}

    function deriveBoardAfter(move) {{
      if (!move || !move.board_before || !move.chosen_action) return move?.board_after || null;
      if (move.board_after) return move.board_after;
      const marker = inferMarker(move.board_before, move.board_after, move.chosen_action);
      if (!marker) return null;
      const nextBoard = move.board_before.map(row => [...row]);
      const [row, col] = move.chosen_action;
      if (nextBoard[row] && nextBoard[row][col] == null) {{
        nextBoard[row][col] = marker;
      }}
      return nextBoard;
    }}

    function formatAction(action) {{
      return Array.isArray(action) ? `(${{action[0]}}, ${{action[1]}})` : 'n/a';
    }}

    function formatSigned(value, digits = 4) {{
      if (typeof value !== 'number' || Number.isNaN(value)) return 'n/a';
      const fixed = value.toFixed(digits);
      return value > 0 ? `+${{fixed}}` : fixed;
    }}

    function resultChip(result) {{
      if (result === 'win') return '<span class="chip good">Win</span>';
      if (result === 'loss') return '<span class="chip bad">Loss</span>';
      return '<span class="chip neutral">Draw</span>';
    }}

    function escapeHtml(text) {{
      return String(text)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
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
      const moves = trace ? trace.payload.action_trace.map(move => {{
        const marker = move.player_marker || inferMarker(move.board_before, move.board_after, move.chosen_action) || '?';
        return `Move ${{move.turn_index}}: ${{marker}} -> ${{formatAction(move.chosen_action)}}`;
      }}) : [];
      setOptions(moveSelect, moves, Math.min(activeMoveIndex, Math.max(moves.length - 1, 0)));
    }}

    function table(headers, rows, emptyText) {{
      const head = headers.map(header => `<th>${{header}}</th>`).join('');
      const body = rows.length
        ? rows.map(row => `<tr>${{row.map(cell => `<td>${{cell}}</td>`).join('')}}</tr>`).join('')
        : `<tr><td colspan="${{headers.length}}">${{emptyText}}</td></tr>`;
      return `<table><thead><tr>${{head}}</tr></thead><tbody>${{body}}</tbody></table>`;
    }}

    function normalizeActionValues(move) {{
      if (!move) return [];
      if (Array.isArray(move.action_values) && move.action_values.length) return move.action_values;
      return (move.legal_actions || []).map(action => {{
        const isChosen = JSON.stringify(action) === JSON.stringify(move.chosen_action);
        return {{
          action,
          q_value: 0,
          inferred: true,
          chosen: isChosen,
        }};
      }});
    }}

    function findSelectedUpdate(payload, move, moveIndex) {{
      if (move?.learning_update) return move.learning_update;
      const byTurn = payload.learning_trace.find(item => item.turn_index === move?.turn_index);
      if (byTurn) return byTurn;
      return payload.learning_trace[moveIndex] || null;
    }}

    function buildTraceSummary(payload, trace, move, updateRecord) {{
      const marker = move?.player_marker || updateRecord?.player_marker || inferMarker(move?.board_before, move?.board_after, move?.chosen_action) || '?';
      const result = move?.result || updateRecord?.result || (updateRecord?.done ? (updateRecord.reward > 0 ? 'win' : updateRecord.reward < 0 ? 'loss' : 'draw') : null);
      const winnerMarker = move?.winner_marker || null;
      const outcomeText = winnerMarker ? `Winner: ${{winnerMarker}}` : 'Winner: draw';
      document.getElementById('traceSummary').innerHTML = `
        <div class="hero-title">
          <h2>${{payload.agent_name}} / ${{payload.algorithm.toUpperCase()}}</h2>
          <span class="chip accent">Agent marker: ${{marker}}</span>
          ${{result ? resultChip(result) : ''}}
        </div>
        <div class="small">alpha=${{payload.alpha}}, gamma=${{payload.gamma}}, epsilon after this game=${{Number(payload.epsilon).toFixed(4)}}, Q-table entries=${{payload.q_table_size}}</div>
        <div class="inline-stats">
          <span class="chip neutral">${{trace.file_name}}</span>
          <span class="chip neutral">${{outcomeText}}</span>
          <span class="chip neutral">Agent turns in this game: ${{payload.action_trace.length}}</span>
        </div>
        <div class="callout">The learning logic is not empty here: most early-game states still show zero Q-values because they have not accumulated enough terminal credit yet. The update that changes a value is usually the terminal move first, then earlier moves inherit value over later games through bootstrapping.</div>
      `;
    }}

    function renderSelectedMove(move, updateRecord) {{
      if (!move) {{
        document.getElementById('selectedMoveSummary').innerHTML = '<div class="empty-state">No move trace available.</div>';
        return;
      }}
      const marker = move.player_marker || updateRecord?.player_marker || inferMarker(move.board_before, move.board_after, move.chosen_action) || '?';
      const reward = move.learning_reward ?? updateRecord?.reward;
      document.getElementById('selectedMoveSummary').innerHTML = `
        <div class="inline-stats">
          <span class="chip accent">Turn ${{move.turn_index}}</span>
          <span class="chip neutral">Played: ${{marker}} at ${{formatAction(move.chosen_action)}}</span>
          <span class="chip neutral">${{move.policy === 'explore' ? 'Exploration' : 'Exploitation'}}</span>
          <span class="chip neutral">Learning reward: ${{formatSigned(Number(reward || 0), 2)}}</span>
        </div>
        <div class="callout">The highlighted row in “Action Values At Move” is the action the agent actually chose.</div>
      `;
    }}

    function renderActionValues(move) {{
      const values = normalizeActionValues(move);
      const rows = values.map(item => {{
        const isChosen = JSON.stringify(item.action) === JSON.stringify(move?.chosen_action);
        return `
          <tr class="${{isChosen ? 'selected-row' : ''}}">
            <td>${{formatAction(item.action)}}${{isChosen ? ' <strong>(played)</strong>' : ''}}</td>
            <td>${{formatSigned(Number(item.q_value), 4)}}</td>
            <td>${{isChosen ? 'yes' : 'no'}}</td>
          </tr>
        `;
      }}).join('');
      document.getElementById('actionValueTable').innerHTML = values.length
        ? `<table><thead><tr><th>Action</th><th>Q-value before move</th><th>Chosen</th></tr></thead><tbody>${{rows}}</tbody></table>`
        : table(['Action', 'Q-value before move', 'Chosen'], [], 'No action values recorded.');
    }}

    function renderSelectedUpdate(payload, move, updateRecord) {{
      if (!updateRecord) {{
        document.getElementById('selectedUpdate').innerHTML = '<div class="empty-state">No TD update was linked to this move.</div>';
        return;
      }}
      const algorithm = updateRecord.algorithm || payload.algorithm;
      const bootstrapAction = updateRecord.bootstrap_action || (algorithm === 'sarsa' ? updateRecord.next_action : null);
      const bootstrapValue = Number(updateRecord.bootstrap_q_value || 0);
      const formula = updateRecord.done
        ? `target = reward = ${{formatSigned(Number(updateRecord.reward), 4)}}`
        : algorithm === 'sarsa'
          ? `target = reward + gamma * Q(next_state, next_action actually taken) = ${{formatSigned(Number(updateRecord.reward), 4)}} + ${{payload.gamma}} * ${{formatSigned(bootstrapValue, 4)}} = ${{formatSigned(Number(updateRecord.target), 4)}}`
          : `target = reward + gamma * max_a Q(next_state, a) = ${{formatSigned(Number(updateRecord.reward), 4)}} + ${{payload.gamma}} * ${{formatSigned(bootstrapValue, 4)}} = ${{formatSigned(Number(updateRecord.target), 4)}}`;
      const bootstrapLabel = updateRecord.done
        ? 'Terminal state, so there is no bootstrap action.'
        : algorithm === 'sarsa'
          ? `SARSA used the next action actually taken by this agent: ${{formatAction(bootstrapAction)}}.`
          : `Q-learning used the best-valued next action in the next state: ${{formatAction(bootstrapAction)}}.`;
      document.getElementById('selectedUpdate').innerHTML = `
        <div class="grid two-up">
          <div class="card">
            <div class="label">Value Update</div>
            <div class="value">${{formatSigned(Number(updateRecord.old_value), 4)}} -> ${{formatSigned(Number(updateRecord.new_value), 4)}}</div>
            <div class="small">alpha=${{payload.alpha}} applied toward target ${{formatSigned(Number(updateRecord.target), 4)}}</div>
          </div>
          <div class="card">
            <div class="label">Bootstrap Source</div>
            <div class="value">${{algorithm === 'sarsa' ? 'SARSA' : 'Q-learning'}}</div>
            <div class="small">${{bootstrapLabel}}</div>
          </div>
        </div>
        <div class="formula">${{escapeHtml(formula)}}</div>
      `;
    }}

    function renderLearningTimeline(payload, selectedTurn) {{
      const rows = payload.learning_trace.map(item => {{
        const isSelected = item.turn_index === selectedTurn;
        const bootstrapAction = item.bootstrap_action || (item.algorithm === 'sarsa' ? item.next_action : null);
        return `
          <tr class="${{isSelected ? 'selected-row' : ''}}">
            <td>${{item.turn_index ?? ''}}</td>
            <td>${{formatAction(item.action)}}</td>
            <td>${{formatSigned(Number(item.reward), 2)}}</td>
            <td>${{formatSigned(Number(item.old_value), 4)}}</td>
            <td>${{formatSigned(Number(item.target), 4)}}</td>
            <td>${{formatSigned(Number(item.new_value), 4)}}</td>
            <td>${{bootstrapAction ? formatAction(bootstrapAction) : 'terminal'}}</td>
            <td>${{item.done ? 'yes' : 'no'}}</td>
          </tr>
        `;
      }}).join('');
      document.getElementById('learningTable').innerHTML = payload.learning_trace.length
        ? `<table><thead><tr><th>Turn</th><th>Action</th><th>Reward</th><th>Old value</th><th>Target</th><th>New value</th><th>Bootstrap action</th><th>Done</th></tr></thead><tbody>${{rows}}</tbody></table>`
        : table(['Turn', 'Action', 'Reward', 'Old value', 'Target', 'New value', 'Bootstrap action', 'Done'], [], 'No learning updates recorded.');
    }}

    function renderTopQ(payload) {{
      const topValues = (payload.top_q_values || []).filter(item => Math.abs(Number(item.q_value || 0)) > 1e-9).slice(0, 10);
      const rows = topValues.map(item => {{
        const board = boardToText(boardFromStateKey(item.state_key));
        return [
          `<pre>${{escapeHtml(board)}}</pre>`,
          formatAction(item.action),
          formatSigned(Number(item.q_value), 4),
        ];
      }});
      document.getElementById('topQTable').innerHTML = topValues.length
        ? table(['State', 'Action', 'Q-value'], rows, 'No non-zero Q-values learned yet.')
        : '<div class="empty-state">No non-zero Q-values learned yet for this trace. Early training often looks like this.</div>';
    }}

    function renderTrace() {{
      const trace = DATA[activeTraceIndex];
      if (!trace) return;
      const payload = trace.payload;
      const move = payload.action_trace[activeMoveIndex] || payload.action_trace[0];
      const updateRecord = findSelectedUpdate(payload, move, activeMoveIndex);
      const boardAfter = deriveBoardAfter(move) || updateRecord?.board_after || null;
      const marker = move?.player_marker || updateRecord?.player_marker || inferMarker(move?.board_before, boardAfter, move?.chosen_action) || '?';

      buildTraceSummary(payload, trace, move, updateRecord);
      renderSelectedMove(move, updateRecord);
      document.getElementById('boardBefore').textContent = boardToText(move && move.board_before);
      document.getElementById('boardAfter').textContent = boardToText(boardAfter);
      document.getElementById('boardBeforeCaption').textContent = move ? `Agent marker ${{marker}} had not played this selected move yet.` : '';
      document.getElementById('boardAfterCaption').textContent = move ? `This is the board immediately after ${{marker}} played ${{formatAction(move.chosen_action)}}.` : '';
      renderActionValues(move);
      renderSelectedUpdate(payload, move, updateRecord);
      renderLearningTimeline(payload, move?.turn_index);
      renderTopQ(payload);
    }}

    document.querySelectorAll('.info-button').forEach(button => {{
      button.addEventListener('click', () => {{
        const target = document.getElementById(button.dataset.infoTarget);
        target.classList.toggle('open');
      }});
    }});

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
