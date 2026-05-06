"""
Pit Stop Analysis insight window.

Tracks and visualises pit stop events: timing, stop duration, tyre changes,
and overall strategy effectiveness.
"""

import sys
from collections import defaultdict
from datetime import timedelta

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem
)
from PySide6.QtGui import QFont, QColor
from src.gui.pit_wall_window import PitWallWindow
from src.insights.colours import TYRE_COLOURS


class PitStopAnalysisWindow(PitWallWindow):
    """Analysis of all pit stops: timing, compounds, duration."""

    def __init__(self):
        self._stops: list = []   # [{code, lap, time, duration, from, to, frame}]
        self._last_tyre: dict[str, str] = {}
        self._stop_start: dict[str, float] = {}
        self._active_stopping: dict[str, str] = {}  # code -> start_lap
        self._known_codes: list = []
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Pit Stop Analysis")
        self.setMinimumSize(1000, 600)
        self._total_stops = 0
        self._fastest_stop = None

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        # Top stats
        top_row = QHBoxLayout()
        self._lbl_total = QLabel("Total stops: 0")
        self._lbl_fastest = QLabel("Fastest stop: —")
        self._lbl_total.setFont(QFont("Arial", 11))
        self._lbl_fastest.setFont(QFont("Arial", 11))
        top_row.addWidget(self._lbl_total)
        top_row.addWidget(self._lbl_fastest)
        top_row.addStretch()
        root.addLayout(top_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["Driver", "Lap", "Time", "Duration", "From", "To"])
        header = self._table.horizontalHeader()
        header.setFont(QFont("Arial", 10, QFont.Bold))
        self._table.setFont(QFont("Arial", 10))
        self._table.setAlternatingRowColors(True)
        root.addWidget(self._table)

        # Chart of stop times
        self._fig = plt.figure(figsize=(12, 3), facecolor="#1a1a1a")
        self._canvas = FigureCanvas(self._fig)
        root.addWidget(self._canvas, stretch=1)

    def _update_table(self):
        self._table.setRowCount(len(self._stops))
        for i, stop in enumerate(self._stops):
            self._table.setItem(i, 0, QTableWidgetItem(stop["code"]))
            self._table.setItem(i, 1, QTableWidgetItem(str(stop["lap"])))
            self._table.setItem(i, 2, QTableWidgetItem(stop["time_str"]))
            self._table.setItem(i, 3, QTableWidgetItem(stop["duration"] or "Active"))
            self._table.setItem(i, 4, QTableWidgetItem(stop["from"] or "—"))
            self._table.setItem(i, 5, QTableWidgetItem(stop["to"] or "—"))
            # Colour the tyre compounds
            for col in (4, 5):
                item = self._table.item(i, col)
                if item:
                    compound = item.text()
                    if compound in TYRE_COLOURS:
                        item.setForeground(QColor(TYRE_COLOURS[compound]))

    def _update_chart(self):
        ax = self._fig.gca()
        ax.clear()

        stops_by_driver = defaultdict(list)
        for stop in self._stops:
            stops_by_driver[stop["code"]].append(stop)

        drivers_list = sorted(stops_by_driver.keys())
        for j, driver in enumerate(drivers_list):
            stops = stops_by_driver[driver]
            for k, stop in enumerate(stops):
                duration = self._parse_duration(stop["duration"])
                color = TYRE_COLOURS.get(stop["to"], "#888")
                ax.barh(j, duration, left=sum(
                    self._parse_duration(s["duration"]) for s in stops[:k]
                ), color=color, alpha=0.8)
                ax.text(sum(self._parse_duration(s["duration"]) for s in stops[:k+1]) + 0.1, j,
                        f"Lap {stop['lap']}", va="center", fontsize=8)
                # Use driver label on first bar only to avoid overlap
                if k == 0:
                    ax.text(-0.5, j, driver, va="center", fontsize=9, ha="right", color="white")

        ax.invert_yaxis()
        ax.set_xlabel("Stop Duration (s)", color="#aaa")
        ax.set_facecolor("#1a1a1a")
        ax.tick_params(colors="#aaa")
        # Show y ticks for drivers
        if drivers_list:
            ax.set_yticks(range(len(drivers_list)))
            ax.set_yticklabels(drivers_list)

        self._canvas.draw_idle()

    @staticmethod
    def _parse_duration(duration_str):
        """Parse '12.3s' style strings to float."""
        if not duration_str:
            return 0.0
        try:
            return float(duration_str.replace("s", ""))
        except (ValueError, AttributeError):
            return 0.0

    def _redraw(self):
        self._update_table()
        self._update_chart()

    # ── Telemetry handlers ──

    def on_telemetry_data(self, data):
        frame = data.get("frame")
        if not frame or "drivers" not in frame:
            return

        drivers = frame["drivers"]

        for code, info in drivers.items():
            if code not in self._known_codes:
                self._known_codes.append(code)

            tyre = info.get("tyre_compound", "") or info.get("compound", "")
            lap = int(info.get("lap", 0))
            speed = float(info.get("speed", 0))

            # Active pit lane: slow speed + tyre present (not compound change on lap 0)
            if 0 < speed < 80 and tyre and lap > 0:
                if code not in self._active_stopping:
                    self._active_stopping[code] = lap
                    self._stop_start[code] = data.get("time", 0)
                continue

            # Check for pit stop completion (tyre compound changed after a pit lane event)
            last_tyre = self._last_tyre.get(code)
            if last_tyre and tyre and last_tyre != tyre:
                duration_s = data.get("time", 0) - self._stop_start.get(code, 0)
                stop_entry = {
                    "code": code,
                    "lap": lap,
                    "time_str": str(timedelta(seconds=int(data.get("time", 0)))),
                    "duration": f"{duration_s:.1f}s",
                    "from": last_tyre,
                    "to": tyre,
                }
                self._stops.append(stop_entry)
                self._total_stops += 1
                self._lbl_total.setText(f"Total stops: {self._total_stops}")

                # Track fastest stop
                if self._fastest_stop is None or float(stop_entry["duration"][:-1]) < float(
                        self._fastest_stop["duration"][:-1]):
                    self._fastest_stop = stop_entry
                    self._lbl_fastest.setText(f"Fastest stop: {self._fastest_stop['duration']} (Lap {self._fastest_stop['lap']})")

                self._last_tyre[code] = tyre
                self._active_stopping.pop(code, None)
                # Update chart on new stop
                self._update_chart()

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._stops.clear()
            self._known_codes.clear()
            self._last_tyre.clear()
            self._active_stopping.clear()
            self._total_stops = 0
            self._fastest_stop = None
            self._lbl_total.setText("Total stops: 0")
            self._lbl_fastest.setText("Fastest stop: —")
            self._table.setRowCount(0)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pit Stop Analysis")
    window = PitStopAnalysisWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
