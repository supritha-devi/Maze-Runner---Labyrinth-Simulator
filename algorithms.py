from __future__ import annotations

from collections import deque
import heapq
from typing import Dict, List, Tuple

Coord = Tuple[int, int]


def risk_penalty(grid: List[List[int]]) -> int:
    return len(grid) * len(grid[0]) + 1


def bfs_distances_to_goal(grid: List[List[int]], goal: Coord) -> Dict[Coord, int]:
    queue = deque([goal])
    distances = {goal: 0}
    while queue:
        current = queue.popleft()
        for nxt in get_neighbors(grid, current):
            if nxt not in distances:
                distances[nxt] = distances[current] + 1
                queue.append(nxt)
    return distances


def safe_distances_to_goal(grid: List[List[int]], goal: Coord) -> Dict[Coord, Tuple[int, int]]:
    """Return the minimum (Grievers, steps) from each walkable cell to the goal."""
    queue: List[Tuple[int, int, int, Coord]] = [(0, 0, 0, goal)]
    distances: Dict[Coord, Tuple[int, int]] = {goal: (0, 0)}
    sequence = 0
    while queue:
        dangers, steps, _, current = heapq.heappop(queue)
        if distances.get(current) != (dangers, steps):
            continue
        for predecessor in get_neighbors(grid, current):
            candidate = (dangers + (1 if grid[current[0]][current[1]] == 5 else 0), steps + 1)
            if candidate < distances.get(predecessor, (float('inf'), float('inf'))):
                distances[predecessor] = candidate
                sequence += 1
                heapq.heappush(queue, (candidate[0], candidate[1], sequence, predecessor))
    return distances


def manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def get_neighbors(grid: List[List[int]], pos: Coord):
    r, c = pos
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]):
            value = grid[nr][nc]
            if value in (0, 3, 4, 5):
                yield (nr, nc)


def bfs_path(grid: List[List[int]], start: Coord, goal: Coord):
    queue = deque([start])
    previous: Dict[Coord, Coord | None] = {start: None}
    distance: Dict[Coord, int] = {start: 0}
    expanded = 0

    while queue:
        current = queue.popleft()
        expanded += 1
        if current == goal:
            break
        for nxt in get_neighbors(grid, current):
            if nxt not in previous:
                previous[nxt] = current
                distance[nxt] = distance[current] + 1
                queue.append(nxt)

    if goal not in previous:
        raise ValueError('No BFS route found to the exit.')

    path: List[Coord] = []
    cur: Coord | None = goal
    while cur is not None:
        path.append(cur)
        cur = previous[cur]
    path.reverse()

    danger_hits = sum(1 for r, c in path if grid[r][c] == 5)
    total_cost = len(path) - 1 + danger_hits * risk_penalty(grid)
    return {
        'path': path,
        'steps': len(path) - 1,
        'danger_hits': danger_hits,
        'total_cost': total_cost,
        'nodes_expanded': expanded,
        'algorithm': 'BFS',
    }


def astar_path(grid: List[List[int]], start: Coord, goal: Coord):
    if not grid or not grid[0]:
        raise ValueError('Maze grid cannot be empty.')

    open_heap: List[Tuple[float, float, int, Coord]] = []
    heapq.heappush(open_heap, (manhattan(start, goal), 0.0, 0, start))
    came_from: Dict[Coord, Coord | None] = {start: None}
    g_score: Dict[Coord, float] = {start: 0.0}
    # This makes safety the first priority: a longer safe path beats any path
    # that crosses a Griever, as long as a safe route exists.
    danger_penalty = risk_penalty(grid)
    expanded = 0
    sequence = 0

    while open_heap:
        _, current_cost, _, current = heapq.heappop(open_heap)
        if current_cost != g_score.get(current):
            continue
        expanded += 1
        if current == goal:
            break

        for nxt in get_neighbors(grid, current):
            enters_griever = grid[nxt[0]][nxt[1]] == 5
            move_cost = 1.0 + (danger_penalty if enters_griever else 0.0)
            tentative_g = current_cost + move_cost
            if tentative_g < g_score.get(nxt, float('inf')):
                came_from[nxt] = current
                g_score[nxt] = tentative_g
                priority = tentative_g + manhattan(nxt, goal)
                sequence += 1
                heapq.heappush(open_heap, (priority, tentative_g, sequence, nxt))

    if goal not in g_score:
        raise ValueError('No A* route found to the exit.')

    path: List[Coord] = []
    cur: Coord | None = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()

    danger_hits = sum(1 for r, c in path if grid[r][c] == 5)
    total_cost = len(path) - 1 + danger_hits * danger_penalty
    return {
        'path': path,
        'steps': len(path) - 1,
        'danger_hits': danger_hits,
        'total_cost': total_cost,
        'nodes_expanded': expanded,
        'algorithm': 'A*',
    }
