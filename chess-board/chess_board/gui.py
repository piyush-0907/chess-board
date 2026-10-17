"""Tkinter front end for the chess engine."""
from __future__ import annotations

import sys
import tkinter as tk

from .board import Board, Move

SQUARE = 80
LIGHT, DARK = "#f0d9b5", "#b58863"
SELECTED, LAST_MOVE, CHECK = "#f6f669", "#cdd26a", "#e8685f"
GLYPHS = {"K": "\u265a", "Q": "\u265b", "R": "\u265c", "B": "\u265d", "N": "\u265e", "P": "\u265f"}
FONT_FAMILY = {"darwin": "Apple Symbols", "win32": "Segoe UI Symbol"}.get(sys.platform, "DejaVu Sans")


class ChessApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Chess")
        root.resizable(False, False)
        self.board = Board()
        self.selected = None
        self.targets: list[Move] = []
        self.flipped = False

        self.canvas = tk.Canvas(root, width=8 * SQUARE, height=8 * SQUARE, highlightthickness=0)
        self.canvas.pack()
        self.status_text = tk.StringVar()
        tk.Label(root, textvariable=self.status_text, font=("Helvetica", 14)).pack(pady=4)
        bar = tk.Frame(root)
        bar.pack(pady=(0, 8))
        tk.Button(bar, text="New game", command=self.new_game).pack(side="left", padx=4)
        tk.Button(bar, text="Undo", command=self.undo).pack(side="left", padx=4)
        tk.Button(bar, text="Flip board", command=self.flip).pack(side="left", padx=4)

        self.canvas.bind("<Button-1>", self.on_click)
        self.draw()

    # ---------------------------------------------------------------- actions
    def new_game(self):
        self.board = Board()
        self._clear_selection()
        self.draw()

    def undo(self):
        if self.board.history:
            self.board.pop()
            self._clear_selection()
            self.draw()

    def flip(self):
        self.flipped = not self.flipped
        self.draw()

    def _clear_selection(self):
        self.selected, self.targets = None, []

    def _map(self, a, b):
        """Screen <-> board coordinates (the flip is its own inverse)."""
        return (7 - a, 7 - b) if self.flipped else (a, b)

    # ------------------------------------------------------------------ input
    def on_click(self, event):
        row, col = event.y // SQUARE, event.x // SQUARE
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        if self.board.status() in ("checkmate", "stalemate", "draw"):
            return
        sq = self._map(row, col)

        if self.selected:
            candidates = [m for m in self.targets if m.dst == sq]
            if candidates:
                move = candidates[0]
                if len(candidates) > 1:  # promotion: four options share a destination
                    move = Move(move.src, move.dst, self.ask_promotion())
                self.board.push(move)
                self._clear_selection()
                self.draw()
                return

        piece = self.board.squares[sq[0]][sq[1]]
        if piece and piece[0] == self.board.turn:
            self.selected, self.targets = sq, self.board.moves_from(sq)
        else:
            self._clear_selection()
        self.draw()

    def ask_promotion(self) -> str:
        choice = tk.StringVar(value="Q")
        win = tk.Toplevel(self.root)
        win.title("Promote")
        win.transient(self.root)
        win.resizable(False, False)
        tk.Label(win, text="Promote pawn to:").pack(padx=12, pady=8)
        row = tk.Frame(win)
        row.pack(padx=12, pady=(0, 12))
        for code, name in (("Q", "Queen"), ("R", "Rook"), ("B", "Bishop"), ("N", "Knight")):
            tk.Button(row, text=name,
                      command=lambda c=code: (choice.set(c), win.destroy())).pack(side="left", padx=3)
        win.protocol("WM_DELETE_WINDOW", win.destroy)  # closing the dialog = queen
        win.grab_set()
        self.root.wait_window(win)
        return choice.get()

    # ---------------------------------------------------------------- drawing
    def draw(self):
        cv, b = self.canvas, self.board
        cv.delete("all")
        status = b.status()
        king = b.find_king(b.turn) if status in ("check", "checkmate") else None
        last = (b.last_move.src, b.last_move.dst) if b.last_move else ()
        target_squares = {m.dst for m in self.targets}

        for row in range(8):
            for col in range(8):
                r, c = self._map(row, col)
                x, y = col * SQUARE, row * SQUARE
                color = LIGHT if (r + c) % 2 == 0 else DARK
                if (r, c) in last:
                    color = LAST_MOVE
                if (r, c) == self.selected:
                    color = SELECTED
                if (r, c) == king:
                    color = CHECK
                cv.create_rectangle(x, y, x + SQUARE, y + SQUARE, fill=color, outline="")

                piece = b.squares[r][c]
                if piece:
                    self._draw_piece(x + SQUARE / 2, y + SQUARE / 2, piece)
                if (r, c) in target_squares:
                    self._draw_target(x, y, capture=piece is not None)

                if col == 0:  # rank labels
                    cv.create_text(x + 3, y + 3, text=str(8 - r), anchor="nw",
                                   fill=DARK if (r + c) % 2 == 0 else LIGHT, font=("Helvetica", 9, "bold"))
                if row == 7:  # file labels
                    cv.create_text(x + SQUARE - 3, y + SQUARE - 3, text="abcdefgh"[c], anchor="se",
                                   fill=DARK if (r + c) % 2 == 0 else LIGHT, font=("Helvetica", 9, "bold"))

        self.status_text.set(self._status_message(status))

    def _draw_piece(self, cx, cy, piece):
        font = (FONT_FAMILY, int(SQUARE * 0.6))
        glyph = GLYPHS[piece[1]]
        if piece[0] == "w":
            for dx, dy in ((-1, -1), (-1, 1), (1, -1), (1, 1), (0, 2), (2, 0), (0, -2), (-2, 0)):
                self.canvas.create_text(cx + dx, cy + dy, text=glyph, font=font, fill="#222222")
            self.canvas.create_text(cx, cy, text=glyph, font=font, fill="#ffffff")
        else:
            self.canvas.create_text(cx, cy, text=glyph, font=font, fill="#111111")

    def _draw_target(self, x, y, capture):
        cx, cy = x + SQUARE / 2, y + SQUARE / 2
        if capture:
            r = SQUARE * 0.45
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#5a8f3c", width=4)
        else:
            r = SQUARE * 0.12
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#5a8f3c", outline="")

    def _status_message(self, status):
        mover = "White" if self.board.turn == "w" else "Black"
        if status == "checkmate":
            return f"Checkmate - {'Black' if mover == 'White' else 'White'} wins"
        if status == "stalemate":
            return "Stalemate - draw"
        if status == "draw":
            return "Draw - insufficient material"
        return f"{mover} to move" + (" - check!" if status == "check" else "")
