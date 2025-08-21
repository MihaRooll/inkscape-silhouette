# Plotter State Functions

This directory contains a copy of the core implementation for querying the
state of a Silhouette cutter and controlling blade depth.

## Files

- `Graphtec.py` – copy of `silhouette/Graphtec.py`. It provides:
  - `SilhouetteCameo.status()` – send `CMD_ENQ` and return `'ready'`, `'moving'` or `'unloaded'`.
  - `SilhouetteCameo.wait_for_ready()` – poll `status()` until the device reports `'ready'`.
  - `SilhouetteCameoTool.depth()` – form the `TF{depth}` command to set the blade depth.
  - `SilhouetteCameo.setup(autoblade=True, depth=<0–10>)` – automatically set the blade depth when an AutoBlade is installed in tool holder 1.

## Usage

```python
from PLOTTER_STATE.Graphtec import SilhouetteCameo, SilhouetteCameoTool

cutter = SilhouetteCameo(dry_run=True)
print(cutter.status())          # -> 'ready', 'moving' or 'unloaded'
print(cutter.wait_for_ready())  # blocks until state is 'ready'

tool = SilhouetteCameoTool(toolholder=1)
print(tool.depth(5))            # -> 'TF5,1'
```

Use `SilhouetteCameo.setup(autoblade=True, depth=5)` to automatically adjust
the AutoBlade in tool holder 1 to depth 5.
