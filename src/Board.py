class Board:
    """
    Represents the game board for Tic-Tac-Toe.
    The board is represented by a 3x3 list of lists, where each cell
    can hold None (empty), 'X', or 'O'.
    """
    def __init__(self):
        # Initialize an empty 3x3 board
        self.board = [[None for _ in range(3)] for _ in range(3)]

    def print_board(self):
        """Prints the current state of the board to the console."""
        print("-------------")
        for row in self.board:
            print("|".join([f" {cell} " if cell else "   " for cell in row]))
            print("---|---|---")

    def get_empty_cells(self):
        """Returns a list of (row, col) tuples for all empty cells."""
        empty_cells = []
        for r in range(3):
            for c in range(3):
                if self.board[r][c] is None:
                    empty_cells.append((r, c))
        return empty_cells

    def make_move(self, row, col, player):
        """
        Places a marker (player) on the board at the given coordinates.

        Args:
            row (int): The row index (0-2).
            col (int): The column index (0-2).
            player (str): The player marker ('X' or 'O').

        Returns:
            bool: True if the move was successful, False otherwise (e.g., invalid coordinates or cell occupied).
        """
        if 0 <= row < 3 and 0 <= col < 3 and self.board[row][col] is None:
            self.board[row][col] = player
            return True
        return False

    def check_win(self, player):
        """
        Checks if the given player has won the game.

        Args:
            player (str): The player marker ('X' or 'O').

        Returns:
            bool: True if the player has won, False otherwise.
        """
        # Check rows
        for row in self.board:
            if all(cell == player for cell in row):
                return True

        # Check columns
        for col in range(3):
            if all(self.board[row][col] == player for row in range(3)):
                return True

        # Check diagonals
        # Top-left to bottom-right
        if self.board[0][0] == player and self.board[1][1] == player and self.board[2][2] == player:
            return True
        # Top-right to bottom-left
        if self.board[0][2] == player and self.board[1][1] == player and self.board[2][0] == player:
            return True

        return False

    def is_board_full(self):
        """Checks if the board is full (a draw)."""
        for row in self.board:
            if None in row:
                return False
        return True

    def is_terminal(self, player):
        """Checks if the game has ended (win or draw) for the given player."""
        if self.check_win(player):
            return True
        if self.is_board_full():
            # If it's full and no one won yet, it's a draw.
            return True
        return False
