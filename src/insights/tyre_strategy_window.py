"""
Tyre Strategy insight window.

Shows tyre compound and age for each driver as a stacked bar chart,
highlighting pit stop events and tyre strategy patterns.
"""

import sys
from collections import defaultdict

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtGui import QFont
from src.gui.pit_wall_window import PitWallWindow

# Tyre compound colours (F1 standard)
TYRE_COLOURS = {
    "SOFT":    "#FF3333",   # Red
    "MEDIUM":  "#FFD700",   # Yellow/Gold
    "HARD":    "#FFFFFF",    # White
    "INTERMEDIATE": "#00AA00",  # Green
    "WET":     "#0080FF",    # Blue
}


class TyreStrategyWindow(PitWallWindow):
    """Tyre compound and age for all drivers at a glance."""

    def __init__(self):
        self._driver_tyres: dict[str, dict] = {}   # code -> {compound, age}
        self._pit_stops: list = []   # [(frame, code, lap, from_compound, to_compound)]
        self._known_codes: list = []
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Tyre Strategy")
        self.setMinimumSize(800, 500)

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        control_row = QHBoxLayout()
        self._lbl_stops = QLabel("Pit stops: 0")
        self._lbl_stops.setFont(QFont("Arial", 11))
        control_row.addWidget(self._lbl_stops)
        control_row.addWidget(QLabel("Legend:"))
        for compound, colour in TYRE_COLOURS.items():
            # Just show a small label per compound
            lbl = QLabel(f"■ {compound} ({colour})")
            lbl.setFont(QFont("Arial", 8))
            lbl.setStyleSheet(f"color: {colour};")
            control_row.addWidget(lbl)
        control_row.addStretch()
        root.addLayout(control_row)

        self._fig = plt.figure(figsize=(12, 6), facecolor="#1a1a1a")
        self._canvas = FigureCanvas(self._fig)
        root.addWidget(self._canvas, stretch=1)

    # ── Redraw ──

    def _redraw(self):
        ax = self._fig.gca()
        ax.clear()

        codes = self._known_codes
        if not codes:
            self._fig.text(0.5, 0.5, "No tyre data yet", ha="center",
                           va="center", color="#666", fontsize=16)
            self._canvas.draw_idle()
            return

        y_positions = list(reversed(range(len(codes))))

        for i, code in enumerate(codes):
            tyre = self._driver_tyres.get(code, {})
            compound = tyre.get("compound", "UNKNOWN")
            age = int(tyre.get("age", 0))

            colour = TYRE_COLOURS.get(compound, "#888888")
            width = 0.7 if compound in TYRE_COLOURS else 0.3

            # Label
            label = f"{code} ({compound} {age} laps)"
            ax.text(0.02, y_positions[i], label, va="center", fontsize=9, color="white")

            ax.barh(y_positions[i], width, left=0, color=colour,
                    edgecolor="#444", linewidth=0.5, alpha=0.9)

        ax.set_ylim(-0.5, len(codes))
        ax.set_xlim(0, 4)
        ax.set_yticks([])
        ax.set_xlabel("Laps on tyre", color="#aaa", fontsize=10)

        # Add pit stop annotations
        pit_stops = self._pit_stops[-10:]
        for pit_frame, code, lap, frm, to_comp in pit_stops:
            pos = y_positions[codes.index(code)] if code in codes else 0
            ax.text(0.5, pos, f"🏁 L{lap}", va="center", fontsize=10,
                    color="#FFD700", rotation=270)

        ax.set_facecolor("#1a1a1a")
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
        frame_idx = data.get("frame_index", 0)

        # Track known codes
        for code in drivers:
            if code not in self._known_codes:
                self._known_codes.append(code)

        # Update tyre data
        for code, info in drivers.items():
            compound = info.get("tyre_compound", "") or info.get("compound", "")
            age = int(info.get("tyre_age", 0) or 0)

            if not compound:
                # Infer from tyre_life fraction
                tyre_life = info.get("tyre_life", info.get("tyreRemainingLife"))
                if tyre_life:
                    if tyre_life > 0.9 * 40:  # ~90% of medium life
                        compound = "HARD"
                    elif tyre_life > 0.6 * 40:
                        compound = "MEDIUM"
                    else:
                        compound = "SOFT"

            if compound:
                # Check for pit stop (compound changed)
                prev = self._driver_tyres.get(code, {})
                prev_compound = prev.get("compound", "")
                if prev_compound and prev_compound != compound:
                    lap = info.get("lap", 0)
                    self._pit_stops.append((frame_idx, code, lap, prev_compound, compound))

                self._driver_tyres[code] = {
                    "compound": compound,
                    "age": age,
                    "lap": info.get("lap", 0),
                }

        self._lbl_stops.setText(f"Pit stops: {len(self._pit_stops)}")
        self._redraw()

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._driver_tyres.clear()
            self._pit_stops.clear()
            self._known_codes.clear()
            self._lbl_stops.setText("Pit stops: 0")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Tyre Strategy")
    window = TyreStrategyWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
