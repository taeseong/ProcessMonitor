import sys
import time
import threading
import psutil
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QPoint, QEvent
import win32gui

"""
ProcessMonitor - Windows
- Windows에서 현재 CPU, Memory 사용량 상위 5개의 Process를 표시
- 각 데이터들의 갱신 주기는 1초
"""
class ProcessMonitorApp(QSystemTrayIcon):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app

        # Windows 트레이 아이콘 설정
        self.setIcon(QIcon("icon.png"))  # 아이콘 파일 경로를 지정하세요
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
        self.window.setGeometry(100, 100, 400, 300)

        # 윈도우 배경 및 텍스트 컬러 설정
        palette = self.window.palette()
        palette.setColor(QPalette.Window, QColor(0, 166, 125))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.window.setPalette(palette)

        # 윈도우 UI에 출력 할 텍스트들 설정
        self.layout = QVBoxLayout()

        #self.title_label = QLabel("Active Window Title: ", self.window)
        #self.title_label.setAlignment(Qt.AlignCenter)
        #self.layout.addWidget(self.title_label)

        self.layout.addSpacing(2)

        self.process_label = QLabel("Top 5 CPU Processes", self.window)
        self.process_label.setAlignment(Qt.AlignLeft)
        self.process_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.process_label)

        self.process_data_label = QLabel("", self.window)
        self.process_data_label.setAlignment(Qt.AlignLeft)
        self.process_data_label.setStyleSheet("margin-top: 0px; margin-bottom: 0px;")
        self.layout.addWidget(self.process_data_label)

        self.layout.addSpacing(10)

        self.memory_label = QLabel("Top 5 Memory Processes", self.window)
        self.memory_label.setAlignment(Qt.AlignLeft)
        self.memory_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.memory_label)

        self.memory_data_label = QLabel("", self.window)
        self.memory_data_label.setAlignment(Qt.AlignLeft)
        self.memory_data_label.setStyleSheet("margin-top: 0px; margin-bottom: 0px;")
        self.layout.addWidget(self.memory_data_label)

        self.window.setLayout(self.layout)

        # 이벤트 필터 추가
        self.window.installEventFilter(self)

        # 데이터 갱신 스레드 시작
        self.update_thread = threading.Thread(target=self.update_info, daemon=True)
        self.update_thread.start()

    def eventFilter(self, obj, event):
        # 창이 비활성화될 때 (다른 창이 포커스를 받을 때) 창을 숨김
        if obj == self.window and event.type() == QEvent.WindowDeactivate:
            self.window.hide()
        return super().eventFilter(obj, event)

    def on_click(self, reason):
        # 트레이 아이콘 클릭 이벤트 핸들링
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()

    def toggle_window(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.move(self.calculate_window_position())
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

    def calculate_window_position(self):
        # 트레이 아이콘의 위치를 가져옴
        tray_geometry = self.geometry()
        screen_geometry = QApplication.primaryScreen().geometry()

        # 윈도우가 트레이 아이콘 위치에 표시되도록 위치를 계산
        x = tray_geometry.center().x() - self.window.width() // 2
        y = tray_geometry.bottom()  # 트레이 아이콘 바로 아래에 창을 표시

        # 윈도우가 화면 경계 내에 있도록 설정
        if x + self.window.width() > screen_geometry.right():
            x = screen_geometry.right() - self.window.width()
        if x < screen_geometry.left():
            x = screen_geometry.left()

        if y + self.window.height() > screen_geometry.bottom():
            y = screen_geometry.bottom() - self.window.height()

        return QPoint(x, y - 100)

    def update_info(self):
        while True:
            #title = self.get_active_window_title()
            #self.title_label.setText(f"Active Window Title: {title}")

            cpu_processes = self.get_top_cpu_processes()
            self.process_data_label.setText(cpu_processes)

            memory_processes = self.get_top_memory_processes()
            self.memory_data_label.setText(memory_processes)

            time.sleep(1)

    def get_active_window_title(self):
        # 활성화된 Window Title 정보 수집
        hwnd = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(hwnd)
        return window_title if window_title else "No active window detected"

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ProcessMonitorApp(app)
    ex.show()
    sys.exit(app.exec_())
