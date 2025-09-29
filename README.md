# PlugData Stage Controller

`stage_main.pd` is a top-level PlugData/Pure Data patch that orchestrates modules. It loads the abstractions under `patches/`, exposes simple transport controls for each, and mixes them through a shared master bus.

