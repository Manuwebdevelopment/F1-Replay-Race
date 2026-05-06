"""
Sector Times insight window.

Shows sector 1, sector 2, sector 3, and total lap times for all drivers.
Highlights fastest sector and compares sector deltas to the leader.
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

_C1_COLOR = "#FF3333"   # Sector 1 (Red)
_C2_COLOR = "#00AAFF"   # Sector 2 (Blue)
_C3_COLOR = "#00CC66"   # Sector 3 (Green)
_TOTAL_COLOR = "#FFD700"


class SectorTimesWindow(PitWallWindow):
    """Current and delta sector times for all active drivers."""

    def __init__(self):
        self._current_laps: dict[str, dict] = {}   # code -> {s1, s2, s3, total}
        self._fastest_sector: dict[str, float] = {}  # sector -> fastest_time
        self._best_laps: dict[str, float] = {}       # code -> best lap time
        self._known_codes: list = []
        self._sectors_detected = False
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Sector Times")
        self.setMinimumSize(1000, 600)

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        # Stats row
        top_row = QHBoxLayout()
        self._lbl_fastest1 = QLabel("S1 Fastest: —")
        self._lbl_fastest2 = QLabel("S2 Fastest: —")
        self._lbl_fastest3 = QLabel("S3 Fastest: —")
        self._lbl_fastest1.setFont(QFont("Arial", 11))
        self._lbl_fastest2.setFont(QFont("Arial", 11))
        self._lbl_fastest3.setFont(QFont("Arial", 11))
        top_row.addWidget(self._lbl_fastest1)
        top_row.addWidget(self._lbl_fastest2)
        top_row.addWidget(self._lbl_fastest3)
        top_row.addStretch()
        root.addLayout(top_row)

        # Table for current lap sector times
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(5)
        self._tbl.setHorizontalHeaderLabels(["Driver", "S1", "S2", "S3", "Total"])
        header = self._tbl.horizontalHeader()
        header.setFont(QFont("Arial", 10, QFont.Bold))
        self._tbl.setFont(QFont("Arial", 10))
        self._tbl.setAlternatingRowColors(True)
        self._tbl.horizontalHeader().setSectionResizeMode(0, QTableWidget.ResizeToContents)
        root.addWidget(self._tbl)

        # Stacked bar chart of sector times
        self._fig = plt.figure(figsize=(12, 4), facecolor="#1a1a1a")
        self._canvas = FigureCanvas(self._fig)
        root.addWidget(self._canvas, stretch=1)

    # ── Update table ──

    def _update_table(self):
        self._tbl.setRowCount(len(self._current_laps))
        for i, (code, laps) in enumerate(self._current_laps.items()):
            self._tbl.setItem(i, 0, QTableWidgetItem(code))
            self._tbl.setItem(i, 1, QTableWidgetItem(self._format_time(laps.get("s1"))) if "s1" in laps else QTableWidgetItem("--: --.-"))
            self._tbl.setItem(i, 2, QTableWidgetItem(self._format_time(laps.get("s2"))) if "s2" in laps else QTableWidgetItem("--: --.-"))
            self._tbl.setItem(i, 3, QTableWidgetItem(self._format_time(laps.get("s3"))) if "s3" in laps else QTableWidgetItem("--: --.-"))
            total = laps.get("s1", 0) + laps.get("s2", 0) + laps.get("s3", 0)
            self._tbl.setItem(i, 4, QTableWidgetItem(self._format_time(total)))

            # Colour the sector times based on if they're the fastest
            for sector_col, sector_name in ((1, "s1"), (2, "s2"), (3, "s3")):
                item = self._tbl.item(i, sector_col)
                if item:
                    val = laps.get(sector_name)
                    if val is not None and self._fastest_sector.get(sector_name) == val:
                        item.setForeground(QColor("#FFD700"))

    @staticmethod
    def _format_time(seconds):
        if not seconds or seconds < 0:
            return "--: --.-"
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins:02d}:{secs:05.2f}"

    # ── Update chart ──

    def _update_chart(self):
        ax = self._fig.gca()
        ax.clear()

        codes = list(self._current_laps.keys())
        if not codes:
            return

        y_positions = list(reversed(range(len(codes))))

        for i, code in enumerate(codes):
            lap = self._current_laps[code]
            s1 = lap.get("s1") or 0
            s2 = lap.get("s2") or 0
            s3 = lap.get("s3") or 0
            total = s1 + s2 + s3

            # Build stacked bar
            ax.barh(y_positions[i], s1, left=0, color=_C1_COLOR, alpha=0.85)
            ax.barh(y_positions[i], s2, left=s1, color=_C2_COLOR, alpha=0.85)
            ax.barh(y_positions[i], s3, left=s1+s2, color=_C3_COLOR, alpha=0.85)

            ax.text(total + 0.2, y_positions[i],
                    f"{self._format_time(total)}", va="center", fontsize=9, color="white")

        ax.set_ylim(-0.5, len(codes))
        ax.set_yticks([])
        ax.set_xlabel("Sector Time (s)", color="#aaa", fontsize=10)
        ax.set_facecolor("#1a1a1a")
        ax.legend(["S1", "S2", "S3"], bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
        ax.set_axisbelow(True)
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

        for code in drivers:
            if code not in self._known_codes:
                self._known_codes.append(code)

        # Look for sector times in telemetry
        for code, info in drivers.items():
            if "lap_time" in info or "lapTime" in info:
                lap = self._current_laps.get(code, {})
                lap["s1"] = lap.get("s1") or float(info.get("sector1") or info.get("lapSegment", {}).get("sector1", 0)) / 1000
                lap["s2"] = lap.get("s2") or float(info.get("sector2") or info.get("lapSegment", {}).get("sector2", 0)) / 1000
                lap["s3"] = lap.get("s3") or float(info.get("sector3") or info.get("lapSegment", {}).get("sector3", 0)) / 1000
                # FIX: use raw numeric value, don't format to string then divide
                lap["total"] = float(info.get("lap_time") or info.get("lapTime") or 0) / 1000
                self._current_laps[code] = lap

                # Track fastest sectors
                for sec in ["s1", "s2", "s3"]:
                    val = lap[sec]
                    if val and val > 0:
                        if sec not in self._fastest_sector or val < self._fastest_sector[sec]:
                            self._fastest_sector[sec] = val

                # Track best lap
                total = lap.get("total") or (lap["s1"] + lap["s2"] + lap["s3"])
                if total > 0:
                    if code not in self._best_laps or total < self._best_laps[code]:
                        self._best_laps[code] = total

            # Also check for individual sector completion times
            for sec_name in ["sector1", "sector2", "sector3"]:
                sec_val = info.get(sec_name)
                if sec_val:
                    lap = self._current_laps.get(code, {})
                    lap[sec_name[-1]] = float(sec_val) / 1000
                    self._current_laps[code] = lap

        self._lbl_fastest1.setText(f"S1 Fastest: {self._format_time(self._fastest_sector.get('s1'))}")
        self._lbl_fastest2.setText(f"S2 Fastest: {self._format_time(self._fastest_sector.get('s2'))}")
        self._lbl_fastest3.setText(f"S3 Fastest: {self._format_time(self._fastest_sector.get('s3'))}")

        self._update_table()
        self._update_chart()

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._current_laps.clear()
            self._fastest_sector.clear()
            self._best_laps.clear()
            self._known_codes.clear()
            self._update_table()
            self._update_chart()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Sector Times")
    window = SectorTimesWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
