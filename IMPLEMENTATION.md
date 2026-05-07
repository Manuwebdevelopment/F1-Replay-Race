# IMPLEMENTATION.md — f1-race-replay

**Last updated:** 2026-05-07
**Location:** `~/.hermes/projects/f1-race-replay/`
**Source of truth for all project decisions and state.**

---

## What the project is
Python F1 race telemetry visualizer. Replays races with driver positions on track, leaderboard, insights menu with telemetry analysis windows, safety car simulation, and live telemetry stream for custom tools.

## Current state

### What's done
- **Core replay engine** — Frame-by-frame race replay with driver positions on rendered track
- **Safety Car** — Simulated SC deployment/return with animation phases (deploying, on-track, returning)
- **GUI Menu System** — Graphical interface for year/round/session selection
- **CLI Menu System** — Arrow-key menu for session selection
- **Full Insights Menu** with 14 analysis windows:
  - Leaderboard (live positions, tyre compounds)
  - Gap Analysis, Sector Times, Pit Stop Analysis, Tyre Strategy
  - Lap Time Evolution, Speed Monitor, Position History
  - Track Position, Heatmap, Race Control Events, Telemetry Stream View
  - Driver Telemetry (per-driver: speed, gear, throttle, brake)
- **Telemetry Stream** — TCP socket on localhost:9999, JSON messages, real-time custom dashboard support
- **Qualifying Session Support** — In development, partial support
- **Custom Window Framework** - PitWallWindow base class for building custom insight windows
- **Interactive controls** — Pause/rewind/fast-forward with both GUI buttons and keyboard shortcuts
- **Git repo** — 3 commits in place (~/.hermes/projects/f1-race-replay/)

### What's modified but uncommitted
- `src/insights/leaderboard_window.py` — Modified (uncommitted)
- `src/insights/speed_monitor_window.py` — Modified (uncommitted)

### What remains
- **P0:** Commit uncommitted changes to leaderboard + speed_monitor windows (both have `M` status)
- **P1:** Real-hardware testing on F1 race data
- **P2:** Practice sessions (FP1/FP2/FP3) support — needs combination of qualifying telemetry + race position logic
- **P2:** Reduce replay rendering lag on lower-end devices
- **P2:** UI de-cluttering, toggle options, preset views
- **P3:** Expand to more historical seasons (current support is 2025+)

### Known issues
- Leaderboard inaccurate for first few corners
- Leaderboard affected when a driver goes to pits mid-race
- Leaderboard sometimes skewed at race end due to final x,y positions
- All caused by telemetry data inaccuracies — complex to fix incrementally

## Key file locations
- `src/f1_data.py` — Telemetry loading, processing, frame generation, SC position simulation
- `src/arcade_replay.py` — Visualization rendering loop
- `src/ui_components.py` — UI components (buttons, leaderboard)
- `src/gui/insights_menu.py` — Insights Menu
- `src/gui/pit_wall_window.py` — PitWallWindow base class
- `src/gui/race_selection.py` — Race selector
- `src/insights/` — All analysis insight windows
- `docs/PitWallWindow.md` — Guide for building custom windows
- `docs/InsightsMenu.md` — How to add insights

## Decisions
- **Rendering:** Arcade.py for the graphics engine
- **Telemetry data:** FastF1 Python library
- **Network protocol for stream:** TCP localhost:9999, newline-delimited JSON
- **Data caching:** Pre-computed telemetry in `computed_data/` directory
- **Custom windows:** PitWallWindow base class with `setup_ui()` and `on_telemetry_data()`

## Model usage per project
- **qwen3.6:23GB** — Architecture decisions, complex code changes, telemetry logic
- **gemma4:9.6GB** — Multi-step refactoring, UI work, insight window development
- **deepseek-coder:18GB** — Code generation, bug fixes
- **dolphin3:4.9GB** — Small UI adjustments, formatting, doc updates
- **aeline/phil:4.7GB** — Brainstorming new insights or features
