"""
Track Position Heatmap insight window.

Shows driver positions on the circuit overlaid on the track layout.
Colour by driver, size by speed, alpha by sector.
"""

import sys

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox
)
from PySide6.QtGui import QFont
from src.gui.pit_wall_window import PitWallWindow

# Driver-specific colours for consistent identification
_DRIVER_COLOURS = [
    "#FF3333", "#3671C6", "#E8002D", "#FF8000",
    "#FFD700", "#00CC66", "#0080FF", "#9966FF",
    "#FF69B4", "#00CED1", "#FF4500", "#7B68EE",
    "#32CD32", "#FF1493", "#1E90FF", "#ADFF2F",
]

# Team colours (F1 2025 palette)
_TEAM_COLOURS = {
    "VER": "#3671C6", "NOR": "#FF8000", "PIA": "#3671C6", "LEC": "#E8002D",
    "SAI": "#0090FF", "HAM": "#67C226", "RUS": "#5E8FAA", "ALO": "#2293D1",
    "GAS": "#5E8A91", "OCO": "#0090FF", "ALB": "#64C4FF", "TSU": "#E20714",
    "DOO": "#00D2BE", "COL": "#0090FF", "BOT": "#52E254", "HUL": "#3671C6",
}


class TrackPositionHeatmapWindow(PitWallWindow):
    """Driver positions overlayed on the circuit track."""

    def __init__(self):
        self._known_codes: list = []
        self._show_grid = True
        self._show_labels = True
        self._show_speed = False
        self._show_history = False
        self._driver_history: dict[str, list] = {}  # code -> [(x, y)]
        self._track_x_min = 0.0
        self._track_y_min = 0.0
        self._track_x_max = 1.0
        self._track_y_max = 1.0
        self._next_colour_idx = 0
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Track Position Heatmap")
        self.setMinimumSize(700, 700)

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        control_row = QHBoxLayout()

        cb_grid = QCheckBox("Grid")
        cb_grid.setChecked(self._show_grid)
        cb_grid.stateChanged.connect(lambda v: setattr(self, '_show_grid', v == 2))
        control_row.addWidget(cb_grid)

        cb_labels = QCheckBox("Labels")
        cb_labels.setChecked(self._show_labels)
        cb_labels.stateChanged.connect(lambda v: setattr(self, '_show_labels', v == 2))
        control_row.addWidget(cb_labels)

        cb_speed = QCheckBox("Speed bubbles")
        cb_speed.setCheckState(0 if self._show_speed else 2)
        cb_speed.stateChanged.connect(lambda v: setattr(self, '_show_speed', v == 2))
        control_row.addWidget(cb_speed)

        cb_hist = QCheckBox("Trail history")
        cb_hist.setCheckState(0 if not self._show_history else 2)
        cb_hist.stateChanged.connect(lambda v: setattr(self, '_show_history', v == 2))
        control_row.addWidget(cb_hist)

        control_row.addStretch()

        self._lbl_status = QLabel("Track Status: —")
        self._lbl_status.setFont(QFont("Arial", 11))
        control_row.addWidget(self._lbl_status)

        root.addLayout(control_row)

        self._fig = plt.figure(figsize=(8, 8), facecolor="#111111")
        self._canvas = FigureCanvas(self._fig)
        root.addWidget(self._canvas, stretch=1)

    # ── Redraw ──

    def _redraw(self, drivers, circuit_length):
        ax = self._fig.gca()
        ax.clear()

        if not drivers:
            self._fig.text(0.5, 0.5, "No driver data yet", ha="center",
                           va="center", color="#666", fontsize=14)
            self._canvas.draw_idle()
            return

        # Plot circuit track if available in session data
        circuit = getattr(self, '_circuit_track', None)
        if circuit and len(circuit) >= 2:
            ax.plot(circuit[0], circuit[1], color="#333333", linewidth=1.5, alpha=0.5)

        # Compute bounding box from all driver positions
        all_x = [float(info.get("x", 0)) for info in drivers.values()]
        all_y = [float(info.get("y", 0)) for info in drivers.values()]
        if all_x and all_y:
            self._track_x_min = min(all_x)
            self._track_y_min = min(all_y)
            self._track_x_max = max(all_x)
            self._track_y_max = max(all_y)

        # Normalise track coords to [0, 1] range
        x_range = (self._track_x_max - self._track_x_min) or 1
        y_range = (self._track_y_max - self._track_y_min) or 1

        normalise = lambda x, y: ((x - self._track_x_min) / x_range,
                                   (y - self._track_y_min) / y_range)

        # Track colour assignment per driver code for consistency
        colour_map: dict[str, str] = {}
        for code in drivers:
            code_upper = code.upper()
            colour_map[code_upper] = _TEAM_COLOURS.get(code_upper) or self._get_next_colour()

        for i, (code, info) in enumerate(drivers.items()):
            code_upper = code.upper()
            driver_x = float(info.get("x", 0))
            driver_y = float(info.get("y", 0))

            norm_x, norm_y = normalise(driver_x, driver_y)

            col = colour_map.get(code_upper, self._get_next_colour())

            speed = float(info.get("speed", 0))

            radius = max(3, speed / 10)

            ax.plot(norm_x, norm_y, "o", color=col, markersize=radius, alpha=0.9)

            if self._show_history and code_upper in self._driver_history:
                hist = self._driver_history[code_upper]
                if len(hist) > 1:
                    hist_norm = [normalise(x, y) for x, y in hist[-20:]]
                    ax.plot([h[0] for h in hist_norm], [h[1] for h in hist_norm],
                            color=col, linewidth=1, alpha=0.3)

            if self._show_labels:
                ax.text(norm_x, norm_y + 0.05, code_upper, color="white", fontsize=8,
                       ha="center", va="bottom")

            if self._show_speed:
                ax.text(norm_x, norm_y - 0.05, f"{speed:.0f}", color=col, fontsize=7,
                       ha="center", va="top", alpha=0.8)

            # Update driver history
            if code_upper not in self._driver_history:
                self._driver_history[code_upper] = []
            self._driver_history[code_upper].append((driver_x, driver_y))
            if len(self._driver_history[code_upper]) > 100:
                self._driver_history[code_upper] = self._driver_history[code_upper][-100:]

        # Draw track geometry if available
        if circuit and len(circuit) >= 2:
            circuit_norm = [normalise(x, y) for x, y in zip(circuit[0], circuit[1])]
            ax.plot([p[0] for p in circuit_norm], [p[1] for p in circuit_norm],
                    color="#444444", linewidth=2, alpha=0.8)

        ax.plot(0, 0, 'k-', alpha=0, clip_on=False)
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.05)
        ax.set_aspect("equal")
        ax.set_facecolor("#111111")
        ax.tick_params(colors="#aaaaaa")
        ax.spines["bottom"].set_color("#444444")
        ax.spines["top"].set_color("#444444")
        ax.spines["left"].set_color("#444444")
        ax.spines["right"].set_color("#444444")
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1])

        if self._show_grid:
            ax.grid(True, alpha=0.15)

        self._canvas.draw_idle()

    def _get_next_colour(self) -> str:
        """Get the next colour from the default palette for a new driver."""
        colour = _DRIVER_COLOURS[self._next_colour_idx % len(_DRIVER_COLOURS)]
        self._next_colour_idx += 1
        return colour

    # ── Telemetry handlers ──

    def on_telemetry_data(self, data):
        frame = data.get("frame")
        if not frame or "drivers" not in frame:
            return

        drivers = frame["drivers"]

        for code in drivers:
            if code not in self._known_codes:
                self._known_codes.append(code)

        self._redraw(drivers, data.get("circuit_length_m", 0))

        track_status = data.get("track_status")
        if track_status:
            self._lbl_status.setText(f"Status: {track_status}")

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._driver_history.clear()
            self._known_codes.clear()
            self._lbl_status.setText("Status: Connected")
            self._redraw({}, 0)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Track Position Heatmap")
    window = TrackPositionHeatmapWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
