import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from Game import Game
from agents.random_agent.Random_agent import RandomAgent
from agents.mcts_agent.MCTS_agent import MCTS_Agent


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@dataclass(frozen=True)
class MatchupSpec:
    label: str
    agent1_cls: type
    agent2_cls: type
    agent1_name: Optional[str] = None
    agent2_name: Optional[str] = None
    agent1_kwargs: Dict[str, Any] = field(default_factory=dict)
    agent2_kwargs: Dict[str, Any] = field(default_factory=dict)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


class Tournament:
    """Runs one or more matchups and writes terminal and HTML summaries."""

    def __init__(
        self,
        agent1_cls: Optional[type] = None,
        agent2_cls: Optional[type] = None,
        matchups: Optional[List[MatchupSpec]] = None,
    ):
        if matchups is not None:
            self.matchups = matchups
        elif agent1_cls is not None and agent2_cls is not None:
            self.matchups = [
                MatchupSpec(
                    label=f"{agent1_cls.__name__} vs {agent2_cls.__name__}",
                    agent1_cls=agent1_cls,
                    agent2_cls=agent2_cls,
                )
            ]
        else:
            self.matchups = [
                MatchupSpec(
                    label="tom vs jerry",
                    agent1_cls=MCTS_Agent,
                    agent2_cls=MCTS_Agent,
                    agent1_name="tom",
                    agent2_name="jerry",
                    agent1_kwargs={"simulations": 50, "simulation_depth":10},
                    agent2_kwargs={"simulations": 50, "simulation_depth":2},
                ),
            ]

        self.game = Game()
        self.results: List[Dict[str, Any]] = []
        self.report_path = Path(__file__).resolve().parent / "tournament_statistics.html"

    def _distribute_games(self, total_games: int) -> List[int]:
        matchup_count = max(len(self.matchups), 1)
        base, remainder = divmod(total_games, matchup_count)
        return [base + (1 if i < remainder else 0) for i in range(matchup_count)]

    def _score_for_winner(self, winner: Optional[str]) -> int:
        if winner == self.game.player1_marker:
            return 1
        if winner == self.game.player2_marker:
            return -1
        return 0

    def _run_single_game(
        self,
        matchup: MatchupSpec,
        agent1,
        agent2,
        global_game_index: int,
        matchup_game_index: int,
    ) -> Dict[str, Any]:
        matchup_slug = _slugify(matchup.label)
        agent1_label = matchup.agent1_name or matchup.agent1_cls.__name__
        agent2_label = matchup.agent2_name or matchup.agent2_cls.__name__

        if hasattr(agent1, "start_game_trace"):
            agent1.start_game_trace(game_id=f"{matchup_slug}_{agent1_label.lower()}_{global_game_index}")
        if hasattr(agent2, "start_game_trace"):
            agent2.start_game_trace(game_id=f"{matchup_slug}_{agent2_label.lower()}_{global_game_index}")

        self.game.reset()

        while self.game.current_turn is not None:
            legal_actions = self.game.board.get_empty_cells()
            if not legal_actions:
                break

            is_agent1_turn = self.game.current_turn == self.game.player1_marker
            current_agent = agent1 if is_agent1_turn else agent2

            try:
                action = current_agent.take_action(self.game.get_state(), legal_actions)
            except Exception as exc:
                print(f"Error running {current_agent.__class__.__name__}: {exc}")
                break

            if not action:
                logging.warning("No valid action returned by an agent.")
                break

            _, _, done, _ = self.game.step(action)
            if done:
                break

        log_dir = Path(__file__).resolve().parent / "game_logs"
        log_dir.mkdir(exist_ok=True)
        log_filename = log_dir / f"game_log_{matchup_slug}_{global_game_index}.txt"
        self.game.save_log(filename=str(log_filename))

        if hasattr(agent1, "save_game_trace"):
            agent1.save_game_trace()
        if hasattr(agent2, "save_game_trace"):
            agent2.save_game_trace()

        winner = self.game.history[-1].get("winner") if self.game.history else None
        outcome_score = self._score_for_winner(winner)
        agent1_score = outcome_score
        agent2_score = -outcome_score

        if winner == self.game.player1_marker:
            winner_side = "agent1"
            winner_name = agent1_label
        elif winner == self.game.player2_marker:
            winner_side = "agent2"
            winner_name = agent2_label
        else:
            winner_side = "draw"
            winner_name = "Draw"

        return {
            "game_index": global_game_index,
            "matchup_game_index": matchup_game_index,
            "matchup_label": matchup.label,
            "agent1_name": agent1_label,
            "agent2_name": agent2_label,
            "agent1_marker": self.game.player1_marker,
            "agent2_marker": self.game.player2_marker,
            "winner_marker": winner,
            "winner_side": winner_side,
            "winner_name": winner_name,
            "agent1_score": agent1_score,
            "agent2_score": agent2_score,
            "is_draw": winner_side == "draw",
            "turn_count": len(self.game.history),
        }

    def run_tournament(self, num_games: int = 100):
        """Runs all configured matchups and writes the final reports."""
        self.results = []
        games_per_matchup = self._distribute_games(num_games)
        global_game_index = 0

        for matchup, games_for_matchup in zip(self.matchups, games_per_matchup):
            for matchup_game_index in range(1, games_for_matchup + 1):
                global_game_index += 1
                agent1_kwargs = dict(matchup.agent1_kwargs)
                agent2_kwargs = dict(matchup.agent2_kwargs)
                if matchup.agent1_name:
                    agent1_kwargs["name"] = matchup.agent1_name
                if matchup.agent2_name:
                    agent2_kwargs["name"] = matchup.agent2_name
                agent1 = matchup.agent1_cls(**agent1_kwargs)
                agent2 = matchup.agent2_cls(**agent2_kwargs)
                result = self._run_single_game(
                    matchup=matchup,
                    agent1=agent1,
                    agent2=agent2,
                    global_game_index=global_game_index,
                    matchup_game_index=matchup_game_index,
                )
                self.results.append(result)

        self.generate_report()
        self.write_html_report()

    def _agent_totals(self) -> Dict[str, Dict[str, int]]:
        totals: Dict[str, Dict[str, int]] = {}
        for result in self.results:
            for side in ("agent1", "agent2"):
                agent_name = result[f"{side}_name"]
                score = result[f"{side}_score"]
                bucket = totals.setdefault(agent_name, {"games": 0, "wins": 0, "losses": 0, "draws": 0})
                bucket["games"] += 1
                if score > 0:
                    bucket["wins"] += 1
                elif score < 0:
                    bucket["losses"] += 1
                else:
                    bucket["draws"] += 1
        return totals

    def _matchup_totals(self) -> Dict[str, Dict[str, int]]:
        totals: Dict[str, Dict[str, int]] = {}
        for result in self.results:
            bucket = totals.setdefault(
                result["matchup_label"],
                {"games": 0, "agent1_wins": 0, "agent2_wins": 0, "draws": 0},
            )
            bucket["games"] += 1
            if result["winner_side"] == "agent1":
                bucket["agent1_wins"] += 1
            elif result["winner_side"] == "agent2":
                bucket["agent2_wins"] += 1
            else:
                bucket["draws"] += 1
        return totals

    def _win_ratio_series(self) -> Dict[str, List[Dict[str, float]]]:
        series: Dict[str, List[Dict[str, float]]] = {}
        counters: Dict[str, Dict[str, int]] = {}

        for result in self.results:
            for side in ("agent1", "agent2"):
                agent_name = result[f"{side}_name"]
                score = result[f"{side}_score"]
                counter = counters.setdefault(agent_name, {"games": 0, "wins": 0})
                counter["games"] += 1
                if score > 0:
                    counter["wins"] += 1
                ratio = counter["wins"] / counter["games"]
                series.setdefault(agent_name, []).append(
                    {
                        "game_index": result["game_index"],
                        "ratio": ratio,
                    }
                )

        return series

    def generate_report(self):
        """Prints a terminal summary with correct per-agent scoring."""
        if not self.results:
            print("No games were played to generate a report.")
            return

        agent_totals = self._agent_totals()
        matchup_totals = self._matchup_totals()

        print("=" * 60)
        print("             TOURNAMENT REPORT SUMMARY")
        print("=" * 60)
        print(f"Total Games Played: {len(self.results)}")
        print("-" * 30)

        for matchup in self.matchups:
            stats = matchup_totals.get(matchup.label, {"games": 0, "agent1_wins": 0, "agent2_wins": 0, "draws": 0})
            print(f"\n--- Matchup: {matchup.label} ---")
            print(f"Games: {stats['games']}")
            print(f"{matchup.agent1_name or matchup.agent1_cls.__name__} wins: {stats['agent1_wins']}")
            print(f"{matchup.agent2_name or matchup.agent2_cls.__name__} wins: {stats['agent2_wins']}")
            print(f"Draws: {stats['draws']}")

        print("\n--- Agent Performance ---")
        for agent_name, stats in agent_totals.items():
            score = stats["wins"] - stats["losses"]
            print(f"{agent_name}:")
            print(f"  Games: {stats['games']}")
            print(f"  Wins: {stats['wins']}")
            print(f"  Losses: {stats['losses']}")
            print(f"  Draws: {stats['draws']}")
            print(f"  Score: {score}")

        print("\n=========================================")

    def _build_html_report(self) -> str:
        total_games = len(self.results)
        agent_totals = self._agent_totals()
        matchup_totals = self._matchup_totals()
        win_ratio_series = self._win_ratio_series()

        rows = []
        for result in self.results:
            rows.append(
                f"""
                <tr>
                  <td>{result['game_index']}</td>
                  <td>{result['matchup_label']}</td>
                  <td>{result['agent1_name']} (X)</td>
                  <td>{result['agent2_name']} (O)</td>
                  <td>{result['winner_name']}</td>
                  <td>{result['agent1_score']:+d}</td>
                  <td>{result['agent2_score']:+d}</td>
                </tr>
                """
            )

        matchup_cards = []
        for matchup in self.matchups:
            stats = matchup_totals.get(matchup.label, {"games": 0, "agent1_wins": 0, "agent2_wins": 0, "draws": 0})
            matchup_cards.append(
                f"""
                <div class="card">
                  <div class="label">Matchup</div>
                  <div class="value">{matchup.label}</div>
                  <div class="small">{matchup.agent1_name or matchup.agent1_cls.__name__} plays X, {matchup.agent2_name or matchup.agent2_cls.__name__} plays O</div>
                  <div class="small">Games: {stats['games']}</div>
                  <div class="small">{matchup.agent1_name or matchup.agent1_cls.__name__} wins: {stats['agent1_wins']}</div>
                  <div class="small">{matchup.agent2_name or matchup.agent2_cls.__name__} wins: {stats['agent2_wins']}</div>
                  <div class="small">Draws: {stats['draws']}</div>
                </div>
                """
            )

        agent_cards = []
        for agent_name, stats in sorted(agent_totals.items()):
            agent_cards.append(
                f"""
                <div class="card">
                  <div class="label">Agent</div>
                  <div class="value">{agent_name}</div>
                  <div class="small">Games: {stats['games']}</div>
                  <div class="small">Wins: {stats['wins']}</div>
                  <div class="small">Losses: {stats['losses']}</div>
                  <div class="small">Draws: {stats['draws']}</div>
                  <div class="small">Score: {stats['wins'] - stats['losses']}</div>
                </div>
                """
            )

        data_json = json.dumps(
            {
                "results": self.results,
                "win_ratio_series": win_ratio_series,
                "agent_totals": agent_totals,
                "matchups": [
                    {
                        "label": m.label,
                        "agent1_name": m.agent1_cls.__name__,
                        "agent2_name": m.agent2_cls.__name__,
                    }
                    for m in self.matchups
                ],
            }
        )

        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tournament Statistics</title>
  <style>
    :root {{
      --bg: #f6f7fb;
      --panel: #ffffff;
      --line: #d9dee7;
      --ink: #111827;
      --muted: #5b6472;
      --accent: #2457ff;
      --accent2: #e11d48;
      --accent3: #059669;
    }}
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      color: var(--ink);
      background: var(--bg);
    }}
    .wrap {{ padding: 24px; }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    .meta {{ margin: 8px 0 18px; color: var(--muted); }}
    .tabs {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }}
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
    .grid {{ display: grid; gap: 12px; }}
    .grid.cards {{ grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); margin-bottom: 18px; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
    }}
    .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }}
    .value {{ font-size: 22px; margin: 4px 0 6px; font-weight: 700; }}
    .small {{ color: var(--muted); font-size: 13px; line-height: 1.4; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    .chartcard {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; }}
    canvas {{ width: 100%; height: 420px; display: block; }}
    .legend {{ display: flex; gap: 14px; flex-wrap: wrap; margin-top: 10px; color: var(--muted); }}
    .legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
    .swatch {{ width: 12px; height: 12px; border-radius: 999px; display: inline-block; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Tournament Statistics</h1>
    <div class="meta">Agent labels are shown by runtime name. Player X and Player O roles are listed in each matchup card.</div>

    <div class="tabs">
      <button class="tabbtn active" data-tab="summary">Summary</button>
      <button class="tabbtn" data-tab="games">Games</button>
      <button class="tabbtn" data-tab="trend">Win Ratio Trend</button>
    </div>

    <section id="summary" class="tab active">
      <div class="grid cards">
        <div class="card"><div class="label">Games</div><div class="value">{total_games}</div></div>
        <div class="card"><div class="label">Matchups</div><div class="value">{len(self.matchups)}</div></div>
        <div class="card"><div class="label">Agents</div><div class="value">{len(agent_totals)}</div></div>
        <div class="card"><div class="label">Draws</div><div class="value">{sum(1 for r in self.results if r['is_draw'])}</div></div>
      </div>
      <h2>Matchups</h2>
      <div class="grid cards">{''.join(matchup_cards)}</div>
      <h2>Agent Totals</h2>
      <div class="grid cards">{''.join(agent_cards)}</div>
    </section>

    <section id="games" class="tab">
      <h2>Game Log</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Matchup</th>
            <th>Agent 1</th>
            <th>Agent 2</th>
            <th>Winner</th>
            <th>Agent 1 Score</th>
            <th>Agent 2 Score</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>

    <section id="trend" class="tab">
      <h2>Cumulative Win Ratio</h2>
      <div class="chartcard">
        <canvas id="trendCanvas" width="1200" height="420"></canvas>
        <div id="legend" class="legend"></div>
      </div>
    </section>
  </div>

  <script>
    const DATA = {data_json};
    const tabs = Array.from(document.querySelectorAll('.tabbtn'));
    const panels = Array.from(document.querySelectorAll('.tab'));
    tabs.forEach(btn => btn.addEventListener('click', () => {{
      tabs.forEach(b => b.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
      if (btn.dataset.tab === 'trend') {{
        drawTrend();
      }}
    }}));

    function drawTrend() {{
      const canvas = document.getElementById('trendCanvas');
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.max(800, Math.floor(rect.width * dpr));
      canvas.height = Math.floor(rect.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const width = rect.width;
      const height = rect.height;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, width, height);

      const padding = {{ left: 56, right: 24, top: 24, bottom: 38 }};
      const plotW = width - padding.left - padding.right;
      const plotH = height - padding.top - padding.bottom;

      ctx.strokeStyle = '#d9dee7';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 5; i++) {{
        const y = padding.top + (plotH * i / 5);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
        const label = (1 - i / 5).toFixed(1);
        ctx.fillStyle = '#5b6472';
        ctx.font = '12px Arial';
        ctx.fillText(label, 10, y + 4);
      }}

      const colors = ['#2457ff', '#e11d48', '#059669', '#7c3aed', '#d97706'];
      const agentNames = Object.keys(DATA.win_ratio_series);
      const allPoints = agentNames.flatMap(name => DATA.win_ratio_series[name]);
      const maxGame = Math.max(1, ...allPoints.map(p => p.game_index));

      ctx.fillStyle = '#5b6472';
      ctx.font = '12px Arial';
      for (let i = 0; i <= Math.min(maxGame, 10); i++) {{
        const x = padding.left + plotW * (i / Math.max(1, maxGame - 1));
        ctx.fillText(String(i + 1), x - 4, height - 14);
      }}

      agentNames.forEach((name, idx) => {{
        const series = DATA.win_ratio_series[name];
        if (!series.length) return;
        ctx.beginPath();
        ctx.strokeStyle = colors[idx % colors.length];
        ctx.lineWidth = 2.5;
        series.forEach((point, i) => {{
          const x = padding.left + plotW * ((point.game_index - 1) / Math.max(1, maxGame - 1));
          const y = padding.top + plotH * (1 - point.ratio);
          if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }});
        ctx.stroke();
      }});

      const legend = document.getElementById('legend');
      legend.innerHTML = agentNames.map((name, idx) => `
        <span><span class="swatch" style="background:${{colors[idx % colors.length]}}"></span>${{name}}</span>
      `).join('');
    }}

    drawTrend();
  </script>
</body>
</html>
"""

    def write_html_report(self):
        self.report_path.write_text(self._build_html_report(), encoding="utf-8")
        try:
            from agents.mcts_agent.mcts_analytics import generate_mcts_analytics_html

            generate_mcts_analytics_html()
        except Exception as exc:
            print(f"[WARN] Could not refresh MCTS analytics: {exc}")
        return self.report_path


if __name__ == "__main__":
    tournament = Tournament()
    tournament.run_tournament(num_games=100)
