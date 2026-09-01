# Tic-Tac-Toe Agents Arena

A small reinforcement-learning playground for running Tic-Tac-Toe matches between agents.

The project currently includes:

- A Tic-Tac-Toe environment in `src/Game.py` and `src/Board.py`
- A random baseline agent
- An MCTS agent with configurable simulation count and rollout depth
- Tabular Q-learning and SARSA agents
- A tournament runner that records game logs, summary statistics, and MCTS traces
- HTML reports for tournament results and MCTS analytics
- YAML tournament configuration

## Project Structure

```text
.
├── main.py
├── pyproject.toml
├── README.md
├── config
│   └── tournament.yaml
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

By default, this reads `config/tournament.yaml`, runs the configured matchups, and writes:

- Game logs to `src/game_logs/`
- Tournament report to `src/tournament_statistics.html`
- MCTS trace data to `src/agents/mcts_agent/mcts_data/`
- MCTS analytics report to `src/agents/mcts_agent/mcts_analytics.html`
- TD trace data to `src/agents/td_agent/td_data/`
- TD analytics report to `src/agents/td_agent/td_analytics.html`

Each tournament run clears prior `game_log_*.txt`, `mcts_trace_*.json`, and `td_trace_*.json` files before writing the new run's data.

You can point to another config file:

```bash
python src/Tournament.py --config config/tournament.yaml
```

You can also override total games when matchups do not set their own `games` value:

```bash
python src/Tournament.py --num-games 200
```

## Tournament Config

The default tournament is configured in `config/tournament.yaml`.

Top-level config values:

- `num_games`: total tournament games used when matchup-level `games` values do not fully define the run
- `rolling_window`: number of recent games per agent used for the rolling win-ratio chart

Supported agent types:

- `random`
- `mcts`
- `q_learning`
- `sarsa`

Example matchup:

```yaml
num_games: 100
rolling_window: 10

matchups:
  - label: Q-learning vs SARSA
    games: 40
    agent1:
      type: q_learning
      name: qbert
      params:
        alpha: 0.3
        gamma: 0.95
        epsilon: 0.25
        epsilon_decay: 0.995
        min_epsilon: 0.02
    agent2:
      type: sarsa
      name: sally
      params:
        alpha: 0.3
        gamma: 0.95
        epsilon: 0.25
```

## Current Default Matchups

At the moment the YAML config pits:

- `qbert`: Q-learning agent
- `sally`: SARSA agent
- `tom`: MCTS agent
- `randy`: random baseline agent

Each MCTS agent can be configured with:

- `simulations`: number of MCTS simulations per move
- `simulation_depth`: rollout depth used during simulation

Example constructor:

```python
MCTS_Agent(name="tom", simulations=50, simulation_depth=10)
```

Q-learning and SARSA agents can be configured with:

- `alpha`: learning rate
- `gamma`: future reward discount
- `epsilon`: exploration rate
- `epsilon_decay`: per-game exploration decay
- `min_epsilon`: exploration floor

## Reports

Open these files in a browser after running a tournament:

```text
src/tournament_statistics.html
src/agents/mcts_agent/mcts_analytics.html
```

The tournament report summarizes wins, losses, draws, matchup totals, and win-ratio trends.
The MCTS analytics report shows per-move search traces for MCTS agents.
The TD analytics report shows per-move action values and learning updates for Q-learning and SARSA agents.

## Notes

MCTS is the most naturally aligned agent for tic-tac-toe move selection because the game is small, deterministic, and fully observable. Q-learning and SARSA are also useful here, but they need many completed games so their Q-tables can improve over time. The tournament keeps learning agents alive for all games in a matchup so they can learn across episodes.
