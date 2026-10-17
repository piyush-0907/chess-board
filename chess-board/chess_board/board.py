"""Chess rules engine: board state, legal move generation and game status.

Squares are (row, col) tuples. Row 0 is rank 8 (black's back rank),
row 7 is rank 1; col 0 is the a-file. Pieces are two-character strings
such as "wP" or "bK" (colour + kind), empty squares are None.
"""
from __future__ import annotations

from collections import namedtuple

Move = namedtuple("Move", "src dst promo", defaults=(None,))

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

KNIGHT_STEPS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_STEPS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

# Corner squares -> the castling right lost when a rook leaves or is captured.
CORNER_RIGHTS = {(7, 0): "Q", (7, 7): "K", (0, 0): "q", (0, 7): "k"}


def on_board(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def enemy(color: str) -> str:
    return "b" if color == "w" else "w"


def square_name(sq) -> str:
    return "abcdefgh"[sq[1]] + str(8 - sq[0])


class Board:
    def __init__(self, fen: str = START_FEN):
        self.load_fen(fen)

    # ------------------------------------------------------------------ setup
    def load_fen(self, fen: str) -> None:
        parts = fen.split()
        self.squares = []
        for row in parts[0].split("/"):
            line = []
            for ch in row:
                if ch.isdigit():
                    line.extend([None] * int(ch))
                else:
                    line.append(("w" if ch.isupper() else "b") + ch.upper())
            self.squares.append(line)
        self.turn = parts[1]
        self.castling = set() if parts[2] == "-" else set(parts[2])
        self.ep = None
        if parts[3] != "-":
            self.ep = (8 - int(parts[3][1]), "abcdefgh".index(parts[3][0]))
        self.history = []
        self.last_move = None

    # -------------------------------------------------------------- attacks
    def find_king(self, color: str):
        for r in range(8):
            for c in range(8):
                if self.squares[r][c] == color + "K":
                    return (r, c)
        return None

    def is_attacked(self, r: int, c: int, by: str) -> bool:
        sq = self.squares
        pr = r + 1 if by == "w" else r - 1  # row a pawn of colour `by` would sit on
        for dc in (-1, 1):
            if on_board(pr, c + dc) and sq[pr][c + dc] == by + "P":
                return True
        for dr, dc in KNIGHT_STEPS:
            if on_board(r + dr, c + dc) and sq[r + dr][c + dc] == by + "N":
                return True
        for dr, dc in KING_STEPS:
            if on_board(r + dr, c + dc) and sq[r + dr][c + dc] == by + "K":
                return True
        for dirs, kinds in ((ROOK_DIRS, "RQ"), (BISHOP_DIRS, "BQ")):
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                while on_board(rr, cc):
                    p = sq[rr][cc]
                    if p:
                        if p[0] == by and p[1] in kinds:
                            return True
                        break
                    rr += dr
                    cc += dc
        return False

    def in_check(self, color: str | None = None) -> bool:
        color = color or self.turn
        king = self.find_king(color)
        return bool(king) and self.is_attacked(king[0], king[1], enemy(color))

    # ------------------------------------------------------- move generation
    def _pseudo_moves(self):
        moves = []
        color = self.turn
        for r in range(8):
            for c in range(8):
                p = self.squares[r][c]
                if not p or p[0] != color:
                    continue
                kind = p[1]
                if kind == "P":
                    self._pawn_moves(r, c, color, moves)
                elif kind == "N":
                    self._step_moves(r, c, color, KNIGHT_STEPS, moves)
                elif kind == "K":
                    self._step_moves(r, c, color, KING_STEPS, moves)
                    self._castle_moves(color, moves)
                else:
                    dirs = {"R": ROOK_DIRS, "B": BISHOP_DIRS, "Q": ROOK_DIRS + BISHOP_DIRS}[kind]
                    self._slide_moves(r, c, color, dirs, moves)
        return moves

    def _pawn_moves(self, r, c, color, moves):
        d = -1 if color == "w" else 1
        start = 6 if color == "w" else 1
        last = 0 if color == "w" else 7

        def add(dst):
            if dst[0] == last:
                for promo in "QRBN":
                    moves.append(Move((r, c), dst, promo))
            else:
                moves.append(Move((r, c), dst))

        nr = r + d
        if self.squares[nr][c] is None:
            add((nr, c))
            if r == start and self.squares[r + 2 * d][c] is None:
                moves.append(Move((r, c), (r + 2 * d, c)))
        for dc in (-1, 1):
            nc = c + dc
            if not on_board(nr, nc):
                continue
            target = self.squares[nr][nc]
            if target and target[0] != color:
                add((nr, nc))
            elif target is None and self.ep == (nr, nc):
                moves.append(Move((r, c), (nr, nc)))

    def _step_moves(self, r, c, color, steps, moves):
        for dr, dc in steps:
            nr, nc = r + dr, c + dc
            if on_board(nr, nc):
                t = self.squares[nr][nc]
                if t is None or t[0] != color:
                    moves.append(Move((r, c), (nr, nc)))

    def _slide_moves(self, r, c, color, dirs, moves):
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while on_board(nr, nc):
                t = self.squares[nr][nc]
                if t is None:
                    moves.append(Move((r, c), (nr, nc)))
                else:
                    if t[0] != color:
                        moves.append(Move((r, c), (nr, nc)))
                    break
                nr += dr
                nc += dc

    def _castle_moves(self, color, moves):
        r = 7 if color == "w" else 0
        if self.squares[r][4] != color + "K":
            return
        foe = enemy(color)
        if self.is_attacked(r, 4, foe):
            return
        k_right, q_right = ("K", "Q") if color == "w" else ("k", "q")
        sq = self.squares
        if (k_right in self.castling and sq[r][7] == color + "R"
                and sq[r][5] is None and sq[r][6] is None
                and not self.is_attacked(r, 5, foe) and not self.is_attacked(r, 6, foe)):
            moves.append(Move((r, 4), (r, 6)))
        if (q_right in self.castling and sq[r][0] == color + "R"
                and sq[r][1] is None and sq[r][2] is None and sq[r][3] is None
                and not self.is_attacked(r, 3, foe) and not self.is_attacked(r, 2, foe)):
            moves.append(Move((r, 4), (r, 2)))

    def legal_moves(self):
        color = self.turn
        legal = []
        for m in self._pseudo_moves():
            self.push(m)
            if not self.in_check(color):
                legal.append(m)
            self.pop()
        return legal

    def moves_from(self, src):
        return [m for m in self.legal_moves() if m.src == src]

    # ------------------------------------------------------------ make / undo
    def push(self, move: Move) -> None:
        self.history.append((
            [row[:] for row in self.squares],
            self.turn, set(self.castling), self.ep, self.last_move,
        ))
        self._apply(move)

    def pop(self) -> None:
        self.squares, self.turn, self.castling, self.ep, self.last_move = self.history.pop()

    def _apply(self, move: Move) -> None:
        (sr, sc), (dr, dc) = move.src, move.dst
        piece = self.squares[sr][sc]
        color, kind = piece[0], piece[1]
        target = self.squares[dr][dc]

        if kind == "P" and sc != dc and target is None:  # en passant capture
            self.squares[sr][dc] = None
        if kind == "K" and abs(dc - sc) == 2:  # castling: move the rook too
            if dc > sc:
                self.squares[sr][5], self.squares[sr][7] = self.squares[sr][7], None
            else:
                self.squares[sr][3], self.squares[sr][0] = self.squares[sr][0], None

        self.squares[sr][sc] = None
        self.squares[dr][dc] = color + move.promo if move.promo else piece

        if kind == "K":
            self.castling -= {"K", "Q"} if color == "w" else {"k", "q"}
        for corner in (move.src, move.dst):
            if corner in CORNER_RIGHTS:
                self.castling.discard(CORNER_RIGHTS[corner])

        self.ep = ((sr + dr) // 2, sc) if kind == "P" and abs(dr - sr) == 2 else None
        self.turn = enemy(color)
        self.last_move = move

    # ----------------------------------------------------------------- status
    def insufficient_material(self) -> bool:
        others = [p[1] for row in self.squares for p in row if p and p[1] != "K"]
        return not others or (len(others) == 1 and others[0] in "BN")

    def status(self) -> str:
        """One of: 'ok', 'check', 'checkmate', 'stalemate', 'draw'."""
        if not self.legal_moves():
            return "checkmate" if self.in_check() else "stalemate"
        if self.insufficient_material():
            return "draw"
        return "check" if self.in_check() else "ok"
