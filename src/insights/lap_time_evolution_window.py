"""
Lap Time Evolution insight window.

Shows lap time progression for a selected driver over the race.
Colour-coded by tyre compound, with best/worst lap markers.
"""

import sys

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
)
from PySide6.QtGui import QFont
from src.gui.pit_wall_window import PitWallWindow

TYRE_COLORS = {
    "SOFT": "#FF3333", "MEDIUM": "#FFD700", "HARD": "#FFFFFF",
    "INTERMEDIATE": "#00AA00", "WET": "#0080FF",
}


class LapTimeEvolutionWindow(PitWallWindow):
    """Lap time progression for a selected driver."""

    def __init__(self):
        self._lap_times: dict[str, list] = {}       # code -> [(lap_n, time_s, tyre_compound)]
        self._best_laps: dict[str, float] = {}       # code -> best lap time
        self._worst_laps: dict[str, float] = {}      # code -> worst lap time
        self._driver_combo_data: dict[str, str] = {}  # combo text -> code mapping
        self._selected_driver = ""
        self._known_codes: list = []
        self._last_processed_lap: dict[str, int] = {}  # code -> last processed lap number
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Lap Time Evolution")
        self.setMinimumSize(900, 500)

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        control_row = QHBoxLayout()

        driver_label = QLabel("Driver:")
        driver_label.setFont(QFont("Arial", 11))
        self._driver_combo = QComboBox()
        self._driver_combo.setMinimumWidth(120)
        self._driver_combo.currentTextChanged.connect(self._on_driver_changed)
        control_row.addWidget(driver_label)
        control_row.addWidget(self._driver_combo)
        control_row.addStretch()

        self._lbl_best = QLabel("Best lap: —")
        self._lbl_best.setFont(QFont("Arial", 10))
        control_row.addWidget(self._lbl_best)

        self._lbl_worst = QLabel("Worst lap: —")
        self._lbl_worst.setFont(QFont("Arial", 10))
        control_row.addWidget(self._lbl_worst)

        root.addLayout(control_row)

        self._fig = plt.figure(figsize=(12, 6), facecolor="#1a1a1a")
        self._canvas = FigureCanvas(self._fig)
        root.addWidget(self._canvas, stretch=1)

    def _on_driver_changed(self, text: str):
        self._selected_driver = self._driver_combo_data.get(text, text)
        self._redraw()

    def _format_time(self, s):
        if not s or s <= 0:
            return "--:--.-"
        m = int(s // 60)
        sec = s % 60
        return f"{m:02d}:{sec:05.2f}"

    # ── Redraw ──

    def _redraw(self):
        ax = self._fig.gca()
        ax.clear()

        if not self._selected_driver or self._selected_driver not in self._lap_times:
            self._fig.text(0.5, 0.5, "No data for selected driver", ha="center",
                           va="center", color="#666", fontsize=16)
            self._canvas.draw_idle()
            return

        times = self._lap_times[self._selected_driver]
        if not times:
            self._fig.text(0.5, 0.5, "No laps yet", ha="center",
                           va="center", color="#666", fontsize=16)
            self._canvas.draw_idle()
            return

        laps = [t[0] for t in times]
        times_s = [t[1] for t in times]
        compounds = [t[2] for t in times]

        # Plot bars by tyre compound
        for i, (lap_n, time_s, comp) in enumerate(times):
            col = TYRE_COLORS.get(comp, "#888888")
            ax.barh(i, time_s * 0.4, left=lap_n, height=0.35,
                    color=col, alpha=0.8, edgecolor="#444444", linewidth=0.5)
            ax.plot(lap_n, time_s, "o", color=col, markersize=5, alpha=0.8)

        ax.invert_yaxis()
        ax.set_ylabel("Lap Number", color="#aaaaaa", fontsize=10)
        ax.set_xlabel("Lap Time (s)", color="#aaaaaa", fontsize=10)
        ax.set_facecolor("#1a1a1a")
        ax.set_axisbelow(True)
        ax.legend(fontsize=8, loc="upper right")
        ax.tick_params(colors="#aaaaaa")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444444")

        self._canvas.draw_idle()

    # ── Telemetry handlers ──

    def on_telemetry_data(self, data):
        frame = data.get("frame")
        if not frame or "drivers" not in frame:
            return

        drivers = frame["drivers"]

        for code in drivers:
            if code not in self._known_codes:
                self._known_codes.append(code)
                self._lap_times[code] = []
                self._best_laps[code] = float("inf")
                self._worst_laps[code] = 0
                self._driver_combo_data[code] = code
                self._driver_combo.addItem(code)

        for code, info in drivers.items():
            lap = int(info.get("lap", 0))
            if not lap:
                continue

            last_lap = self._last_processed_lap.get(code, 0)

            # Only process a new lap when lap number increments
            if lap <= last_lap:
                continue
            self._last_processed_lap[code] = lap

            # Get lap time (ms -> s)
            lap_time = info.get("lap_time") or info.get("lapTime", 0)
            if lap_time:
                lap_time_s = float(lap_time) / 1000
                tyre = info.get("tyre_compound") or info.get("compound", "UNKNOWN")
                self._lap_times[code].append((lap, lap_time_s, tyre))

                if lap_time_s < self._best_laps[code]:
                    self._best_laps[code] = lap_time_s
                if lap_time_s > self._worst_laps[code]:
                    self._worst_laps[code] = lap_time_s

        if self._selected_driver:
            self._lbl_best.setText(f"Best: {self._format_time(self._best_laps.get(self._selected_driver))}")
            self._lbl_worst.setText(f"Worst: {self._format_time(self._worst_laps.get(self._selected_driver))}")

        self._redraw()

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._lap_times.clear()
            self._best_laps.clear()
            self._worst_laps.clear()
            self._selected_driver = ""
            self._driver_combo.clear()
            self._driver_combo_data.clear()
            self._last_processed_lap.clear()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Lap Time Evolution")
    window = LapTimeEvolutionWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
