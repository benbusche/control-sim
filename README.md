# Control Simulation

## Project goal

Build a small browser-based control laboratory. The first simulation is an inverted pendulum that the user can watch and control in real time. It has two modes:

1. **Manual** — apply force with the left/right arrow keys or on-screen buttons.
2. **PID** — a PID controller attempts to keep the pendulum upright.

The initial design should be easy to understand and modify, while keeping the simulation and controller boundaries general enough to support later experiments such as a double pendulum.

## Initial scope

The first useful version should include:

- A cart with a hinged pendulum, rendered on a 2D canvas or SVG.
- A physically meaningful, deterministic simulation with configurable parameters.
- A fixed-step simulation loop, independent of display refresh rate.
- Manual and PID control, with a clear indication of the active mode.
- Start, pause, reset, and return-to-upright controls.
- Live readouts for angle, angular velocity, cart position, and applied force.
- Basic tuning controls for the PID gains and simulation speed or time step where appropriate.
- A short explanation of the controls and the meaning of the displayed values.

Keep the first version local and single-user. Do not add accounts, persistence services, multiplayer, or a general-purpose visual editor.

## Suggested implementation approach

Use Python for the simulation, physics, controllers, and session coordination. A small Python web server (FastAPI is a reasonable choice) can expose controls and stream state snapshots to the browser. Use a lightweight JavaScript frontend with Canvas or SVG for drawing and keyboard/button input. Plain JavaScript is enough for the first version; TypeScript is optional if its types become useful as the frontend grows. This keeps the core project in the language the developer knows best while using browser code for responsive interaction.

Keep the Python simulation independent from the web framework, so it can later be run in scripts, notebooks, or training jobs. Use a WebSocket for live state updates and control events if the frontend needs responsive animation; for an initial prototype, a simple polling endpoint is also acceptable. The browser should render received snapshots using `requestAnimationFrame`, while the backend advances physics at a fixed time step. Do not run an unbounded simulation loop inside an HTTP request handler.

## System design

Organize the code around four responsibilities:

### 1. Simulation model

Define a common model boundary for any mechanism:

- **State**: model-specific positions and velocities. The cart-pole state can be represented as cart position `x`, cart velocity `xDot`, pole angle `theta`, and angular velocity `thetaDot`.
- **Action**: the input applied during a time step. For the cart-pole, this is horizontal cart force.
- **Parameters**: masses, pendulum length, gravity, friction/damping, force limit, and any model-specific constants.
- **Step**: advance state by a specified `dt` under an action and return the next state.
- **Reset**: create a known state, with an optional seed or supplied initial offset for repeatable experiments.
- **Status**: identify whether the model is running, failed, or outside its allowed bounds.

Start with an explicit `CartPoleState` and `CartPoleParameters`; do not prematurely build a generic equation engine. Instead, make the boundary generic enough that a future `DoublePendulumModel` can have a different state shape while exposing the same operations (step, reset, observation, and limits). Keep rendering model-specific through a renderer or view adapter rather than assuming every model is a single rod.

For the cart-pole, document the angle convention (for example, zero means upright) and units. Derive or cite the chosen equations in the source comments or a physics note. Include cart and pole dynamics, gravity, applied force, and optional damping. Use a stable numerical integrator such as fourth-order Runge–Kutta if practical; semi-implicit Euler is a simpler acceptable first implementation if its time step and behavior are validated. Clamp applied force to a configured limit and define what happens when the cart reaches track limits or the pole falls beyond a chosen angle.

### 2. Controller interface

Controllers should consume an observation and time step and produce a requested action. Keep the controller independent from the simulation model and UI.

- **Manual controller**: convert key/button state into a bounded left/right force. With neither direction pressed, apply zero force. Define how simultaneous left and right inputs resolve (zero force is a sensible default).
- **PID controller**: initially regulate pole angle. Compute error from the upright target, proportional response from current error, integral response from accumulated error, and derivative response from the change in error (or measured angular velocity). Clamp output to the force limit and use anti-windup so the integral term does not grow without bound when saturated. Reset the integral and previous-error state whenever the controller or simulation resets.
- **Controller manager**: switch the active controller cleanly, and reset controller memory on mode changes. Always pass the final action through the same force-limit policy.

Expose PID gains (`Kp`, `Ki`, `Kd`) as editable UI values with reasonable initial defaults. The signs and gain scale depend on the chosen angle and force conventions, so calibrate them against the implemented model rather than copying arbitrary values. Make tuning responsive but stable: update the gains without accidentally resetting the simulation unless the user requests it.

Do not try to make the cart position a second PID objective in the first version. If a later controller must balance while keeping the cart near the center, add a documented combined objective or a state-feedback controller as a separate mode.

### 3. Simulation session / loop

Run the authoritative simulation loop in Python at a fixed step (for example, 1/120 second), independent of browser refresh rate. The backend should own the current model state, mode, controller memory, run/pause status, and actuator limits. Use monotonic timing and cap catch-up work after delays rather than attempting an unlimited burst of steps. The browser renders the latest received snapshots at display refresh rate. When the tab is hidden or the client disconnects, pause or safely continue according to an explicit policy; for this local project, pausing is the simplest behavior.

At each fixed step:

1. Read the active manual input or controller output.
2. Clamp the action to the configured actuator limit.
3. Advance the model.
4. Check bounds and update the session status.
5. Publish a snapshot for rendering and readouts.

The Python simulation session should own run/pause/reset state and coordinate the model and controller. The browser should send events (manual input pressed/released, select mode, change gains, reset, pause) and display backend snapshots instead of independently integrating physics. Keep one authoritative simulation state in the backend. Validate incoming values and reject unsupported modes or invalid gain settings gracefully.

### 4. User interface and visualization

Lay out the page so the mechanism is the main focus, with a compact control panel beside or below it. Show:

- An animated cart and pole, track, upright reference, and clear track/balance boundaries.
- Current mode and running/paused/fallen status.
- Manual left/right buttons and keyboard operation. Buttons should work with mouse, touch, and keyboard; release, blur, and visibility changes must not leave a force stuck on.
- A mode selector for Manual and PID. Explain that changing modes resets controller state.
- PID gain fields/sliders only while PID is active, with displayed numeric values.
- Start/pause and reset buttons. Reset should restore the initial state and clear controller memory.
- Numeric state readouts with units and a simple indication of actuator saturation.

Support keyboard controls without hijacking keys while a text field or other editable control has focus. Provide visible focus states and accessible labels. Do not rely on color alone to distinguish status or direction.

## Proposed project structure

Adapt these names to the starter tooling if the repository later adopts a different stack:

```text
backend/
  app.py                # FastAPI routes and WebSocket endpoint
  simulation.py         # cart-pole physics, state, and simulation session
  controller.py         # manual and PID control logic
frontend/
  index.html
  src/
    app.js              # controls, backend connection, drawing, and UI updates
    styles.css
  package.json          # frontend tooling if using a bundler such as Vite
```

Keep the first implementation compact. Split `simulation.py` or `controller.py` into smaller modules only when they become difficult to navigate. Use a Python environment and dependency file (such as `pyproject.toml`) at the repository root or under `backend/`, and document the commands to install dependencies and start both services. Preserve the separation between simulation, control, API, and browser presentation even if these responsibilities share a small number of files.

## Build plan

### Phase 1 — Project skeleton and contracts

1. Inspect the repository and select a Python web backend and minimal JavaScript frontend; document how to install, run, and build them.
2. Add Python state, action, observation, parameter, model, and controller contracts.
3. Decide and document units, angle sign, upright target, actuator limits, failure bounds, and reset behavior.
4. Keep a simple development page that can display a model state before adding animation.

**Done when:** the contracts are clear, and a sample cart-pole state can be serialized by the backend and displayed by the frontend without UI-specific physics logic.

### Phase 2 — Cart-pole physics

1. Implement reset state and parameter defaults.
2. Implement the cart-pole acceleration equations and the selected numerical integrator.
3. Add finite-value and boundary checks, plus force clamping.
4. Advance the model with constant zero force and a constant test force to check signs and expected qualitative behavior.

**Done when:** state evolves deterministically for a fixed initial condition, force direction is intuitive and documented, and failure/bounds behavior is explicit.

### Phase 3 — Manual mode and visualization

1. Draw the track, cart, hinge, and pole from backend state snapshots.
2. Add the backend fixed-step loop and browser rendering/update flow; add start, pause, and reset controls.
3. Implement arrow-key and button input, including safe key release and focus handling, and send those events to the backend.
4. Show state readouts, mode, and fallen/paused status from backend snapshots.

**Done when:** a user can apply force, see the response, pause, reset, and recover without a stuck control input.

### Phase 4 — PID mode

1. Implement angle error, P/I/D terms, output saturation, and anti-windup.
2. Reset controller memory on reset and mode changes.
3. Add editable gains and display the applied force and saturation state.
4. Tune a stable baseline on the implemented physics and document initial gain values and any limitations.

**Done when:** PID can balance from a small range of initial angles, and gain changes have understandable effects. Do not claim robust balancing outside the tested initial range.

### Phase 5 — Fit and finish

1. Add responsive layout, accessible labels and focus indicators, and concise keyboard instructions.
2. Handle tab visibility, animation cleanup, invalid gain input, and numeric overflow gracefully.
3. Add a concise in-app model/controls explanation and link to any equation documentation.
4. Review the code boundaries to ensure a second model can be introduced without rewriting the session loop or controller API.

**Done when:** the app is understandable without reading source code and behaves predictably through normal interaction, reset, mode changes, and browser tab changes.

## Verification plan

Create Python automated checks for pure simulation/controller logic and manually exercise the browser UI and API. At minimum, verify:

- Zero force and zero damping produce the expected equilibrium behavior for an exactly upright, stationary pole.
- A small positive/negative pole angle accelerates in the expected direction under the documented convention.
- Force, cart bounds, and fall bounds are enforced consistently.
- Repeating the same initial state, parameters, actions, and time steps produces the same result.
- PID terms respond in the expected direction; output stays within limits; integral windup is controlled; reset clears accumulated state.
- Manual controls work from both keys and buttons, release cleanly, and do not interfere with editable fields.
- Pause freezes physics; reset restores the initial state; switching modes clears controller memory.
- Rendering remains legible at narrow and wide viewport sizes.
- Backend control events and state snapshots use a documented format; invalid input does not corrupt the simulation.

## Future expansion: double pendulum

When adding a double pendulum, define its own state and parameters (both angles and angular velocities, plus link masses and lengths), equations, reset options, and renderer. Reuse the session loop and common model boundary. Decide whether the second link is passive or actively controlled; a classic double pendulum without actuation cannot be balanced by the cart-pole PID controller. Add a controller suited to the new mechanism rather than assuming one PID implementation works for every model. Consider adding model selection only after the second model can be simulated and visualized independently.

Other likely extensions include a cart-pole with a second passive link, alternative controllers (such as state feedback or learned policies), noise and parameter variation, plots or recorded runs, and exportable experiment settings. Add them as independent models, controllers, or visualization features rather than mixing them into the initial cart-pole implementation.

## Risks and design notes

- **Controller tuning depends on physics conventions.** Fix the angle sign and force sign early and test them with simple inputs.
- **A visually plausible animation can hide unstable physics.** Keep physics stepping deterministic and separate from rendering.
- **Large frame delays can destabilize the loop.** Use fixed steps and cap catch-up work.
- **PID has limits.** Saturation, delays, large initial angles, and cart travel limits can prevent balancing; explain the supported operating range.
- **Double pendulum is a different control problem.** The shared model/session shape is useful, but equations, renderer, and balancing strategy will differ.

## Completion checklist for the first release

- [ ] Web app starts with documented commands.
- [ ] Inverted cart-pole is animated from simulation state.
- [ ] Manual arrow keys and buttons apply bounded force safely.
- [ ] PID balances from documented small initial offsets and exposes tunable gains.
- [ ] Start/pause/reset and mode switching behave consistently.
- [ ] State, units, mode, status, and actuator saturation are visible.
- [ ] Physics, controller, loop, and rendering responsibilities are separate.
- [ ] Verification steps and known limitations are documented.
- [ ] Python backend and JavaScript frontend have clear setup and run instructions.
