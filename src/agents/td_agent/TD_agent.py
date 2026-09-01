import random
import json
import os
from collections import defaultdict
from datetime import datetime


def board_to_key(board_state, marker=None):
    """Converts a Board object or plain board snapshot into a hashable key."""
    cells = getattr(board_state, "board", board_state)
    flat = tuple(cell or "-" for row in cells for cell in row)
    return (marker, flat) if marker else flat


def empty_cells_from_snapshot(board_snapshot):
    return [
        (row_index, col_index)
        for row_index, row in enumerate(board_snapshot)
        for col_index, cell in enumerate(row)
        if cell is None
    ]


class TabularTDAgent:
    """Shared epsilon-greedy table logic for simple TD control agents."""

    update_strategy = "q_learning"

    def __init__(
        self,
        name="TD",
        alpha=0.2,
        gamma=0.95,
        epsilon=0.1,
        epsilon_decay=1.0,
        min_epsilon=0.01,
    ):
        self.name = name
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.q_values = defaultdict(float)
        self.game_trace = []
        self.learning_trace = []
        self._trace_turn = 0
        self._current_game_id = None

    def start_game_trace(self, game_id=None):
        self.game_trace = []
        self.learning_trace = []
        self._trace_turn = 0
        self._current_game_id = game_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _q_key(self, state_key, action):
        return (state_key, action)

    def _best_action(self, state_key, legal_actions):
        if not legal_actions:
            return None

        best_value = max(self.q_values[self._q_key(state_key, action)] for action in legal_actions)
        best_actions = [
            action
            for action in legal_actions
            if self.q_values[self._q_key(state_key, action)] == best_value
        ]
        return random.choice(best_actions)

    def take_action(self, state, legal_actions):
        if not legal_actions:
            return None

        state_key = board_to_key(state)
        action_values = [
            {
                "action": list(action),
                "q_value": self.q_values[self._q_key(state_key, action)],
            }
            for action in legal_actions
        ]
        if random.random() < self.epsilon:
            action = random.choice(legal_actions)
            policy = "explore"
        else:
            action = self._best_action(state_key, legal_actions)
            policy = "exploit"

        self._trace_turn += 1
        self.game_trace.append(
            {
                "turn_index": self._trace_turn,
                "agent_name": self.name,
                "algorithm": self.update_strategy,
                "epsilon": self.epsilon,
                "policy": policy,
                "board_before": [row[:] for row in state.board],
                "state_key": list(state_key),
                "legal_actions": [list(move) for move in legal_actions],
                "action_values": action_values,
                "chosen_action": list(action),
            }
        )
        return action

    def _target_value(self, reward, next_state_key, next_legal_actions, next_action, done):
        if done:
            return reward

        if self.update_strategy == "sarsa":
            if next_action is None:
                return reward
            return reward + self.gamma * self.q_values[self._q_key(next_state_key, next_action)]

        best_next = self._best_action(next_state_key, next_legal_actions)
        if best_next is None:
            return reward
        return reward + self.gamma * self.q_values[self._q_key(next_state_key, best_next)]

    def update(self, state_key, action, reward, next_state_key, next_legal_actions, next_action=None, done=False):
        key = self._q_key(state_key, action)
        current_value = self.q_values[key]
        target = self._target_value(reward, next_state_key, next_legal_actions, next_action, done)
        self.q_values[key] = current_value + self.alpha * (target - current_value)
        return {
            "state_key": list(state_key),
            "action": list(action),
            "reward": reward,
            "next_state_key": list(next_state_key),
            "next_legal_actions": [list(move) for move in next_legal_actions],
            "next_action": list(next_action) if next_action else None,
            "done": done,
            "old_value": current_value,
            "target": target,
            "new_value": self.q_values[key],
        }

    def learn_from_episode(self, history, marker):
        """Learns one same-agent transition at a time from a completed game."""
        if not history:
            return

        winner = history[-1].get("winner")
        final_state = history[-1]["next_state"]
        final_reward = 0.0 if winner is None else (1.0 if winner == marker else -1.0)
        own_turn_indexes = [
            index
            for index, entry in enumerate(history)
            if entry["player"] == marker
        ]

        for position, history_index in enumerate(own_turn_indexes):
            entry = history[history_index]
            state_key = board_to_key(entry["state_before"])
            action = tuple(entry["action"])

            is_last_own_turn = position == len(own_turn_indexes) - 1
            if is_last_own_turn:
                update_record = self.update(
                    state_key=state_key,
                    action=action,
                    reward=final_reward,
                    next_state_key=board_to_key(final_state),
                    next_legal_actions=[],
                    done=True,
                )
                self.learning_trace.append(update_record)
                continue

            next_entry = history[own_turn_indexes[position + 1]]
            next_state_key = board_to_key(next_entry["state_before"])
            next_legal_actions = empty_cells_from_snapshot(next_entry["state_before"])
            next_action = tuple(next_entry["action"])
            update_record = self.update(
                state_key=state_key,
                action=action,
                reward=0.0,
                next_state_key=next_state_key,
                next_legal_actions=next_legal_actions,
                next_action=next_action,
                done=False,
            )
            self.learning_trace.append(update_record)

        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

    def _top_q_values(self, limit=20):
        ranked = sorted(self.q_values.items(), key=lambda item: abs(item[1]), reverse=True)
        return [
            {
                "state_key": list(state_key),
                "action": list(action),
                "q_value": value,
            }
            for (state_key, action), value in ranked[:limit]
        ]

    def save_game_trace(self, output_dir=None, game_index=None):
        if not self.game_trace and not self.learning_trace:
            return None
        base_dir = output_dir or os.path.join(os.path.dirname(__file__), "td_data")
        os.makedirs(base_dir, exist_ok=True)
        suffix = self._current_game_id or (f"game_{game_index}" if game_index is not None else "game")
        path = os.path.join(base_dir, f"td_trace_{suffix}.json")
        payload = {
            "agent_name": self.name,
            "algorithm": self.update_strategy,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "epsilon": self.epsilon,
            "epsilon_decay": self.epsilon_decay,
            "min_epsilon": self.min_epsilon,
            "q_table_size": len(self.q_values),
            "top_q_values": self._top_q_values(),
            "action_trace": self.game_trace,
            "learning_trace": self.learning_trace,
        }
        with open(path, "w", encoding="utf-8") as trace_file:
            json.dump(payload, trace_file, indent=2)
        return path


class QLearningAgent(TabularTDAgent):
    """Off-policy tabular Q-learning agent."""

    update_strategy = "q_learning"

    def __init__(self, name="Q-Learning", **kwargs):
        super().__init__(name=name, **kwargs)


class SARSAAgent(TabularTDAgent):
    """On-policy SARSA agent."""

    update_strategy = "sarsa"

    def __init__(self, name="SARSA", **kwargs):
        super().__init__(name=name, **kwargs)
