# Control Simulation

## Project overview

A small browser app for watching and controlling an inverted pendulum on a cart.
The backend will be written mostly in Python. A small JavaScript frontend will
draw the simulation and handle keyboard and button input.

The first goal is a working cart-pole simulation with two control modes:

- **Manual:** move the cart with the left and right arrow keys or buttons.
- **PID:** let a controller try to keep the pole upright.

The code should stay simple and easy to learn from. A double pendulum may be
added later, after the first simulation works.

## Features

### Python backend

- Simulate cart and pole motion using clear physical values and units.
- Support reset, pause, and start controls.
- Apply bounded force from manual input or the PID controller.
- In PID mode, balance the pole while moving the cart toward a chosen target position.
- Send the current position, angle, and control mode to the browser.
- Keep the physics separate from the web server so it can be reused later.

### Browser frontend

- Draw the cart, pole, and track, and animate their movement.
- Accept arrow-key and on-screen button input in Manual mode.
- Let the user switch between Manual and PID modes.
- Show the pole angle, cart position, and whether the simulation is running.
- Provide start, pause, and reset controls.
- Let the user adjust PID settings once PID mode is added.
- Let the user choose the cart's target position in PID mode.

## Project layout

```text
backend/
  app.py          # web server and browser connection
  simulation.py   # cart-pole physics and state
  controller.py   # manual and PID control
frontend/
  index.html      # page structure
  src/
    app.js        # input, display, and backend connection
    styles.css    # page appearance
```

## Important conventions

- The pole angle is measured in radians from upright: `0` means straight up.
- Positive force moves the cart to the right.
- Measurements use meters, seconds, kilograms, and radians.
- The simulation uses small time steps for stable motion.
- A double pendulum will need its own physics and control approach; it will not
  be handled automatically by the cart-pole controller.

## Progress

- [x] Create a simple project folder structure.
- [x] Add Python cart-pole state, parameters, reset, and one physics step.
- [x] Add Manual and PID controllers.
- [x] Add the Python web server and connection to the browser.
- [x] Draw and animate the cart-pole in the browser.
- [x] Add keyboard and on-screen manual controls.
- [x] Add PID tuning and live state readouts.
- [x] Add start, pause, and reset controls.
- [x] Document how to run the app.
- [ ] Add a PID target-position control and move the cart toward that position.
- [ ] Check that both control modes behave as expected.

## Running the project

From the project folder, run:

```powershell
python -m backend.app
```

Then open <http://127.0.0.1:8000>. The Python server also serves the frontend,
so no separate frontend server or JavaScript packages are needed.
