"""Physics for a cart with an inverted pendulum."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CartPoleParameters:
    """Physical values use SI units: kilograms, meters, and seconds."""

    cart_mass: float = 1.0
    pole_mass: float = 0.1
    pole_com_length: float = 0.5  # Pivot to the pole's center of mass.
    gravity: float = 9.81
    max_force: float = 10.0

    def __post_init__(self) -> None:
        values = (
            self.cart_mass,
            self.pole_mass,
            self.pole_com_length,
            self.gravity,
            self.max_force,
        )
        if not all(math.isfinite(value) and value > 0 for value in values):
            raise ValueError("All parameters must be finite and greater than zero")


@dataclass(frozen=True)
class CartPoleState:
    """Current cart and pole position and velocity.

    ``theta`` is measured in radians from upright, so zero means balanced.
    Positive force moves the cart to the right.
    """

    x: float = 0.0
    x_dot: float = 0.0
    theta: float = 0.0
    theta_dot: float = 0.0


DEFAULT_PARAMETERS = CartPoleParameters()


def reset_state(theta: float = 0.0) -> CartPoleState:
    """Create a stationary state, optionally starting with the pole tilted."""

    if not math.isfinite(theta):
        raise ValueError("theta must be finite")
    return CartPoleState(theta=theta)


def step(
    state: CartPoleState,
    force: float,
    dt: float,
    parameters: CartPoleParameters = DEFAULT_PARAMETERS,
) -> CartPoleState:
    """Advance the simulation by ``dt`` seconds and return the new state.

    This uses semi-implicit Euler integration: calculate acceleration, update
    velocity, then use that new velocity to update position. Keep ``dt`` small
    (around 1/120 second for the browser simulation). Force is limited by the
    actuator. Track limits and fall detection belong to the session layer.
    """

    if not math.isfinite(force):
        raise ValueError("force must be finite")
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and greater than zero")

    state_values = (state.x, state.x_dot, state.theta, state.theta_dot)
    if not all(math.isfinite(value) for value in state_values):
        raise ValueError("All state values must be finite")

    # Clamp the requested force to what the actuator can apply.
    force = max(-parameters.max_force, min(parameters.max_force, force))

    sin_theta = math.sin(state.theta)
    cos_theta = math.cos(state.theta)
    total_mass = parameters.cart_mass + parameters.pole_mass
    pole_mass_length = parameters.pole_mass * parameters.pole_com_length

    # These equations give the cart and pole accelerations for a uniform rod.
    cart_acceleration_term = (
        force + pole_mass_length * state.theta_dot**2 * sin_theta
    ) / total_mass
    theta_acc = (
        parameters.gravity * sin_theta - cos_theta * cart_acceleration_term
    ) / (
        parameters.pole_com_length
        * (
            4.0 / 3.0
            - parameters.pole_mass * cos_theta**2 / total_mass
        )
    )
    x_acc = (
        cart_acceleration_term
        - pole_mass_length * theta_acc * cos_theta / total_mass
    )

    # Update velocities first, then positions using those new velocities.
    x_dot = state.x_dot + x_acc * dt
    theta_dot = state.theta_dot + theta_acc * dt

    return CartPoleState(
        x=state.x + x_dot * dt,
        x_dot=x_dot,
        theta=state.theta + theta_dot * dt,
        theta_dot=theta_dot,
    )
