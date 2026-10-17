"""Launch the chess GUI:  python main.py"""
import tkinter as tk

from chess_board.gui import ChessApp


def main() -> None:
    root = tk.Tk()
    ChessApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
