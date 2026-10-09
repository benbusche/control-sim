const canvas = document.querySelector("#simulation");
const context = canvas.getContext("2d");
const modeSelect = document.querySelector("#mode");
const manualControls = document.querySelector("#manual-controls");
const pidControls = document.querySelector("#pid-controls");
const connectionStatus = document.querySelector("#connection-status");
const manualInput = { left: false, right: false };
let currentMode = "manual";
let polling = false;
let commandQueue = Promise.resolve();

const trackY = 300;
const cartWidth = 70;
const cartHeight = 36;
const pixelsPerMeter = 100;
const rodLength = 130;

function drawCartPole(state) {
  context.clearRect(0, 0, canvas.width, canvas.height);

  const pivotX = canvas.width / 2 + state.x * pixelsPerMeter;
  const cartTop = trackY - cartHeight;
  const cartX = pivotX - cartWidth / 2;
  const pivotY = cartTop;
  const rodEndX = pivotX + Math.sin(state.theta) * rodLength;
  const rodEndY = pivotY - Math.cos(state.theta) * rodLength;

  // Track
  context.strokeStyle = "black";
  context.lineWidth = 3;
  context.beginPath();
  context.moveTo(80, trackY);
  context.lineTo(canvas.width - 80, trackY);
  context.stroke();

  // Pendulum rod
  context.strokeStyle = "blue";
  context.lineWidth = 8;
  context.lineCap = "round";
  context.beginPath();
  context.moveTo(pivotX, pivotY);
  context.lineTo(rodEndX, rodEndY);
  context.stroke();

  // Cart
  context.fillStyle = "gray";
  context.fillRect(cartX, cartTop, cartWidth, cartHeight);
}

function sendCommand(command) {
  commandQueue = commandQueue.then(async () => {
    const response = await fetch("/api/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Request failed");
    connectionStatus.textContent = "Connected to Python backend";
  }).catch((error) => {
    connectionStatus.textContent = `Backend error: ${error.message}`;
  });
  return commandQueue;
}

function sendManualInput() {
  if (currentMode === "manual") {
    sendCommand({ action: "manual", ...manualInput });
  }
}

function releaseManualInput() {
  manualInput.left = false;
  manualInput.right = false;
  sendManualInput();
}

function setButtonInput(button, pressed) {
  if (currentMode !== "manual") return;
  manualInput[button] = pressed;
  sendManualInput();
}

for (const direction of ["left", "right"]) {
  const button = document.querySelector(`#${direction}`);
  button.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    button.setPointerCapture(event.pointerId);
    setButtonInput(direction, true);
  });
  button.addEventListener("pointerup", () => setButtonInput(direction, false));
  button.addEventListener("pointercancel", () => setButtonInput(direction, false));
}

document.addEventListener("keydown", (event) => {
  if (event.target.matches("input, select, textarea")) return;
  const direction = event.key === "ArrowLeft" ? "left" :
    event.key === "ArrowRight" ? "right" : null;
  if (direction && currentMode === "manual") {
    event.preventDefault();
    if (!event.repeat && !manualInput[direction]) {
      manualInput[direction] = true;
      sendManualInput();
    }
  }
});

document.addEventListener("keyup", (event) => {
  const direction = event.key === "ArrowLeft" ? "left" :
    event.key === "ArrowRight" ? "right" : null;
  if (direction && manualInput[direction]) {
    manualInput[direction] = false;
    sendManualInput();
  }
});

window.addEventListener("blur", releaseManualInput);

modeSelect.addEventListener("change", () => {
  releaseManualInput();
  sendCommand({ action: "mode", mode: modeSelect.value });
});

document.querySelector("#start").addEventListener("click", () => {
  sendCommand({ action: "start" });
});
document.querySelector("#pause").addEventListener("click", () => {
  releaseManualInput();
  sendCommand({ action: "pause" });
});
document.querySelector("#reset").addEventListener("click", () => {
  releaseManualInput();
  sendCommand({ action: "reset" });
});

function updatePIDGains() {
  const names = ["kp", "ki", "kd"];
  const inputs = names.map((name) => document.querySelector(`#${name}`));
  const gains = Object.fromEntries(
    names.map((name, index) => [name, Number(inputs[index].value)]),
  );
  if (
    inputs.every((input) => input.value.trim() !== "") &&
    Object.values(gains).every(Number.isFinite)
  ) {
    sendCommand({ action: "pid", ...gains });
  }
}

for (const name of ["kp", "ki", "kd"]) {
  document.querySelector(`#${name}`).addEventListener("change", updatePIDGains);
}

async function refreshState() {
  if (polling) return;
  polling = true;
  try {
    const response = await fetch("/api/state");
    if (!response.ok) throw new Error("Could not read simulation state");
    const state = await response.json();
    currentMode = state.mode;
    modeSelect.value = state.mode;
    manualControls.hidden = state.mode !== "manual";
    pidControls.disabled = state.mode !== "pid";
    drawCartPole(state);

    document.querySelector("#angle").textContent = `${(state.theta * 180 / Math.PI).toFixed(1)}°`;
    document.querySelector("#position").textContent = `${state.x.toFixed(2)} m`;
    document.querySelector("#force").textContent = `${state.force.toFixed(1)} N`;
    document.querySelector("#simulation-status").textContent = state.status;
    connectionStatus.textContent = "Connected to Python backend";

    for (const name of ["kp", "ki", "kd"]) {
      const input = document.querySelector(`#${name}`);
      if (document.activeElement !== input) input.value = state[name];
    }
  } catch (error) {
    connectionStatus.textContent = "Backend not connected. Start it with: python -m backend.app";
  } finally {
    polling = false;
  }
}

refreshState();
setInterval(refreshState, 50);
