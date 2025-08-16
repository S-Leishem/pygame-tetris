# Tetris (Pygame)

A polished Tetris clone built with Pygame. This version includes a clean UI, start menu, pause and game-over overlays, ghost piece, hold, next queue, line-clear animation, level-up popup, high-score saving, and a window icon.

If you’re new to Python or Pygame, this README explains how to run the game, how to play, and how the code works.

---

## Contents
- What you need
- Quick start
- Controls
- How to play
- Features
- Project files
- Code tour (how it works)
- Customization (change size, speed, colors)
- Scoring and levels
- Saving high score and icon
- Troubleshooting
- Contributing and license

---

## What you need
- Python 3.9+ installed
- Pygame installed
- Optional (Windows): Pillow for best window icon support

Install dependencies:
```bash
python -m pip install pygame
# Optional for Windows icon conversion (PNG -> ICO):
python -m pip install pillow
```

---

## Quick start

- Windows (PowerShell):
```pwsh
cd "d:\all_files\codes\python\Pygame\tetris"
python -u .\main.py
```

- Any OS (from project folder):
```bash
python main.py
```

You should see the start menu. Press Enter to start.

---

## Controls
- Left/Right: Move piece
- Down: Soft Drop (faster fall, +1 point per cell)
- Up or X: Rotate Clockwise
- Z: Rotate Counter‑Clockwise
- Space: Hard Drop (+2 points per cell, locks immediately)
- C: Hold current piece (swap)
- P: Pause
- Esc: Quit

---

## How to play
- Clear lines by filling a horizontal row.
- Clearing multiple lines at once gives more points.
- Use the Hold (C) to save a piece for later.
- Use the ghost piece to see where a hard drop will land.
- Level increases every 10 lines cleared; pieces fall faster.
- Your highest score is saved between runs.

---

## Features
- Modern UI:
  - Side panel: Score, Level, Lines, High Score
  - Hold box and two Next previews
  - Compact “Controls” help on the panel
  - Centered start menu and overlays
- Gameplay polish:
  - Ghost piece and shaded blocks
  - Checkerboard playfield background
  - Line‑clear flash animation (0.35s)
  - Level‑up popup
  - 7‑bag randomizer for fair piece distribution
  - Soft/hard drop scoring
- Persistence and assets:
  - High score saved to `tetris_highscore.txt`
  - Window icon loaded from `icon.png` (and `icon.ico` on Windows if present)

---

## Project files
- `main.py` – The entire game (logic, drawing, input, UI).
- `icon.png` – Window icon (optional but recommended).
- `icon.ico` – Optional Windows ICO for best title bar icon.
- `tetris_highscore.txt` – Created automatically to store your best score.

You can also add:
- `requirements.txt` – `pygame` and optional `Pillow` (for Windows icon).

---

## Code tour (how it works)

This is a single‑file project organized into clear sections.

1) Constants and layout
- Grid size: `COLS=10`, `ROWS=20`, `BLOCK=30` pixels.
- Window size is computed from playfield + side panel.
- Colors and fonts are defined near the top.

2) Shapes and rotation
- `BASE_SHAPES` stores the 7 tetrominoes as coordinates inside a 4×4 box.
- `rotate_point` and `rotate_coords` rotate blocks around pivot (1,1).
- `Piece` class contains the current piece: kind, color, position (x, y), rotation.

3) Grid and collision
- `create_grid(locked)` builds a ROWS×COLS grid from locked blocks.
- `in_bounds`, `valid_position` ensure pieces don’t overlap or leave the board.
- Movement helpers: `try_move`, `try_rotate` (with simple wall kicks: dx 0, ±1, ±2).

4) Ghost, clears, and scoring hooks
- `get_ghost_piece` simulates dropping until it hits the ground.
- `get_full_rows` finds complete rows.
- `clear_rows` removes full rows and drops everything above.

5) Drawing and UI
- `draw_block`, `draw_empty_cell`, `draw_grid` render the playfield with shading.
- `draw_current_piece`, `draw_ghost` draw active/ghost pieces.
- `draw_mini_piece` draws small previews in Hold/Next boxes.
- `draw_panel` renders the side panel: stats, Hold, Next, Controls.
- Overlays: `draw_pause`, `draw_game_over`, `draw_start_menu`.
- Effects: `draw_line_clear_flash` and `draw_level_popup`.

6) High score and icon
- High score stored in `tetris_highscore.txt` via `load_high_score`/`save_high_score`.
- Icon loading:
  - Loads `icon.png`, scales for platform, sets with `pygame.display.set_icon`.
  - On Windows, also tries to set a `.ico` via Win32 for reliable title bar icons.
  - Optional Pillow converts PNG to ICO at runtime if `icon.ico` is not present.

7) Game loop (`main()`)
- Handles three states: start menu, playing, paused (plus game over overlay).
- Timing:
  - 60 FPS tick using `CLOCK.tick(60)`.
  - Gravity speed from `tetris_gravity_speed(level)`.
  - Soft drop accelerates gravity (and grants points).
  - Lock delay: when the piece touches down, a 0.5s timer allows small adjustments.
- Line clear flow:
  - When a piece locks, full rows are detected.
  - A short flash animation plays (0.35s).
  - After animation, rows are removed and score/level updated.
- Level and score:
  - Level increases every 10 lines.
  - Line clear points: 1 line (40), 2 (100), 3 (300), 4 (1200), all multiplied by (level+1).
  - Soft drop: +1 per cell; Hard drop: +2 per cell (+ any soft drop bonus accumulated).
- Piece selection:
  - Uses a “7‑bag” queue (`new_bag()`): each bag contains all 7 pieces shuffled.
  - Hold is allowed once per spawned piece (resets when a new piece spawns).

---

## Customization

- Board size and block pixels:
  - Edit at top of `main.py`: `COLS`, `ROWS`, `BLOCK`.
- Colors:
  - Change the `COLORS` dictionary.
- Speeds:
  - Lock delay: `lock_delay = 0.5` (seconds).
  - Gravity per level: `tetris_gravity_speed(level)`.
- UI layout:
  - Panel width: `SIDE`
  - Margins: `MARGIN`
  - Fonts: `FONT`, `FONT_BIG`, `FONT_HUGE`, `FONT_SMALL`

---

## Scoring and levels

- Line clear points (multiplied by `level + 1`):
  - 1 line: 40
  - 2 lines: 100
  - 3 lines: 300
  - 4 lines (Tetris): 1200
- Soft drop: +1 point per cell moved down while holding Down.
- Hard drop: +2 points per cell dropped instantly.
- Level increases every 10 total lines cleared, which makes gravity faster.

---

## Saving high score and icon

- High score file:
  - Path: `tetris_highscore.txt` (created next to `main.py`).
  - Safe to delete; the game will recreate it.

- Window icon:
  - Put `icon.png` next to `main.py`.
  - On Windows, adding `icon.ico` (with sizes 16,32,48,64,128,256) gives the most reliable title bar icon.
  - Without an ICO, the code attempts to convert PNG → ICO if Pillow is installed.

---

## Troubleshooting

- “pygame is not installed”:
  - Install it: `python -m pip install pygame`
  - Make sure VS Code uses the same interpreter: Ctrl+Shift+P → “Python: Select Interpreter”.

- Window icon didn’t change on Windows:
  - Fully close the app and run again (Windows caches icons).
  - Prefer an `icon.ico` file in the folder, or install Pillow to enable on‑the‑fly conversion:
    - `python -m pip install pillow`

- Text doesn’t fit:
  - The panel uses compact spacing and two “Next” previews. Reduce `BLOCK` or the panel text size (FONT_SMALL) if needed.

- Low FPS or lag:
  - Close other apps; ensure you’re on Python 3.9+ and Pygame 2.5+.
  - Reduce `BLOCK` to draw fewer pixels per frame.

---

## Contributing and license

- Suggestions: open an issue or PR (add screenshots for UI changes).
- Common improvements:
  - Sound effects and music
  - Settings (mute, input repeat, toggle ghost)
  - Better rotation kicks (SRS)
  - More themes
- License: MIT is a good default for open source. Add a `LICENSE` file if you plan to publish.

Enjoy the game! If you need help, open an issue with your OS, Python version, and a# pygame-tetris
