"""
Position History insight window.

Shows driver positions over the course of the race as a line chart.
Tracks position changes for overtakes and pit-stop effects.
"""

import sys
from collections import deque

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtGui import QFont
from src.gui.pit_wall_window import PitWallWindow

_TIME_WINDOW = 90        # seconds kept in rolling-time mode
_MAX_LAPS = 300


class PositionHistoryWindow(PitWallWindow):
    """Historical driver positions over the race."""

    def __init__(self):
        self._history: dict[str, deque] = {}   # code -> deque of (frame_idx, position)
        self._known_codes: list = []
        self._last_positions: dict[str, int] = {}
        self._overtakes: list = []
        self._max_frames = 500
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Position History")
        self.setMinimumSize(900, 500)

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        self._lbl_overtakes = QLabel("Overtakes: 0")
        self._lbl_overtakes.setFont(QFont("Arial", 11))
        root.addWidget(self._lbl_overtakes)

        self._fig = plt.figure(figsize=(12, 6), facecolor="#1a1a1a")
        self._canvas = FigureCanvas(self._fig)
        root.addWidget(self._canvas, stretch=1)

    # ── Redraw ──

    def _ensure_history(self, code: str):
        if code not in self._history:
            self._history[code] = deque(maxlen=self._max_frames)

    def _redraw(self):
        ax = self._fig.gca()
        ax.clear()

        for code in self._known_codes:
            hist = self._history.get(code)
            if not hist:
                continue
            xs = [h[0] for h in hist]
            ys = [h[1] for h in hist]
            ax.plot(xs, ys, label=code, linewidth=1.5, alpha=0.8)

        # Invert Y so position 1 is at top
        ax.invert_yaxis()
        ax.set_xlabel("Frame Index", color="#aaa", fontsize=10)
        ax.set_ylabel("Position", color="#aaa", fontsize=10)
        ax.set_ylim(1, max(20, len(self._known_codes) + 2))
        ax.set_yticks(range(1, max(20, len(self._known_codes) + 2)))
        ax.legend(fontsize=8, loc="upper right")
        ax.set_facecolor("#1a1a1a")
        ax.set_axisbelow(True)
        ax.grid(alpha=0.15)
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")
        ax.tick_params(colors="#aaa")

        self._canvas.draw_idle()

    # ── Telemetry handlers ──

    def on_telemetry_data(self, data):
        frame = data.get("frame")
        if not frame or "drivers" not in frame:
            return

        frame_idx = data.get("frame_index", 0)
        drivers = frame["drivers"]

        # Track known codes
        for code in drivers:
            if code not in self._known_codes:
                self._known_codes.append(code)
                self._ensure_history(code)

        # Compute positions
        positions = {}
        for code, info in drivers.items():
            position = info.get("position")
            if position and position > 0:
                positions[code] = int(position)
            else:
                dist = info.get("dist", 0)
                positions[code] = dist

        # Detect overtakes (position changes)
        for code, pos in positions.items():
            prev = self._last_positions.get(code)
            if prev is not None and pos < prev:
                self._overtakes.append((frame_idx, code, pos))
            self._last_positions[code] = pos

        self._lbl_overtakes.setText(f"Overtakes detected: {len(self._overtakes)}")

        # Record positions
        for code in self._known_codes:
            self._ensure_history(code)
            pos = positions.get(code, 0)
            if pos > 0:
                self._history[code].append((frame_idx, pos))

        self._redraw()

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._history.clear()
            self._known_codes.clear()
            self._last_positions.clear()
            self._overtakes.clear()
            self._lbl_overtakes.setText("Overtakes: 0")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Position History")
    window = PositionHistoryWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
