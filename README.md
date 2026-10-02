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
