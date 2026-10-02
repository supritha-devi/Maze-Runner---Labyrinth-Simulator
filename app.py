from __future__ import annotations

import tkinter as tk
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageTk

from algorithms import astar_path, bfs_path, risk_penalty
from maze import collapse_corridor, generate_maze_variant, get_start_goal
from maze_view import render_first_person

Coord = Tuple[int, int]


class MazeRunnerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Maze Runner: Labyrinth Simulator')
        self.geometry('1380x900')
        self.minsize(1100, 760)
        self.configure(bg='#090B0F')

        self.current_page = 0
        self.style = {
            'bg': '#090B0F',
            'panel': '#111820',
            'panel_alt': '#1A212B',
            'line': '#233040',
            'text': '#E6EEF8',
            'muted': '#97A8BA',
            'glade': '#7ACB6C',
            'exit': '#5BA9FF',
            'danger': '#D44C4C',
            'warning': '#F4C95D',
            'wall': '#5C6672',
            'path': '#9DD7FF',
            'button_blue': '#3D7CFF',
            'button_green': '#3AA66D',
            'button_red': '#C5554D',
            'button_gray': '#27313B',
        }

        self.maze = generate_maze_variant(25)
        self.start, self.goal = get_start_goal(self.maze)
        self.player_pos = self.start
        self.agent_pos = self.start
        self.view_direction = (0.0, -1.0)
        initial_route = bfs_path(self.maze, self.start, self.goal)['path']
        if len(initial_route) > 1:
            self.face_toward(initial_route[0], initial_route[1])
        self.active_path: List[Coord] = []
        self.traversed_path: List[Coord] = []
        self.explored: set[Coord] = set()
        self.run_mode: Optional[str] = None
        self.human_mode = False
        self.player_dead = False
        self.run_results: Dict[str, dict] = {}
        self.animation_job = None
        self.turn_target_position: Optional[Coord] = None
        self.turn_frames_remaining = 0
        self.turn_angle_delta = 0.0
        self.render_job = None
        self.animation_index = 0
        self.turn_target_position = None
        self.turn_frames_remaining = 0
        self.night_shift_used = False
        self.log_text = []

        self.build_header()
        self.build_content()
        self.build_navigation()

        self.show_page(0)
        self.bind_keys()

    def build_header(self):
        self.header = tk.Frame(self, bg=self.style['bg'])
        self.header.pack(fill='x', padx=20, pady=(18, 10))

        badge = tk.Label(
            self.header,
            text='W.C.K.D. // LABYRINTH SIMULATOR',
            bg='#0E151D',
            fg='#F6A752',
            font=('Segoe UI', 10, 'bold'),
            highlightbackground=self.style['line'],
            highlightthickness=1,
            padx=12,
            pady=6,
        )
        badge.pack(side='left')

        self.progress_label = tk.Label(
            self.header,
            text='Page 1 of 6',
            bg=self.style['bg'],
            fg=self.style['muted'],
            font=('Segoe UI', 10, 'bold'),
        )
        self.progress_label.pack(side='right')

    def build_content(self):
        self.content = tk.Frame(self, bg=self.style['bg'])
        self.content.pack(fill='both', expand=True, padx=20, pady=(0, 14))

        self.pages = [
            self.make_start_page(),
            self.make_story_page(),
            self.make_agent_page(),
            self.make_rules_page(),
            self.make_simulation_page(),
            self.make_analysis_page(),
        ]

    def build_navigation(self):
        self.nav = tk.Frame(self, bg=self.style['bg'])
        self.nav.pack(fill='x', padx=20, pady=(0, 20))

        self.back_button = tk.Button(
            self.nav,
            text='Back',
            command=self.go_back,
            bg='#202A34',
            fg=self.style['text'],
            font=('Segoe UI', 11, 'bold'),
            width=16,
            height=2,
            bd=0,
            relief='flat',
        )
        self.back_button.pack(side='left')

        self.next_button = tk.Button(
            self.nav,
            text='Next',
            command=self.go_next,
            bg=self.style['button_blue'],
            fg='#F4F8FF',
            font=('Segoe UI', 11, 'bold'),
            width=16,
            height=2,
            bd=0,
            relief='flat',
        )
        self.next_button.pack(side='right')

    def bind_keys(self):
        self.bind('<Up>', lambda e: self.human_move('forward'))
        self.bind('<Down>', lambda e: self.human_move('back'))
        self.bind('<Left>', lambda e: self.human_move('turn_left'))
        self.bind('<Right>', lambda e: self.human_move('turn_right'))
        self.bind('w', lambda e: self.human_move('forward'))
        self.bind('s', lambda e: self.human_move('back'))
        self.bind('a', lambda e: self.human_move('turn_left'))
        self.bind('d', lambda e: self.human_move('turn_right'))
        self.bind('q', lambda e: self.human_move('turn_left'))
        self.bind('e', lambda e: self.human_move('turn_right'))

    def make_start_page(self):
        frame = tk.Frame(self.content, bg=self.style['bg'])
        inner = tk.Frame(frame, bg=self.style['bg'])
        inner.pack(expand=True)

        title = tk.Label(
            inner,
            text='MAZE RUNNER',
            bg=self.style['bg'],
            fg=self.style['text'],
            font=('Segoe UI', 34, 'bold'),
        )
        title.pack(pady=(30, 8))

        sub = tk.Label(
            inner,
            text='Labyrinth Simulator',
            bg=self.style['bg'],
            fg=self.style['muted'],
            font=('Segoe UI', 17, 'bold'),
        )
        sub.pack(pady=(0, 18))

        panel = tk.Frame(
            inner,
            bg=self.style['panel'],
            highlightbackground=self.style['line'],
            highlightthickness=2,
            padx=18,
            pady=18,
        )
        panel.pack(fill='x', padx=30, pady=10)

        cover_path = Path(__file__).resolve().parent / 'assets' / 'front_cover.jpg'
        cover_image = None
        if cover_path.exists():
            try:
                image = Image.open(cover_path)
                image = image.resize((720, 388), Image.LANCZOS)
                cover_image = ImageTk.PhotoImage(image)
            except Exception:
                cover_image = None

        if cover_image is not None:
            cover_label = tk.Label(panel, image=cover_image, bg=self.style['panel'])
            cover_label.image = cover_image
            cover_label.pack(pady=(0, 10))
        else:
            art = tk.Label(
                panel,
                text='[  LABYRINTH  ]\n\n   ╔═╗\n  ║ ░║\n   ╚═╝\n\n GLADE / EXIT',
                bg=self.style['panel'],
                fg='#7CC9FF',
                font=('Consolas', 18, 'bold'),
                justify='center',
            )
            art.pack(pady=10)

        start_btn = tk.Button(
            panel,
            text='Start',
            command=lambda: self.show_page(1),
            bg=self.style['button_blue'],
            fg='#FFFFFF',
            font=('Segoe UI', 13, 'bold'),
            width=18,
            height=2,
            bd=0,
            relief='flat',
        )
        start_btn.pack(pady=(10, 0))

        jump_btn = tk.Button(
            panel,
            text='Open Simulation',
            command=lambda: self.show_page(4),
            bg=self.style['button_green'],
            fg='#FFFFFF',
            font=('Segoe UI', 11, 'bold'),
            width=18,
            height=2,
            bd=0,
            relief='flat',
        )
        jump_btn.pack(pady=(8, 0))
        return frame

    def make_story_page(self):
        frame = tk.Frame(self.content, bg=self.style['bg'])
        panel = tk.Frame(frame, bg=self.style['panel'], highlightbackground=self.style['line'], highlightthickness=2, padx=30, pady=24)
        panel.pack(fill='both', expand=True, padx=30, pady=20)

        title = tk.Label(panel, text='The Maze Awakens', bg=self.style['panel'], fg=self.style['text'], font=('Segoe UI', 26, 'bold'))
        title.pack(anchor='w', pady=(0, 14))

        story = (
            'You wake in the Glade with no memory, trapped inside a shifting Labyrinth. '
            'Runners move before dawn and risk the Grievers in the dark. W.C.K.D. watches every move.\n\n'
            'This is not a game for comfort. It is a test of decision-making: some paths are fast, but danger is always hidden in plain sight.\n\n'
            'Your job is simple: move from the Glade to the Exit, survive the night, and decide whether speed or judgment wins.'
        )
        tk.Label(panel, text=story, bg=self.style['panel'], fg=self.style['text'], justify='left', wraplength=980, font=('Segoe UI', 12), padx=4).pack(anchor='w')
        tk.Button(
            panel,
            text='Open Simulation',
            command=lambda: self.show_page(4),
            bg=self.style['button_blue'],
            fg='#FFFFFF',
            font=('Segoe UI', 11, 'bold'),
            width=18,
            height=2,
            bd=0,
            relief='flat',
        ).pack(anchor='w', pady=(18, 0))
        return frame

    def make_agent_page(self):
        frame = tk.Frame(self.content, bg=self.style['bg'])
        panel = tk.Frame(frame, bg=self.style['panel'], highlightbackground=self.style['line'], highlightthickness=2, padx=28, pady=24)
        panel.pack(fill='both', expand=True, padx=30, pady=20)

        tk.Label(panel, text='Meet Thomas', bg=self.style['panel'], fg=self.style['text'], font=('Segoe UI', 26, 'bold')).pack(anchor='w')
        tk.Label(
            panel,
            text='Thomas is the AI agent. An agent is just a system that senses the world, interprets what it sees, and chooses actions to reach a goal. He does not control the maze; he reads the maze and decides which route is best.',
            bg=self.style['panel'],
            fg=self.style['text'],
            justify='left',
            wraplength=980,
            font=('Segoe UI', 12),
            pady=12,
        ).pack(anchor='w')
        tk.Label(
            panel,
            text='In this demo, we watch Thomas think in real time. Each move is a decision: wall, corridor, shortcut, danger, or safe detour. The maze is not solved by luck — it is solved by strategy.',
            bg=self.style['panel'],
            fg=self.style['text'],
            justify='left',
            wraplength=980,
            font=('Segoe UI', 12),
        ).pack(anchor='w')
        return frame

    def make_algorithms_page(self):
        frame = tk.Frame(self.content, bg=self.style['bg'])
        panel = tk.Frame(frame, bg=self.style['panel'], highlightbackground=self.style['line'], highlightthickness=2, padx=28, pady=24)
        panel.pack(fill='both', expand=True, padx=30, pady=20)

        tk.Label(panel, text='Simulation Brief', bg=self.style['panel'], fg=self.style['text'], font=('Segoe UI', 26, 'bold')).pack(anchor='w')
        tk.Label(
            panel,
            text='The full comparison explanation appears on the final results page after both agents have run. This page keeps the flow focused on the simulation itself.',
            bg=self.style['panel'],
            fg=self.style['text'],
            justify='left',
            wraplength=980,
            font=('Segoe UI', 12),
            pady=12,
        ).pack(anchor='w')
        return frame

    def make_rules_page(self):
        frame = tk.Frame(self.content, bg=self.style['bg'])
        panel = tk.Frame(frame, bg=self.style['panel'], highlightbackground=self.style['line'], highlightthickness=2, padx=28, pady=24)
        panel.pack(fill='both', expand=True, padx=30, pady=20)

        rules_header = tk.Frame(panel, bg=self.style['panel'])
        rules_header.pack(fill='x', pady=(0, 8))
        tk.Label(rules_header, text='How to Play', bg=self.style['panel'], fg=self.style['text'], font=('Segoe UI', 26, 'bold')).pack(side='left')
        tk.Button(
            rules_header,
            text='Open Simulation',
            command=lambda: self.show_page(4),
            bg=self.style['button_blue'],
            fg='#FFFFFF',
            font=('Segoe UI', 10, 'bold'),
            padx=14,
            pady=8,
            bd=0,
            relief='flat',
            cursor='hand2',
        ).pack(side='right', padx=(12, 0))

        rules = [
            '1. Choose BFS or A* to run the algorithm automatically from the Glade to the Exit.',
            '2. The maze contains concrete walls, open corridors, the Glade (start), the Exit, and lethal Grievers. Touching a Griever ends Human Play. A* prefers a Griever-free route whenever one exists, even if it is longer.',
            '3. Night Shift can collapse one corridor during a run; the active agent immediately reroutes from its current position.',
            '4. Refresh creates a new maze and clears all stats for a fresh run.',
            '5. Human Play lets you move using arrow keys or WASD and finish the maze yourself.',
            '6. The simulation uses a first-person 3D corridor view and a live telemetry log. The agent follows grid cells and cannot enter a wall.',
        ]

        for rule in rules:
            tk.Label(panel, text=rule, bg=self.style['panel'], fg=self.style['text'], justify='left', wraplength=980, font=('Segoe UI', 12), pady=6).pack(anchor='w')

        color_box = tk.Frame(panel, bg=self.style['panel_alt'], highlightbackground=self.style['line'], highlightthickness=1, padx=14, pady=12)
        color_box.pack(fill='x', pady=(14, 0))
        tk.Label(color_box, text='Legend', bg=self.style['panel_alt'], fg=self.style['warning'], font=('Segoe UI', 14, 'bold')).pack(anchor='w')

        legend = [
            ('Glade', self.style['glade']),
            ('Exit', self.style['exit']),
            ('Griever', self.style['danger']),
            ('Wall', self.style['wall']),
            ('Path', self.style['path']),
        ]
        for label, color in legend:
            row = tk.Frame(color_box, bg=self.style['panel_alt'])
            row.pack(fill='x', pady=4)
            tk.Label(row, text='■', bg=self.style['panel_alt'], fg=color, font=('Segoe UI', 18, 'bold')).pack(side='left')
            tk.Label(row, text=label, bg=self.style['panel_alt'], fg=self.style['text'], font=('Segoe UI', 11)).pack(side='left', padx=(8, 0))

        return frame

    def make_simulation_page(self):
        frame = tk.Frame(self.content, bg=self.style['bg'])

        view_frame = tk.Frame(frame, bg='#070A0E', highlightbackground='#334550', highlightthickness=2)
        view_frame.pack(side='left', fill='both', expand=True, padx=(0, 18))
        self.viewport = tk.Label(view_frame, bg='#070A0E', bd=0, anchor='center')
        self.viewport.pack(fill='both', expand=True)
        self.viewport.bind('<Configure>', self.schedule_view_render)

        side = tk.Frame(frame, bg=self.style['bg'], width=290)
        side.pack(side='right', fill='y')

        controls = tk.Frame(side, bg=self.style['panel'], highlightbackground=self.style['line'], highlightthickness=2, padx=12, pady=12)
        controls.pack(fill='x', pady=(0, 12))
        tk.Label(controls, text='Controls', bg=self.style['panel'], fg=self.style['text'], font=('Segoe UI', 16, 'bold')).pack(anchor='w')

        buttons = [
            ('Run BFS', lambda: self.run_algorithm('BFS'), self.style['warning']),
            ('Run A*', lambda: self.run_algorithm('A*'), '#A5E3FF'),
            ('Human Play', self.enable_human_mode, '#55C57E'),
            ('Night Shift', self.trigger_night_shift, '#D86C61'),
            ('Refresh', self.refresh_maze, '#2F3C49'),
        ]

        for text, command, color in buttons:
            btn = tk.Button(
                controls,
                text=text,
                command=command,
                bg=color,
                fg='#111111' if color not in ('#2F3C49', '#D86C61', '#55C57E') else '#F7F9FB',
                font=('Segoe UI', 11, 'bold'),
                width=18,
                height=2,
                bd=0,
                relief='flat',
            )
            btn.pack(fill='x', pady=6)

        log_frame = tk.Frame(side, bg=self.style['panel'], highlightbackground=self.style['line'], highlightthickness=2, padx=12, pady=12)
        log_frame.pack(fill='both', expand=True)
        tk.Label(log_frame, text='Telemetry Log', bg=self.style['panel'], fg=self.style['text'], font=('Segoe UI', 16, 'bold')).pack(anchor='w')

        self.log = tk.Text(log_frame, bg='#0B0F14', fg=self.style['text'], height=15, wrap='word', font=('Consolas', 10))
        self.log.pack(fill='both', expand=True, pady=(8, 0))

        self.log_message('System online. Maze ready.')
        self.render_maze()
        return frame

    def make_analysis_page(self):
        frame = tk.Frame(self.content, bg=self.style['bg'])
        panel = tk.Frame(frame, bg=self.style['panel'], highlightbackground=self.style['line'], highlightthickness=2, padx=28, pady=24)
        panel.pack(fill='both', expand=True, padx=30, pady=20)

        tk.Label(panel, text='Comparison & What We Learned', bg=self.style['panel'], fg=self.style['text'], font=('Segoe UI', 30, 'bold')).pack(anchor='w')

        self.result_text = tk.Label(panel, text='Run both agents to compare their results.', bg=self.style['panel'], fg=self.style['text'], justify='left', wraplength=980, font=('Segoe UI', 12))
        self.result_text.pack(anchor='w', pady=(12, 12))

        table = tk.Frame(panel, bg=self.style['panel_alt'], highlightbackground=self.style['line'], highlightthickness=1)
        table.pack(fill='x', pady=(8, 18))

        headers = ['Metric', 'BFS', 'A*']
        for idx, header in enumerate(headers):
            tk.Label(table, text=header, bg=self.style['panel_alt'], fg=self.style['warning'], font=('Segoe UI', 11, 'bold'), width=18, anchor='center').grid(row=0, column=idx, padx=8, pady=8)

        self.metric_steps = tk.Label(table, text='Steps', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.metric_steps.grid(row=1, column=0, padx=8, pady=6)
        self.bfs_steps = tk.Label(table, text='--', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.bfs_steps.grid(row=1, column=1, padx=8, pady=6)
        self.astar_steps = tk.Label(table, text='--', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.astar_steps.grid(row=1, column=2, padx=8, pady=6)

        self.metric_danger = tk.Label(table, text='Griever hits', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.metric_danger.grid(row=2, column=0, padx=8, pady=6)
        self.bfs_danger = tk.Label(table, text='--', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.bfs_danger.grid(row=2, column=1, padx=8, pady=6)
        self.astar_danger = tk.Label(table, text='--', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.astar_danger.grid(row=2, column=2, padx=8, pady=6)

        self.metric_cost = tk.Label(table, text='Risk-weighted cost', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.metric_cost.grid(row=3, column=0, padx=8, pady=6)
        self.bfs_cost = tk.Label(table, text='--', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.bfs_cost.grid(row=3, column=1, padx=8, pady=6)
        self.astar_cost = tk.Label(table, text='--', bg=self.style['panel_alt'], fg=self.style['text'], width=18, anchor='center')
        self.astar_cost.grid(row=3, column=2, padx=8, pady=6)

        explainer = tk.Frame(panel, bg=self.style['panel'], highlightbackground=self.style['line'], highlightthickness=1, padx=16, pady=16)
        explainer.pack(fill='x', pady=(10, 0))
        tk.Label(explainer, text='BFS vs A* — what the numbers mean', bg=self.style['panel'], fg=self.style['warning'], font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        tk.Label(
            explainer,
            text='BFS is the blind baseline. It expands the maze in layers and stops as soon as it finds the Exit, so it prefers the shortest route in step count. It does not factor danger, so a corridor with a Griever looks just like any other open path.\n\nA* is the informed agent. It uses the distance to the goal and adds a penalty for danger. That means it may choose a longer route if the shorter route crosses a Griever or a collapsing section. This is why A* may look less efficient in pure steps but is better when safety matters.\n\nNight Shift proves the agent can adapt to a changing maze instead of memorizing one fixed route. The best agent is not the one that is fastest at all costs — it is the one that reaches the goal safely while reacting to new conditions.',
            bg=self.style['panel'],
            fg=self.style['text'],
            justify='left',
            wraplength=930,
            font=('Segoe UI', 12),
        ).pack(anchor='w', pady=(8, 0))

        tk.Label(panel, text='The core lesson is simple: a good agent does not only move quickly. It weighs danger, adapts to change, and reroutes when the maze itself shifts underfoot.', bg=self.style['panel'], fg=self.style['text'], justify='left', wraplength=980, font=('Segoe UI', 12)).pack(anchor='w', pady=(10, 0))
        return frame

    def show_page(self, index: int):
        self.current_page = index
        for page in self.pages:
            page.pack_forget()
        self.pages[index].pack(fill='both', expand=True)
        self.progress_label.config(text=f'Page {index + 1} of {len(self.pages)}')

        if index == 3:
            self.back_button.config(state='normal')
            self.next_button.config(text='Open Simulation')
        elif index == 4:
            self.back_button.config(state='normal')
            self.next_button.config(text='View Results')
        else:
            self.back_button.config(state='normal' if index > 0 else 'disabled')
            self.next_button.config(text='Next' if index < len(self.pages) - 1 else 'Finish')

    def go_back(self):
        if self.current_page > 0:
            self.show_page(self.current_page - 1)

    def go_next(self):
        if self.current_page < len(self.pages) - 1:
            self.show_page(self.current_page + 1)
        else:
            self.show_page(0)

    def log_message(self, msg: str):
        self.log_text.append(msg)
        if hasattr(self, 'log'):
            self.log.insert('end', msg + '\n')
            self.log.see('end')

    def schedule_view_render(self, _event=None):
        if self.render_job is not None:
            self.after_cancel(self.render_job)
        self.render_job = self.after(80, self.render_maze)

    def render_maze(self):
        self.render_job = None
        if not hasattr(self, 'viewport'):
            return

        view_width = self.viewport.winfo_width()
        view_height = self.viewport.winfo_height()
        if view_width < 320 or view_height < 240:
            view_width, view_height = 800, 500
        width = max(640, min(1100, view_width - 12))
        height = max(400, min(760, view_height - 12))
        position = self.player_pos if self.human_mode else self.agent_pos
        image = render_first_person(
            self.maze,
            position,
            self.view_direction,
            route=self.active_path,
            dead=self.player_dead,
            width=width,
            height=height,
        )
        self.viewport_image = ImageTk.PhotoImage(image)
        self.viewport.config(image=self.viewport_image)

    def run_algorithm(self, algorithm: str):
        self.human_mode = False
        self.player_dead = False
        self.run_mode = algorithm
        self.agent_pos = self.start
        self.active_path = []
        self.traversed_path = [self.start]
        self.explored = set()
        self.animation_index = 0
        self.turn_target_position = None
        self.turn_frames_remaining = 0
        self.turn_angle_delta = 0.0
        self.night_shift_used = False

        if self.animation_job is not None:
            self.after_cancel(self.animation_job)
            self.animation_job = None

        if algorithm == 'BFS':
            result = bfs_path(self.maze, self.start, self.goal)
        else:
            result = astar_path(self.maze, self.start, self.goal)

        self.run_results[algorithm] = result
        self.active_path = result['path']
        if len(self.active_path) > 1:
            self.face_toward(self.active_path[0], self.active_path[1])
        self.explored = set(self.active_path)
        self.log_message(f'{algorithm} route found. Steps: {result["steps"]}, danger: {result["danger_hits"]}, total cost: {result["total_cost"]}.')
        self.update_results_page()
        self.render_maze()
        self.animate_agent()

    def animate_agent(self):
        if not self.active_path:
            return

        if self.turn_frames_remaining:
            current_angle = math.atan2(self.view_direction[1], self.view_direction[0])
            remaining = self.turn_frames_remaining
            angle_step = self.turn_angle_delta / remaining
            self.view_direction = (
                math.cos(current_angle + angle_step),
                math.sin(current_angle + angle_step),
            )
            self.turn_angle_delta -= angle_step
            self.turn_frames_remaining -= 1
            self.render_maze()
            self.animation_job = self.after(150, self.animate_agent)
            return

        if self.animation_index < len(self.active_path) - 1:
            next_position = self.active_path[self.animation_index + 1]
            if self.maze[next_position[0]][next_position[1]] == 1:
                raise RuntimeError(f'{self.run_mode} route attempted to enter a wall at {next_position}.')

            desired_direction = (
                float(next_position[1] - self.agent_pos[1]),
                float(next_position[0] - self.agent_pos[0]),
            )
            current_angle = math.atan2(self.view_direction[1], self.view_direction[0])
            target_angle = math.atan2(desired_direction[1], desired_direction[0])
            angle_delta = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi

            if abs(angle_delta) > 0.01:
                self.turn_target_position = next_position
                self.turn_angle_delta = angle_delta
                self.turn_frames_remaining = 8
                turn = 'right' if angle_delta > 0 else 'left'
                direction_name = self.direction_name(desired_direction)
                self.log_message(f'Turning {turn} to face {direction_name}.')
                self.animation_job = self.after(180, self.animate_agent)
                return

            self.animation_index += 1
            self.agent_pos = next_position
            self.traversed_path.append(next_position)
            self.explored = set(self.active_path[: self.animation_index + 1])
            direction_name = self.direction_name(desired_direction)
            self.log_message(f'Step {self.animation_index}: moving {direction_name}.')
            self.render_maze()
            self.animation_job = self.after(1400, self.animate_agent)
        else:
            self.record_executed_route()
            self.log_message(f'{self.run_mode} reached the Exit.')
            self.animation_job = None

    @staticmethod
    def direction_name(direction: Coord | Tuple[float, float]) -> str:
        dx, dy = direction
        if abs(dx) > abs(dy):
            return 'EAST' if dx > 0 else 'WEST'
        return 'SOUTH' if dy > 0 else 'NORTH'

    def record_executed_route(self):
        if self.run_mode not in ('BFS', 'A*') or not self.traversed_path:
            return
        danger_hits = sum(1 for r, c in self.traversed_path if self.maze[r][c] == 5)
        self.run_results[self.run_mode] = {
            'path': list(self.traversed_path),
            'steps': len(self.traversed_path) - 1,
            'danger_hits': danger_hits,
            'total_cost': len(self.traversed_path) - 1 + danger_hits * risk_penalty(self.maze),
            'nodes_expanded': self.run_results.get(self.run_mode, {}).get('nodes_expanded', 0),
            'algorithm': self.run_mode,
        }
        self.update_results_page()

    def enable_human_mode(self):
        self.human_mode = True
        self.player_dead = False
        self.run_mode = 'Human'
        self.agent_pos = self.start
        self.player_pos = self.start
        self.active_path = []
        self.traversed_path = []
        self.explored = set()
        try:
            preview = bfs_path(self.maze, self.start, self.goal)['path']
            if len(preview) > 1:
                self.face_toward(preview[0], preview[1])
        except ValueError:
            self.view_direction = (0.0, -1.0)
        self.log_message('Human mode enabled. Use arrow keys or WASD to move.')
        self.render_maze()

    def face_toward(self, source: Coord, destination: Coord):
        self.view_direction = (
            float(destination[1] - source[1]),
            float(destination[0] - source[0]),
        )

    def human_move(self, action: str):
        if not self.human_mode or self.player_dead:
            return

        dx, dy = self.view_direction
        if abs(dx) < 0.01 and abs(dy) < 0.01:
            dx, dy = 1.0, 0.0

        if action == 'turn_left':
            self.view_direction = (dy, -dx)
            self.render_maze()
            return
        if action == 'turn_right':
            self.view_direction = (-dy, dx)
            self.render_maze()
            return

        forward_dx = 1.0 if abs(dx) > abs(dy) else 0.0
        forward_dy = 0.0 if abs(dx) > abs(dy) else 1.0
        if abs(dx) > abs(dy):
            if dx < 0:
                forward_dx = -1.0
        else:
            if dy < 0:
                forward_dy = -1.0

        if action == 'back':
            forward_dx *= -1.0
            forward_dy *= -1.0

        dr = int(round(forward_dy))
        dc = int(round(forward_dx))
        r, c = self.player_pos
        nr, nc = r + dr, c + dc

        if 0 <= nr < len(self.maze) and 0 <= nc < len(self.maze[0]):
            if self.maze[nr][nc] == 1:
                self.log_message('The wall blocks the corridor. The runner turns and reassesses.')
                self.render_maze()
                return
            self.face_toward((r, c), (nr, nc))
            self.player_pos = (nr, nc)
            if self.maze[nr][nc] == 5:
                self.player_dead = True
                self.log_message('GRIEVER CONTACT. Runner eliminated. Refresh the maze to try again.')
                self.render_maze()
                return
            self.log_message(f'Human runner moved to ({nr}, {nc}).')
            self.explored.add(self.player_pos)
            self.render_maze()
            if self.player_pos == self.goal:
                self.log_message('The human player reaches the Exit.')
                self.human_mode = False
                self.run_mode = 'Human'

    def move_player(self, dr: int, dc: int):
        if not self.human_mode or self.player_dead:
            return

        r, c = self.player_pos
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(self.maze) and 0 <= nc < len(self.maze[0]):
            if self.maze[nr][nc] == 1:
                return
            self.face_toward((r, c), (nr, nc))
            self.player_pos = (nr, nc)
            if self.maze[nr][nc] == 5:
                self.player_dead = True
                self.log_message('GRIEVER CONTACT. Runner eliminated. Refresh the maze to try again.')
                self.render_maze()
                return
            self.log_message(f'Human runner moved to ({nr}, {nc}).')
            self.explored.add(self.player_pos)
            self.render_maze()
            if self.player_pos == self.goal:
                self.log_message('The human player reaches the Exit.')
                self.human_mode = False
                self.run_mode = 'Human'

    def trigger_night_shift(self):
        if not self.run_mode or self.run_mode == 'Human':
            self.log_message('Start a BFS or A* run before triggering Night Shift.')
            return
        if self.night_shift_used:
            self.log_message('Night Shift has already been used for this run. Start a new run to trigger it again.')
            return

        current = self.agent_pos
        # Pick a future cell on the actual planned route, not a random corridor elsewhere.
        candidates = [
            cell
            for cell in self.active_path[self.animation_index + 1:]
            if cell != self.goal and self.maze[cell[0]][cell[1]] == 0
        ]
        if not candidates:
            self.log_message('No untraveled open corridor remains on this route to collapse.')
            return

        planner = bfs_path if self.run_mode == 'BFS' else astar_path
        collapse_cell = None
        replanned_result = None
        for candidate in candidates:
            original_cell = self.maze[candidate[0]][candidate[1]]
            self.maze[candidate[0]][candidate[1]] = 1
            try:
                trial = planner(self.maze, current, self.goal)
            except ValueError:
                trial = None
            finally:
                self.maze[candidate[0]][candidate[1]] = original_cell

            if trial is not None and len(trial['path']) > 1:
                collapse_cell = candidate
                replanned_result = trial
                break

        if collapse_cell is None or replanned_result is None:
            self.log_message('Night Shift could not find a future corridor whose collapse leaves a route to the Exit.')
            return

        if self.animation_job is not None:
            self.after_cancel(self.animation_job)
            self.animation_job = None

        if not collapse_corridor(self.maze, collapse_cell):
            raise RuntimeError(f'Night Shift selected a cell that could not be collapsed: {collapse_cell}')

        self.night_shift_used = True
        self.log_message(
            f'Night Shift: corridor {collapse_cell} collapsed ahead. Re-planning from current position {current}.'
        )
        previous_expansions = self.run_results[self.run_mode]['nodes_expanded']
        self.active_path = replanned_result['path']
        forecast_path = self.traversed_path + self.active_path[1:]
        forecast_danger = sum(1 for r, c in forecast_path if self.maze[r][c] == 5)
        self.run_results[self.run_mode] = {
            'path': forecast_path,
            'steps': len(forecast_path) - 1,
            'danger_hits': forecast_danger,
            'total_cost': len(forecast_path) - 1 + forecast_danger * risk_penalty(self.maze),
            'nodes_expanded': previous_expansions + replanned_result['nodes_expanded'],
            'algorithm': self.run_mode,
        }
        self.explored.update(self.active_path)
        self.animation_index = 0
        self.render_maze()
        self.update_results_page()
        self.animate_agent()

    def refresh_maze(self):
        if self.animation_job is not None:
            self.after_cancel(self.animation_job)
            self.animation_job = None

        self.maze = generate_maze_variant(25)
        self.start, self.goal = get_start_goal(self.maze)
        self.player_pos = self.start
        self.agent_pos = self.start
        self.view_direction = (0.0, -1.0)
        initial_route = bfs_path(self.maze, self.start, self.goal)['path']
        if len(initial_route) > 1:
            self.face_toward(initial_route[0], initial_route[1])
        self.active_path = []
        self.traversed_path = []
        self.explored = set()
        self.run_mode = None
        self.human_mode = False
        self.player_dead = False
        self.run_results = {}
        self.animation_index = 0
        self.night_shift_used = False
        self.log_message('Fresh maze generated. New run ready.')
        self.render_maze()
        self.update_results_page()

    def update_results_page(self):
        bfs = self.run_results.get('BFS')
        ast = self.run_results.get('A*')
        if bfs is None and ast is None:
            self.result_text.config(text='Run both agents to compare their results.')
            self.bfs_steps.config(text='--')
            self.astar_steps.config(text='--')
            self.bfs_danger.config(text='--')
            self.astar_danger.config(text='--')
            self.bfs_cost.config(text='--')
            self.astar_cost.config(text='--')
            return

        if bfs is not None:
            self.bfs_steps.config(text=str(bfs['steps']))
            self.bfs_danger.config(text=str(bfs['danger_hits']))
            self.bfs_cost.config(text=str(bfs['total_cost']))
        else:
            self.bfs_steps.config(text='--')
            self.bfs_danger.config(text='--')
            self.bfs_cost.config(text='--')

        if ast is not None:
            self.astar_steps.config(text=str(ast['steps']))
            self.astar_danger.config(text=str(ast['danger_hits']))
            self.astar_cost.config(text=str(ast['total_cost']))
        else:
            self.astar_steps.config(text='--')
            self.astar_danger.config(text='--')
            self.astar_cost.config(text='--')

        if bfs and ast:
            if ast['danger_hits'] < bfs['danger_hits']:
                extra_steps = ast['steps'] - bfs['steps']
                extra = f'{extra_steps} extra steps' if extra_steps != 1 else '1 extra step'
                self.result_text.config(
                    text=(
                        f'BFS took the shortest route ({bfs["steps"]} steps) and crossed {bfs["danger_hits"]} Griever(s). '
                        f'A* chose a longer route ({ast["steps"]} steps, {extra}) and reached the Exit without Griever contact.'
                    )
                )
            elif bfs['danger_hits'] < ast['danger_hits']:
                self.result_text.config(
                    text=(
                        f'BFS took {bfs["steps"]} steps with {bfs["danger_hits"]} Griever hit(s); '
                        f'A* took {ast["steps"]} steps with {ast["danger_hits"]}. '
                        'Inspect this run: the safe-route planner should avoid Grievers whenever a safe route exists.'
                    )
                )
            else:
                self.result_text.config(
                    text=(
                        f'Both agents took {bfs["steps"]} steps and encountered {bfs["danger_hits"]} Griever(s). '
                        'This maze did not create a visible safety trade-off; refresh to generate another experiment.'
                    )
                )
        else:
            self.result_text.config(text='Run both agents to compare the path choice and danger tradeoff.')


if __name__ == '__main__':
    app = MazeRunnerApp()
    app.mainloop()
