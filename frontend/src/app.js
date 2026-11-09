import { getState, sendCommand as sendBackendCommand } from "./api.js";
import { drawCartPole } from "./view.js";

const modeSelect = document.querySelector("#mode");
const pidControls = document.querySelector("#pid-controls");
const connectionStatus = document.querySelector("#connection-status");
const readouts = {
  angle: document.querySelector("#angle"),
  position: document.querySelector("#position"),
  force: document.querySelector("#force"),
  status: document.querySelector("#simulation-status"),
};
const pidInputs = {
  kp: document.querySelector("#kp"),
  ki: document.querySelector("#ki"),
  kd: document.querySelector("#kd"),
  position_kp: document.querySelector("#position-kp"),
  position_kd: document.querySelector("#position-kd"),
  target_position: document.querySelector("#target-position"),
};
const manualInput = { left: false, right: false };
let polling = false;

function sendCommand(command) {
  sendBackendCommand(command)
    .then(() => {
      connectionStatus.textContent = "Connected to Python backend";
    })
    .catch((error) => {
      connectionStatus.textContent = `Backend error: ${error.message}`;
    });
}

function sendManualInput() {
  sendCommand({ action: "manual", ...manualInput });
}

function releaseManualInput() {
  manualInput.left = false;
  manualInput.right = false;
  sendManualInput();
}

function setButtonInput(direction, pressed) {
  manualInput[direction] = pressed;
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

function directionFromKey(key) {
  if (key === "ArrowLeft") return "left";
  if (key === "ArrowRight") return "right";
  return null;
}

document.addEventListener("keydown", (event) => {
  if (event.target.matches("input, select, textarea")) return;
  const direction = directionFromKey(event.key);
  if (!direction) return;

  event.preventDefault();
  if (!event.repeat && !manualInput[direction]) {
    manualInput[direction] = true;
    sendManualInput();
  }
});

document.addEventListener("keyup", (event) => {
  const direction = directionFromKey(event.key);
  if (!direction || !manualInput[direction]) return;

  manualInput[direction] = false;
  sendManualInput();
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

function updatePIDSettings() {
  const settings = Object.fromEntries(
    Object.entries(pidInputs).map(([name, input]) => [name, Number(input.value)]),
  );
  if (
    Object.values(pidInputs).every((input) => input.value.trim() !== "") &&
    Object.values(settings).every(Number.isFinite)
  ) {
    sendCommand({ action: "pid", ...settings });
  }
}

for (const input of Object.values(pidInputs)) {
  input.addEventListener("change", updatePIDSettings);
}

async function refreshState() {
  if (polling) return;
  polling = true;

  try {
    const state = await getState();
    modeSelect.value = state.mode;
    pidControls.disabled = state.mode !== "pid";
    drawCartPole(state);

    readouts.angle.textContent = `${(state.theta * 180 / Math.PI).toFixed(1)}°`;
    readouts.position.textContent = `${state.x.toFixed(2)} m`;
    readouts.force.textContent = `${state.force.toFixed(1)} N`;
    readouts.status.textContent = state.status;
    connectionStatus.textContent = "Connected to Python backend";

    for (const [name, input] of Object.entries(pidInputs)) {
      if (document.activeElement !== input) input.value = state[name];
    }
  } catch {
    connectionStatus.textContent = "Backend not connected. Start it with: python -m backend.app";
  } finally {
    polling = false;
  }
}

refreshState();
setInterval(refreshState, 1000 / 60);
