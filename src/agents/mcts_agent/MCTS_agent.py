import random
from collections import defaultdict
import math
import json
import os
from datetime import datetime
from Board import Board


def _copy_board_state(board: Board):
    return [row[:] for row in board.board]


def _board_to_text(board_state):
    lines = ["-------------"]
    for row in board_state:
        lines.append("|".join([f" {cell} " if cell else "   " for cell in row]))
        lines.append("---|---|---")
    return "\n".join(lines)


def _next_player_for_state(board_state):
    x_count = sum(1 for row in board_state for cell in row if cell == 'X')
    o_count = sum(1 for row in board_state for cell in row if cell == 'O')
    return 'X' if x_count <= o_count else 'O'

class MCTSNode:
    """Represents a node in the Monte Carlo Search Tree."""
    def __init__(self, state=None, parent=None, action_from_parent=None):
        self.state = state  # The board state (Board object) - may be None for root
        self.parent = parent
        self.action_from_parent = action_from_parent  # Action that led to this state
        self.children = {}  # Maps action -> MCTSNode
        self.visits = 0
        self.total_value = 0.0  # Sum of rewards obtained from simulations passing through this node

    def is_fully_expanded(self, legal_actions):
        """Checks if all possible actions have been added as children."""
        return len(self.children) == len(legal_actions)

    def to_summary(self):
        """Returns a compact summary for analytics export."""
        board_state = _copy_board_state(self.state) if self.state is not None else [[None for _ in range(3)] for _ in range(3)]
        return {
            "action_from_parent": self.action_from_parent,
            "board": board_state,
            "board_text": _board_to_text(board_state),
            "player_to_move": _next_player_for_state(board_state),
            "visits": self.visits,
            "total_value": self.total_value,
            "average_value": (self.total_value / self.visits) if self.visits else 0.0,
            "children": [
                {
                    "action": list(action),
                    "node": child.to_summary(),
                }
                for action, child in self.children.items()
            ],
        }


class MCTS:
    """Implements the core Monte Carlo Tree Search algorithm."""
    def __init__(self, simulation_depth=5, exploration_constant=1.414):
        self.simulation_depth = simulation_depth
        self.C = exploration_constant  # Exploration constant (sqrt(2))

    def select(self, node: MCTSNode, legal_actions: list) -> MCTSNode:
        """Selects the best child node using UCB1 formula."""
        # If not fully expanded, return this node to signal expansion is needed.
        if not node.is_fully_expanded(legal_actions):
            return node

        if not node.children:
            return node

        best_score = -float('inf')
        best_child = node

        for child in node.children.values():
            if child.visits == 0:
                return child

            exploitation = child.total_value / child.visits
            exploration = self.C * (math.sqrt(math.log(max(node.visits, 1))) / math.sqrt(child.visits))
            score = exploitation + exploration

            if score > best_score:
                best_score = score
                best_child = child

        return best_child

    def expand(self, node: MCTSNode, legal_actions: list) -> MCTSNode:
        """Expands the selected node by creating one new child."""
        unexpanded_actions = [a for a in legal_actions if a not in node.children]
        if not unexpanded_actions:
            raise Exception("Cannot expand: No legal actions available.")

        action = random.choice(unexpanded_actions)
        row, col = action

        # Create a COPY of the current board state to simulate without mutating real environment
        if node.state is not None:
            new_board = Board()
            for r in range(3):
                for c in range(3):
                    new_board.board[r][c] = node.state.board[r][c]
        else:
            new_board = Board()

        # Determine whose turn it is for this simulated state
        # Count X and O to figure out next player (X always goes first)
        x_count = sum(1 for row in new_board.board for cell in row if cell == 'X')
        o_count = sum(1 for row in new_board.board for cell in row if cell == 'O')
        current_player = 'X' if x_count <= o_count else 'O'

        # Simulate the move on the copied board. Legal actions are computed from
        # this node's state, so this should only fail if the caller is inconsistent.
        if not new_board.make_move(row, col, current_player):
            raise ValueError(f"Cannot expand illegal action {action} for current node.")

        new_node = MCTSNode(
            state=new_board,
            parent=node,
            action_from_parent=action
        )
        node.children[action] = new_node
        return new_node

    def simulate(self, start_state: Board, root_player: str) -> float:
        """Runs a random rollout simulation from the given board state until terminal or depth limit."""
        # Create a working copy for simulation
        sim_board = Board()
        for r in range(3):
            for c in range(3):
                sim_board.board[r][c] = start_state.board[r][c]

        # Determine current player
        x_count = sum(1 for row in sim_board.board for cell in row if cell == 'X')
        o_count = sum(1 for row in sim_board.board for cell in row if cell == 'O')
        current_player = 'X' if x_count <= o_count else 'O'

        reward = 0.0
        done = False

        for _ in range(self.simulation_depth):
            legal_moves = sim_board.get_empty_cells()
            if not legal_moves or done:
                break

            action = random.choice(legal_moves)
            row, col = action
            sim_board.make_move(row, col, current_player)

            if sim_board.check_win(current_player):
                done = True
                reward = 1.0 if current_player == root_player else -1.0
            elif sim_board.is_board_full():
                done = True
                reward = 0.0  # Draw

            current_player = 'O' if current_player == 'X' else 'X'

        return reward

    def backpropagate(self, node: MCTSNode, value):
        """Updates the statistics (visits and total value) up to the root."""
        while node is not None:
            node.visits += 1
            node.total_value += value
            node = node.parent


class MCTS_Agent:
    """An agent that uses Monte Carlo Tree Search to select moves in Tic-Tac-Toe."""
    def __init__(self, name="MCTS", simulations=50, simulation_depth=5):
        self.name = name
        self.mcts = MCTS(simulation_depth=simulation_depth, exploration_constant=1.414)
        self.simulations = simulations
        self.game_trace = []
        self._trace_turn = 0
        self._current_game_id = None

    def start_game_trace(self, game_id=None):
        self.game_trace = []
        self._trace_turn = 0
        self._current_game_id = game_id or datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    def _record_trace(self, entry):
        self.game_trace.append(entry)

    def save_game_trace(self, output_dir=None, game_index=None):
        if not self.game_trace:
            return None
        base_dir = output_dir or os.path.join(os.path.dirname(__file__), "mcts_data")
        os.makedirs(base_dir, exist_ok=True)
        suffix = self._current_game_id or (f"game_{game_index}" if game_index is not None else "game")
        path = os.path.join(base_dir, f"mcts_trace_{suffix}.json")
        payload = {
            "agent_name": self.name,
            "simulation_count": self.simulations,
            "trace": self.game_trace,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        return path

    def take_action(self, state: Board, legal_actions: list):
        """Selects the best action using MCTS based on the current game state."""
        # 1. Initialize Root Node
        root = MCTSNode(state=state)
        self._trace_turn += 1
        x_count = sum(1 for row in state.board for cell in row if cell == 'X')
        o_count = sum(1 for row in state.board for cell in row if cell == 'O')
        root_player = 'X' if x_count <= o_count else 'O'

        # 2. Build the Tree (Selection -> Expansion -> Simulation -> Backpropagation)
        for _ in range(self.simulations):
            current_node = root
            path_nodes = [root]

            # Selection Phase: Traverse down the tree using UCB1
            while True:
                node_legal_actions = current_node.state.get_empty_cells()
                if not node_legal_actions:
                    break

                selected = self.mcts.select(current_node, node_legal_actions)

                if selected is current_node:
                    # Node not fully expanded - expand it.
                    break

                current_node = selected
                path_nodes.append(current_node)

            # Expansion Phase: Expand the leaf node
            node_legal_actions = current_node.state.get_empty_cells()
            if not node_legal_actions:
                self.mcts.backpropagate(current_node, 0.0)
                continue

            expanded_child = self.mcts.expand(current_node, node_legal_actions)

            # Simulation Phase: Run a random rollout
            reward = self.mcts.simulate(expanded_child.state, root_player)

            # Backpropagation Phase: Update statistics from expanded node up to root
            self.mcts.backpropagate(expanded_child, reward)

        # 3. Determine Best Move: Choose action leading to highest average value
        best_action = None
        max_score = -float('inf')

        for action, child in root.children.items():
            if child.visits > 0:
                score = child.total_value / child.visits
                if score > max_score:
                    max_score = score
                    best_action = action

        root_summary = {
            "turn_index": self._trace_turn,
            "root_player": root_player,
            "board_before": _copy_board_state(state),
            "board_before_text": _board_to_text(_copy_board_state(state)),
            "requested_legal_actions": [list(move) for move in legal_actions],
            "simulations": self.simulations,
            "chosen_action": list(best_action) if best_action else None,
            "chosen_action_value": max_score if best_action else None,
            "tree": root.to_summary(),
            "children": [
                {
                    "action": list(action),
                    "visits": child.visits,
                    "total_value": child.total_value,
                    "average_value": (child.total_value / child.visits) if child.visits else 0.0,
                }
                for action, child in root.children.items()
            ],
        }
        if best_action:
            board_after = _copy_board_state(state)
            board_after[best_action[0]][best_action[1]] = root_player
            root_summary["board_after"] = board_after
            root_summary["board_after_text"] = _board_to_text(board_after)
        else:
            root_summary["board_after"] = _copy_board_state(state)
            root_summary["board_after_text"] = _board_to_text(root_summary["board_after"])
        self._record_trace(root_summary)

        return best_action if best_action else random.choice(legal_actions)
