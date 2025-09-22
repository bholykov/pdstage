# PlugData Stage Controller

`stage_main.pd` is a top-level PlugData/Pure Data patch that orchestrates five of your existing modules from `Documents/Pd`. It loads the abstractions under `patches/`, exposes simple transport controls for each, and mixes them through a shared master bus.

## Modules and controls

When you open `stage_main.pd` in PlugData (with the `patches/` folder on the same path), it instantiates the following abstractions:

| Module | Patch file | Key sends | Notes |
| ------ | ---------- | --------- | ----- |
| Controlled Rhythm | `patches/controlled_rhythm_stage.pd` | `stage/controlled_rhythm/start`, `stage/controlled_rhythm/tempo`, `stage/controlled_rhythm/master` | Clocked kick/snare loop with tempo control. |
| Ambient Texture | `patches/ambient_stage.pd` | `stage/ambient/start` | Slow evolving pad generator. |
| New Drone | `patches/new_drone_stage.pd` | `stage/new_drone/start`, `stage/new_drone/click`, `stage/new_drone/master` | Layered drone with optional click pulses. |
| Noise Texture | `patches/some_new_shit_stage.pd` | `stage/noise/start`, `stage/noise/cutoff` | Filtered noise sweeps. |
| Rich Ambient | `patches/rich_ambient_stage.pd` | `stage/rich/start` | Long-form harmonic pad engine. |

Each channel has a mix slider (`stage/mix/<name>`) that feeds the main bus. A master slider (`stage/master/level`) controls the final level before audio hits `dac~`.

## Signal flow

- Every module throws audio to its own stereo pair (e.g. `stage/new_drone/L` and `/R`).
- `stage_main.pd` catches those pairs, applies the per-channel mix gain, and throws them into `stage/mix_bus/L/R`.
- The master section catches the mix bus, applies `stage/master/level`, and routes to `dac~`.

Because the subpatches use throw~/catch~ pairs, you can drop additional effects or recorders onto the shared bus by tapping `stage/mix_bus/L` and `stage/mix_bus/R`.

## Default behaviour

A `loadbang` inside `stage_main.pd` sets sensible defaults:

- Starts the rhythmic, ambient, drone, and rich patches.
- Leaves the noise texture idle until you toggle it.
- Sets initial mix and tempo values so you get sound right away.

Adjust any of the sliders or toggles in the controller window—everything updates the underlying abstractions through their send/receive bindings. You can still open the individual patches (they are ordinary abstractions) if you want to tweak internals or add new controls.

## Extending the stage

- To add a new module, copy the patch into `patches/`, swap any direct `dac~` objects for `throw~ stage/<module>/L` and `/R`, give your UI elements `stage/<module>/...` send names, and add a channel strip in `stage_main.pd` that catches and mixes its audio.
- Use the existing modules as templates: each one is already adapted for remote control and mixing.

Enjoy building the set! If you run into clipping, pull back the per-channel mixes or the master slider—everything stays in one place now.

Keep `stage_main.pd` and the `patches/` directory together; the controller instantiates each module via `patches/<name>`, so opening `stage_main.pd` from that folder ensures everything resolves.
