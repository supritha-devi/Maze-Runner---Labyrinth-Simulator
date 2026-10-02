from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

Coord = Tuple[int, int]
Direction = Tuple[float, float]


def render_first_person(
    grid: List[List[int]],
    position: Coord,
    direction: Direction,
    route: Sequence[Coord] = (),
    dead: bool = False,
    width: int = 800,
    height: int = 500,
) -> Image.Image:
    if not grid or not grid[0]:
        raise ValueError('Maze grid cannot be empty.')
    if width < 320 or height < 240:
        raise ValueError('3D viewport must be at least 320 by 240 pixels.')

    rows, cols = len(grid), len(grid[0])
    px, py = position[1] + 0.5, position[0] + 0.5
    dx, dy = direction
    length = math.hypot(dx, dy)
    if length == 0:
        raise ValueError('View direction cannot be zero.')
    dx, dy = dx / length, dy / length
    plane_x, plane_y = -dy * 0.66, dx * 0.66

    image = Image.new('RGB', (width, height), '#080B10')
    draw = ImageDraw.Draw(image)
    horizon = int(height * 0.43)

    # Cold, dim light fades into fog along the corridor.
    for y in range(horizon):
        t = y / max(horizon, 1)
        color = (int(15 + 11 * t), int(25 + 16 * t), int(35 + 20 * t))
        draw.line((0, y, width, y), fill=color)
    for y in range(horizon, height):
        t = (y - horizon) / max(height - horizon, 1)
        shade = int(18 + 22 * t)
        draw.line((0, y, width, y), fill=(shade, shade + 3, shade + 5))

    # Rasterize the stone floor in perspective, with worn slab joints and haze.
    camera_x = [-1.0 + 2.0 * (x + 0.5) / width for x in range(width)]
    ray_dirs = [(dx + plane_x * cx, dy + plane_y * cx) for cx in camera_x]
    floor_pixels = image.load()
    for y in range(horizon + 1, height, 2):
        depth = (0.5 * height) / (y - horizon)
        for x in range(0, width, 2):
            ray_x, ray_y = ray_dirs[x]
            world_x = px + ray_x * depth
            world_y = py + ray_y * depth
            cell_x, cell_y = math.floor(world_x), math.floor(world_y)
            if 0 <= cell_x < cols and 0 <= cell_y < rows and grid[cell_y][cell_x] == 1:
                base = 23
            else:
                seam = min(world_x % 1, 1 - world_x % 1, world_y % 1, 1 - world_y % 1)
                base = 40 if seam < 0.035 else 48
                if (cell_x + cell_y) % 2:
                    base -= 4
            fog = min(0.72, depth / 18)
            shade = int(base * (1 - fog) + 25 * fog)
            color = (shade, shade + 2, shade + 4)
            for fy in range(y, min(y + 2, height)):
                for fx in range(x, min(x + 2, width)):
                    floor_pixels[fx, fy] = color

    z_buffer = [float('inf')] * width
    strip_width = 2
    view_distance = 32

    # Cast one DDA ray per two screen pixels; continuous vertical slices form walls.
    for x in range(0, width, strip_width):
        ray_x, ray_y = ray_dirs[x]
        map_x, map_y = int(px), int(py)
        delta_x = abs(1 / ray_x) if ray_x else float('inf')
        delta_y = abs(1 / ray_y) if ray_y else float('inf')
        step_x = 1 if ray_x >= 0 else -1
        step_y = 1 if ray_y >= 0 else -1
        side_x = (map_x + 1 - px) * delta_x if step_x > 0 else (px - map_x) * delta_x
        side_y = (map_y + 1 - py) * delta_y if step_y > 0 else (py - map_y) * delta_y
        side = 0
        hit_x, hit_y = map_x, map_y
        distance = 0.0

        for _ in range(view_distance * 4):
            if side_x < side_y:
                side_x += delta_x
                map_x += step_x
                side = 0
                distance = side_x - delta_x
            else:
                side_y += delta_y
                map_y += step_y
                side = 1
                distance = side_y - delta_y

            if not (0 <= map_x < cols and 0 <= map_y < rows):
                hit_x, hit_y = max(0, min(cols - 1, map_x)), max(0, min(rows - 1, map_y))
                break
            if grid[map_y][map_x] == 1:
                hit_x, hit_y = map_x, map_y
                break
        else:
            continue

        distance = max(0.12, min(distance, view_distance))
        z_buffer[x:min(x + strip_width, width)] = [distance] * min(strip_width, width - x)
        wall_height = min(height * 2, int(height * 0.78 / distance))
        top = max(0, horizon - wall_height // 2)
        bottom = min(height - 1, horizon + wall_height // 2)
        hit_pos = py + distance * ray_y if side == 0 else px + distance * ray_x
        texture_u = hit_pos % 1.0
        if (side == 0 and ray_x > 0) or (side == 1 and ray_y < 0):
            texture_u = 1 - texture_u

        wall_hash = (hit_x * 73856093) ^ (hit_y * 19349663)
        shade = 1.0 if side == 0 else 0.76
        fog = max(0.25, 1 - distance / 27)
        stone = 82 + (wall_hash % 17) + int(11 * math.sin(texture_u * 41 + (wall_hash % 13)))
        stone = int(stone * shade * fog)
        mortar = texture_u < 0.025 or texture_u > 0.975
        if mortar:
            stone = max(12, int(stone * 0.55))
        draw.rectangle((x, top, min(x + strip_width, width - 1), bottom), fill=(stone, int(stone * 1.04), int(stone * 1.08)))

        # Repeating block courses, offset per wall face, read as masonry rather than flat panels.
        course = max(5, wall_height // 4)
        for seam_y in range(top + course, bottom, course):
            if ((seam_y - top) // course + hit_x + hit_y) % 2 == 0:
                draw.line((x, seam_y, min(x + strip_width, width - 1), seam_y), fill=(max(9, stone - 24), max(10, stone - 22), max(12, stone - 19)))
        if texture_u < 0.045:
            draw.line((x, top, x, bottom), fill=(min(150, stone + 25), min(155, stone + 26), min(160, stone + 28)))

    draw = ImageDraw.Draw(image)

    # Visible cell markers are projected as perspective sprites. The Exit is intentionally
    # very bright so the player can always locate the goal in the first-person view.
    sprites = []
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell in (3, 4, 5):
                world_dx, world_dy = c + 0.5 - px, r + 0.5 - py
                determinant = plane_x * dy - dx * plane_y
                inverse_determinant = 1.0 / determinant
                transform_x = inverse_determinant * (dy * world_dx - dx * world_dy)
                transform_y = inverse_determinant * (-plane_y * world_dx + plane_x * world_dy)
                if transform_y > 0.12:
                    sprites.append((transform_y, transform_x, cell))
    sprites.sort(reverse=True)

    for depth, lateral, cell in sprites:
        screen_x = int(width / 2 * (1 + lateral / (depth * 0.72)))
        if not 4 <= screen_x < width - 4:
            continue
        if cell != 4 and depth > z_buffer[screen_x]:
            continue
        if cell == 4:
            size = max(18, min(86, int(height * 0.22 / max(0.4, depth))))
            center_y = horizon + 8
            glow = Image.new('RGBA', (size * 4, size * 4), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.ellipse((0, 0, size * 4, size * 4), fill=(40, 180, 255, 110))
            image.paste(glow, (screen_x - size * 2, center_y - size * 2), glow)
            draw.ellipse((screen_x - size // 2, center_y - size // 2, screen_x + size // 2, center_y + size // 2), fill='#7DE3FF', outline='#EAFBFF', width=2)
            draw.line((screen_x, center_y - 2 * size, screen_x, center_y - size // 2), fill='#7DE3FF', width=3)
            draw.line((screen_x, center_y + size // 2, screen_x, center_y + 2 * size), fill='#7DE3FF', width=3)
            draw.line((screen_x - 2 * size, center_y, screen_x - size // 2, center_y), fill='#7DE3FF', width=3)
            draw.line((screen_x + size // 2, center_y, screen_x + 2 * size, center_y), fill='#7DE3FF', width=3)
        elif cell == 5:
            size = max(10, min(52, int(height * (0.16 if depth < 2 else 0.10) / max(0.5, depth))))
            center_y = horizon + size // 2
            color = '#B8262F'
            draw.ellipse((screen_x - size // 2, center_y - size // 2, screen_x + size // 2, center_y + size // 2), fill=color, outline='#F45A5A', width=max(1, size // 10))
            draw.ellipse((screen_x - size // 3, center_y - size // 3, screen_x + size // 3, center_y + size // 3), fill='#FFCF54')
        else:
            size = max(10, min(46, int(height * 0.12 / max(0.6, depth))))
            center_y = horizon + size // 2
            color = '#66E37B'
            draw.ellipse((screen_x - size // 2, center_y - size // 2, screen_x + size // 2, center_y + size // 2), fill=color, outline='#E2F5FF', width=2)
            draw.line((screen_x, center_y + size // 2, screen_x, center_y + size), fill=color, width=max(1, size // 12))

    draw = ImageDraw.Draw(image, 'RGBA')

    def facing_name(vx: float, vy: float) -> str:
        if abs(vx) > abs(vy):
            return 'EAST' if vx > 0 else 'WEST'
        return 'SOUTH' if vy > 0 else 'NORTH'

    facing = facing_name(dx, dy)
    exit_dx = 0
    exit_dy = 0
    exit_cell = None
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == 4:
                exit_dx = c - position[1]
                exit_dy = r - position[0]
                exit_cell = (r, c)
                break
        if exit_dx or exit_dy:
            break
    exit_relative = 'AHEAD'
    if abs(exit_dx) + abs(exit_dy) > 0:
        dot = exit_dx * dx + exit_dy * dy
        cross = exit_dx * dy - exit_dy * dx
        if dot > 0.3:
            exit_relative = 'AHEAD'
        elif cross > 0.3:
            exit_relative = 'LEFT'
        elif cross < -0.3:
            exit_relative = 'RIGHT'
        else:
            exit_relative = 'BEHIND'
    exit_distance = abs(exit_dx) + abs(exit_dy)

    # Surveillance reticle, restrained scanlines, and HUD establish the research-facility mood.
    for y in range(1, height, 4):
        draw.line((0, y, width, y), fill=(2, 5, 8, 24), width=1)
    reticle_x, reticle_y = width // 2, horizon
    draw.line((reticle_x - 11, reticle_y, reticle_x - 4, reticle_y), fill=(177, 218, 230, 170), width=1)
    draw.line((reticle_x + 4, reticle_y, reticle_x + 11, reticle_y), fill=(177, 218, 230, 170), width=1)
    draw.line((reticle_x, reticle_y - 11, reticle_x, reticle_y - 4), fill=(177, 218, 230, 170), width=1)
    draw.line((reticle_x, reticle_y + 4, reticle_x, reticle_y + 11), fill=(177, 218, 230, 170), width=1)
    draw.rectangle((14, 14, 226, 44), fill=(5, 10, 14, 208), outline=(100, 143, 161, 175), width=1)
    draw.text((25, 22), 'W.C.K.D.  //  LIVE FEED', fill='#A9C3CF')
    draw.rounded_rectangle((14, height - 70, 330, height - 39), radius=5, fill=(4, 18, 28, 225), outline=(64, 190, 238, 230), width=2)
    draw.text((25, height - 61), f'EXIT  {exit_relative}  //  {exit_distance} STEPS', fill='#8FE6FF')
    draw.text((350, height - 61), f'FACING: {facing}', fill='#D8F1FF')
    draw.text((20, height - 30), 'ONE KEY PRESS = ONE CAREFUL STEP', fill='#A5BBCB')
    if dead:
        draw.rectangle((width // 2 - 190, height // 2 - 28, width // 2 + 190, height // 2 + 28), fill=(50, 5, 9, 220), outline=(242, 50, 62, 255), width=2)
        draw.text((width // 2 - 105, height // 2 - 8), 'SUBJECT LOST // GRIEVER CONTACT', fill='#FF737C')

    # A compact overhead inset preserves context and lets viewers compare the planned route.
    inset_size = min(220, height // 2)
    inset_pad = 14
    inset_x = width - inset_size - inset_pad
    inset_y = inset_pad
    draw.rectangle((inset_x - 4, inset_y - 4, inset_x + inset_size + 4, inset_y + inset_size + 21), fill=(4, 8, 12, 225), outline=(116, 151, 165, 210), width=1)
    draw.text((inset_x + 5, inset_y + inset_size + 3), 'SECTOR MAP  //  BLUE = EXIT', fill='#A9C3CF')
    map_image = Image.new('RGB', (inset_size, inset_size), '#090D12')
    map_draw = ImageDraw.Draw(map_image)
    cell_w, cell_h = inset_size / cols, inset_size / rows
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            colors = {0: '#1D2A31', 1: '#697782', 3: '#58D96D', 4: '#48BFFF', 5: '#D52D3A'}
            map_draw.rectangle(
                (int(c * cell_w), int(r * cell_h), int((c + 1) * cell_w + 0.5), int((r + 1) * cell_h + 0.5)),
                fill=colors[cell],
            )
    for r, c in route:
        x, y = int((c + 0.5) * cell_w), int((r + 0.5) * cell_h)
        map_draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill='#65D9FF')
    player_x = int((position[1] + 0.5) * cell_w)
    player_y = int((position[0] + 0.5) * cell_h)
    map_draw.ellipse((player_x - 3, player_y - 3, player_x + 3, player_y + 3), fill='#FFE66D', outline='#FFFFFF', width=1)
    if exit_cell is not None:
        exit_r, exit_c = exit_cell
        exit_x = int((exit_c + 0.5) * cell_w)
        exit_y = int((exit_r + 0.5) * cell_h)
        marker_radius = max(4, int(min(cell_w, cell_h) * 0.65))
        map_draw.ellipse(
            (exit_x - marker_radius, exit_y - marker_radius, exit_x + marker_radius, exit_y + marker_radius),
            fill='#36BFFF',
            outline='#F4FCFF',
            width=2,
        )
        map_draw.line((exit_x - 3, exit_y, exit_x + 3, exit_y), fill='#FFFFFF', width=2)
        map_draw.line((exit_x, exit_y - 3, exit_x, exit_y + 3), fill='#FFFFFF', width=2)
    image.paste(map_image, (inset_x, inset_y))

    draw = ImageDraw.Draw(image)
    draw.line((0, height - 34, width, height - 34), fill='#536875', width=1)
    draw.text((16, height - 24), 'WASD / ARROWS  MOVE', fill='#B5C3C9')
    draw.text((width - 170, height - 24), 'CONCRETE // SECTOR 07', fill='#8CA1AA')

    # Darken the outside edge to suggest a camera housing and corridor vignette.
    for inset in range(0, 28, 4):
        alpha = int(16 * (1 - inset / 32))
        draw.rectangle((inset, inset, width - 1 - inset, height - 1 - inset), outline=(0, 0, 0, alpha), width=4)

    return image.convert('RGB')
