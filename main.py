import sys
import platform
from PyQt5.QtWidgets import QApplication

"""
Mac / Windows 각각 OS에 맞는 모듈을 실행합니다.
"""
def main():
    app = QApplication(sys.argv)
    system = platform.system()

    if system == 'Darwin':
        from mac.process_monitor import ProcessMonitorApp
    elif system == 'Windows':
        from windows.process_monitor import ProcessMonitorApp
    else:
        raise NotImplementedError(f"Unsupported operating system: {system}")

    ex = ProcessMonitorApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
