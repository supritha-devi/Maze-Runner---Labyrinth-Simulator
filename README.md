## Play the game

[W.C.K.D. // Labyrinth Simulator](https://supritha-devi.github.io/Maze-Runner---Labyrinth-Simulator/)

# W.C.K.D. Labyrinth Simulator

A desktop-browser maze game comparing BFS, A*, and human navigation through a changing labyrinth.

## Play

Open the public GitHub Pages link on a laptop or desktop. The game is designed for a wide screen.

## Game flow

Arrival → Story → Simulation → Comparison → What We Learned

The Simulation page keeps the maze map, first-person player view, controls, and telemetry together.

## Controls

- **BFS** finds a route with the fewest steps without considering Griever danger.
- **A\*** prioritizes avoiding Grievers, even when the safe route is longer.
- **Human Play** lets you navigate with the on-screen controls or arrow keys.
- **Night Shift** collapses a corridor during an active run, requiring the agent to replan.
- **Refresh** generates a new maze and resets the comparison.

## Run locally

From the folder containing `index.html`, start a local web server:

```powershell
py -m http.server 8000

## Tech Stack

- **HTML5** — page structure and guided game screens
- **CSS3** — responsive styling, dark W.C.K.D. theme, and desktop layout
- **JavaScript** — maze generation, BFS/A* pathfinding, human controls, animation, telemetry, and Night Shift replanning
- **HTML Canvas** — overhead maze map and first-person perspective renderer
- **GitHub Pages** — static website hosting

## Tools and Packages

- Vanilla HTML, CSS, and JavaScript — no npm packages or frameworks
- HTML Canvas API — draws the maze map and first-person view
- Browser APIs — keyboard input, timers, and page navigation
- Python’s built-in `http.server` — optional local testing server; not a game dependency
- GitHub Pages — hosting
