from __future__ import annotations

import random
from typing import Iterable, Iterator, List, Tuple

Cell = int
Coord = Tuple[int, int]


def build_maze(size: int = 15) -> List[List[int]]:
    if size < 9:
        raise ValueError('Maze size must be at least 9 cells.')
    if size % 2 == 0:
        size += 1

    grid = [[1 for _ in range(size)] for _ in range(size)]
    start_axis = size // 2
    start = (start_axis, start_axis)
    visited = {start}
    stack = [start]
    grid[start[0]][start[1]] = 0

    # Randomized depth-first carving creates continuous, branching corridors.
    while stack:
        r, c = stack[-1]
        options = [
            (r + dr, c + dc)
            for dr, dc in ((2, 0), (-2, 0), (0, 2), (0, -2))
            if 1 <= r + dr < size - 1
            and 1 <= c + dc < size - 1
            and (r + dr, c + dc) not in visited
        ]
        if not options:
            stack.pop()
            continue

        nr, nc = random.choice(options)
        grid[(r + nr) // 2][(c + nc) // 2] = 0
        grid[nr][nc] = 0
        visited.add((nr, nc))
        stack.append((nr, nc))

    # Open a few extra junctions so the maze has alternate routes, not one corridor.
    loop_walls = []
    for r in range(1, size - 1):
        for c in range(1, size - 1):
            if grid[r][c] != 1:
                continue
            horizontal = grid[r][c - 1] == 0 and grid[r][c + 1] == 0
            vertical = grid[r - 1][c] == 0 and grid[r + 1][c] == 0
            if horizontal or vertical:
                loop_walls.append((r, c))
    random.shuffle(loop_walls)
    for r, c in loop_walls[:max(4, size // 2)]:
        grid[r][c] = 0

    exits = []
    lattice_offset = start_axis % 2
    first_lattice_pos = 1 if lattice_offset else 2
    for pos in range(first_lattice_pos, size - 1, 2):
        exits.extend(((1, pos, 0, pos), (size - 2, pos, size - 1, pos),
                      (pos, 1, pos, 0), (pos, size - 2, pos, size - 1)))
    random.shuffle(exits)
    inner_r, inner_c, goal_r, goal_c = exits[0]
    grid[inner_r][inner_c] = 0
    grid[goal_r][goal_c] = 4
    start_r, start_c = start
    grid[start_r][start_c] = 3

    corridors = [
        (r, c)
        for r in range(1, size - 1)
        for c in range(1, size - 1)
        if grid[r][c] == 0 and (r, c) != start
    ]
    random.shuffle(corridors)
    danger_count = max(5, size // 3)
    for r, c in corridors[:danger_count]:
        grid[r][c] = 5

    return grid


RAW_GRID: List[List[int]] = build_maze(15)
HEIGHT = {0: 0.05, 1: 1.7, 3: 0.4, 4: 0.45, 5: 0.55}
CELL_COLORS = {
    0: '#1B2028',
    1: '#5B6470',
    3: '#7CCB6C',
    4: '#67B5FF',
    5: '#D95C4A',
}


def get_start_goal(grid: List[List[int]]) -> Tuple[Coord, Coord]:
    start: Coord | None = None
    goal: Coord | None = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 3:
                start = (r, c)
            elif value == 4:
                goal = (r, c)
    if start is None or goal is None:
        raise ValueError('Maze must contain exactly one start and one exit cell.')
    return start, goal


START, GOAL = get_start_goal(RAW_GRID)


def clone_grid(grid: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in grid]


def in_bounds(grid: List[List[int]], r: int, c: int) -> bool:
    return 0 <= r < len(grid) and 0 <= c < len(grid[0])


def walkable(grid: List[List[int]], r: int, c: int) -> bool:
    if not in_bounds(grid, r, c):
        return False
    return grid[r][c] in (0, 3, 4, 5)


def neighbors(grid: List[List[int]], r: int, c: int) -> Iterator[Coord]:
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if walkable(grid, nr, nc):
            yield (nr, nc)


def step_cost(grid: List[List[int]], r: int, c: int) -> int:
    value = grid[r][c]
    return 4 if value == 5 else 1


def collapse_corridor(grid: List[List[int]], cell: Coord) -> bool:
    r, c = cell
    if not in_bounds(grid, r, c):
        return False
    if grid[r][c] in (0, 5):
        grid[r][c] = 1
        return True
    return False


def reset_maze() -> List[List[int]]:
    return clone_grid(RAW_GRID)


_LAST_VARIANT_SIGNATURE = None


def generate_maze_variant(size: int = 25) -> List[List[int]]:
    global _LAST_VARIANT_SIGNATURE
    from algorithms import astar_path, bfs_path

    for _ in range(500):
        grid = build_maze(size)
        signature = tuple(tuple(row) for row in grid)
        if signature == _LAST_VARIANT_SIGNATURE:
            continue
        start, goal = get_start_goal(grid)
        blind_result = bfs_path(grid, start, goal)
        safe_result = astar_path(grid, start, goal)
        if (
            blind_result['danger_hits'] > 0
            and safe_result['danger_hits'] == 0
            and safe_result['steps'] > blind_result['steps']
        ):
            _LAST_VARIANT_SIGNATURE = signature
            return grid
    raise RuntimeError('Could not generate a maze with a short dangerous route and a longer safe route.')


def get_open_cells(grid: List[List[int]]) -> Iterable[Coord]:
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 3, 4, 5):
                yield (r, c)
