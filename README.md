# Tic-Tac-Toe Agents Arena

A small reinforcement-learning playground for running Tic-Tac-Toe matches between agents.

The project currently includes:

- A Tic-Tac-Toe environment in `src/Game.py` and `src/Board.py`
- A random baseline agent
- An MCTS agent with configurable simulation count and rollout depth
- A tournament runner that records game logs, summary statistics, and MCTS traces
- HTML reports for tournament results and MCTS analytics

## Project Structure

```text
.
├── main.py
├── pyproject.toml
├── README.md
└── src
    ├── Board.py
    ├── Game.py
    ├── Tournament.py
    ├── tournament_statistics.html
    ├── game_logs/
    └── agents
        ├── mcts_agent/
        └── random_agent/
```

## Requirements

- Python 3.11 or newer

This project does not currently declare external Python dependencies in `pyproject.toml`.

## Run The Tournament

From the project root:

```bash
python src/Tournament.py
```

By default, this runs 100 games and writes:

- Game logs to `src/game_logs/`
- Tournament report to `src/tournament_statistics.html`
- MCTS trace data to `src/agents/mcts_agent/mcts_data/`
- MCTS analytics report to `src/agents/mcts_agent/mcts_analytics.html`

## Current Default Matchup

The default tournament is configured in `src/Tournament.py`.

At the moment it pits:

- `tom`: MCTS agent
- `jerry`: MCTS agent

Each MCTS agent can be configured with:

- `simulations`: number of MCTS simulations per move
- `simulation_depth`: rollout depth used during simulation

Example constructor:

```python
MCTS_Agent(name="tom", simulations=50, simulation_depth=10)
```

## Reports

Open these files in a browser after running a tournament:

```text
src/tournament_statistics.html
src/agents/mcts_agent/mcts_analytics.html
```

The tournament report summarizes wins, losses, draws, matchup totals, and win-ratio trends.
The MCTS analytics report shows per-move search traces for MCTS agents.

## Notes

The tournament currently creates agents from code in `src/Tournament.py`. A natural next step is to move tournament setup into a YAML config file so matchups, MCTS parameters, and first-player order can be changed without editing Python.
