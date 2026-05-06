"""
Race Control Events insight window.

Shows race control messages (caution, safety car, VSC, etc.) in a scrolling list
with timestamps and severity indicators.
"""

import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QFrame
)
from PySide6.QtGui import QFont, QColor
from src.gui.pit_wall_window import PitWallWindow


class RaceControlEventsWindow(PitWallWindow):
    """Race control messages in chronological order with severity colours."""

    def __init__(self):
        self._messages: list = []
        self._known_codes: list = []
        super().__init__()
        self.setWindowTitle("F1 Race Replay - Race Control Events")
        self.setMinimumSize(600, 400)

    # ── UI ──

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        controls = QHBoxLayout()
        self._lbl_count = QLabel("Events: 0")
        self._lbl_count.setFont(QFont("Arial", 11))
        controls.addWidget(self._lbl_count)
        controls.addStretch()
        root.addLayout(controls)

        self._event_list = QListWidget()
        self._event_list.setFont(QFont("Courier", 10))
        self._event_list.setAlternatingRowColors(True)
        root.addWidget(self._event_list)

    def _severity_colour(self, event_type: str) -> QColor:
        evt = event_type.upper()
        if "YELLOW" in evt or "GREEN" in evt:
            return QColor("#FFD700")
        if "RED" in evt:
            return QColor("#FF3333")
        if "SAFETY CAR" in evt or "VSC" in evt:
            return QColor("#FF8000")
        if "BLACK" in evt or "WHITE" in evt or "DISQUALIFIED" in evt:
            return QColor("#666666")
        return QColor("#FFFFFF")

    def _severity_label(self, event_type: str) -> str:
        evt = event_type.upper()
        if "GREEN" in evt:
            return "🟢🟢🟢"
        if "YELLOW" in evt:
            return "🟡"
        if "RED" in evt or "VSC" in evt:
            return "🟠"
        if "BLACK" in evt or "DISQUALIFIED" in evt:
            return "⚫"
        if "WHITE" in evt:
            return "⚪"
        return "⚪"

    # ── Telemetry handlers ──

    def on_telemetry_data(self, data):
        rc_events = data.get("race_control_messages")
        if not rc_events:
            return

        known_codes = data.get("known_codes")
        if known_codes and set(known_codes) != set(self._known_codes):
            self._known_codes = known_codes.copy()

        if not isinstance(rc_events, list):
            return

        for event in rc_events:
            if isinstance(event, str):
                text = event
            elif isinstance(event, dict):
                msg = event.get("message", event.get("Message", event.get("text", event.get("Text", ""))))
                time = event.get("time", event.get("Time", event.get("lap", "?")))
                text = f"[{time}]: {msg}" if time else msg
            else:
                text = str(event)

            # Add to events list
            item = QListWidgetItem(text)
            item.setBackground(QColor("#1a1a1a"))
            item.setForeground(QColor("#FFFFFF"))
            self._event_list.insertItem(0, item)

            self._messages.append(text)

            if self._event_list.count() > 100:
                self._event_list.takeItem(100)

            self._lbl_count.setText(f"Events: {self._event_list.count()}")

    def on_connection_status_changed(self, status):
        if status == "Connected":
            self._lbl_count.setText("Events: 0")
            self._event_list.clear()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Race Control Events")
    window = RaceControlEventsWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
