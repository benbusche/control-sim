import pytest

from backend.controller import PIDController, manual_force
from backend.simulation import (
    CartPoleParameters,
    CartPoleState,
    reset_state,
    step,
)


def test_reset_state_starts_at_rest_with_requested_angle():
    assert reset_state(0.2) == CartPoleState(theta=0.2)


def test_parameters_must_be_positive():
    with pytest.raises(ValueError):
        CartPoleParameters(cart_mass=0)


def test_upright_pole_stays_still_with_no_force():
    state = step(CartPoleState(), force=0, dt=1 / 120)

    assert state == CartPoleState()


def test_tilted_pole_falls_further_without_control():
    state = step(CartPoleState(theta=0.1), force=0, dt=1 / 120)

    assert state.theta > 0.1
    assert state.theta_dot > 0


def test_force_is_limited_by_parameters():
    parameters = CartPoleParameters(max_force=2)

    assert step(CartPoleState(), 20, 0.01, parameters) == step(
        CartPoleState(), 2, 0.01, parameters
    )


def test_step_rejects_non_positive_time_step():
    with pytest.raises(ValueError):
        step(CartPoleState(), force=0, dt=0)


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(True, False, -10), (False, True, 10), (False, False, 0), (True, True, 0)],
)
def test_manual_force(left, right, expected):
    assert manual_force(left, right) == expected


def test_manual_force_uses_requested_limit():
    assert manual_force(True, False, max_force=3) == -3


def test_pid_pushes_toward_upright_and_limits_force():
    controller = PIDController(kp=20, ki=0, kd=0, max_force=1)

    assert controller.force(CartPoleState(theta=0.1), dt=0.01) == 1


def test_pid_reset_clears_accumulated_error():
    controller = PIDController(kp=0, ki=1, kd=0)
    controller.force(CartPoleState(theta=0.2), dt=0.5)
    controller.reset()

    assert controller.force(CartPoleState(), dt=0.5) == 0


def test_pid_rejects_non_positive_time_step():
    with pytest.raises(ValueError):
        PIDController().force(CartPoleState(), dt=0)
