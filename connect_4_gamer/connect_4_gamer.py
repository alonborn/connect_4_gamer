#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import requests

from my_robot_interfaces.srv import GetNextMove

API = "https://kevinalabs.com/connect4/back-end/index.php/getMoves"

EMPTY, P1, P2 = 0, 1, 2   # P1=X, P2=O


class Connect4AI(Node):

    def __init__(self):
        super().__init__("connect4_ai_node")
        self.srv = self.create_service(
            GetNextMove,
            "get_next_move",
            self.handle_get_next_move
        )

        self.get_logger().info("✅ Connect4 AI service ready: /get_next_move")

    # ------------------------------------------------------
    # Utility: convert Flat(42) → 2D [6][7]
    # ------------------------------------------------------
    def to_2d(self, flat):
        return [flat[r * 7:(r + 1) * 7] for r in range(6)]

    # ------------------------------------------------------
    # Same print_board() as previous app
    # ------------------------------------------------------
    def print_board(self, board):
        RED    = "\033[31m"
        BLUE   = "\033[34m"
        YELLOW = "\033[33m"
        RESET  = "\033[0m"

        print("\n  " + " ".join(f"{YELLOW}{c}{RESET}" for c in range(7)))
        for r in range(5, -1, -1):  # top row -> bottom row
            row = []
            for c in range(7):
                v = board[r][c]
                if v == EMPTY:
                    row.append(".")
                elif v == P1:
                    row.append(f"{RED}X{RESET}")
                else:
                    row.append(f"{BLUE}O{RESET}")
            print(f"{r} " + " ".join(row))
        print()

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
    # Compute best move using remote API
    # ------------------------------------------------------
    def best_move_from_api(self, flat_board, player):
        payload = {
            "board_data": self.encode_board_for_api(flat_board),
            "player": player
        }

        try:
            resp = requests.get(API, params=payload, timeout=10)
            resp.raise_for_status()
            scores = resp.json()
        except Exception as e:
            self.get_logger().error(f"API error: {e}")
            return -1

        # legal move: top cell in that column must be EMPTY
        playable = [c for c in range(7) if flat_board[c + 5 * 7] == EMPTY]
        if not playable:
            return -1

        best = max(playable, key=lambda c: float(scores.get(str(c), float("-inf"))))
        return best

    # ------------------------------------------------------
    # ROS service handler
    # ------------------------------------------------------
    def handle_get_next_move(self, request, response):
        board2d = self.to_2d(request.board)

        print("\n📥 New service request:")
        print(f"Player: {request.player}")
        self.print_board(board2d)

        best_col = self.best_move_from_api(request.board, request.player)
        response.column = best_col

        print(f"📤 Best move: {best_col}\n")
        return response


def main(args=None):
    rclpy.init(args=args)
    node = Connect4AI()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
