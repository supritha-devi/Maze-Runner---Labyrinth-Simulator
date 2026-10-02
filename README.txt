MAZE RUNNER - DESKTOP SOURCE FILES

This small folder contains the original Windows desktop game source.
It does not contain the large prebuilt EXE.

Files:
- app.py, maze.py, algorithms.py, maze_view.py
- requirements.txt
- assets\front_cover.jpg

To run on Windows:
1. Install Python 3.10 or later.
2. Open PowerShell in this folder.
3. Run: py -m pip install -r requirements.txt
4. Run: py app.py

The included requirements.txt installs Pillow, which the app needs.
The Tkinter GUI is included with the standard Windows Python installer.
