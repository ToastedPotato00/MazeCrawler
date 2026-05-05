"""
tile_picker.py  -  MazeCrawler dev tool

Controls:
  - Hover  : see tile coordinates
  - Click  : print coords + which sheet to terminal
  - TAB    : switch between spritesheets
  - Scroll : zoom in/out
  - ESC    : quit
"""

import pygame
import os
import sys

SPRITES_DIR = os.path.join("Assets", "sprites", "0x72_DungeonTilesetII_v1.7")

# All sheets you might want to pick from
SHEETS = [
    ("MAIN  (0x72_DungeonTilesetII_v1.7.png)",  os.path.join(SPRITES_DIR, "0x72_DungeonTilesetII_v1.7.png")),
    ("WALLS (atlas_walls_low-16x16.png)",        os.path.join(SPRITES_DIR, "atlas_walls_low-16x16.png")),
    ("FLOOR (atlas_floor-16x16.png)",            os.path.join(SPRITES_DIR, "atlas_floor-16x16.png")),
    ("WALLS HIGH (atlas_walls_high-16x32.png)",  os.path.join(SPRITES_DIR, "atlas_walls_high-16x32.png")),
]

TILE_SRC = 16
ZOOM     = 3
C_BG     = (20, 20, 30)
C_GRID   = (80, 80, 100, 120)
C_HOVER  = (255, 255, 0, 140)
C_TEXT   = (255, 255, 255)
C_SHADOW = (0, 0, 0)
C_TAB_ON = (60, 120, 200)
C_TAB_OFF= (35, 35, 50)


def shadow_text(surface, font, text, x, y, colour=C_TEXT):
    surface.blit(font.render(text, True, C_SHADOW), (x+1, y+1))
    surface.blit(font.render(text, True, colour),   (x,   y))


def main():
    pygame.init()

    # check which sheets actually exist
    available = [(name, path) for name, path in SHEETS if os.path.exists(path)]
    if not available:
        print("ERROR: No spritesheets found. Check your Assets folder path.")
        sys.exit(1)

    screen = pygame.display.set_mode((900, 700), pygame.RESIZABLE)
    pygame.display.set_caption("MazeCrawler Tile Picker")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("monospace", 14, bold=True)
    small  = pygame.font.SysFont("monospace", 12)

    # load all available sheets
    raw_sheets = {}
    for name, path in available:
        raw_sheets[name] = pygame.image.load(path).convert_alpha()

    current_idx = 0
    zoom        = ZOOM
    hovered     = None

    # which variable name to tell the user to update
    SHEET_VAR = {
        available[i][0]: name for i, (name, _) in enumerate(available)
    }

    VAR_HINT = {
        "MAIN  (0x72_DungeonTilesetII_v1.7.png)" : "FIRE_POS / KEY_POS / CHEST_POS / etc.",
        "WALLS (atlas_walls_low-16x16.png)"       : "WALL_SPRITES  <-- use these coords for walls!",
        "FLOOR (atlas_floor-16x16.png)"           : "FLOOR_POS",
        "WALLS HIGH (atlas_walls_high-16x32.png)" : "WALL_SPRITES (tall walls)",
    }

    running = True
    while running:
        name, _ = available[current_idx]
        raw      = raw_sheets[name]
        sw, sh   = raw.get_size()
        tile_disp = TILE_SRC * zoom
        cols = sw // TILE_SRC
        rows = sh // TILE_SRC

        win_w, win_h = screen.get_size()
        TAB_H   = 36
        INFO_H  = 70
        MAP_H   = win_h - TAB_H - INFO_H

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_TAB:
                    current_idx = (current_idx + 1) % len(available)
            if event.type == pygame.MOUSEWHEEL:
                zoom = max(1, min(8, zoom + event.y))
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # check if clicked a tab
                tab_w = win_w // len(available)
                if event.pos[1] < TAB_H:
                    current_idx = min(event.pos[0] // tab_w, len(available) - 1)
                elif hovered and event.pos[1] >= TAB_H:
                    col, row = hovered
                    hint = VAR_HINT.get(name, "sprites.py")
                    print(f"\n  Sheet  : {name}")
                    print(f"  Tile   : col={col}  row={row}")
                    print(f"  Update : {hint}")
                    print(f"  Value  : ({col}, {row})\n")

        tile_disp = TILE_SRC * zoom

        # scaled sheet
        scaled = pygame.transform.scale(raw, (cols * tile_disp, rows * tile_disp))

        # hover detection (relative to below the tab bar)
        mx, my = pygame.mouse.get_pos()
        my_rel  = my - TAB_H
        if 0 <= mx < cols * tile_disp and 0 <= my_rel < rows * tile_disp:
            hovered = (mx // tile_disp, my_rel // tile_disp)
        else:
            hovered = None

        # ── Draw ──────────────────────────────────────────────────────────
        screen.fill(C_BG)

        # tab bar
        tab_w = win_w // len(available)
        for i, (tname, _) in enumerate(available):
            colour = C_TAB_ON if i == current_idx else C_TAB_OFF
            pygame.draw.rect(screen, colour, (i * tab_w, 0, tab_w - 2, TAB_H - 2))
            # short label
            short = tname.split("(")[0].strip()
            shadow_text(screen, small, short, i * tab_w + 6, 10)

        # spritesheet
        sheet_surf = pygame.Surface((win_w, MAP_H))
        sheet_surf.fill(C_BG)
        sheet_surf.blit(scaled, (0, 0))

        # grid overlay
        grid = pygame.Surface((cols * tile_disp, rows * tile_disp), pygame.SRCALPHA)
        for c in range(cols + 1):
            pygame.draw.line(grid, C_GRID, (c * tile_disp, 0), (c * tile_disp, rows * tile_disp))
        for r in range(rows + 1):
            pygame.draw.line(grid, C_GRID, (0, r * tile_disp), (cols * tile_disp, r * tile_disp))
        sheet_surf.blit(grid, (0, 0))

        # hover highlight
        if hovered:
            col, row = hovered
            hs = pygame.Surface((tile_disp, tile_disp), pygame.SRCALPHA)
            hs.fill(C_HOVER)
            sheet_surf.blit(hs, (col * tile_disp, row * tile_disp))

        screen.blit(sheet_surf, (0, TAB_H))

        # info bar
        bar_y = win_h - INFO_H
        pygame.draw.rect(screen, (10, 10, 20), (0, bar_y, win_w, INFO_H))
        pygame.draw.line(screen, (60, 60, 90), (0, bar_y), (win_w, bar_y))

        hint = VAR_HINT.get(name, "sprites.py")
        shadow_text(screen, font, f"Sheet: {name}", 12, bar_y + 6)
        shadow_text(screen, small, f"Update: {hint}", 12, bar_y + 26, (180, 220, 180))

        if hovered:
            col, row = hovered
            shadow_text(screen, font,
                f"col={col}  row={row}   ->   ({col}, {row})",
                12, bar_y + 46, (255, 255, 100))
        else:
            shadow_text(screen, small,
                "TAB = switch sheet  |  Scroll = zoom  |  Click = print to terminal  |  ESC = quit",
                12, bar_y + 46, (140, 140, 140))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()