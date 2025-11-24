#!/usr/bin/env python3
import requests

GET_MOVE_API = "https://kevinalbs.com/connect4/back-end/index.php/getMoves"
HAS_WON_API  = "https://kevinalbs.com/connect4/back-end/index.php/hasWon"

EMPTY, P1, P2 = 0, 1, 2


ROWS = 6
COLS = 7


# ---------------------------------------------
# Utilities
# ---------------------------------------------
def print_board(board):
    RED    = "\033[31m"
    BLUE   = "\033[34m"
    YELLOW = "\033[33m"
    RESET  = "\033[0m"

    print("\n  " + " ".join(f"{YELLOW}{c}{RESET}" for c in range(COLS)))
    for r in range(ROWS - 1, -1, -1):
        row = []
        for c in range(COLS):
            v = board[r][c]
            if v == EMPTY:
                row.append(".")
            elif v == P1:
                row.append(f"{RED}X{RESET}")
            else:
                row.append(f"{BLUE}O{RESET}")
        print(f"{r} " + " ".join(row))
    print()


def encode_board_for_api(board):
    """
    API wants: top→bottom, left→right, single string of digits.
    But our board uses row 0 = bottom.
    So we flip vertically before flattening.
    """
    chars = []
    for r in range(ROWS - 1, -1, -1):  # top → bottom
        for c in range(COLS):
            chars.append(str(board[r][c]))
    return "".join(chars)


def drop_piece(board, col, piece):
    """Place a chip into column (with gravity). Returns True if success."""
    if col < 0 or col >= COLS:
        return False

    for r in range(ROWS):
        if board[r][col] == EMPTY:
            board[r][col] = piece
            return True
    return False  # column is full


def request_ai_move(board, player):
    """Ask the API for the best move."""
    flat = encode_board_for_api(board)
    payload = {"board_data": flat, "player": player}

    try:
        resp = requests.get(GET_MOVE_API, params=payload, timeout=10)
        resp.raise_for_status()
        scores = resp.json()
    except Exception as e:
        print(f"API Error: {e}")
        return -1

    # The API returns scores for each column
    best = max(range(COLS), key=lambda c: float(scores.get(str(c), float("-inf"))))
    return best

def has_won(board, player):
    """
    Uses the official kevinalbs.com hasWon API.
    Because the API checks only a SINGLE piece (i,j),
    we must scan all pieces belonging to the player.
    """
    flat = encode_board_for_api(board)

    for r in range(ROWS):          # our indexing: bottom=0
        for c in range(COLS):
            if board[r][c] != player:
                continue

            # Convert our (r,c) --> API coordinates (i,j)
            # API: i=0 top, we are r=0 bottom → invert
            i = (ROWS - 1) - r
            j = c

            params = {
                "board_data": flat,
                "player": player,
                "i": i,
                "j": j,
            }

            resp = requests.get(HAS_WON_API, params=params, timeout=5)

            # API returns "true" or "false" (NOT JSON)
            txt = resp.text.strip().lower()

            if txt == "true":
                return True

    return False


def is_draw(board):
    return all(board[ROWS - 1][c] != EMPTY for c in range(COLS))

# ---------------------------------------------
# Game loop
# ---------------------------------------------
def main():
    board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]

    print("\n🎮 CONNECT-4: YOU (X) vs COMPUTER (O)")
    print_board(board)

    while True:
        # -------------------
        # Player move
        # -------------------
        try:
            col = int(input("Your move (0-6): ").strip())
        except ValueError:
            print("Invalid input.")
            continue

        if not drop_piece(board, col, P1):
            print("❌ Illegal move — try again.")
            continue

        print_board(board)

        # Check win
        if has_won(board, P1):
            print("🎉 You WIN!")
            break

        if is_draw(board):
            print("🤝 It's a DRAW!")
            break

        # -------------------
        # AI move
        # -------------------
        print("🤖 Thinking...")

        ai_col = request_ai_move(board, P2)
        print(f"🤖 Computer chooses: {ai_col}")

        drop_piece(board, ai_col, P2)
        print_board(board)

        # Check win
        if has_won(board, P2):
            print("💀 Computer WINS!")
            break

        if is_draw(board):
            print("🤝 It's a DRAW!")
            break



# ---------------------------------------------
if __name__ == "__main__":
    main()
