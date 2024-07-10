import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
from drd import execute_claude_command, update_metadata_with_claude, initialize_project_metadata, run_dev_server_with_monitoring


class WorkerThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.function(*self.args, **self.kwargs)
        self.update_signal.emit(str(result))


class DravidGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Dravid Desktop')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Query input
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your query here...")
        layout.addWidget(self.query_input)

        # Execute button
        self.execute_button = QPushButton('Execute Query')
        self.execute_button.clicked.connect(self.execute_query)
        layout.addWidget(self.execute_button)

        # Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        layout.addWidget(self.results_display)

        # Metadata buttons
        metadata_layout = QHBoxLayout()
        self.init_metadata_button = QPushButton('Initialize Metadata')
        self.init_metadata_button.clicked.connect(self.init_metadata)
        metadata_layout.addWidget(self.init_metadata_button)

        self.update_metadata_button = QPushButton('Update Metadata')
        self.update_metadata_button.clicked.connect(self.update_metadata)
        metadata_layout.addWidget(self.update_metadata_button)

        layout.addLayout(metadata_layout)

        # Dev server monitor button
        self.monitor_button = QPushButton('Start Dev Server Monitor')
        self.monitor_button.clicked.connect(self.start_monitor)
        layout.addWidget(self.monitor_button)

        central_widget.setLayout(layout)

    def execute_query(self):
        query = self.query_input.toPlainText()
        self.worker = WorkerThread(execute_claude_command, query, None, False)
        self.worker.update_signal.connect(self.update_results)
        self.worker.start()

    def update_results(self, result):
        self.results_display.setPlainText(result)

    def init_metadata(self):
        self.worker = WorkerThread(initialize_project_metadata)
        self.worker.update_signal.connect(self.update_results)
        self.worker.start()

    def update_metadata(self):
        description = self.query_input.toPlainText()
        self.worker = WorkerThread(update_metadata_with_claude, description)
        self.worker.update_signal.connect(self.update_results)
        self.worker.start()

    def start_monitor(self):
        self.worker = WorkerThread(run_dev_server_with_monitoring)
        self.worker.update_signal.connect(self.update_results)
        self.worker.start()


def main():
    app = QApplication(sys.argv)
    ex = DravidGUI()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
