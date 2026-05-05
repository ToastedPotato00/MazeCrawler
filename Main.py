import pygame
import sys
from sprites import load_tile_sprites, build_wall_cache, BotSprite

TILE_SIZE = 32
MAP_COLS  = 25
MAP_ROWS  = 20
SCREEN_W  = TILE_SIZE * MAP_COLS
SCREEN_H  = TILE_SIZE * MAP_ROWS + 80
FPS       = 60
TITLE     = "MazeCrawler"

C_BG     = (18, 18, 24)
C_WALL   = (50, 50, 70)
C_HUD_BG = (12, 12, 18)
C_TEXT   = (220, 220, 220)

TEST_MAP = [
    "#########################",
    "#S..#.....#...........#.#",
    "#.#.#.###.#.#########.#.#",
    "#.#...#.#...#.........#.#",
    "#.#####.#####.#######.#.#",
    "#.......#.....#.......#.#",
    "#########.#####.#######.#",
    "#.........#.....#.......#",
    "#.#########.#####.#####.#",
    "#.............#...#.....#",
    "#.###########.#.#.#.###.#",
    "#.#...........#.#...#...#",
    "#.#.###########.#####.#.#",
    "#.#...................#.##",
    "#.###########.#######.#.#",
    "#.#...........#.......#.#",
    "#.#.###########.#######.#",
    "#.#...................#.#",
    "#...#################.G.#",
    "#####               #####",
]


def draw_map(screen, game_map, tile_sprites, wall_cache):
    for row_idx, row in enumerate(game_map):
        for col_idx, tile in enumerate(row):
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE
            if tile == '#':
                # use the autotiled wall sprite for this position
                sprite = wall_cache.get((row_idx, col_idx), tile_sprites.get('.'))
            else:
                sprite = tile_sprites.get(tile, tile_sprites['.'])
            screen.blit(sprite, (x, y))


def draw_hud(screen, font, hp=100, steps=0, keys=0, score=0):
    hud_y = SCREEN_H - 80
    pygame.draw.rect(screen, C_HUD_BG, (0, hud_y, SCREEN_W, 80))
    pygame.draw.line(screen, C_WALL, (0, hud_y), (SCREEN_W, hud_y), 2)

    bar_x, bar_y = 20, hud_y + 10
    pygame.draw.rect(screen, (80, 0, 0),    (bar_x, bar_y, 150, 18))
    pygame.draw.rect(screen, (200, 50, 50), (bar_x, bar_y, int(150 * hp / 100), 18))
    screen.blit(font.render(f"HP  {hp}/100", True, C_TEXT), (bar_x, bar_y + 22))
    screen.blit(font.render(f"Steps : {steps}", True, C_TEXT), (220, hud_y + 10))
    screen.blit(font.render(f"Keys  : {keys}",  True, C_TEXT), (220, hud_y + 32))
    screen.blit(font.render(f"Score : {score}", True, C_TEXT), (380, hud_y + 10))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("monospace", 14)

    tile_sprites = load_tile_sprites()
    wall_cache   = build_wall_cache(TEST_MAP, tile_sprites['_wall_sheet'])
    bot          = BotSprite()

    bot_col, bot_row = 1, 1
    for r, row in enumerate(TEST_MAP):
        for c, tile in enumerate(row):
            if tile == 'S':
                bot_col, bot_row = c, r

    running = True
    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        bot.update(dt)
        screen.fill(C_BG)
        draw_map(screen, TEST_MAP, tile_sprites, wall_cache)
        bot.draw(screen, bot_col * TILE_SIZE, bot_row * TILE_SIZE)
        draw_hud(screen, font)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()