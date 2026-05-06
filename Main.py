import pygame
import sys
from sprites import load_tile_sprites, build_wall_cache, BotSprite
from map_loader import load_map, get_map_info
from bot import Bot, GameState

# ── Constants ─────────────────────────────────────────────────────────────────
TILE_SIZE = 32
SCREEN_W  = 800
SCREEN_H  = 720
HUD_H     = 80
FPS       = 60
TITLE     = "MazeCrawler"

C_BG      = (18,  18,  24)
C_HUD_BG  = (12,  12,  18)
C_WALL    = (50,  50,  70)
C_TEXT    = (220, 220, 220)
C_DIM     = (100, 100, 120)
C_RED     = (200,  50,  50)
C_GREEN   = ( 50, 200,  80)
C_YELLOW  = (220, 200,  50)
C_GOLD    = (230, 180,  40)

# overlay colours per tile kind
OVERLAY_COLOURS = {
    'visited'   : (60,  100, 220,  90),   # blue tint
    'backtrack' : (200,  50,  50,  90),   # red tint
    'final'     : (220, 180,  40, 140),   # gold tint
}

# ── Drawing ───────────────────────────────────────────────────────────────────
def draw_map(screen, game_map, tile_sprites, wall_cache, overlay):
    for row_idx, row in enumerate(game_map):
        for col_idx, tile in enumerate(row):
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE

            if tile == '#':
                sprite = wall_cache.get((row_idx, col_idx),
                                        tile_sprites['.'])
            else:
                sprite = tile_sprites.get(tile, tile_sprites['.'])

            screen.blit(sprite, (x, y))

            # draw overlay tint on top of floor/special tiles
            if (row_idx, col_idx) in overlay:
                kind   = overlay[(row_idx, col_idx)]
                colour = OVERLAY_COLOURS.get(kind)
                if colour:
                    tint = pygame.Surface((TILE_SIZE, TILE_SIZE),
                                          pygame.SRCALPHA)
                    tint.fill(colour)
                    screen.blit(tint, (x, y))


def draw_hud(screen, font, hp, steps, keys, score, map_name,
             state_label, state_colour):
    hud_y = SCREEN_H - HUD_H
    pygame.draw.rect(screen, C_HUD_BG, (0, hud_y, SCREEN_W, HUD_H))
    pygame.draw.line(screen, C_WALL,   (0, hud_y), (SCREEN_W, hud_y), 2)

    # HP bar
    bx, by = 20, hud_y + 10
    pygame.draw.rect(screen, (80, 0, 0), (bx, by, 150, 16))
    bar_col = C_GREEN if hp > 50 else C_YELLOW if hp > 25 else C_RED
    pygame.draw.rect(screen, bar_col, (bx, by, int(150 * max(hp,0) / 100), 16))
    screen.blit(font.render(f"HP {hp}/100", True, C_TEXT), (bx, by + 20))

    screen.blit(font.render(f"Steps : {steps}", True, C_TEXT), (210, hud_y + 10))
    screen.blit(font.render(f"Keys  : {keys}",  True, C_TEXT), (210, hud_y + 32))
    screen.blit(font.render(f"Score : {score}", True, C_TEXT), (360, hud_y + 10))

    # map name
    lbl = font.render(map_name, True, C_DIM)
    screen.blit(lbl, (SCREEN_W - lbl.get_width() - 10, hud_y + 10))

    # status label (READY / RUNNING / GOAL / DEAD)
    slbl = font.render(state_label, True, state_colour)
    screen.blit(slbl, (SCREEN_W - slbl.get_width() - 10, hud_y + 32))


def draw_start_prompt(screen, font):
    """Overlay shown before the bot starts."""
    big = pygame.font.SysFont("monospace", 26, bold=True)
    msg = big.render("Press SPACE to Start", True, C_GOLD)
    x   = (SCREEN_W - msg.get_width())  // 2
    y   = (SCREEN_H - HUD_H - msg.get_height()) // 2
    # dark box behind text
    pad = 16
    box = pygame.Rect(x - pad, y - pad,
                      msg.get_width() + pad*2,
                      msg.get_height() + pad*2)
    bg  = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 180))
    screen.blit(bg,  (box.x, box.y))
    screen.blit(msg, (x, y))


def draw_goal_banner(screen, font):
    big = pygame.font.SysFont("monospace", 28, bold=True)
    msg = big.render("Goal Reached!", True, C_GOLD)
    x   = (SCREEN_W - msg.get_width())  // 2
    y   = 20
    pad = 12
    bg  = pygame.Surface((msg.get_width() + pad*2,
                           msg.get_height() + pad*2), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 180))
    screen.blit(bg,  (x - pad, y - pad))
    screen.blit(msg, (x, y))


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("monospace", 14)

    # ── Load map ──────────────────────────────────────────────────────────
    MAP_FILE = "map1.txt"
    try:
        game_map = load_map(MAP_FILE)
    except Exception as e:
        print(f"Failed to load map: {e}")
        sys.exit(1)

    map_info = get_map_info(game_map)
    print(f"Loaded {MAP_FILE}  |  "
          f"{map_info['cols']}x{map_info['rows']}  |  "
          f"walkable={map_info['walkable_tiles']}")

    # ── Load sprites ──────────────────────────────────────────────────────
    tile_sprites = load_tile_sprites()
    wall_cache   = build_wall_cache(game_map, tile_sprites['_wall_sheet'])
    bot_sprite   = BotSprite()

    # ── Game state ────────────────────────────────────────────────────────
    start        = map_info['start']
    state        = GameState(start, map_info['walkable_tiles'])
    bot          = Bot(game_map, state, step_delay=0.12)

    started      = False   # True once SPACE has been pressed

    # ── Game loop ─────────────────────────────────────────────────────────
    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE and not started:
                    started = True
                    bot.start()

        # animate bot only while algorithm is running
        if state.running:
            bot_sprite.update(dt)

        # get thread-safe copies for rendering
        overlay      = state.get_overlay_copy()
        bot_row, bot_col = state.get_pos()
        hp, steps, keys, score = state.snapshot()

        # status label
        if not started:
            state_label, state_colour = "READY",   C_DIM
        elif state.reached:
            state_label, state_colour = "GOAL!",   C_GOLD
        elif state.dead:
            state_label, state_colour = "FAILED",  C_RED
        elif state.running:
            state_label, state_colour = "RUNNING", C_GREEN
        else:
            state_label, state_colour = "DONE",    C_DIM

        # ── Draw ──────────────────────────────────────────────────────────
        screen.fill(C_BG)
        draw_map(screen, game_map, tile_sprites, wall_cache, overlay)
        bot_sprite.draw(screen, bot_col * TILE_SIZE, bot_row * TILE_SIZE)
        draw_hud(screen, font, hp, steps, keys, score,
                 MAP_FILE, state_label, state_colour)

        if not started:
            draw_start_prompt(screen, font)
        if state.reached:
            draw_goal_banner(screen, font)

        pygame.display.flip()

    # stop bot thread cleanly
    state.running = False
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()