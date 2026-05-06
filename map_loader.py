"""
map_loader.py — MazeCrawler
Loads map .txt files from the maps/ folder and validates them.
"""

import os

MAPS_DIR = "maps"

VALID_TILES = set('#%.MFRTtKSG')   # all legal tile symbols
REQUIRED    = {'S', 'G'}           # every map must have these


class MapError(Exception):
    pass


def load_map(filename: str) -> list[str]:
    """
    Load a map from maps/<filename>.
    Returns a list of strings, one per row.
    Raises MapError if the file is missing or invalid.
    """
    path = os.path.join(MAPS_DIR, filename)

    if not os.path.exists(path):
        raise MapError(f"Map file not found: {path}")

    with open(path, 'r') as f:
        raw_lines = f.readlines()

    # strip newlines, skip blank lines
    lines = [line.rstrip('\n') for line in raw_lines if line.strip()]

    if not lines:
        raise MapError(f"Map file is empty: {path}")

    # make all rows the same width (pad with walls)
    max_width = max(len(row) for row in lines)
    lines = [row.ljust(max_width, '#') for row in lines]

    # validate tiles
    found = set()
    for r, row in enumerate(lines):
        for c, tile in enumerate(row):
            if tile not in VALID_TILES:
                raise MapError(f"Unknown tile '{tile}' at row {r} col {c}")
            found.add(tile)

    for req in REQUIRED:
        if req not in found:
            raise MapError(f"Map is missing required tile '{req}'")

    return lines


def get_map_list() -> list[str]:
    """Return all .txt filenames in the maps/ folder, sorted."""
    if not os.path.exists(MAPS_DIR):
        os.makedirs(MAPS_DIR)
        return []
    files = [f for f in os.listdir(MAPS_DIR) if f.endswith('.txt')]
    return sorted(files)


def find_tile(game_map: list[str], symbol: str) -> tuple[int,int] | None:
    """Find the first occurrence of a tile symbol. Returns (row, col) or None."""
    for r, row in enumerate(game_map):
        for c, tile in enumerate(row):
            if tile == symbol:
                return (r, c)
    return None


def find_all_tiles(game_map: list[str], symbol: str) -> list[tuple[int,int]]:
    """Find all occurrences of a tile symbol. Returns list of (row, col)."""
    return [(r, c)
            for r, row in enumerate(game_map)
            for c, tile in enumerate(row)
            if tile == symbol]


def get_map_info(game_map: list[str]) -> dict:
    """
    Return useful stats about a map:
      - rows, cols
      - start and goal positions
      - teleporter pairs
      - walkable tile count (for score normalization)
    """
    rows = len(game_map)
    cols = len(game_map[0]) if rows else 0

    walkable = sum(
        1 for row in game_map
        for tile in row
        if tile != '#'
    )

    # pair up teleporters: T pairs with t
    T_tiles = find_all_tiles(game_map, 'T')
    t_tiles = find_all_tiles(game_map, 't')
    teleporter_pairs = list(zip(T_tiles, t_tiles))

    return {
        'rows'             : rows,
        'cols'             : cols,
        'start'            : find_tile(game_map, 'S'),
        'goals'            : find_all_tiles(game_map, 'G'),
        'walkable_tiles'   : walkable,
        'teleporter_pairs' : teleporter_pairs,
    }