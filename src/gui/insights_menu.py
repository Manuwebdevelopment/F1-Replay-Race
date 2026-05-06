import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class InsightsMenu(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Insights")
        self.setGeometry(50, 50, 300, 600)
        self.opened_windows = []
        self._dispatch = self._build_dispatch()
        self.setup_ui()

    def _build_dispatch(self):
        return {
            "launch_leaderboard": ("src.insights.leaderboard_window", "LeaderboardWindow"),
            "launch_example_window": ("src.insights.example_pit_wall_window", "ExamplePitWallWindow"),
            "launch_gap_analysis": ("src.insights.gap_analysis_window", "GapAnalysisWindow"),
            "launch_sector_times": ("src.insights.sector_times_window", "SectorTimesWindow"),
            "launch_pit_analysis": ("src.insights.pit_stop_analysis_window", "PitStopAnalysisWindow"),
            "launch_tyre_strategy": ("src.insights.tyre_strategy_window", "TyreStrategyWindow"),
            "launch_speed_monitor": ("src.insights.speed_monitor_window", "SpeedMonitorWindow"),
            "launch_lap_evolution": ("src.insights.lap_time_evolution_window", "LapTimeEvolutionWindow"),
            "launch_position_history": ("src.insights.position_history_window", "PositionHistoryWindow"),
            "launch_track_position": ("src.insights.track_position_window", "TrackPositionWindow"),
            "launch_heatmap": ("src.insights.track_position_heatmap_window", "TrackPositionHeatmapWindow"),
            "launch_race_control": ("src.insights.race_control_events_window", "RaceControlEventsWindow"),
            "launch_driver_telemetry": ("src.insights.driver_telemetry_window", "DriverTelemetryWindow"),
            "launch_telemetry_viewer": (None, None),
        }

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = self.create_header()
        main_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(10, 10, 10, 10)

        # Category: Race Analysis
        content_layout.addWidget(self.create_category_section(
            "Race Analysis",
            [
                ("🏁 Leaderboard", "Live driver positions, compounds, and speeds", "launch_leaderboard"),
                ("⏱️ Sector Times", "Real-time sector times and comparisons", "launch_sector_times"),
                ("📊 Gap Analysis", "Gap between all drivers and the leader", "launch_gap_analysis"),
                ("🛑 Pit Stop Analysis", "Timing, compounds, and strategy viz", "launch_pit_analysis"),
                ("🔵 Tyre Strategy", "Tyre wear, compounds, changes", "launch_tyre_strategy"),
                ("⚡ Speed Monitor", "Speed vs max speed for all drivers", "launch_speed_monitor"),
                ("📈 Lap Time Evolution", "Lap progression by compound", "launch_lap_evolution"),
                ("🏎️ Position History", "All positions throughout the race", "launch_position_history"),
            ]
        ))

        # Category: Track & Position
        content_layout.addWidget(self.create_category_section(
            "Track & Position",
            [
                ("🗺️ Track Position", "Circular or real-track map", "launch_track_position"),
                ("🔥 Heatmap", "Driver positions on circuit", "launch_heatmap"),
            ]
        ))

        # Category: Race Events
        content_layout.addWidget(self.create_category_section(
            "Race Events",
            [
                ("🏁 Race Control", "Live flags, penalties, SC, DRS", "launch_race_control"),
                ("📡 Telemetry View", "Raw telemetry stream viewer", "launch_telemetry_viewer"),
            ]
        ))

        # Category: Drivers
        content_layout.addWidget(self.create_category_section(
            "Drivers",
            [
                ("💨 Driver Telemetry", "Speed, gear, throttle & brake", "launch_driver_telemetry"),
            ]
        ))

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        footer = self.create_footer()
        main_layout.addWidget(footer)

    def create_header(self):
        header = QFrame()
        header.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(header)
        title = QLabel("🏎️ F1 Insights")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        layout.addWidget(title)
        subtitle = QLabel("Launch telemetry insights and analysis tools")
        subtitle.setFont(QFont("Arial", 11))
        layout.addWidget(subtitle)
        return header

    def create_footer(self):
        footer = QFrame()
        footer.setFrameShape(QFrame.NoFrame)
        layout = QHBoxLayout(footer)
        info_label = QLabel("Requires telemetry stream enabled")
        info_label.setFont(QFont("Arial", 10))
        layout.addWidget(info_label)
        layout.addStretch()
        close_btn = QPushButton("Close Menu")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        return footer

    def create_category_section(self, category_name, items):
        section = QFrame()
        section.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(section)
        layout.setSpacing(4)
        category_label = QLabel(category_name.upper())
        category_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(category_label)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        layout.addWidget(separator)
        for name, description, key in items:
            btn = self.create_insight_button(name, description, key)
            layout.addWidget(btn)
        return section

    def create_insight_button(self, name, description, key):
        button = QPushButton()
        button.setCursor(Qt.PointingHandCursor)
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(2)
        btn_layout.setContentsMargins(4, 4, 4, 4)
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        btn_layout.addWidget(name_label)
        btn_layout.addWidget(desc_label)
        button.setLayout(btn_layout)
        button.setMinimumHeight(50)
        button.clicked.connect(lambda _: self._open_insight(key))
        return button

    def _open_insight(self, key: str):
        """Resolve a key to its module/class and launch the window."""
        entry = self._dispatch.get(key)
        if not entry:
            QMessageBox.warning(self, "Not Found", f"{key} is not registered.")
            return
        module_path, cls_name = entry
        if module_path is None:
            # Telemetry viewer is a subprocess
            self._open_telemetry_viewer()
            return
        try:
            mod = __import__(module_path, fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            win = cls()
            win.show()
            self.opened_windows.append(win)
        except ImportError as e:
            QMessageBox.warning(self, "Import Error",
                                f"Could not launch {cls_name}:\n{e}\n\n"
                                f"Ensure the window file exists at src/insights/{module_path.split('.')[-1]}.py")
        except Exception as e:
            QMessageBox.warning(self, "Launch Error",
                                f"Failed to launch {cls_name}:\n{e}")

    def _open_telemetry_viewer(self):
        try:
            import subprocess
            subprocess.Popen(
                [sys.executable, "-m", "src.insights.telemetry_stream_viewer"],
                cwd=sys.argv[0][:sys.argv[0].rfind("/") or None],
            )
        except Exception as e:
            self.show_placeholder_message("Telemetry Stream Viewer")

    def show_placeholder_message(self, insight_name):
        msg = QMessageBox(self)
        msg.setWindowTitle("Coming Soon")
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"{insight_name} will be available soon!")
        msg.setInformativeText(
            "This insight is planned for a future release.\n\n"
            "Developers can use PitWallWindow to create custom insights.\n"
            "See docs/PitWallWindow.md for more information."
        )
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()


def launch_insights_menu():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    menu = InsightsMenu()
    menu.show()
    return menu


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("F1 Insights Menu")
    menu = InsightsMenu()
    menu.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
