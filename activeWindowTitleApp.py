import sys
import time
import threading
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from AppKit import NSWorkspace
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID

class ActiveWindowTitleApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        self.update_thread = threading.Thread(target=self.update_title, daemon=True)
        self.update_thread.start()

    def initUI(self):
        self.setWindowTitle('Active Window Title')

        self.layout = QVBoxLayout()
        self.title_label = QLabel('Active Window Title: ', self)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.title_label)
        self.setLayout(self.layout)

        self.setStyleSheet("background-color: white; color: black;")
        self.setGeometry(100, 100, 400, 200)
        self.show()

    def get_active_window_title(self):
        # Get the active application name
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        app_name = active_app.localizedName() if active_app else "No active application"

        # Get the active window title
        options = kCGWindowListOptionOnScreenOnly
        window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
        for window in window_list:
            if window.get('kCGWindowOwnerName', '') == app_name:
                window_title = window.get('kCGWindowName', 'Unknown')
                # Debug: Print all window properties
                print(window)
                if window_title:
                    return f"{app_name} - {window_title}"

        return app_name

    def update_title(self):
        while True:
            title = self.get_active_window_title()
            self.title_label.setText(f"Active Window Title: {title}")
            time.sleep(1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ActiveWindowTitleApp()
    sys.exit(app.exec_())
