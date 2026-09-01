import logging
from Board import Board
from datetime import datetime

# Setup basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Game:
    """
    Manages the flow of the Tic-Tac-Toe game between two players ('X' and 'O').
    This class acts as the environment interface.
    """
    def __init__(self, player1_marker='X', player2_marker='O'):
        self.board = Board()
        self.player1_marker = player1_marker
        self.player2_marker = player2_marker
        self.current_turn = self.player1_marker  # X starts first
        self.history = [] # To store game logs

    def reset(self):
        """Resets the game board to its initial state."""
        self.__init__(self.player1_marker, self.player2_marker)
        return self.get_state()

    def get_state(self):
        """Returns the current state of the game (the board object)."""
        # For logging/review, we'll return a simple representation or the object itself
        return self.board

    def _board_snapshot(self):
        """Returns a plain list copy of the current board for stable logging."""
        return [row[:] for row in self.board.board]

    def _format_board(self, board_state):
        """Builds a text visualization of a board snapshot."""
        lines = ["-------------"]
        for row in board_state:
            lines.append("|".join([f" {cell} " if cell else "   " for cell in row]))
            lines.append("---|---|---")
        return "\n".join(lines)

    def step(self, action):
        """
        Processes one turn in the environment.

        Args:
            action (tuple): A tuple representing the move (row, col).

        Returns:
            tuple: (next_state, reward, done, info)
                - next_state: The board state after the move.
                - reward: The immediate reward for the agent that made the move.
                - done: Boolean indicating if the game has ended.
                - info: Dictionary with extra information (e.g., winner).
        """
        row, col = action
        current_player = self.current_turn
        state_before = self._board_snapshot()

        # 1. Check if the move is valid and execute it
        if not self.board.make_move(row, col, current_player):
            logging.warning(f"Invalid move attempted by {current_player} at ({row}, {col}).")
            return self.get_state(), -10.0, True, {"message": "Invalid Move"} # Penalize invalid moves

        # 2. Check game status after the move
        winner = None
        done = False
        reward = 0.0

        if self.board.check_win(current_player):
            winner = current_player
            done = True
            # Reward structure: Positive for agent's win, negative for opponent's win (if X is the agent)
            reward = 1.0 if current_player == 'X' else -1.0
        elif self.board.is_board_full():
            done = True
            reward = 0.0 # Draw

        # 3. Switch turn and update state tracking
        if done:
            self.current_turn = None # Game over
        else:
            self.current_turn = self.player2_marker if current_player == self.player1_marker else self.player1_marker

        # 4. Log the transition for review
        log_entry = {
            "state_before": state_before,
            "action": action,
            "player": current_player,
            "reward": reward,
            "done": done,
            "winner": winner,
            "next_state": self._board_snapshot(),
        }
        self.history.append(log_entry)

        # Return standard OpenAI Gym
        return self.get_state(), reward, done, {"winner": winner}


    def play_game_interactive(self):
        """Allows two human players to play the game interactively."""
        print("\n=========================================")
        print("       Tic-Tac-Toe Game (Interactive)   ")
        print("=========================================")
        print(f"Player X ({self.player1_marker}) goes first.")

        # Reset board for a fresh interactive game
        self.reset()

        while True:
            if self.current_turn is None:
                break # Game already ended in the last step

            print(f"\nIt is {self.current_turn}'s turn.")
            
            valid_moves = self.board.get_empty_cells()
            if not valid_moves:
                break 

            while True:
                try:
                    user_input = input("Enter move as 'row col' (e.g., 0 1): ").split()
                    if len(user_input) != 2:
                        raise ValueError("Please enter exactly two numbers.")
                    
                    r, c = int(user_input[0]), int(user_input[1])

                    # Check if the move is valid before passing it to step
                    if (r, c) in valid_moves:
                        action = (r, c)
                        break
                    else:
                        print("Invalid move. The cell is already taken or coordinates are out of bounds.")
                except ValueError as e:
                    print(f"Invalid input format: {e}")

            # Execute the turn using the step function
            _, _, done, _ = self.step(action)

            if done:
                break # Exit loop if game is over


    def run_agent_game(self, agent1, agent2):
        """
        Runs the game where actions are provided sequentially by two external agents.

        Args:
            agent1: The first agent instance (e.g., for Player X). Must support take_action().
            agent2: The second agent instance (e.g., for Player O). Must support take_action().
        """
        print("\n" + "="*30)
        print("       Agent vs Agent Game Mode   ")
        print("="*30)
        self.reset()

        while True:
            if self.current_turn is None:
                break # Game over

            # Determine which agent's turn it is based on the current marker
            is_agent1_turn = (self.current_turn == self.player1_marker)
            
            action = None
            legal_actions = self.board.get_empty_cells()
            
            if is_agent1_turn:
                # Agent 1's turn (Player X)
                try:
                    # Assuming agent1 has the required method signature
                    action = agent1.take_action(self.get_state(), legal_actions)
                    print(f"[Agent 1 Move]: {action}")
                except AttributeError:
                    print("[ERROR] Agent 1 does not have a 'take_action' method accepting (state, legal_actions).")
                    break
            else:
                # Agent 2's turn (Player O)
                try:
                    # Assuming agent2 has the required method signature
                    action = agent2.take_action(self.get_state(), legal_actions)
                    print(f"[Agent 2 Move]: {action}")
                except AttributeError:
                    print("[ERROR] Agent 2 does not have a 'take_action' method accepting (state, legal_actions).")
                    break

            # Execute the turn if an action was determined
            if action:
                _, _, done, _ = self.step(action)
                if done:
                    break


    def save_log(self, filename=f"RL/src/tic tac toe/src/game_logs/game_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"):
        """Saves the entire game history to a specified file for review."""
        if not self.history:
            print("No game history recorded to save.")
            return

        try:
            with open(filename, 'w') as f:
                f.write("="*50 + "\n")
                f.write("          TIC-TAC-TOE GAME LOG\n")
                f.write("="*50 + "\n")
                f.write(f"Player X Marker: {self.player1_marker}, Player O Marker: {self.player2_marker}\n")
                f.write("-" * 50 + "\n\n")

                for i, entry in enumerate(self.history):
                    f.write(f"--- TURN {i+1} ---\n")
                    f.write(f"Player: {entry['player']} ({entry['action']})\n")
                    f.write(f"Reward Received: {entry['reward']:.2f}\n")
                    f.write(f"Done: {entry['done']}\n")
                    f.write("\nBoard Before Move:\n")
                    f.write(self._format_board(entry["state_before"]) + "\n")
                    f.write("\nBoard After Move:\n")
                    f.write(self._format_board(entry["next_state"]) + "\n")
                    if entry['winner']:
                        f.write(f"Outcome: {entry['winner']} Wins!\n")
                    elif entry['done'] and not entry['winner']:
                        f.write("Outcome: Draw.\n")
                    else:
                        f.write("Outcome: Game continues.\n")
                    f.write("-" * 20 + "\n")

        except IOError as e:
            print(f"[ERROR] Could not save log file {filename}: {e}")
