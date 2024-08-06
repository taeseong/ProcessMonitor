import sys
import time
import threading
import subprocess
import psutil
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt

try:
    from AppKit import NSWorkspace
except ImportError:
    print("AppKit module is not available")

"""
ProcessMonitor - Mac
- Mac에서 현재 사용자가 활성화 시킨 Window의 정보와, CPU 사용량 상위 5개의 Process를 표시
- 각 데이터들의 갱신 주기는 1초
"""
class ProcessMonitorApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        self.update_thread = threading.Thread(target=self.update_info, daemon=True)
        self.update_thread.start()

    def initUI(self):
        self.setWindowTitle('Process Monitor')

        self.layout = QVBoxLayout()
        self.title_label = QLabel('Active Window Title: ', self)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.process_label = QLabel('Top 5 Processes: ', self)
        self.process_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.process_label)
        self.setLayout(self.layout)

        self.setStyleSheet("background-color: white; color: black;")
        self.setGeometry(100, 100, 400, 400)
        self.show()

    def get_active_window_title(self):
        # 활성화된 Window Title 정보 수집
        if 'NSWorkspace' in globals():
            active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            app_name = active_app.localizedName() if active_app else "No active application"

            if app_name == "Safari":
                # Safari 브라우저의 Title 값 수집이 안 되어 AppleScript로 우회
                script = '''
                tell application "Safari"
                    set currentTab to tab 1 of front window
                    set tabName to name of currentTab
                end tell
                return tabName
                '''
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                window_title = result.stdout.strip()
                return f"{app_name} - {window_title}" if window_title else app_name

            return app_name
        else:
            return "NSWorkspace not available"

    def get_top_processes(self):
        # CPU 사용률 상위 5개의 Process를 수집
        processes = [(p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['name', 'cpu_percent'])]
        # CPU 사용률이 None인 데이터는 필터링
        processes = [(name, cpu) for name, cpu in processes if cpu is not None]
        processes.sort(key=lambda x: x[1], reverse=True)
        top_processes = processes[:5]
        process_info = "\n".join([f"{name}: {cpu}%" for name, cpu in top_processes])
        return process_info

    def update_info(self):
        while True:
            title = self.get_active_window_title()
            self.title_label.setText(f"Active Window Title: {title}")

            processes = self.get_top_processes()
            self.process_label.setText(f"Top 5 Processes:\n{processes}")

            time.sleep(1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ProcessMonitorApp()
    sys.exit(app.exec_())
