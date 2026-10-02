"use strict";

const SIZE = 25;
const WALL = 1;
const OPEN = 0;
const START = 3;
const EXIT = 4;
const GRIEVER = 5;
const DIRECTIONS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
const COLORS = { 0: "#18242a", 1: "#687176", 3: "#6ed27b", 4: "#43c8f5", 5: "#dd3944" };

const ui = {
  pov: document.querySelector("#pov"),
  map: document.querySelector("#map"),
  log: document.querySelector("#log"),
  status: document.querySelector("#status"),
  direction: document.querySelector("#direction"),
  stepCounter: document.querySelector("#step-counter"),
  summary: document.querySelector("#summary"),
  start: document.querySelector("#start"),
};

const state = {
  grid: [],
  start: null,
  goal: null,
  pos: null,
  facing: [0, -1],
  route: [],
  index: 0,
  mode: null,
  human: false,
  dead: false,
  running: false,
  timer: null,
  nightUsed: false,
  results: { BFS: null, "A*": null },
  runPath: [],
};

function inBounds(r, c) { return r >= 0 && c >= 0 && r < SIZE && c < SIZE; }
function walkable(r, c) { return inBounds(r, c) && state.grid[r][c] !== WALL; }
function neighbors([r, c]) {
  return DIRECTIONS.map(([dr, dc]) => [r + dr, c + dc]).filter(([nr, nc]) => walkable(nr, nc));
}
function key([r, c]) { return `${r},${c}`; }
function same(a, b) { return a[0] === b[0] && a[1] === b[1]; }

function makeGrid() {
  const grid = Array.from({ length: SIZE }, () => Array(SIZE).fill(WALL));
  const center = Math.floor(SIZE / 2);
  const visited = new Set([key([center, center])]);
  const stack = [[center, center]];
  grid[center][center] = OPEN;
  while (stack.length) {
    const [r, c] = stack[stack.length - 1];
    const options = DIRECTIONS.map(([dr, dc]) => [r + 2 * dr, c + 2 * dc, dr, dc])
      .filter(([nr, nc]) => nr > 0 && nc > 0 && nr < SIZE - 1 && nc < SIZE - 1 && !visited.has(key([nr, nc])));
    if (!options.length) { stack.pop(); continue; }
    const [nr, nc, dr, dc] = options[Math.floor(Math.random() * options.length)];
    grid[r + dr][c + dc] = OPEN;
    grid[nr][nc] = OPEN;
    visited.add(key([nr, nc]));
    stack.push([nr, nc]);
  }
  const loopWalls = [];
  for (let r = 1; r < SIZE - 1; r++) {
    for (let c = 1; c < SIZE - 1; c++) {
      if (grid[r][c] !== WALL) continue;
      if ((grid[r][c - 1] === OPEN && grid[r][c + 1] === OPEN) ||
          (grid[r - 1][c] === OPEN && grid[r + 1][c] === OPEN)) loopWalls.push([r, c]);
    }
  }
  shuffle(loopWalls);
  for (const [r, c] of loopWalls.slice(0, Math.max(4, SIZE >> 1))) grid[r][c] = OPEN;

  const start = [center, center];
  const exits = [];
  for (let p = 1; p < SIZE - 1; p += 2) exits.push([[1, p], [0, p]], [[SIZE - 2, p], [SIZE - 1, p]], [[p, 1], [p, 0]], [[p, SIZE - 2], [p, SIZE - 1]]);
  shuffle(exits);
  const [inner, goal] = exits[0];
  grid[inner[0]][inner[1]] = OPEN;
  grid[goal[0]][goal[1]] = EXIT;
  grid[start[0]][start[1]] = START;

  const corridors = [];
  for (let r = 1; r < SIZE - 1; r++) for (let c = 1; c < SIZE - 1; c++) if (grid[r][c] === OPEN) corridors.push([r, c]);
  shuffle(corridors);
  for (const [r, c] of corridors.slice(0, Math.max(5, SIZE / 3))) grid[r][c] = GRIEVER;
  return { grid, start, goal };
}
function shuffle(items) {
  for (let i = items.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }
}

function shortestPath(grid, start, goal) {
  const queue = [start];
  const previous = new Map([[key(start), null]]);
  for (let i = 0; i < queue.length; i++) {
    const current = queue[i];
    if (same(current, goal)) break;
    for (const next of neighbors(current)) {
      if (previous.has(key(next))) continue;
      previous.set(key(next), current);
      queue.push(next);
    }
  }
  if (!previous.has(key(goal))) return null;
  const path = [];
  for (let p = goal; p; p = previous.get(key(p))) path.push(p);
  return path.reverse();
}

function astarPath(start, goal) {
  const penalty = SIZE * SIZE + 1;
  const open = [{ p: start, g: 0, f: manhattan(start, goal) }];
  const previous = new Map([[key(start), null]]);
  const score = new Map([[key(start), 0]]);
  while (open.length) {
    open.sort((a, b) => a.f - b.f || a.g - b.g);
    const current = open.shift();
    if (current.g !== score.get(key(current.p))) continue;
    if (same(current.p, goal)) break;
    for (const next of neighbors(current.p)) {
      const g = current.g + 1 + (state.grid[next[0]][next[1]] === GRIEVER ? penalty : 0);
      if (g >= (score.get(key(next)) ?? Infinity)) continue;
      score.set(key(next), g);
      previous.set(key(next), current.p);
      open.push({ p: next, g, f: g + manhattan(next, goal) });
    }
  }
  if (!score.has(key(goal))) return null;
  const path = [];
  for (let p = goal; p; p = previous.get(key(p))) path.push(p);
  return path.reverse();
}
function manhattan(a, b) { return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]); }
function countDanger(path) { return path.filter(([r, c]) => state.grid[r][c] === GRIEVER).length; }
function createQualifiedMaze() {
  for (let tries = 0; tries < 500; tries++) {
    const maze = makeGrid();
    state.grid = maze.grid;
    const bfs = shortestPath(state.grid, maze.start, maze.goal);
    const safe = astarPath(maze.start, maze.goal);
    if (bfs && safe && countDanger(bfs) > 0 && countDanger(safe) === 0 && safe.length > bfs.length) return maze;
  }
  throw new Error("Could not create a maze with the required BFS/A* safety comparison. Please try again.");
}

function addLog(message) {
  const li = document.createElement("li");
  li.textContent = message;
  ui.log.prepend(li);
  while (ui.log.children.length > 30) ui.log.lastElementChild.remove();
}
function announce(message) { ui.status.textContent = message; }
function clearTimer() { if (state.timer) { clearTimeout(state.timer); state.timer = null; } }
function resetResults() {
  state.results = { BFS: null, "A*": null };
  for (const id of ["bfs-steps", "bfs-danger", "bfs-cost", "astar-steps", "astar-danger", "astar-cost"]) document.getElementById(id).textContent = "—";
  ui.summary.textContent = "Run both agents to compare speed and safety.";
}

function newMaze() {
  clearTimer();
  try {
    const maze = createQualifiedMaze();
    state.start = maze.start;
    state.goal = maze.goal;
    state.pos = [...maze.start];
    state.facing = [0, -1];
    state.route = [];
    state.index = 0;
    state.mode = null;
    state.human = false;
    state.dead = false;
    state.running = false;
    state.nightUsed = false;
    state.runPath = [];
    resetResults();
    ui.log.replaceChildren();
    addLog("New maze generated. Glade start point is marked green; Exit is blue.");
    announce("New maze ready. Choose BFS, A*, or Human Play.");
    render();
  } catch (error) {
    announce(error.message);
    addLog(error.message);
  }
}

function startRun(mode) {
  clearTimer();
  state.mode = mode;
  state.human = false;
  state.dead = false;
  state.running = true;
  state.pos = [...state.start];
  state.index = 0;
  state.nightUsed = false;
  state.runPath = [state.start];
  state.route = mode === "BFS" ? shortestPath(state.grid, state.start, state.goal) : astarPath(state.start, state.goal);
  if (!state.route) { announce("No route to the Exit was found."); return; }
  const plannedSteps = state.route.length - 1;
  const plannedDangers = countDanger(state.route);
  addLog(`${mode} route selected: ${plannedSteps} steps, ${plannedDangers} planned Griever hit(s).`);
  announce(`${mode} running. Watch the arrow for each turn; movement pauses between steps.`);
  render();
  tickAgent();
}

function directionName([dc, dr]) {
  if (Math.abs(dc) > Math.abs(dr)) return dc > 0 ? "EAST" : "WEST";
  return dr > 0 ? "SOUTH" : "NORTH";
}
function rotateTo([r, c]) {
  const desired = [c - state.pos[1], r - state.pos[0]];
  if (same(desired, state.facing)) return false;
  const turn = state.facing[0] * desired[1] - state.facing[1] * desired[0];
  state.facing = desired;
  addLog(`Turning ${turn > 0 ? "right" : "left"} to face ${directionName(desired)}.`);
  render();
  return true;
}
function tickAgent() {
  if (!state.running) return;
  if (state.index >= state.route.length - 1) {
    state.running = false;
    const dangers = countDanger(state.runPath);
    state.results[state.mode] = {
      path: [...state.runPath],
      steps: state.runPath.length - 1,
      dangers,
      cost: state.runPath.length - 1 + dangers * (SIZE * SIZE + 1),
    };
    updateResults();
    addLog(`${state.mode} reached the Exit.`);
    announce(`${state.mode} completed the maze.`);
    return;
  }
  const next = state.route[state.index + 1];
  if (state.grid[next[0]][next[1]] === WALL) {
    addLog("Route blocked. Re-planning from current position.");
    state.route = state.mode === "BFS" ? shortestPath(state.grid, state.pos, state.goal) : astarPath(state.pos, state.goal);
    state.index = 0;
    state.runPath = [state.pos];
    if (!state.route) { state.running = false; announce("No route remains to the Exit."); return; }
    clearTimer();
    state.timer = setTimeout(tickAgent, 900);
    return;
  }
  if (rotateTo(next)) {
    state.timer = setTimeout(tickAgent, 850);
    return;
  }
  state.pos = [...next];
  state.index++;
  state.runPath.push(state.pos);
  addLog(`Step ${state.runPath.length - 1}: moving ${directionName(state.facing)}${state.grid[next[0]][next[1]] === GRIEVER ? " — GRIEVER CORRIDOR!" : "."}`);
  if (state.grid[next[0]][next[1]] === GRIEVER) {
    announce(`${state.mode} crossed a Griever corridor.`);
  }
  render();
  state.timer = setTimeout(tickAgent, 1200);
}

function enableHuman() {
  clearTimer();
  state.running = false;
  state.human = true;
  state.dead = false;
  state.mode = "Human";
  state.pos = [...state.start];
  state.facing = [0, -1];
  state.route = [];
  announce("Human Play: turn left/right, then move forward/back.");
  addLog("Human Play enabled. Use the on-screen arrow controls.");
  render();
}
function humanAction(action) {
  if (!state.human || state.dead) { announce("Tap Human Play first."); return; }
  if (action === "left" || action === "right") {
    const [dx, dy] = state.facing;
    state.facing = action === "left" ? [dy, -dx] : [-dy, dx];
    addLog(`You turned ${action}; now facing ${directionName(state.facing)}.`);
    render();
    return;
  }
  const [dx, dy] = state.facing;
  const sign = action === "back" ? -1 : 1;
  const next = [state.pos[0] + dy * sign, state.pos[1] + dx * sign];
  if (!walkable(next[0], next[1])) {
    announce("Wall ahead. Turn left or right to find an open corridor.");
    addLog("A concrete wall blocks the way.");
    return;
  }
  state.pos = next;
  addLog(`Human runner moved ${directionName(state.facing)}.`);
  if (state.grid[next[0]][next[1]] === GRIEVER) {
    state.dead = true;
    state.human = false;
    announce("Griever contact. Runner eliminated — generate a new maze to try again.");
    addLog("GRIEVER CONTACT. Subject lost.");
  } else if (same(next, state.goal)) {
    state.human = false;
    announce("You reached the Exit. Run BFS and A* to compare their decisions.");
    addLog("Human runner reached the Exit.");
  }
  render();
}

function nightShift() {
  if (!state.running) { announce("Start a BFS or A* run before Night Shift."); return; }
  if (state.nightUsed) { announce("Night Shift has already been used this run."); return; }
  const candidates = state.route.slice(state.index + 1).filter(([r, c]) => state.grid[r][c] === OPEN && !same([r, c], state.goal));
  for (const cell of candidates) {
    state.grid[cell[0]][cell[1]] = WALL;
    const route = state.mode === "BFS" ? shortestPath(state.grid, state.pos, state.goal) : astarPath(state.pos, state.goal);
    if (route && route.length > 1) {
      state.nightUsed = true;
      state.route = route;
      state.index = 0;
      addLog(`NIGHT SHIFT: corridor at ${cell.join(",")} collapsed. Re-planning from current position.`);
      announce("Corridor collapsed. Agent is re-planning from where it stands.");
      render();
      clearTimer();
      state.timer = setTimeout(tickAgent, 1200);
      return;
    }
    state.grid[cell[0]][cell[1]] = OPEN;
  }
  announce("No future corridor could be collapsed without blocking every route to the Exit.");
}

function updateResults() {
  for (const [mode, prefix] of [["BFS", "bfs"], ["A*", "astar"]]) {
    const result = state.results[mode];
    if (!result) continue;
    document.getElementById(`${prefix}-steps`).textContent = result.steps;
    document.getElementById(`${prefix}-danger`).textContent = result.dangers;
    document.getElementById(`${prefix}-cost`).textContent = result.steps + result.dangers * (SIZE * SIZE + 1);
  }
  const b = state.results.BFS, a = state.results["A*"];
  if (b && a) ui.summary.textContent = `BFS: ${b.steps} steps, ${b.dangers} Griever hit(s). A*: ${a.steps} steps, ${a.dangers} hit(s). Compare the step cost against the safety gained.`;
}

function render() {
  drawMap();
  drawPOV();
  const relative = exitRelative();
  ui.direction.innerHTML = `FACING ${directionName(state.facing)} <span>·</span> EXIT ${relative} <span>·</span> ${manhattan(state.pos, state.goal)} STEPS AWAY`;
  ui.stepCounter.textContent = `STEP ${state.runPath.length ? state.runPath.length - 1 : 0}`;
}
function exitRelative() {
  const dx = state.goal[1] - state.pos[1], dy = state.goal[0] - state.pos[0];
  const dot = dx * state.facing[0] + dy * state.facing[1];
  const cross = dx * state.facing[1] - dy * state.facing[0];
  if (dot > 0) return "AHEAD";
  if (dot < 0 && Math.abs(cross) < Math.abs(dot)) return "BEHIND";
  return cross > 0 ? "LEFT" : "RIGHT";
}
function fitCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.max(1, Math.floor(rect.width * dpr));
  const h = Math.max(1, Math.floor(rect.height * dpr));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  return canvas.getContext("2d");
}
function drawMap() {
  if (!state.grid.length) return;
  const ctx = fitCanvas(ui.map);
  const w = ui.map.width, h = ui.map.height;
  const cellW = w / SIZE, cellH = h / SIZE;
  ctx.fillStyle = "#080b0e";
  ctx.fillRect(0, 0, w, h);
  for (let r = 0; r < SIZE; r++) for (let c = 0; c < SIZE; c++) {
    ctx.fillStyle = COLORS[state.grid[r][c]];
    ctx.fillRect(c * cellW, r * cellH, Math.ceil(cellW), Math.ceil(cellH));
    if (state.grid[r][c] === WALL) {
      ctx.fillStyle = "rgba(255,255,255,.10)";
      ctx.fillRect(c * cellW, r * cellH, cellW, Math.max(1, cellH * .12));
    }
  }
  if (state.route.length) {
    ctx.strokeStyle = "rgba(78,221,255,.8)";
    ctx.lineWidth = Math.max(1, cellW * .25);
    ctx.beginPath();
    state.route.slice(state.index).forEach(([r, c], i) => {
      const x = (c + .5) * cellW, y = (r + .5) * cellH;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  const [r, c] = state.pos;
  const cx = (c + .5) * cellW, cy = (r + .5) * cellH;
  ctx.fillStyle = "#fff18a";
  ctx.beginPath(); ctx.arc(cx, cy, Math.max(3, cellW * .42), 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = "#fff"; ctx.lineWidth = Math.max(1, cellW * .16);
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(cx + state.facing[0] * cellW * .9, cy + state.facing[1] * cellH * .9);
  ctx.stroke();
  const [gr, gc] = state.goal;
  ctx.strokeStyle = "#e8fbff"; ctx.lineWidth = Math.max(1, cellW * .18);
  ctx.strokeRect(gc * cellW + 1, gr * cellH + 1, cellW - 2, cellH - 2);
}

function drawPOV() {
  if (!state.grid.length) return;
  const ctx = fitCanvas(ui.pov);
  const w = ui.pov.width, h = ui.pov.height, horizon = h * .43;
  const sky = ctx.createLinearGradient(0, 0, 0, horizon);
  sky.addColorStop(0, "#091116"); sky.addColorStop(1, "#26383d");
  ctx.fillStyle = sky; ctx.fillRect(0, 0, w, horizon);
  const floor = ctx.createLinearGradient(0, horizon, 0, h);
  floor.addColorStop(0, "#20272a"); floor.addColorStop(1, "#090c0e");
  ctx.fillStyle = floor; ctx.fillRect(0, horizon, w, h - horizon);
  for (let x = 0; x < w; x += 2) {
    const camera = (x / w - .5) * 1.25;
    const ray = [state.facing[0] - state.facing[1] * camera, state.facing[1] + state.facing[0] * camera];
    let mapX = state.pos[1], mapY = state.pos[0];
    const deltaX = Math.abs(1 / (ray[0] || 1e-9)), deltaY = Math.abs(1 / (ray[1] || 1e-9));
    const stepX = ray[0] < 0 ? -1 : 1, stepY = ray[1] < 0 ? -1 : 1;
    let sideX = (ray[0] < 0 ? .5 : .5) * deltaX, sideY = .5 * deltaY;
    let distance = 0, hit = false, side = 0;
    for (let i = 0; i < 50 && !hit; i++) {
      if (sideX < sideY) { sideX += deltaX; mapX += stepX; side = 0; distance = sideX - deltaX; }
      else { sideY += deltaY; mapY += stepY; side = 1; distance = sideY - deltaY; }
      if (!inBounds(mapY, mapX) || state.grid[mapY][mapX] === WALL) hit = true;
    }
    distance = Math.max(.2, distance);
    const wallHeight = Math.min(h * 1.5, h * .75 / distance);
    const top = Math.max(0, horizon - wallHeight / 2), bottom = Math.min(h, horizon + wallHeight / 2);
    const fog = Math.max(.25, 1 - distance / 20);
    const shade = Math.floor((78 + (side ? -22 : 0)) * fog);
    ctx.fillStyle = `rgb(${shade},${shade + 5},${shade + 8})`;
    ctx.fillRect(x, top, 2, bottom - top);
    ctx.fillStyle = `rgba(3,7,9,${Math.min(.5, 1 / distance)})`;
    for (let seam = top + wallHeight / 4; seam < bottom; seam += wallHeight / 4) ctx.fillRect(x, seam, 2, 1);
  }
  ctx.fillStyle = "rgba(3,10,14,.75)";
  ctx.fillRect(8, 8, Math.min(w - 16, 270), 23);
  ctx.fillStyle = "#b3d4de";
  ctx.font = `${Math.max(11, Math.floor(h * .055))}px monospace`;
  ctx.fillText("W.C.K.D. // SUBJECT LIVE FEED", 15, 24);
  if (state.dead) {
    ctx.fillStyle = "rgba(65,5,10,.9)"; ctx.fillRect(w * .12, h * .43, w * .76, h * .14);
    ctx.fillStyle = "#ff8585"; ctx.textAlign = "center";
    ctx.fillText("SUBJECT LOST // GRIEVER CONTACT", w / 2, h * .52); ctx.textAlign = "left";
  }
}

document.querySelector("#start").addEventListener("click", () => {
  document.querySelector("#game").scrollIntoView({ behavior: "smooth" });
  document.querySelector("#run-bfs").focus({ preventScroll: true });
});
document.querySelector("#run-bfs").addEventListener("click", () => startRun("BFS"));
document.querySelector("#run-astar").addEventListener("click", () => startRun("A*"));
document.querySelector("#human").addEventListener("click", enableHuman);
document.querySelector("#night").addEventListener("click", nightShift);
document.querySelector("#refresh").addEventListener("click", newMaze);
document.querySelectorAll("[data-action]").forEach(button => button.addEventListener("click", () => humanAction(button.dataset.action)));
window.addEventListener("keydown", event => {
  const actions = { ArrowLeft: "left", ArrowRight: "right", ArrowUp: "forward", ArrowDown: "back" };
  if (actions[event.key] && state.human) { event.preventDefault(); humanAction(actions[event.key]); }
});
window.addEventListener("resize", render);
window.addEventListener("orientationchange", () => setTimeout(render, 150));
newMaze();
