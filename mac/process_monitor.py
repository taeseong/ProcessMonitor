import sys
import time
import threading
import psutil
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap, QBrush
from PyQt5.QtCore import Qt, QPoint
from AppKit import NSWorkspace

"""
ProcessMonitor - Mac
- Mac에서 현재 사용자가 활성화 시킨 Window의 정보와, CPU 사용량 상위 5개의 Process를 표시
- 각 데이터들의 갱신 주기는 1초
"""
class ProcessMonitorApp(QSystemTrayIcon):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app

        # Mac OS 메뉴바 아이콘 설정
        self.setIcon(QIcon("icon.png"))
        self.setToolTip("Process Monitor")

        # 메뉴 생성
        menu = QMenu(parent)

        # 메뉴 액션
        show_action = QAction("Show", parent)
        quit_action = QAction("Quit", parent)
        menu.addAction(show_action)
        menu.addAction(quit_action)

        show_action.triggered.connect(self.toggle_window)
        quit_action.triggered.connect(self.quit)

        self.setContextMenu(menu)
        self.activated.connect(self.on_click)

        # UI를 보여줄 메인 윈도우 생성
        self.window = QWidget()
        self.window.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.window.setWindowTitle("Process Monitor")
        self.window.setGeometry(100, 100, 300, 200)

        # 윈도우 배경 및 텍스트 컬러 설정
        palette = self.window.palette()
        palette.setColor(QPalette.Window, QColor(0, 166, 125))  # Background color: white
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))    # Text color: black
        self.window.setPalette(palette)

        # 윈도우에 배경 이미지를 적용할 때 사용
        #palette = QPalette()
        #pixmap = QPixmap("background.png")
        #palette.setBrush(QPalette.Window, QBrush(pixmap))
        #self.window.setPalette(palette)

        # 윈도우 UI에 출력 할 텍스트들 설정
        self.layout = QVBoxLayout()
        #self.title_label = QLabel("Active Window Title: ", self.window)
        #self.title_label.setAlignment(Qt.AlignCenter)
        #self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;") # 폰트 크기와 볼드 속성 부여
        #self.layout.addWidget(self.title_label)

        self.layout.addSpacing(20)

        self.process_label = QLabel("Top 5 CPU Processes\n", self.window)
        self.process_label.setAlignment(Qt.AlignLeft)
        self.process_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.process_label)

        self.process_data_label = QLabel("", self.window)
        self.process_data_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.process_data_label)

        self.layout.addSpacing(20)

        self.memory_label = QLabel("Top 5 Memory Processes\n", self.window)
        self.memory_label.setAlignment(Qt.AlignLeft)
        self.memory_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.memory_label)

        self.memory_data_label = QLabel("", self.window)
        self.memory_data_label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.memory_data_label)

        self.window.setLayout(self.layout)

        # 데이터 갱신 스레드 시작
        self.update_thread = threading.Thread(target=self.update_info, daemon=True)
        self.update_thread.start()

    def on_click(self, reason):
        # 메뉴바 아이콘 클릭 이벤트 핸들링
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()

    def toggle_window(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            # 윈도우 표시 위치 조정
            self.window.move(self.calculate_window_position())
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

    def calculate_window_position(self):
        # 메뉴바 아이콘의 위치를 가져옴
        tray_geometry = self.geometry()

        # 메뉴바 아이콘이 속한 모니터를 찾음
        for screen in QApplication.screens():
            if screen.geometry().contains(tray_geometry.center()):
                screen_geometry = screen.geometry()
                break
        else:
            # 메뉴바 아이콘의 위치를 찾을 수 없으면 기본 모니터 사용
            screen_geometry = QApplication.primaryScreen().geometry()

        # 윈도우가 메뉴바 아이콘 위치에 표시되도록 위치를 계산
        x = tray_geometry.center().x() - self.window.width() // 2
        y = tray_geometry.y() - self.window.height()

        # 윈도우가 화면 경계에 있도록 설정
        if x + self.window.width() > screen_geometry.right():
            x = screen_geometry.right() - self.window.width()
        if x < screen_geometry.left():
            x = screen_geometry.left()

        if y < screen_geometry.top():
            y = screen_geometry.top()

        return QPoint(x, y)

    def update_info(self):
        while True:
            #UI가 변경되며 Active Window가 의미 없어져 주석 처리
            #title = self.get_active_window_title()
            #self.title_label.setText(f"Active Window Title: {title}")

            cpu_processes = self.get_top_cpu_processes()
            self.process_data_label.setText(cpu_processes)

            memory_processes = self.get_top_memory_processes()
            self.memory_data_label.setText(memory_processes)

            time.sleep(1)

    def get_active_window_title(self):
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        app_name = active_app.localizedName() if active_app else "No active application"

        return app_name

    def get_top_cpu_processes(self):
        # CPU 사용율 상위 5개의 Process 수집
        processes = [(p.info['name'], p.info['cpu_percent']) for p in psutil.process_iter(['name', 'cpu_percent'])]
        # cpu_percent가 None인 데이터 필터링
        processes = [(name, cpu) for name, cpu in processes if cpu is not None]
        processes.sort(key=lambda x: x[1], reverse=True)
        top_processes = processes[:5]
        process_info = "\n".join([f"{name}: {cpu}%" for name, cpu in top_processes])
        return process_info

    def get_top_memory_processes(self):
        # 메모리 사용율 상위 5개의 Process 수집
        processes = [(p.info['name'], p.info['memory_percent']) for p in psutil.process_iter(['name', 'memory_percent'])]
        # memory_percent가 None인 데이터 필터링
        processes = [(name, memory) for name, memory in processes if memory is not None]
        processes.sort(key=lambda x: x[1], reverse=True)
        top_processes = processes[:5]
        process_info = "\n".join([f"{name}: {memory:.2f}%" for name, memory in top_processes])
        return process_info

    def quit(self):
        self.window.close()
        self.app.quit()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ProcessMonitor")
    app.setApplicationDisplayName("ProcessMonitor")
    tray_app = ProcessMonitorApp(app)
    tray_app.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
