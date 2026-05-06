"""
Gap Analysis insight window.

Shows the time gap and distance gap between all drivers and the leader
in real-time. Useful for understanding race pacing and chase sequences.
"""

import sys
from collections import deque
from datetime import timedelta

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel
)
from PySide6.QtGui import QFont
from src.gui.pit_wall_window import PitWallWindow

_TIME_WINDOW = 120        # seconds for rolling history


class GapAnalysisWindow(PitWallWindow):
    """Gaps between all drivers and the race leader."""

    def __init__(self):
        self._driver_gaps: dict[str, float] = {}   # code -> gap to leader (seconds)
        self._driver_dist_gaps: dict[str, float] = {}   # code -> distance gap (metres)
        self._leader_code: str = ""
        self._gap_history: dict[str, deque] = {}
        self._known_codes: list = []
        self._max_history = 300
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Gap Analysis")
        self.setMinimumSize(900, 500)

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        self._lbl_leader = QLabel("Leader: —")
        self._lbl_leader.setFont(QFont("Arial", 12, QFont.Bold))
        root.addWidget(self._lbl_leader)

        self._fig = plt.figure(figsize=(12, 6), facecolor="#1a1a1a")
        self._canvas = FigureCanvas(self._fig)
        root.addWidget(self._canvas, stretch=1)

    # ── Redraw ──

    def _redraw(self):
        ax = self._fig.gca()
        ax.clear()

        if not self._driver_gaps:
            self._fig.text(0.5, 0.5, "No gap data yet", ha="center",
                           va="center", color="#666", fontsize=16)
            self._canvas.draw_idle()
            return

        codes = [c for c in self._driver_gaps if c != self._leader_code]
        gaps = [self._driver_gaps.get(c, 0) for c in codes]

        # Sort by gap (smallest first, i.e., closest to leader)
        sorted_pairs = sorted(zip(codes, gaps), key=lambda x: x[1])
        sorted_codes, sorted_gaps = zip(*sorted_pairs) if sorted_pairs else ([], [])

        y_pos = list(reversed(range(len(sorted_codes))))

        for i, (c, g) in enumerate(zip(sorted_codes, sorted_gaps)):
            # Colour: green if close (< 2s), yellow if moderate (< 5s), red if far
            if g < 2:
                col = "#2ECC71"
            elif g < 5:
                col = "#FFD700"
            else:
                col = "#E74C3C"

            ax.barh(y_pos[i], g, color=col, edgecolor="#444", linewidth=0.5, alpha=0.85)
            label = f"{c} +{g:.3f}s" if g > 0 else c
            ax.text(g + 0.02, y_pos[i], label, va="center",
                    fontsize=9, color="white")

        # Leader is at position 0, draw as a thick bar
        if self._leader_code:
            ax.barh(len(sorted_codes), 1, color="#FFD700", edgecolor="#B8860B",
                    linewidth=1, alpha=1)

        ax.set_ylim(-0.5, len(sorted_codes) + 0.5)
        ax.set_xlim(0, max(10, max(sorted_gaps) * 1.2) if sorted_gaps else 10)
        ax.set_yticks([])
        ax.set_xlabel("Gap to Leader (seconds)", color="#aaa", fontsize=10)
        ax.set_facecolor("#1a1a1a")
        ax.set_axisbelow(True)

        # Add DRS zone annotation (if applicable)
        if sorted_gaps and max(sorted_gaps) < 1.0:
            ax.axvspan(0, 1.0, alpha=0.05, color="green", label="DRS Zone")

        ax.legend(fontsize=8)
        ax.tick_params(colors="#aaa")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

        self._canvas.draw_idle()

    # ── Telemetry handlers ──

    def on_telemetry_data(self, data):
        frame = data.get("frame")
        if not frame or "drivers" not in frame:
            return

        drivers = frame["drivers"]

        # Find leader
        leader_code = None
        for code, info in drivers.items():
            if info.get("position") == 1:
                leader_code = code
                break

        if leader_code:
            self._leader_code = leader_code
            self._lbl_leader.setText(f"Leader: {leader_code}")

        self._ensure_history(leader_code)

        for code in drivers:
            if code not in self._known_codes:
                self._known_codes.append(code)
            self._ensure_history(code)

        # Compute gaps using distance from start line
        max_dist = 0
        max_dist_driver = None
        for code, info in drivers.items():
            dist = info.get("dist", 0)
            if dist > max_dist:
                max_dist = dist
                max_dist_driver = code

        # Use leader's distance as reference
        leader_dist = drivers.get(leader_code, {}).get("dist", 0) if leader_code else 0

        for code, info in drivers.items():
            if code == leader_code:
                self._driver_gaps[code] = 0
                self._driver_dist_gaps[code] = 0
                continue

            # Use distance-based gap calculation
            dist_driver = info.get("dist", 0)
            leader_info = drivers.get(leader_code, {})
            dist_leader = leader_info.get("dist", 0)

            # Gap in distance (metres)
            self._driver_dist_gaps[code] = dist_leader - dist_driver

            # Estimated time gap (approximate using speed)
            speed_driver = info.get("speed", 100)
            speed_leader = leader_info.get("speed", 100)
            speed_leader = max(speed_leader, 1)

            if speed_leader > 0:
                time_gap = (self._driver_dist_gaps[code] / (speed_leader * 1000 / 3600))
                self._driver_gaps[code] = max(0, time_gap)
            else:
                self._driver_gaps[code] = 0

            # History
            session_t = data.get("t", 0)
            self._gap_history[code].append((session_t, self._driver_gaps[code]))

        self._redraw()

    def _ensure_history(self, code):
        if code and code not in self._gap_history:
            self._gap_history[code] = deque(maxlen=self._max_history)

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._driver_gaps.clear()
            self._driver_dist_gaps.clear()
            self._leader_code = ""
            self._known_codes.clear()
            self._lbl_leader.setText("Leader: —")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Gap Analysis")
    window = GapAnalysisWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
