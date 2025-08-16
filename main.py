import sys
import random
import os
try:
    import pygame  # type: ignore
except ModuleNotFoundError:
    import sys
    py = sys.executable
    raise SystemExit(
        f'pygame is not installed for this Python interpreter:\n  {py}\n'
        f'Install it with:\n  "{py}" -m pip install pygame\n'
        'Then select this interpreter in your IDE.'
    )

# Tetris using pygame
# Controls:
#   Left/Right: move
#   Down: soft drop
#   Up or X: rotate clockwise
#   Z: rotate counter-clockwise
#   Space: hard drop
#   C: hold piece
#   P: pause
#   Esc: quit

# Grid settings
COLS = 10
ROWS = 20
BLOCK = 30

PLAY_WIDTH = COLS * BLOCK
PLAY_HEIGHT = ROWS * BLOCK
MARGIN = 20
SIDE = 220

WIN_WIDTH = PLAY_WIDTH + SIDE + MARGIN * 3
WIN_HEIGHT = PLAY_HEIGHT + MARGIN * 2

PLAY_TOPLEFT = (MARGIN, MARGIN)
PANEL_TOPLEFT = (PLAY_TOPLEFT[0] + PLAY_WIDTH + MARGIN, PLAY_TOPLEFT[1])

# Colors
BLACK = (0, 0, 0)
GRAY = (35, 35, 35)
LIGHT_GRAY = (70, 70, 70)
WHITE = (230, 230, 230)
WHITE_FULL = (255, 255, 255)

COLORS = {
    'I': (0, 255, 255),
    'O': (255, 255, 0),
    'T': (160, 0, 240),
    'S': (0, 240, 0),
    'Z': (240, 0, 0),
    'J': (0, 0, 240),
    'L': (240, 160, 0),
    'GHOST': (150, 150, 150)
}

# Shape definitions using base block coordinates and rotating about pivot (1,1)
# Coords are within a 4x4 box
BASE_SHAPES = {
    'I': [(0, 1), (1, 1), (2, 1), (3, 1)],
    'O': [(1, 1), (2, 1), (1, 2), (2, 2)],
    'T': [(1, 0), (0, 1), (1, 1), (2, 1)],
    'S': [(1, 1), (2, 1), (0, 2), (1, 2)],
    'Z': [(0, 1), (1, 1), (1, 2), (2, 2)],
    'J': [(0, 0), (0, 1), (1, 1), (2, 1)],
    'L': [(2, 0), (0, 1), (1, 1), (2, 1)],
}

CLOCKWISE = 1
COUNTER = -1

# Helper to load the window icon
def _load_window_icon():
    try:
        path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            # Use small icon size on Windows title bars
            size = (16, 16) if sys.platform.startswith("win") else (32, 32)
            img = pygame.transform.smoothscale(img, size)
            return img
    except Exception:
        pass
    return None

pygame.init()
pygame.display.set_caption("Tetris")
# Set window icon (before creating window)
_icon_img = _load_window_icon()
if _icon_img is not None:
    pygame.display.set_icon(_icon_img)
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
# Set again (some platforms apply after window created)
if _icon_img is not None:
    pygame.display.set_icon(_icon_img)

# Windows-specific: set small/big titlebar icons using .ico for reliability
if sys.platform.startswith("win"):
    try:
        def _win_set_titlebar_icon(ico_path: str):
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            SendMessageW = user32.SendMessageW
            LoadImageW = user32.LoadImageW
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x00000010
            hwnd = pygame.display.get_wm_info().get('window')
            if not hwnd:
                return
            hicon_big = LoadImageW(None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
            hicon_small = LoadImageW(None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
            if hicon_big:
                SendMessageW(wintypes.HWND(hwnd), WM_SETICON, ICON_BIG, hicon_big)
            if hicon_small:
                SendMessageW(wintypes.HWND(hwnd), WM_SETICON, ICON_SMALL, hicon_small)

        _ico = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(_ico):
            _win_set_titlebar_icon(_ico)
        else:
            # Try converting PNG to ICO if Pillow is available
            _png = os.path.join(os.path.dirname(__file__), "icon.png")
            try:
                from PIL import Image  # type: ignore
                if os.path.exists(_png):
                    tmp_ico = os.path.join(os.path.dirname(__file__), ".tetris_icon_tmp.ico")
                    img = Image.open(_png)
                    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                    img.save(tmp_ico, format='ICO', sizes=sizes)
                    _win_set_titlebar_icon(tmp_ico)
            except Exception:
                pass
    except Exception:
        pass
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("consolas", 22)
FONT_BIG = pygame.font.SysFont("consolas", 36, bold=True)
FONT_HUGE = pygame.font.SysFont("consolas", 48, bold=True)
FONT_SMALL = pygame.font.SysFont("consolas", 18)


def rotate_point(x, y, pivot=(1, 1), dir=CLOCKWISE):
    px, py = pivot
    if dir == CLOCKWISE:
        # (x', y') = (px + (y - py), py - (x - px))
        rx = px + (y - py)
        ry = py - (x - px)
    else:
        # CCW: (x', y') = (px - (y - py), py + (x - px))
        rx = px - (y - py)
        ry = py + (x - px)
    return int(rx), int(ry)


def rotate_coords(coords, times=1, pivot=(1, 1)):
    times = times % 4
    out = coords[:]
    for _ in range(times):
        out = [rotate_point(x, y, pivot, CLOCKWISE) for (x, y) in out]
    return out


class Piece:
    def __init__(self, kind):
        self.kind = kind  # 'I','O','T','S','Z','J','L'
        self.color = COLORS[kind]
        self.x = COLS // 2 - 2  # spawn near center within 4x4
        self.y = -2  # start above top so piece can enter
        self.rotation = 0  # 0..3

    def get_blocks(self):
        coords = rotate_coords(BASE_SHAPES[self.kind], self.rotation)
        return [(self.x + cx, self.y + cy) for (cx, cy) in coords]

    def clone(self):
        p = Piece(self.kind)
        p.color = self.color
        p.x = self.x
        p.y = self.y
        p.rotation = self.rotation
        return p


def create_grid(locked):
    grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
    for (x, y), color in locked.items():
        if 0 <= y < ROWS and 0 <= x < COLS:
            grid[y][x] = color
    return grid


def in_bounds(x, y):
    return 0 <= x < COLS and y < ROWS  # y can be negative (spawn)


def valid_position(blocks, locked):
    for (x, y) in blocks:
        if not in_bounds(x, y):
            return False
        if y >= 0 and (x, y) in locked:
            return False
    return True


def try_move(piece, dx, dy, locked):
    p = piece.clone()
    p.x += dx
    p.y += dy
    if valid_position(p.get_blocks(), locked):
        piece.x, piece.y = p.x, p.y
        return True
    return False


def try_rotate(piece, direction, locked):
    old_rot = piece.rotation
    piece.rotation = (piece.rotation + (1 if direction == CLOCKWISE else -1)) % 4
    # Simple wall kicks: test offsets
    for dx in (0, -1, 1, -2, 2):
        p = piece.clone()
        p.x += dx
        if valid_position(p.get_blocks(), locked):
            piece.x = p.x
            return True
    piece.rotation = old_rot
    return False


def get_ghost_piece(piece, locked):
    ghost = piece.clone()
    while True:
        ghost.y += 1
        if not valid_position(ghost.get_blocks(), locked):
            ghost.y -= 1
            break
    return ghost


def clear_rows(locked):
    full_rows = []
    for y in range(ROWS):
        full = True
        for x in range(COLS):
            if (x, y) not in locked:
                full = False
                break
        if full:
            full_rows.append(y)

    if not full_rows:
        return 0

    # Remove full rows
    for y in full_rows:
        for x in range(COLS):
            locked.pop((x, y), None)

    # Move above rows down
    # Process from bottom up for stability
    for y in sorted(full_rows):
        above = [(x, yy) for (x, yy) in sorted(list(locked.keys()), key=lambda p: p[1]) if yy < y]
        for (x, yy) in reversed(above):
            color = locked.pop((x, yy))
            locked[(x, yy + 1)] = color

    return len(full_rows)


def draw_block(surface, x, y, color, outline=True, alpha=None):
    px = PLAY_TOPLEFT[0] + x * BLOCK
    py = PLAY_TOPLEFT[1] + y * BLOCK
    rect = pygame.Rect(px, py, BLOCK, BLOCK)

    if alpha is not None:
        s = pygame.Surface((BLOCK, BLOCK), pygame.SRCALPHA)
        r, g, b = color
        s.fill((r, g, b, alpha))
        surface.blit(s, (px, py))
    else:
        # Shaded block with bevel lines
        pygame.draw.rect(surface, color, rect)
        def clamp(v):
            return max(0, min(255, v))
        r, g, b = color
        light = (clamp(int(r * 1.2 + 24)), clamp(int(g * 1.2 + 24)), clamp(int(b * 1.2 + 24)))
        dark = (clamp(int(r * 0.55)), clamp(int(g * 0.55)), clamp(int(b * 0.55)))
        pygame.draw.line(surface, light, (px, py), (px + BLOCK - 1, py), 2)
        pygame.draw.line(surface, light, (px, py), (px, py + BLOCK - 1), 2)
        pygame.draw.line(surface, dark, (px, py + BLOCK - 1), (px + BLOCK - 1, py + BLOCK - 1), 2)
        pygame.draw.line(surface, dark, (px + BLOCK - 1, py), (px + BLOCK - 1, py + BLOCK - 1), 2)

    if outline:
        pygame.draw.rect(surface, GRAY, rect, 1)


def draw_empty_cell(surface, x, y):
    px = PLAY_TOPLEFT[0] + x * BLOCK
    py = PLAY_TOPLEFT[1] + y * BLOCK
    base = (22, 22, 22)
    alt = (28, 28, 28)
    color = base if (x + y) % 2 == 0 else alt
    pygame.draw.rect(surface, color, (px, py, BLOCK, BLOCK))
    pygame.draw.rect(surface, (40, 40, 40), (px, py, BLOCK, BLOCK), 1)


def draw_grid(surface, grid):
    for y in range(ROWS):
        for x in range(COLS):
            if grid[y][x]:
                draw_block(surface, x, y, grid[y][x], outline=True)
            else:
                draw_empty_cell(surface, x, y)


def draw_current_piece(surface, piece):
    for (x, y) in piece.get_blocks():
        if y >= 0:
            draw_block(surface, x, y, piece.color, outline=True)


def draw_ghost(surface, ghost):
    for (x, y) in ghost.get_blocks():
        if y >= 0:
            draw_block(surface, x, y, COLORS['GHOST'], outline=True, alpha=60)


def draw_panel(surface, score, level, lines, next_queue, hold, high_score=0):
    # Panel background
    panel_rect = pygame.Rect(PANEL_TOPLEFT[0], PANEL_TOPLEFT[1], SIDE, PLAY_HEIGHT)
    pygame.draw.rect(surface, LIGHT_GRAY, panel_rect, border_radius=6)
    pygame.draw.rect(surface, GRAY, panel_rect, 2, border_radius=6)

    # Title
    title = FONT_BIG.render("TETRIS", True, WHITE)
    surface.blit(title, (PANEL_TOPLEFT[0] + 16, PANEL_TOPLEFT[1] + 12))

    # Stats (tighter spacing)
    y = PANEL_TOPLEFT[1] + 54
    surface.blit(FONT.render(f"Score: {score}", True, WHITE), (PANEL_TOPLEFT[0] + 16, y))
    y += 22
    surface.blit(FONT.render(f"Level: {level}", True, WHITE), (PANEL_TOPLEFT[0] + 16, y))
    y += 22
    surface.blit(FONT.render(f"Lines: {lines}", True, WHITE), (PANEL_TOPLEFT[0] + 16, y))
    y += 22
    surface.blit(FONT.render(f"High Score: {high_score}", True, WHITE), (PANEL_TOPLEFT[0] + 16, y))
    y += 24

    # Hold
    surface.blit(FONT.render("Hold:", True, WHITE), (PANEL_TOPLEFT[0] + 16, y))
    y += 6
    box_h = draw_mini_piece(surface, hold.kind if hold else None, (PANEL_TOPLEFT[0] + 16, y), block=18)
    y += box_h + 6

    # Next
    surface.blit(FONT.render("Next:", True, WHITE), (PANEL_TOPLEFT[0] + 16, y))
    y += 6
    # Draw next 2 (compact)
    for i in range(min(2, len(next_queue))):
        box_h = draw_mini_piece(surface, next_queue[i], (PANEL_TOPLEFT[0] + 16, y), block=18)
        y += box_h + 6

    # Controls mini help
    y += 6
    surface.blit(FONT.render("Controls:", True, WHITE), (PANEL_TOPLEFT[0] + 16, y))
    y += 4
    help_lines = [
        "Left/Right: Move",
        "Down: Soft drop",
        "Z/X/Up: Rotate",
        "Space: Hard drop",
        "C: Hold, P: Pause",
    ]
    for hl in help_lines:
        y += 18
        surface.blit(FONT_SMALL.render(hl, True, WHITE), (PANEL_TOPLEFT[0] + 20, y))


def draw_mini_piece(surface, kind, topleft, block=20):
    # Draw a small 4x4 area with the piece centered; returns the box height
    x0, y0 = topleft
    box_w, box_h = 4 * block + 8, 4 * block + 8
    rect = pygame.Rect(x0, y0, box_w, box_h)
    pygame.draw.rect(surface, (50, 50, 50), rect, border_radius=6)
    pygame.draw.rect(surface, GRAY, rect, 1, border_radius=6)

    if not kind:
        return box_h

    coords = BASE_SHAPES[kind]
    # center coords within 4x4
    minx = min(c[0] for c in coords)
    miny = min(c[1] for c in coords)
    maxx = max(c[0] for c in coords)
    maxy = max(c[1] for c in coords)
    w = maxx - minx + 1
    h = maxy - miny + 1
    offset_x = (4 - w) // 2
    offset_y = (4 - h) // 2

    for (cx, cy) in coords:
        px = x0 + 4 + (cx + offset_x) * block
        py = y0 + 4 + (cy + offset_y) * block
        pygame.draw.rect(surface, COLORS[kind], (px, py, block, block))
        pygame.draw.rect(surface, GRAY, (px, py, block, block), 1)

    return box_h


def draw_playfield_border(surface):
    rect = pygame.Rect(PLAY_TOPLEFT[0], PLAY_TOPLEFT[1], PLAY_WIDTH, PLAY_HEIGHT)
    pygame.draw.rect(surface, LIGHT_GRAY, rect, 2, border_radius=4)


def draw_pause(surface):
    s = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, 140))
    surface.blit(s, (0, 0))
    txt = FONT_HUGE.render("PAUSED", True, WHITE)
    surface.blit(txt, (PLAY_TOPLEFT[0] + PLAY_WIDTH // 2 - txt.get_width() // 2,
                       PLAY_TOPLEFT[1] + PLAY_HEIGHT // 2 - txt.get_height() // 2))


def draw_game_over(surface, score):
    s = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))
    surface.blit(s, (0, 0))
    txt = FONT_HUGE.render("GAME OVER", True, WHITE)
    sub = FONT_BIG.render("Press Enter to play again, Esc to quit", True, WHITE)
    scr = FONT_BIG.render(f"Score: {score}", True, WHITE)
    cx = PLAY_TOPLEFT[0] + PLAY_WIDTH // 2
    cy = PLAY_TOPLEFT[1] + PLAY_HEIGHT // 2
    surface.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2 - 40))
    surface.blit(scr, (cx - scr.get_width() // 2, cy - scr.get_height() // 2 + 4))
    surface.blit(sub, (cx - sub.get_width() // 2, cy - sub.get_height() // 2 + 44))


def draw_start_menu(surface):
    # Dim entire window and center text across full width
    s = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, 150))
    surface.blit(s, (0, 0))
    title = FONT_HUGE.render("TETRIS", True, WHITE)
    subtitle = FONT_BIG.render("Press Enter to Start", True, WHITE)
    cx = WIN_WIDTH // 2
    cy = WIN_HEIGHT // 2
    surface.blit(title, (cx - title.get_width() // 2, cy - 140))
    surface.blit(subtitle, (cx - subtitle.get_width() // 2, cy - 80))
    controls = [
        "Controls:",
        "Left/Right: Move",
        "Down: Soft Drop",
        "Up or X: Rotate CW",
        "Z: Rotate CCW",
        "Space: Hard Drop",
        "C: Hold",
        "P: Pause",
        "Esc: Quit",
    ]
    y = cy - 20
    for line in controls:
        surf = FONT.render(line, True, WHITE)
        surface.blit(surf, (cx - surf.get_width() // 2, y))
        y += 28


def draw_line_clear_flash(surface, rows, phase):
    alpha = int(180 * (1 - abs(phase * 2 - 1)))
    alpha = max(60, alpha)
    for y in rows:
        s = pygame.Surface((PLAY_WIDTH, BLOCK), pygame.SRCALPHA)
        s.fill((*WHITE_FULL, alpha))
        surface.blit(s, (PLAY_TOPLEFT[0], PLAY_TOPLEFT[1] + y * BLOCK))


def draw_level_popup(surface, level, t):
    a = max(0, min(1.0, t / 1.2))
    s = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
    s.fill((0, 0, 0, int(80 * a)))
    surface.blit(s, (0, 0))
    txt = FONT_BIG.render(f"Level Up! Level {level}", True, WHITE)
    x = PLAY_TOPLEFT[0] + PLAY_WIDTH // 2 - txt.get_width() // 2
    y = PLAY_TOPLEFT[1] + 20
    surface.blit(txt, (x, y))


def get_full_rows(locked):
    full = []
    for y in range(ROWS):
        if all((x, y) in locked for x in range(COLS)):
            full.append(y)
    return full


HS_FILE = os.path.join(os.path.dirname(__file__), "tetris_highscore.txt")


def load_high_score():
    try:
        with open(HS_FILE, "r", encoding="utf-8") as f:
            return int(f.read().strip() or 0)
    except Exception:
        return 0


def save_high_score(score):
    try:
        with open(HS_FILE, "w", encoding="utf-8") as f:
            f.write(str(int(score)))
    except Exception:
        pass


def new_bag():
    bag = list(BASE_SHAPES.keys())
    random.shuffle(bag)
    return bag


def tetris_gravity_speed(level):
    # Approximate gravity speeds decreasing with level
    # Start ~0.8s per cell; faster per level
    return max(0.8 - (level * 0.07), 0.05)


def main():
    running = True
    paused = False
    in_menu = True

    score = 0
    level = 0
    lines_cleared_total = 0
    high_score = load_high_score()

    locked = {}

    # Piece queue - 7-bag
    bag = new_bag()
    next_queue = bag[:]
    current = Piece(next_queue.pop(0))
    if len(next_queue) < 7:
        next_queue += new_bag()

    hold_piece = None
    can_hold = True

    fall_timer = 0.0
    lock_timer = 0.0
    lock_delay = 0.5  # seconds on ground before locking
    on_ground = False

    soft_drop = False
    soft_drop_bonus_cells = 0

    game_over = False
    clear_anim = None  # {'rows': [...], 't': seconds}
    level_popup_t = 0.0

    while running:
        dt = CLOCK.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                if in_menu:
                    if event.key == pygame.K_RETURN:
                        # start new game
                        score = 0
                        level = 0
                        lines_cleared_total = 0
                        locked = {}
                        bag = new_bag()
                        next_queue = bag[:]
                        current = Piece(next_queue.pop(0))
                        if len(next_queue) < 7:
                            next_queue += new_bag()
                        hold_piece = None
                        can_hold = True
                        fall_timer = 0.0
                        lock_timer = 0.0
                        on_ground = False
                        soft_drop = False
                        soft_drop_bonus_cells = 0
                        game_over = False
                        clear_anim = None
                        level_popup_t = 0.0
                        in_menu = False
                    continue
                if game_over:
                    if event.key == pygame.K_RETURN:
                        # restart
                        score = 0
                        level = 0
                        lines_cleared_total = 0
                        locked = {}
                        bag = new_bag()
                        next_queue = bag[:]
                        current = Piece(next_queue.pop(0))
                        if len(next_queue) < 7:
                            next_queue += new_bag()
                        hold_piece = None
                        can_hold = True
                        fall_timer = 0.0
                        lock_timer = 0.0
                        on_ground = False
                        soft_drop = False
                        soft_drop_bonus_cells = 0
                        game_over = False
                        clear_anim = None
                        level_popup_t = 0.0
                    continue

                if event.key == pygame.K_p:
                    paused = not paused

                if paused:
                    continue
                if clear_anim is not None:
                    continue

                if event.key == pygame.K_LEFT:
                    moved = try_move(current, -1, 0, locked)
                    if moved and on_ground:
                        lock_timer = 0.0
                elif event.key == pygame.K_RIGHT:
                    moved = try_move(current, 1, 0, locked)
                    if moved and on_ground:
                        lock_timer = 0.0
                elif event.key in (pygame.K_UP, pygame.K_x):
                    rotated = try_rotate(current, CLOCKWISE, locked)
                    if rotated and on_ground:
                        lock_timer = 0.0
                elif event.key == pygame.K_z:
                    rotated = try_rotate(current, COUNTER, locked)
                    if rotated and on_ground:
                        lock_timer = 0.0
                elif event.key == pygame.K_DOWN:
                    soft_drop = True
                elif event.key == pygame.K_SPACE:
                    # Hard drop
                    dist = 0
                    while try_move(current, 0, 1, locked):
                        dist += 1
                    score += 2 * dist
                    # Lock immediately
                    for (x, y) in current.get_blocks():
                        locked[(x, y)] = current.color
                    # Soft drop bonus accrued
                    score += soft_drop_bonus_cells
                    soft_drop_bonus_cells = 0
                    rows = get_full_rows(locked)
                    if rows:
                        clear_anim = {"rows": rows, "t": 0.35}
                        current = None
                    else:
                        current = Piece(next_queue.pop(0))
                        if len(next_queue) < 7:
                            next_queue += new_bag()
                        can_hold = True
                        fall_timer = 0.0
                        lock_timer = 0.0
                        on_ground = False
                elif event.key == pygame.K_c:
                    if can_hold:
                        if hold_piece is None:
                            hold_piece = current.clone()
                            current = Piece(next_queue.pop(0))
                            if len(next_queue) < 7:
                                next_queue += new_bag()
                        else:
                            hold_piece.kind, current.kind = current.kind, hold_piece.kind
                            hold_piece.color = COLORS[hold_piece.kind]
                            current.color = COLORS[current.kind]
                        # Reset current piece position/rotation when swapped
                        current.x = COLS // 2 - 2
                        current.y = -2
                        current.rotation = 0
                        can_hold = False
                        fall_timer = 0.0
                        lock_timer = 0.0
                        on_ground = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    soft_drop = False

        if not running:
            break

        if paused:
            # Draw paused screen
            WIN.fill(BLACK)
            grid = create_grid(locked)
            draw_grid(WIN, grid)
            if current is not None:
                draw_current_piece(WIN, current)
                ghost = get_ghost_piece(current, locked)
                draw_ghost(WIN, ghost)
            draw_panel(WIN, score, level, lines_cleared_total, next_queue, hold_piece, high_score)
            draw_playfield_border(WIN)
            draw_pause(WIN)
            pygame.display.flip()
            continue

        if in_menu:
            # Keep background visible, then overlay centered start menu
            WIN.fill(BLACK)
            grid = create_grid(locked)
            draw_grid(WIN, grid)
            draw_panel(WIN, 0, 0, 0, [], None, high_score)
            draw_playfield_border(WIN)
            draw_start_menu(WIN)
            pygame.display.flip()
            continue

        if not game_over and clear_anim is None:
            # Gravity
            fall_timer += dt
            speed = tetris_gravity_speed(level)
            if soft_drop:
                # Speed up gravity and award soft drop points per cell moved
                # We simulate faster ticks by reducing threshold
                speed = min(0.02, speed * 0.25)

            moved_down = False
            while fall_timer >= speed:
                fall_timer -= speed
                if try_move(current, 0, 1, locked):
                    moved_down = True
                    if soft_drop:
                        soft_drop_bonus_cells += 1
                else:
                    # On ground
                    on_ground = True
                    break

            if moved_down:
                # If moved down successfully, not on ground yet necessarily
                # Check if the next cell is blocked to start lock timer
                p = current.clone()
                p.y += 1
                if not valid_position(p.get_blocks(), locked):
                    on_ground = True
                else:
                    on_ground = False
                    lock_timer = 0.0

            if on_ground:
                lock_timer += dt
                if lock_timer >= lock_delay:
                    # Lock piece
                    for (x, y) in current.get_blocks():
                        if y < 0:
                            # Game over
                            game_over = True
                            break
                        locked[(x, y)] = current.color
                    if not game_over:
                        # Score soft drop bonus
                        score += soft_drop_bonus_cells
                        soft_drop_bonus_cells = 0

                        # Detect clears for animation
                        rows = get_full_rows(locked)
                        if rows:
                            clear_anim = {"rows": rows, "t": 0.35}
                            current = None
                        else:
                            # Spawn next
                            current = Piece(next_queue.pop(0))
                            if len(next_queue) < 7:
                                next_queue += new_bag()
                            can_hold = True
                            fall_timer = 0.0
                            lock_timer = 0.0
                            on_ground = False

        # Handle line clear animation timing
        if clear_anim is not None and not game_over:
            clear_anim["t"] -= dt
            if clear_anim["t"] <= 0:
                rows = clear_anim["rows"]
                cleared = len(rows)
                _ = clear_rows(locked)
                if cleared:
                    lines_cleared_total += cleared
                    score += [0, 40, 100, 300, 1200][cleared] * (level + 1)
                    old_level = level
                    level = lines_cleared_total // 10
                    if level > old_level:
                        level_popup_t = 1.2
                current = Piece(next_queue.pop(0))
                if len(next_queue) < 7:
                    next_queue += new_bag()
                can_hold = True
                fall_timer = 0.0
                lock_timer = 0.0
                on_ground = False
                clear_anim = None

        # Render
        WIN.fill(BLACK)
        grid = create_grid(locked)
        draw_grid(WIN, grid)
        if current is not None:
            ghost = get_ghost_piece(current, locked)
            draw_ghost(WIN, ghost)
            draw_current_piece(WIN, current)
        draw_panel(WIN, score, level, lines_cleared_total, next_queue, hold_piece, high_score)
        draw_playfield_border(WIN)
        if clear_anim is not None:
            total = 0.35
            phase = max(0.0, min(1.0, 1.0 - clear_anim["t"] / total))
            draw_line_clear_flash(WIN, clear_anim["rows"], phase)
        if level_popup_t > 0:
            draw_level_popup(WIN, level, level_popup_t)
            level_popup_t -= dt
        if game_over:
            if score > high_score:
                high_score = score
                save_high_score(high_score)
            s = pygame.Surface((WIN_WIDTH, WIN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            WIN.blit(s, (0, 0))
            txt = FONT_HUGE.render("GAME OVER", True, WHITE)
            scr = FONT_BIG.render(f"Score: {score}", True, WHITE)
            best = FONT_BIG.render(f"High Score: {high_score}", True, WHITE)
            sub = FONT_BIG.render("Press Enter to play again, Esc to quit", True, WHITE)
            cx = PLAY_TOPLEFT[0] + PLAY_WIDTH // 2
            cy = PLAY_TOPLEFT[1] + PLAY_HEIGHT // 2
            WIN.blit(txt, (cx - txt.get_width() // 2, cy - txt.get_height() // 2 - 60))
            WIN.blit(scr, (cx - scr.get_width() // 2, cy - scr.get_height() // 2 - 10))
            WIN.blit(best, (cx - best.get_width() // 2, cy - best.get_height() // 2 + 30))
            WIN.blit(sub, (cx - sub.get_width() // 2, cy - sub.get_height() // 2 + 70))
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()