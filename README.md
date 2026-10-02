# Maze Runner: Labyrinth Simulator

A desktop game prototype built in Python with Tkinter and Pillow.

## Play on a phone
The Tkinter `.exe` is for Windows and cannot run directly on Android or iPhone. A browser-based mobile edition is in the `mobile` folder; it is responsive, works with touch controls, and can be installed from a supported mobile browser after hosting it over HTTPS.

### Test the mobile edition on your computer
From the project folder, start a local web server:

```powershell
py -m http.server 8000
```

Open `http://localhost:8000/mobile/` in your computer browser. To test on a phone connected to the same Wi-Fi, find your computer's local IPv4 address with `ipconfig`, then open `http://<computer-ip>:8000/mobile/` on the phone. The phone and computer must be on the same network, and Windows Firewall may ask permission for Python to accept local connections.

### Publish it for access anywhere
Create a GitHub repository and upload the contents of the clean `MazeRunnerProject` folder (or the project source files and folders) to the repository root. The repository should contain `app.py`, `maze.py`, `algorithms.py`, `maze_view.py`, `requirements.txt`, `assets/`, and `mobile/`. Do **not** upload `.venv`, `build`, or `dist`.

In GitHub, open **Settings → Pages**, choose **Deploy from a branch**, select the `main` branch and `/(root)` folder, then save. GitHub Pages publishes the browser version at `https://<your-username>.github.io/<repository-name>/mobile/`. The Python/Tkinter desktop game is source code in the repository; GitHub Pages does not run it as a website. To distribute the Windows desktop edition, use the PyInstaller instructions below. On a phone, open the Pages URL and use **Add to Home Screen** (iPhone/Safari) or **Install app** (Android/Chrome). The mobile edition is cached for offline use after it has been opened successfully online once.

## Features
- Dark Maze Runner themed UI
- First-person perspective maze view with textured stone walls, corridor depth, fog, threat markers, and an overhead route inset
- Linear page flow with Back/Next
- BFS and A* simulation
- Human play mode with keyboard controls
- Randomly generated rectangular labyrinths with a centered Glade and perimeter exit
- Griever contact ends a Human Play run
- Night Shift collapses an open corridor ahead of the moving agent, pauses the run, and replans from the agent's current location
- Refresh to generate a new maze
- Telemetry log and comparison page

## Run locally
1. Install Python 3.10 or newer.
2. Open PowerShell or Command Prompt in this project folder.
3. Install the image-rendering dependency if needed:
   ```powershell
   py -m pip install pillow
   ```
4. Run the app:
   ```powershell
   py app.py
   ```

## Deploy for Windows desktop
The app is a Windows desktop application, not a website. Build the executable on a Windows computer:

```powershell
.\.venv\Scripts\python.exe -m pip install pillow pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --onefile --windowed --add-data "assets;assets" --name MazeRunner app.py
```

PyInstaller creates `dist\MazeRunner.exe`. The `--add-data` option bundles the front-cover image from `assets`, and `--windowed` prevents a console window from appearing.

To share the game, copy `dist\MazeRunner.exe` to the other Windows computer and run it there. Python does not need to be installed on that computer. Windows may show a SmartScreen warning because the executable is unsigned; only run it if you trust its source.

If the single-file executable does not launch on a target computer, build a folder-based version instead:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --windowed --add-data "assets;assets" --name MazeRunner app.py
```

Share the entire `dist\MazeRunner` folder in that case, not just the executable inside it. Build on Windows for Windows; a Windows executable is not a macOS or Linux build.

## Controls
- Mouse: use the on-screen buttons
- Keyboard: use Arrow keys or WASD in Human Play mode; touching a Griever ends the run
- Buttons:
  - Run BFS
  - Run A*
  - Human Play
  - Night Shift
  - Refresh

## Important note
The project is a working prototype and is tuned around the algorithm comparison idea: BFS is the blind baseline, A* prioritizes a Griever-free route whenever one exists (even if it is longer), and Night Shift collapses an untraveled corridor on the active route then replans from the agent's current position. It pauses the old animation, rejects collapses that leave no exit route, and can be used once per run. The main simulation uses a software-rendered first-person perspective of the wall corridors, with concrete texture, distance shading, fog, and a small overhead maze/route inset. It is rendered into the existing Tkinter app with Pillow rather than a 3D camera library. Movement is still grid-based and validated, so the agent cannot enter a wall. Each generated maze is checked to ensure its shortest route crosses a Griever while a longer safe route exists. Both algorithms use the same current maze so their results remain comparable.

The phone edition in `mobile/` is a self-contained static web app. It runs in a browser and can be hosted on GitHub Pages or another static HTTPS host; the desktop edition is a separate Tkinter app.
