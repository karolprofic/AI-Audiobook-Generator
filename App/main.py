from PyQt5.QtWidgets import QApplication
from modules.ApplicationGUI import ApplicationGUI
import sys


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ApplicationGUI()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
