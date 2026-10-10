"""Own simulation state and apply controls on each fixed time step."""

from dataclasses import asdict, replace
import math
import threading

from .controller import PIDController, manual_force
from .simulation import DEFAULT_PARAMETERS, reset_state, step


TIME_STEP = 1 / 120
FALL_ANGLE = math.radians(80)
TRACK_LIMIT = 2.5
CART_BRAKE_RATE = 3.0
POLE_DAMPING_RATE = 0.5


class SimulationSession:
    def __init__(self):
        self.lock = threading.Lock()
        self.state = reset_state(theta=0.1)
        self.mode = "manual"
        self.running = False
        self.status = "paused"
        self.left_pressed = False
        self.right_pressed = False
        self.force = 0.0
        self.controller = PIDController()

    def snapshot(self):
        with self.lock:
            return {
                **asdict(self.state),
                "mode": self.mode,
                "running": self.running,
                "status": self.status,
                "force": self.force,
                "kp": self.controller.kp,
                "ki": self.controller.ki,
                "kd": self.controller.kd,
            }

    def handle_command(self, command):
        if not isinstance(command, dict):
            raise ValueError("Command must be a JSON object")

        action = command.get("action")
        with self.lock:
            if action == "mode":
                mode = command.get("mode")
                if mode not in ("manual", "pid"):
                    raise ValueError("Mode must be 'manual' or 'pid'")
                self.mode = mode
                self._release_manual_input()
                self.controller.reset()

            elif action == "manual":
                left = command.get("left")
                right = command.get("right")
                if not isinstance(left, bool) or not isinstance(right, bool):
                    raise ValueError("Manual left and right values must be true or false")
                self.left_pressed = left
                self.right_pressed = right

            elif action == "pid":
                try:
                    self.controller = PIDController(
                        kp=float(command["kp"]),
                        ki=float(command["ki"]),
                        kd=float(command["kd"]),
                        max_force=DEFAULT_PARAMETERS.max_force,
                    )
                except (KeyError, TypeError, ValueError) as error:
                    raise ValueError("PID gains must be finite numbers") from error

            elif action == "start":
                if self.status not in ("fallen", "track limit"):
                    self.running = True
                    self.status = "running"

            elif action == "pause":
                self.running = False
                self.status = "paused"
                self._release_manual_input()

            elif action == "reset":
                self.state = reset_state(theta=0.1)
                self.running = False
                self.status = "paused"
                self._release_manual_input()
                self.force = 0.0
                self.controller.reset()

            else:
                raise ValueError("Unknown action")

    def advance(self, dt: float) -> None:
        with self.lock:
            if self.status in ("fallen", "track limit"):
                self._advance_without_control(dt)
                return
            if not self.running:
                return

            if self.mode == "manual":
                force = manual_force(
                    self.left_pressed,
                    self.right_pressed,
                    DEFAULT_PARAMETERS.max_force,
                )
            else:
                force = self.controller.force(self.state, dt)

            self.state = step(self.state, force, dt)
            self.force = force

            if abs(self.state.theta) >= FALL_ANGLE:
                self.running = False
                self.status = "fallen"
                self._release_manual_input()
                self.force = 0.0
            elif abs(self.state.x) >= TRACK_LIMIT:
                self.running = False
                self.status = "track limit"
                self._release_manual_input()
                self.force = 0.0

    def _advance_without_control(self, dt: float) -> None:
        """Let the arm swing while the cart brakes or stays at the track edge."""

        next_state = step(self.state, force=0.0, dt=dt)
        at_track_limit = (
            self.status == "track limit" or abs(next_state.x) >= TRACK_LIMIT
        )
        if at_track_limit:
            cart_x = math.copysign(TRACK_LIMIT, next_state.x)
            cart_x_dot = 0.0
        else:
            cart_x = next_state.x
            cart_x_dot = next_state.x_dot * math.exp(-CART_BRAKE_RATE * dt)

        self.state = replace(
            next_state,
            x=cart_x,
            x_dot=cart_x_dot,
            theta_dot=next_state.theta_dot * math.exp(-POLE_DAMPING_RATE * dt),
        )
        self.force = 0.0

    def _release_manual_input(self) -> None:
        self.left_pressed = False
        self.right_pressed = False
