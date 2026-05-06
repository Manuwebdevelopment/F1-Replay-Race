"""
Speed Monitor insight window.

Shows live speed as thick horizontal bars for all drivers, sorted by speed.
Highlights the fastest car and shows the delta to the leader.
"""

import sys
import math
from collections import deque

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton
)
from PySide6.QtGui import QFont
from src.gui.pit_wall_window import PitWallWindow
from src.insights.colours import TEAM_COLOURS, _DEFAULT_COL, DRIVER_TEAM_MAP

_TIME_WINDOW = 60        # seconds kept in rolling-time mode
_MAX_SPEED = 380         # km/h

# Helper: get driver colour by looking up driver → team → colour
def _get_driver_colour(code: str) -> str:
    team = DRIVER_TEAM_MAP.get(code, DRIVER_TEAM_MAP.get(code.upper(), ""))
    return TEAM_COLOURS.get(team, TEAM_COLOURS.get(code.upper(), _DEFAULT_COL))

# For backward compatibility with existing code
_TEAM_COLOURS = _get_driver_colour
# Default colour for unknown drivers
_DEFAULT_COL = "#FFFFFF"


class SpeedMonitorWindow(PitWallWindow):
    """Horizontal speed bars for all active drivers."""

    def __init__(self):
        self._speed_history: dict[str, deque] = {}
        self._max_history = 300
        self._driver_speeds: dict = {}
        self._known_codes: list = []
        self._show_history = False
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Speed Monitor")
        self.setMinimumSize(960, 480)

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        control_row = QHBoxLayout()

        self._lbl_mode = QLabel("Mode:")
        self._lbl_mode.setFont(QFont("Arial", 11))
        self._combo_mode = QComboBox()
        self._combo_mode.addItems(["Current Lap", "Historical"])
        self._combo_mode.currentIndexChanged.connect(self._on_toggle_history)
        control_row.addWidget(self._lbl_mode)
        control_row.addWidget(self._combo_mode)
        control_row.addStretch()

        self._lbl_fastest = QLabel("Fastest: —")
        self._lbl_fastest.setFont(QFont("Arial", 11))
        control_row.addWidget(self._lbl_fastest)

        root.addLayout(control_row)

        self._fig = plt.figure(figsize=(12, 6), facecolor="#1a1a1a")
        self._canvas = FigureCanvas(self._fig)
        root.addWidget(self._canvas, stretch=1)

    # ── History toggle ──

    def _on_toggle_history(self, idx: int):
        self._show_history = (idx == 1)
        self._redraw(self._driver_speeds)

    # ── Redraw ──

    def _redraw(self, speeds: dict):
        if not speeds:
            self._fig.clear()
            self._fig.text(0.5, 0.5, "No speed data yet", ha="center",
                           va="center", color="#666", fontsize=16)
            self._canvas.draw_idle()
            return

        ax = self._fig.gca()
        ax.clear()

        if not self._show_history:
            self._draw_current(ax, speeds)
        else:
            self._draw_history(ax)

        ax.set_facecolor("#1a1a1a")
        self._canvas.draw_idle()

    def _draw_current(self, ax, speeds):
        c = list(speeds.keys())
        spd_vals = list(speeds.values())

        # Sort by speed descending
        indices = sorted(range(len(spd_vals)), key=lambda i: spd_vals[i], reverse=True)
        sorted_c = [c[i] for i in indices]
        sorted_spd = [spd_vals[i] for i in indices]

        # Y positions (reversed so fastest is at top)
        y_pos = list(reversed(range(len(sorted_c))))

        for i, (c, s) in enumerate(zip(sorted_c, sorted_spd)):
            col = _TEAM_COLOURS.get(c, _DEFAULT_COL)
            # Use hex directly - strip alpha if present
            if col.startswith('#'):
                try:
                    col_rgb = tuple(int(col[i:i+2], 16) / 255.0 for i in (1, 3, 5))[:3] + (1.0,)
                except ValueError:
                    col_rgb = (1.0, 1.0, 1.0, 1.0)
            else:
                col_rgb = (1.0, 1.0, 1.0, 1.0)

            bar = mpatches.FancyBboxPatch((0, y_pos[i] - 0.35), s / _MAX_SPEED, 0.7,
                                          facecolor=col_rgb, edgecolor="#555", linewidth=0.5,
                                          boxstyle="round,pad=0.02")
            ax.add_patch(bar)

            # Code label
            ax.text(s / _MAX_SPEED + 0.005, y_pos[i], c, va="center",
                    fontsize=10, color="white", weight="bold")

            # Speed value
            ax.text(s / _MAX_SPEED - 0.02, y_pos[i], f"{s:.0f}", va="center",
                    fontsize=9, color="white", ha="right")

        # Fastest driver
        if sorted_c and sorted_spd:
            fastest_code = sorted_c[0]
            fastest_spd = sorted_spd[0]
            self._lbl_fastest.setText(f"Fastest: {fastest_code} @ {fastest_spd:.0f} km/h")

        ax.set_xlim(0, 1.05)
        ax.set_ylim(-0.5, len(sorted_c))
        ax.set_xlabel("Speed (km/h)", color="#aaa", fontsize=10)
        ax.set_yticks([])
        ax.tick_params(colors="#aaa")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")
        ax.set_axisbelow(True)

    def _draw_history(self, ax):
        """Draw speed history for all drivers."""
        for code in self._known_codes:
            col = _TEAM_COLOURS.get(code, _DEFAULT_COL)
            hist = self._speed_history.get(code)
            if hist and len(hist) > 1:
                ax.plot([h[0] for h in hist], [h[1] for h in hist],
                        color=col, linewidth=1.2, label=code)
        if not self._speed_history:
            ax.text(0.5, 0.5, "No speed history yet",
                    transform=ax.transAxes, ha="center", va="center", fontsize=14, color="#666")
            ax.set_xlabel("Frame", color="#aaa", fontsize=10)
            ax.set_ylabel("Speed (km/h)", color="#aaa", fontsize=10)
            ax.legend(fontsize=8, loc="upper right")
            ax.set_axisbelow(True)
            return

        ax.set_xlabel("Frame", color="#aaa", fontsize=10)
        ax.set_ylabel("Speed (km/h)", color="#aaa", fontsize=10)
        ax.invert_xaxis()
        ax.legend(fontsize=8, loc="upper right")
        ax.set_axisbelow(True)

    # ── Telemetry handlers ──

    def on_telemetry_data(self, data):
        frame = data.get("frame")
        if not frame or "drivers" not in frame:
            return

        drivers = frame["drivers"]
        speeds = {}
        for code, info in drivers.items():
            spd = float(info.get("speed") or 0)
            speeds[code] = spd

        # Track known codes and record history
        for code in speeds:
            if code not in self._known_codes:
                self._known_codes.append(code)
                self._speed_history[code] = deque(maxlen=self._max_history)

        # Record history
        if speeds:
            frame_idx = data.get("frame_index", 0) if "frame_index" in data else len(speeds)
            for code, spd in speeds.items():
                self._speed_history[code].append((frame_idx, spd))

        self._driver_speeds = speeds
        self._redraw(speeds)

    def on_connection_status_changed(self, status):
        pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Speed Monitor")
    window = SpeedMonitorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
