import pygame
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
SPRITES_DIR = os.path.join("Assets", "sprites", "0x72_DungeonTilesetII_v1.7")
MAIN_SHEET  = os.path.join(SPRITES_DIR, "0x72_DungeonTilesetII_v1.7.png")
FLOOR_SHEET = os.path.join(SPRITES_DIR, "atlas_floor-16x16.png")
WALLS_SHEET = os.path.join(SPRITES_DIR, "atlas_walls_low-16x16.png")
FRAMES_DIR  = os.path.join(SPRITES_DIR, "frames")

TILE_SRC  = 16    # source tile size in the spritesheet
TILE_SIZE = 32    # rendered tile size (2x upscale)


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_sheet(path):
    return pygame.image.load(path).convert_alpha()


def crop_tile(sheet, col, row, src_w=TILE_SRC, src_h=TILE_SRC):
    rect    = pygame.Rect(col * src_w, row * src_h, src_w, src_h)
    surface = pygame.Surface((src_w, src_h), pygame.SRCALPHA)
    surface.blit(sheet, (0, 0), rect)
    return pygame.transform.scale(surface, (TILE_SIZE, TILE_SIZE))


def tint_surface(surface, colour, alpha=120):
    tinted  = surface.copy()
    overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    overlay.fill((*colour, alpha))
    tinted.blit(overlay, (0, 0))
    return tinted


# ── Non-wall tile positions ───────────────────────────────────────────────────
FLOOR_POS  = (0, 0)   # atlas_floor
FIRE_POS   = (7, 0)   # main sheet
KEY_POS    = (8, 6)
CHEST_POS  = (0, 6)
REGEN_POS  = (8, 4)
TELE_POS   = (9, 2)
BRWALL_POS = (4, 2)
MUD_POS    = (3, 3)


# ── Wall autotile table ───────────────────────────────────────────────────────
#
#  For each wall tile, we check 4 neighbours (N E S W).
#  Each present wall neighbour adds to a bitmask:  N=1  E=2  S=4  W=8
#
#  Map every possible bitmask (0-15) to a (col, row) in atlas_walls_low.
#  Use tile_picker.py to find the right coords, then fill them in below.
#
#  If you only have e.g. horizontal / vertical / corner sprites, you can
#  point multiple masks to the same (col, row) -- see the comment examples.
#
WALL_SPRITES = {
    #  mask : (col, row)     neighbours
     0 : (0, 0),   # none              - isolated pillar
     1 : (2, 2),   # N                 - south end-cap
     2 : (4, 2),   # E                 - west end-cap
     3 : (1, 2),   # N+E               - bottom-left corner
     4 : (2, 0),   # S                 - north end-cap
     5 : (0, 1),   # N+S               - vertical wall  <-- set this one!
     6 : (1, 0),   # E+S               - top-left corner
     7 : (4, 1),   # N+E+S             - T open-left
     8 : (7, 2),   # W                 - east end-cap
     9 : (3, 2),   # N+W               - bottom-right corner
    10 : (2, 3),   # E+W               - horizontal wall  <-- set this one!
    11 : (0, 0),   # N+E+W             - T open-bottom
    12 : (3, 0),   # S+W               - top-right corner
    13 : (7, 1),   # N+S+W             - T open-right
    14 : (9, 1),   # E+S+W             - T open-top
    15 : (0, 0),   # N+E+S+W           - cross / centre
}

# WALLS that count as "solid" for neighbour detection
# (breakable walls also block, so include '%')
SOLID_TILES = {'#', '%'}


def compute_wall_mask(game_map, row, col):
    """
    Return the 4-bit neighbour mask for the wall at (row, col).
    Bits: N=1  E=2  S=4  W=8
    """
    rows = len(game_map)
    cols = len(game_map[0]) if rows else 0

    def is_solid(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False  # treat out-of-bounds as open space
        return game_map[r][c] in SOLID_TILES

    mask = 0
    if is_solid(row - 1, col): mask |= 1   # N
    if is_solid(row,     col + 1): mask |= 2   # E
    if is_solid(row + 1, col): mask |= 4   # S
    if is_solid(row,     col - 1): mask |= 8   # W
    return mask


def build_wall_cache(game_map, wall_sheet, debug_masks=False):
    """
    Pre-compute the correct wall sprite for every '#' tile in the map.
    Returns a dict: {(row, col): pygame.Surface}
    """
    pygame.font.init()
    debug_font = pygame.font.SysFont('monospace', 11, bold=True)

    cache = {}
    for r, row in enumerate(game_map):
        for c, tile in enumerate(row):
            if tile == '#':
                mask = compute_wall_mask(game_map, r, c)

                if debug_masks == 1:
                    # draw a coloured tile with the mask number on it
                    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    surf.fill((50, 50, 80))
                    pygame.draw.rect(surf, (80, 80, 120), surf.get_rect(), 1)
                    label = debug_font.render(str(mask), True, (255, 230, 80))
                    lx = (TILE_SIZE - label.get_width())  // 2
                    ly = (TILE_SIZE - label.get_height()) // 2
                    surf.blit(label, (lx, ly))
                    cache[(r, c)] = surf
                else:
                    pos = WALL_SPRITES.get(mask, (0, 0))
                    cache[(r, c)] = crop_tile(wall_sheet, *pos)
    return cache


def load_tile_sprites():
    main   = load_sheet(MAIN_SHEET)
    floors = load_sheet(FLOOR_SHEET)
    walls  = load_sheet(WALLS_SHEET)

    sprites = {
        '.': crop_tile(floors, *FLOOR_POS),
        '%': crop_tile(main,   *BRWALL_POS),
        'F': crop_tile(main,   *FIRE_POS),
        'M': crop_tile(main,   *MUD_POS),
        'K': crop_tile(main,   *KEY_POS),
        'R': crop_tile(main,   *REGEN_POS),
        'T': crop_tile(main,   *TELE_POS),
        't': crop_tile(main,   *TELE_POS),
        'S': crop_tile(floors, *FLOOR_POS),
        'G': crop_tile(main,   *CHEST_POS),
        # '#' is intentionally NOT here — handled by wall cache
    }

    sprites['visited']   = tint_surface(sprites['.'], (80, 130, 255))
    sprites['backtrack'] = tint_surface(sprites['.'], (255, 80,  80))

    # store the wall sheet so main.py can call build_wall_cache later
    sprites['_wall_sheet'] = walls

    return sprites


def load_bot_frames():
    frame_files = [
        "knight_run_anim_f0.png",
        "knight_run_anim_f1.png",
        "knight_run_anim_f2.png",
        "knight_run_anim_f3.png",
    ]
    frames = []
    for fname in frame_files:
        fpath = os.path.join(FRAMES_DIR, fname)
        if os.path.exists(fpath):
            img = pygame.image.load(fpath).convert_alpha()
            frames.append(pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE)))
        else:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill((60, 200, 60, 220))
            frames.append(surf)

    if not frames:
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        surf.fill((60, 200, 60, 220))
        frames = [surf]
    return frames


class BotSprite:
    FRAME_DURATION = 150

    def __init__(self):
        self.frames = load_bot_frames()
        self.index  = 0
        self.timer  = 0
        self.flip_x = False

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.FRAME_DURATION:
            self.index = (self.index + 1) % len(self.frames)
            self.timer = 0

    def draw(self, screen, pixel_x, pixel_y):
        frame = self.frames[self.index]
        if self.flip_x:
            frame = pygame.transform.flip(frame, True, False)
        screen.blit(frame, (pixel_x, pixel_y))