const canvas = document.querySelector("#simulation");
const context = canvas.getContext("2d");

const trackY = 300;
const cartWidth = 70;
const cartHeight = 36;
const pixelsPerMeter = 100;
const rodLength = 130;

export function drawCartPole(state) {
  context.clearRect(0, 0, canvas.width, canvas.height);

  const pivotX = canvas.width / 2 + state.x * pixelsPerMeter;
  const pivotY = trackY - cartHeight;
  const cartX = pivotX - cartWidth / 2;
  const rodEndX = pivotX + Math.sin(state.theta) * rodLength;
  const rodEndY = pivotY - Math.cos(state.theta) * rodLength;

  context.strokeStyle = "black";
  context.lineWidth = 3;
  context.beginPath();
  context.moveTo(80, trackY);
  context.lineTo(canvas.width - 80, trackY);
  context.stroke();

  context.fillStyle = "gray";
  context.fillRect(cartX, pivotY, cartWidth, cartHeight);

  const armIsRed = state.status === "fallen" || state.status === "track limit";
  context.strokeStyle = armIsRed ? "red" : "blue";
  context.lineWidth = 8;
  context.lineCap = "round";
  context.beginPath();
  context.moveTo(pivotX, pivotY);
  context.lineTo(rodEndX, rodEndY);
  context.stroke();
}
