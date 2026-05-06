"""
bot.py — MazeCrawler Part 2
Backtracking algorithm that runs in a background thread.
Communicates with main.py via a shared GameState object.
"""

import threading
import time


# ── Tile rules ────────────────────────────────────────────────────────────────
WALKABLE = set('.SFMRTtKG%')   # tiles the bot can step on

STEP_COST = {
    'M': 3,   # mud costs 3 steps
}
DEFAULT_STEP_COST = 1

HP_EFFECT = {
    'F': -25,   # fire damages
    'R': +15,   # regen heals
}
MAX_HP = 100


# ── Shared game state ─────────────────────────────────────────────────────────
class GameState:
    """
    All mutable state shared between the bot thread and the render loop.
    The bot writes to this; main.py reads from it every frame.
    """
    def __init__(self, start: tuple, walkable_tiles: int):
        self.lock = threading.Lock()

        # bot position (row, col)
        self.row, self.col = start

        # stats
        self.hp         = MAX_HP
        self.steps      = 0
        self.keys       = 0
        self.score      = 0

        # path overlay: {(row,col): 'visited' | 'backtrack' | 'final'}
        self.overlay    = {}

        # status flags
        self.running    = False   # True while algorithm is active
        self.reached    = False   # True when goal found
        self.dead       = False   # True when bot ran out of HP everywhere

        # for score normalisation (Map 3)
        self.max_steps  = walkable_tiles

    # convenience wrappers so callers don't need to manage the lock
    def set_pos(self, row, col):
        with self.lock:
            self.row, self.col = row, col

    def get_pos(self):
        with self.lock:
            return self.row, self.col

    def set_overlay(self, row, col, kind):
        with self.lock:
            self.overlay[(row, col)] = kind

    def get_overlay_copy(self):
        with self.lock:
            return dict(self.overlay)

    def add_steps(self, n):
        with self.lock:
            self.steps += n

    def change_hp(self, delta):
        with self.lock:
            self.hp = min(MAX_HP, max(0, self.hp + delta))
            return self.hp

    def snapshot(self):
        """Return a consistent snapshot of all HUD values."""
        with self.lock:
            return self.hp, self.steps, self.keys, self.score


# ── Bot algorithm ─────────────────────────────────────────────────────────────
class Bot:
    def __init__(self, game_map: list, state: GameState,
                 step_delay: float = 0.12):
        self.game_map   = game_map
        self.state      = state
        self.step_delay = step_delay   # seconds between moves
        self._thread    = None

    # ── public API ────────────────────────────────────────────────────────
    def start(self):
        """Kick off the backtracking algorithm in a background thread."""
        self.state.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ── internal ──────────────────────────────────────────────────────────
    def _tile(self, row, col) -> str:
        return self.game_map[row][col]

    def _neighbors(self, row, col) -> list:
        """Return walkable (row, col) neighbors in N E S W order."""
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        result = []
        rows = len(self.game_map)
        cols = len(self.game_map[0])
        for dr, dc in directions:
            nr, nc = row + dr, col + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if self._tile(nr, nc) in WALKABLE:
                    result.append((nr, nc))
        return result

    def _step_onto(self, row, col):
        """
        Move bot to (row, col), apply tile effects, update state.
        Returns False if the bot died (HP reached 0).
        """
        tile = self._tile(row, col)

        # movement cost
        cost = STEP_COST.get(tile, DEFAULT_STEP_COST)
        self.state.add_steps(cost)

        # move
        self.state.set_pos(row, col)

        # tile effect
        if tile in HP_EFFECT:
            remaining = self.state.change_hp(HP_EFFECT[tile])
            if remaining <= 0:
                return False   # bot died

        # mud: extra visual pause on top of step delay
        if tile == 'M':
            time.sleep(self.step_delay * 2)

        time.sleep(self.step_delay)
        return True

    def _run(self):
        """
        Iterative DFS backtracking.
        Uses an explicit stack so we never hit Python's recursion limit
        on large maps.

        Stack entries: (row, col, [unvisited_neighbours])
        """
        s = self.state
        start_row, start_col = s.get_pos()

        visited = set()
        visited.add((start_row, start_col))

        # each frame: (row, col, iterator-over-neighbours)
        stack = [(start_row, start_col,
                  iter(self._neighbors(start_row, start_col)))]

        goal_reached = False

        while stack and s.running:
            row, col, neighbours = stack[-1]

            # try the next unvisited neighbour
            try:
                nr, nc = next(neighbours)
            except StopIteration:
                # dead end — backtrack
                stack.pop()
                s.set_overlay(row, col, 'backtrack')
                if stack:
                    prev_r, prev_c, _ = stack[-1]
                    alive = self._step_onto(prev_r, prev_c)
                    if not alive:
                        break
                continue

            if (nr, nc) in visited:
                continue

            visited.add((nr, nc))

            # move forward
            alive = self._step_onto(nr, nc)
            s.set_overlay(row, col, 'visited')   # colour the tile we left

            if not alive:
                # ran out of HP — treat current cell as dead end
                s.set_overlay(nr, nc, 'backtrack')
                stack.pop()
                if stack:
                    prev_r, prev_c, _ = stack[-1]
                    self._step_onto(prev_r, prev_c)
                break

            # check for goal
            if self._tile(nr, nc) == 'G':
                s.set_overlay(nr, nc, 'visited')
                goal_reached = True
                break

            stack.append((nr, nc, iter(self._neighbors(nr, nc))))

        # ── Finish ────────────────────────────────────────────────────────
        if goal_reached:
            self._highlight_final_path(stack)
            s.reached = True
        else:
            s.dead = True

        s.running = False

    def _highlight_final_path(self, stack):
        """
        Mark every tile in the current stack as 'final' (gold highlight).
        This is the successful path from S to G.
        """
        time.sleep(0.3)   # brief pause before lighting up
        for row, col, _ in stack:
            self.state.set_overlay(row, col, 'final')
            time.sleep(0.04)