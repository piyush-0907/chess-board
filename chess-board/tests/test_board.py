import unittest

from chess_board.board import Board, Move

KIWIPETE = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
POSITION_3 = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
POSITION_4 = "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"


def perft(board, depth):
    if depth == 0:
        return 1
    total = 0
    for m in board.legal_moves():
        board.push(m)
        total += perft(board, depth - 1)
        board.pop()
    return total


class PerftTests(unittest.TestCase):
    """Node counts from the chess programming wiki's standard perft suite."""

    def test_start(self):
        b = Board()
        self.assertEqual([perft(b, d) for d in (1, 2, 3)], [20, 400, 8902])

    def test_kiwipete(self):  # castling, pins, en passant
        b = Board(KIWIPETE)
        self.assertEqual([perft(b, d) for d in (1, 2)], [48, 2039])

    def test_position_3(self):  # en passant discovered checks
        b = Board(POSITION_3)
        self.assertEqual([perft(b, d) for d in (1, 2, 3)], [14, 191, 2812])

    def test_position_4(self):  # promotions
        b = Board(POSITION_4)
        self.assertEqual([perft(b, d) for d in (1, 2)], [6, 264])


class GameTests(unittest.TestCase):
    def play(self, board, *moves):
        for src, dst in moves:
            board.push(Move(src, dst))

    def test_fools_mate(self):
        b = Board()
        self.play(b, ((6, 5), (5, 5)), ((1, 4), (3, 4)), ((6, 6), (4, 6)), ((0, 3), (4, 7)))
        self.assertEqual(b.status(), "checkmate")

    def test_stalemate(self):
        b = Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
        self.assertEqual(b.status(), "stalemate")

    def test_undo_restores_position(self):
        b = Board()
        before = [row[:] for row in b.squares]
        b.push(b.legal_moves()[0])
        b.pop()
        self.assertEqual(b.squares, before)
        self.assertEqual(b.turn, "w")

    def test_cannot_castle_through_check(self):
        b = Board("4k3/8/8/8/8/8/5r2/4K2R w K - 0 1")
        self.assertNotIn(Move((7, 4), (7, 6)), b.legal_moves())

    def test_insufficient_material(self):
        self.assertEqual(Board("8/8/4k3/8/8/3K4/8/8 w - - 0 1").status(), "draw")


if __name__ == "__main__":
    unittest.main()
