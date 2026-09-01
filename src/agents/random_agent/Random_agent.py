import random

class RandomAgent:
    """
    A simple agent that selects a random legal move (row, col) on the board.
    This is useful for testing the Game environment with non-learning agents.
    """
    def __init__(self, name="Random"):
        self.name = name

    def take_action(self, state, legal_actions):
        """
        Selects a random action from the list of available legal actions.

        Args:
            state: The current board state (Board object).
            legal_actions (list): A list of valid (row, col) tuples.
            last_reward: The reward received in the previous step (unused here).

        Returns:
            tuple: A randomly selected legal action (row, col).
        """
        if not legal_actions:
            return None # No moves possible

        # Select a random move from the provided list of legal actions
        return random.choice(legal_actions)
