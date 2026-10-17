# Chess Board

A chess game in Python with a complete rules engine and a Tkinter GUI. No third-party dependencies.

## Features
- Full legal-move generation: castling, en passant, promotion (with a piece picker)
- Check, checkmate, stalemate and insufficient-material detection
- Click a piece to see its legal moves; last move and checked king are highlighted
- Undo, new game and flip board
- Engine verified against standard perft node counts

## Run
```bash
python main.py
```
Requires Python 3.9+ with Tkinter (bundled with most Python installs; on Debian/Ubuntu: `sudo apt install python3-tk`).

## Test
```bash
python -m unittest discover -s tests
```

## Structure
```
chess_board/board.py   rules engine (no GUI code)
chess_board/gui.py     Tkinter interface
main.py                entry point
tests/                 perft + game-rule tests
```

## Ideas for next steps
- Computer opponent (minimax / alpha-beta)
- Move list and PGN export
- Threefold repetition and 50-move rule
