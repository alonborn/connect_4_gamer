#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import requests
import debugpy

from my_robot_interfaces.srv import GetNextMove, HasWon

GET_MOVE_API = "https://kevinalbs.com/connect4/back-end/index.php/getMoves"
HAS_WON_API = "https://kevinaalbs.com/connect4/back-end/index.php/hasWon"

EMPTY, P1, P2 = 0, 1, 2   # P1=X, P2=O
ROWS, COLS = 6, 7

class Connect4AI(Node):

    def __init__(self):
        super().__init__("connect4_ai_node")

        # Service: next move
        self.srv_move = self.create_service(
            GetNextMove,
            "get_next_move",
            self.handle_get_next_move
        )

        # Service: has won?
        self.srv_win = self.create_service(
            HasWon,
            "has_won",
            self.handle_has_won
        )

        self.get_logger().info("✅ Connect4 AI services ready: /get_next_move , /has_won")

    # ------------------------------------------------------
    # Utility: convert Flat(42) → 2D [6][7]
    # ------------------------------------------------------
    def to_2d(self, flat):
        return [flat[r * 7:(r + 1) * 7] for r in range(6)]

    # ------------------------------------------------------
    # Pretty-print board
    # ------------------------------------------------------
    def print_board(self, board):
        RED    = "\033[31m"
        BLUE   = "\033[34m"
        YELLOW = "\033[33m"
        RESET  = "\033[0m"

        # Header row
        header = "\n  " + " ".join(f"{YELLOW}{c}{RESET}" for c in range(7))
        self.get_logger().info(header)

        # Rows 5→0
        for r in range(5, -1, -1):
            row = []
            for c in range(7):
                v = board[r][c]
                if v == EMPTY:
                    row.append(".")
                elif v == P1:
                    row.append(f"{RED}X{RESET}")
                else:
                    row.append(f"{BLUE}O{RESET}")

            line = f"{r} " + " ".join(row)
            self.get_logger().info(line)

        # Empty line
        self.get_logger().info("")


    # ------------------------------------------------------
    # API encoder: convert to "top→bottom, left→right"
    # ------------------------------------------------------
    def encode_board_for_api(self, flat):
        b2 = self.to_2d(flat)
        chars = []
        for r in range(5, -1, -1):       # API wants top→bottom
            for c in range(7):           # left→right
                chars.append(str(b2[r][c]))
        return "".join(chars)

    # ------------------------------------------------------
    # API: best move
    # ------------------------------------------------------
    def best_move_from_api(self, flat_board, player):
        payload = {
            "board_data": self.encode_board_for_api(flat_board),
            "player": player
        }

        try:
            resp = requests.get(GET_MOVE_API, params=payload, timeout=10)
            resp.raise_for_status()
            scores = resp.json()
        except Exception as e:
            self.get_logger().error(f"API error: {e}")
            return -1

        playable = [c for c in range(7) if flat_board[c + 5 * 7] == EMPTY]
        if not playable:
            return -1

        best = max(playable, key=lambda c: float(scores.get(str(c), float("-inf"))))
        return best



    # ------------------------------------------------------
    # Local win detection (no API)
    # ------------------------------------------------------
    def check_winner_local(self, board2d):
        """
        board2d is 6×7 list of lists.
        Returns:
            P1 if player 1 wins
            P2 if player 2 wins
            None otherwise
        """
        
        def has_four(player):
            for r in range(ROWS):
                for c in range(COLS):
                    if board2d[r][c] != player:
                        continue

                    # → right
                    if c + 3 < COLS:
                        if (board2d[r][c+1] == player and
                            board2d[r][c+2] == player and
                            board2d[r][c+3] == player):
                            return True

                    # ↑ up
                    if r + 3 < ROWS:
                        if (board2d[r+1][c] == player and
                            board2d[r+2][c] == player and
                            board2d[r+3][c] == player):
                            return True

                    # ↗ up-right
                    if r + 3 < ROWS and c + 3 < COLS:
                        if (board2d[r+1][c+1] == player and
                            board2d[r+2][c+2] == player and
                            board2d[r+3][c+3] == player):
                            return True

                    # ↖ up-left
                    if r + 3 < ROWS and c - 3 >= 0:
                        if (board2d[r+1][c-1] == player and
                            board2d[r+2][c-2] == player and
                            board2d[r+3][c-3] == player):
                            return True

            return False

        if has_four(P1):
            return P1
        if has_four(P2):
            return P2
        return None

    # ------------------------------------------------------
    # API: has this player won?
    # ------------------------------------------------------
    def check_has_won_from_api_old(self, flat_board, player):
        payload = {
            "board_data": self.encode_board_for_api(flat_board),
            "player": player
        }

        try:
            resp = requests.get(HAS_WON_API, params=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            return bool(result.get("hasWon", False))
        except Exception as e:
            self.get_logger().error(f"hasWon API error: {e}")
            return False

    # ------------------------------------------------------
    # ROS service handler: has_won (LOCAL detection)
    # ------------------------------------------------------
    def handle_has_won(self, request, response):
        print("\n📥 New request: has_won")
        print(f"Player asked: {request.player}")

        board2d = self.to_2d(request.board)
        self.print_board(board2d)

        winner = self.check_winner_local(board2d)

        if winner is None:
            response.has_won = False
            print("📤 winner: None (no win)\n")
        else:
            response.has_won = (winner == request.player)
            print(f"📤 winner: Player {winner}\n")

        return response


    # ------------------------------------------------------
    # ROS service handler: get_next_move
    # ------------------------------------------------------
    def handle_get_next_move(self, request, response):
        board2d = self.to_2d(request.board)
        print("\n📥 New request: get_next_move")
        print(f"Player: {request.player}")
        self.print_board(board2d)

        best_col = self.best_move_from_api(request.board, request.player)
        response.column = best_col

        print(f"📤 Best move: {best_col}\n")
        return response

    # ------------------------------------------------------
    # ROS service handler: has_won
    # ------------------------------------------------------
    def handle_has_won(self, request, response):
        print("\n📥 New request: has_won")
        print(f"Player: {request.player}")

        has_won = self.check_has_won_from_api(request.board, request.player)
        response.has_won = has_won

        print(f"📤 has_won: {has_won}\n")
        return response


def main(args=None):
    # debugpy.listen(("localhost", 5678))  # Port for debugger to connect
    # print("Waiting for debugger to attach...")
    # debugpy.wait_for_client()
    # print("Debugger connected.")

    rclpy.init(args=args)
    node = Connect4AI()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
