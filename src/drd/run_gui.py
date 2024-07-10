import sys
from drd.gui import DravidGUI
from PyQt6.QtWidgets import QApplication


def main():
    app = QApplication(sys.argv)
    ex = DravidGUI()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
