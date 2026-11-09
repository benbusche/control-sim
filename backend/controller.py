"""Manual and PID controls for the cart-pole simulation."""

from dataclasses import dataclass, field
import math

from .simulation import CartPoleState, DEFAULT_PARAMETERS


def manual_force(
    left_pressed: bool,
    right_pressed: bool,
    max_force: float = DEFAULT_PARAMETERS.max_force,
) -> float:
    """Choose a force from the left and right button/key states."""

    if not math.isfinite(max_force) or max_force <= 0:
        raise ValueError("max_force must be finite and greater than zero")
    if left_pressed == right_pressed:
        return 0.0
    return max_force if right_pressed else -max_force


@dataclass
class PIDController:
    """Balance the pole while keeping the cart near a target position.

    The angle error is measured minus target, so positive pole tilt produces
    positive corrective force for this simulation's angle/force conventions.
    The default gains are a starting point and may need tuning.
    """

    kp: float = 20.0
    ki: float = 0.0
    kd: float = 5.0
    target_position: float = 0.0
    position_kp: float = 1.0
    position_kd: float = 1.0
    max_force: float = DEFAULT_PARAMETERS.max_force
    integral_limit: float = 1.0
    _integral: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        values = (
            self.kp,
            self.ki,
            self.kd,
            self.target_position,
            self.position_kp,
            self.position_kd,
            self.max_force,
            self.integral_limit,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("PID settings must all be finite")
        if min(self.position_kp, self.position_kd) < 0:
            raise ValueError("Position gains cannot be negative")
        if min(self.max_force, self.integral_limit) <= 0:
            raise ValueError("Limits must be greater than zero")

    def reset(self) -> None:
        """Clear the accumulated error, for example after a simulation reset."""

        self._integral = 0.0

    def force(self, state: CartPoleState, dt: float) -> float:
        """Calculate a bounded force to balance and position the cart."""

        if not math.isfinite(dt) or dt <= 0:
            raise ValueError("dt must be finite and greater than zero")

        angle_error = state.theta
        next_integral = self._integral + angle_error * dt
        next_integral = max(
            -self.integral_limit,
            min(self.integral_limit, next_integral),
        )

        position_error = state.x - self.target_position
        requested_force = (
            self.kp * angle_error
            + self.ki * next_integral
            + self.kd * state.theta_dot
            + self.position_kp * position_error
            + self.position_kd * state.x_dot
        )
        bounded_force = max(-self.max_force, min(self.max_force, requested_force))

        # Keep integral memory only when it is not pushing farther into saturation.
        if requested_force == bounded_force or requested_force * angle_error < 0:
            self._integral = next_integral

        return bounded_force
