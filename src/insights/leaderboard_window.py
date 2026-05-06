"""
Leaderboard insight - real-time driver standings with tyre compounds, laps, and status.
"""

import enum
from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QSplitter,
    QFrame, QPixmap, QPainter, QColor, QFont,
    QStylePainter, QStyleOptionButton, QCheckBox
)
from PySide6.QtCore import Qt, QUrl, QSize
from PySide6.QtGui import QPalette, QColor, QFontMetrics, QPainter, QPen, QFont
import sys
from enum import Enum

from src.insights.colours import (
    TEAM_COLOURS, TYRE_COLOURS, TYRE_LABELS, FLAG_MAP,
    DRIVER_TEAM_MAP, _DEFAULT_COL, _LEADER_COLOUR, _POLE_COLOUR,
)
from src.gui.pit_wall_window import PitWallWindow

# ─── Constants ────────────────────────────────────────────────────────────

_DRIVER_BK = {
    "MAX": "#3671C6", "PIA": "#FF8000", "LEC": "#E8002D",
    "ALO": "#225D4B", "NOR": "#FF8000", "RUS": "#27F4D2",
    "TSU": "#6099DA", "LAW": "#B6BABD", "ALB": "#64C4FF",
    "GAS": "#FF87BC", "HUL": "#52E252", "OCO": "#FF87BC",
    "STR": "#52E252", "ZHE": "#6099DA", "BOT": "#52E252",
    "MAR": "#B6BABD", "DEN": "#64C4FF", "PER": "#3671C6",
    "SAI": "#E8002D", "MAG": "#B6BABD", "CHI": "#6099DA",
    "DON": "#43C6C6", "SUR": "#52E252", "LAF": "#FF87BC",
    "BOU": "#FF87BC", "COL": "#64C4FF",
    "RUS": "#27F4D2", "HAM": "#27F4D2",
}

_KIT_DIR = "resources/kits"  # will be resolved via importlib


def _driver_flag_str(code: str, flags: int) -> str:
    """Map flags to the nearest string representation."""
    return FLAG_MAP.get(flags, "🟢")


def _make_flag_icon(
    colour: str = "#006400", size: int = 16
) -> QPixmap:
    """Return a 16×16 flag QPixmap for *colour*."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.fillRect(1, 1, size - 2, size, QColor(colour))
    for _w in range(0, size, 4):
        painter.fillRect(1, 1 + _w, size - 2, 2, QColor("white"))
    painter.end()
    return pm


def _find_flag_file(code: str) -> str:
    """Find an icon file for *code* under *KIT_DIR*/flags."""
    import importlib.resources

    pkg = (
        __import__("pkgutil", globals(), locals())
        .get_data(__import__(f"src.{_KIT_DIR}"), "")
        or None
    )
    try:
        entry = importlib.resources.files(f"src.{_KIT_DIR}.flags").joinpath(
            f"{code.lower()[:3]}.svg"
        )
        if entry.exists():
            return str(entry)
    except (ModuleNotFoundError, FileNotFoundError):
        pass
    return ""


@enum.unique
class TyreName(Enum):
    SOFT = "S"
    MEDIUM = "M"
    HARD = "H"
    INTERMEDIATE = "I"
    WET = "W"


_KIT_DIR = "resources/kits"  # Will be resolved in _make_flag_file

# ──────────────────────────────────────────────────────────────────────────


class LeaderboardWindow(PitWallWindow):
    """Leaderboard with driver positions."""

    def __init__(self):
        self._positions: dict[str, int] = {}
        self._driver_data: dict[str, dict] = {}
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Leaderboard")
        self.setMinimumSize(420, 580)
        self._build_ui()

    # ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self._layout = QVBoxLayout(central)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(8)

        # ── Header ────────────────────────────────────────────────────
        header = QFrame()
        header.setFrameShape(QFrame.HLine)
        header.setFrameShadow(QFrame.Sunken)
        header.setStyleSheet("color: #888")
        self._layout.addWidget(header)

        # ── Driver list ───────────────────────────────────────────────
        self._list = QListWidget()
        self._list.setFont(QFont("Arial", 11))
        self._list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #2ECC71;
                color: white;
            }
        """)
        self._list.itemClicked.connect(self._on_driver_selected)
        self._layout.addWidget(self._list)

        # ── Footer ────────────────────────────────────────────────────
        self._status_label = QLabel("⏳ Waiting for data...")
        self._status_label.setStyleSheet(
            "color: #666; font-size: 11px;"
        )
        self._status_label.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self._status_label)

    # ── Telemetry update ────────────────────────────────────────────────

    def on_telemetry_data(self, data):
        frame = data.get("frame")
        if not frame or "drivers" not in frame:
            return
        for code, info in frame["drivers"].items():
            self._driver_data[code] = info
            self._positions[code] = info.get("position", 999)
        self._update_leaderboard()
        self._status_label.setText(
            f"📡 {len(frame['drivers'])} drivers connected"
        )

    def _update_leaderboard(self):
        # sort by position
        sorted_drivers = sorted(
            self._positions.items(), key=lambda item: item[1]
        )
        self._list.clear()
        for pos, (code, _position) in enumerate(sorted_drivers, 1):
            info = self._driver_data.get(code, {})
            tyre = info.get("tyre", "Unknown")[:1]

            team = info.get("team", info.get("team_name", ""))
            team_colour = TEAM_COLOURS.get(team, "#FFFFFF")

            line = (
                f"{pos}. "
                f"<span style='color:{team_colour};'>"
                f'{info.get("name", code)}'
                f"</span> "
                f" [{tyre}]"
            )

            item = QListWidgetItem(line)
            if pos <= 1:
                item.setForeground(Qt.yellow)
            self._list.addItem(item)

    def _on_driver_selected(self, item):
        # Extract the driver code from the text
        text = item.text()
        code = self._find_code_in_text(text)
        if code:
            driver = self._driver_data.get(code, {})
            print(f"\n🏁 Driver: {driver.get('name', code)} ({code})")
            print(f"   Team: {driver.get('team', 'Unknown')}")
            print(f"   Position: {driver.get('position', '?')}")
            print(f"   Speed: {driver.get('speed', 0):.1f} km/h")

    def _find_code_in_text(self, text: str) -> str:
        for code in self._positions:
            if code in text:
                return code
        return ""

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._list.clear()
            self._positions.clear()
            self._driver_data.clear()

    # ────────────────────────────────────────────────────────────────────
    # ── Standalone main (runs as `python -m src.insights.leaderboard_window`)
    # ────────────────────────────────────────────────────────────────────


def _make_flag_icon(colour: str = "#006400", size: int = 16) -> QPixmap:
    """Return a coloured flag QPixmap for displaying telemetry flags."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    painter.fillRect(1, 1, size - 2, size, QColor(colour))
    for w in range(0, size, 4):
        painter.fillRect(1, 1 + w, size - 2, 2, QColor("white"))
    painter.end()
    return pm


def _driver_flag_str(code: str, flags: int) -> str:
    """Convert telemetry flags into an emoji string for display."""
    return FLAG_MAP.get(flags, "🟢")


def _find_flag_file(code: str) -> str:
    """Try to locate an SVG flag file for *code* under resources/kits/flags/."""
    flags_dir = "resources/kits/flags"
    candidate = f"{flags_dir}/{code.lower()[:3]}.svg"
    if __import__("os").path.exists(candidate):
        return candidate
    return ""


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Leaderboard")
    win = LeaderboardWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
