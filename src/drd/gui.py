import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QFileDialog, QLabel, QMenu, QMenuBar, QListWidget,
                             QListWidgetItem, QStyledItemDelegate, QStyle)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QSize, QRect
from PyQt6.QtGui import QAction, QIcon, QPainter, QColor, QPen, QBrush, QPixmap
from drd import execute_claude_command, update_metadata_with_claude, initialize_project_metadata, run_dev_server_with_monitoring


class ChatBubbleDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = option.rect
        is_user = index.data(Qt.ItemDataRole.UserRole)

        if is_user:
            bubble_color = QColor(230, 230, 250)  # Light purple for user
            text_color = QColor(0, 0, 0)
            rect = rect.adjusted(10, 5, -100, -5)
        else:
            bubble_color = QColor(220, 248, 198)  # Light green for assistant
            text_color = QColor(0, 0, 0)
            rect = rect.adjusted(100, 5, -10, -5)

        painter.setPen(QPen(bubble_color.darker(110), 1))
        painter.setBrush(QBrush(bubble_color))
        painter.drawRoundedRect(rect, 15, 15)

        painter.setPen(QPen(text_color))
        painter.drawText(rect.adjusted(15, 10, -15, -10), Qt.AlignmentFlag.AlignLeft |
                         Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, index.data())

    def sizeHint(self, option, index):
        width = option.rect.width() - 130
        metrics = option.fontMetrics
        text = index.data()
        height = metrics.boundingRect(
            QRect(0, 0, width, 0), Qt.TextFlag.TextWordWrap, text).height() + 30
        return QSize(option.rect.width(), height)


class WorkerThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.function(*self.args, **self.kwargs)
        self.update_signal.emit(str(result))
        self.finished_signal.emit()


class DravidGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Dravid Desktop')
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # Image preview area
        self.image_preview = QLabel("No image attached")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet(
            "background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 5px;")
        self.image_preview.setFixedHeight(50)
        self.image_preview.hide()
        main_layout.addWidget(self.image_preview)

        clear_image_button = QPushButton("Clear Image")
        clear_image_button.clicked.connect(self.clear_image)
        clear_image_button.hide()
        main_layout.addWidget(clear_image_button)
        self.clear_image_button = clear_image_button

        # Chat area
        self.chat_list = QListWidget()
        self.chat_list.setItemDelegate(ChatBubbleDelegate())
        self.chat_list.setStyleSheet(
            "QListWidget {background-color: #f9f9f9; border: none;}")
        main_layout.addWidget(self.chat_list)

        # Query input area
        query_widget = QWidget()
        query_layout = QHBoxLayout(query_widget)
        main_layout.addWidget(query_widget)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Enter your query here...")
        self.query_input.setAcceptDrops(True)
        self.query_input.setFixedHeight(60)
        self.query_input.dragEnterEvent = self.dragEnterEvent
        self.query_input.dropEvent = self.dropEvent
        query_layout.addWidget(self.query_input)

        self.submit_button = QPushButton('Submit')
        self.submit_button.clicked.connect(self.submit_query)
        query_layout.addWidget(self.submit_button)

        # Kebab menu
        self.create_kebab_menu()

        self.image_path = None

        # Apply stylesheet
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

    def create_kebab_menu(self):
        menubar = self.menuBar()
        kebab_menu = menubar.addMenu('⋮')

        init_metadata_action = QAction('Initialize Metadata', self)
        init_metadata_action.triggered.connect(self.init_metadata)
        kebab_menu.addAction(init_metadata_action)

        update_metadata_action = QAction('Update Metadata', self)
        update_metadata_action.triggered.connect(self.update_metadata)
        kebab_menu.addAction(update_metadata_action)

        monitor_action = QAction('Start Dev Server Monitor', self)
        monitor_action.triggered.connect(self.start_monitor)
        kebab_menu.addAction(monitor_action)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.image_path = f
                self.show_image_preview(f)
                break

    def show_image_preview(self, image_path):
        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(
            40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_preview.setPixmap(scaled_pixmap)
        self.image_preview.setText(
            f"Image attached: {os.path.basename(image_path)}")
        self.image_preview.show()
        self.clear_image_button.show()

    def clear_image(self):
        self.image_path = None
        self.image_preview.clear()
        self.image_preview.setText("No image attached")
        self.image_preview.hide()
        self.clear_image_button.hide()

    def submit_query(self):
        query = self.query_input.toPlainText()
        if not query:
            return

        self.add_chat_message(query, is_user=True)
        self.query_input.setDisabled(True)
        self.submit_button.setText('Stop')
        self.submit_button.clicked.disconnect()
        self.submit_button.clicked.connect(self.stop_execution)

        self.worker = WorkerThread(
            execute_claude_command, query, self.image_path, True)
        self.worker.update_signal.connect(self.update_chat)
        self.worker.finished_signal.connect(self.on_execution_finished)
        self.worker.start()

    def stop_execution(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        self.on_execution_finished()

    def update_chat(self, message):
        self.add_chat_message(message, is_user=False)

    def on_execution_finished(self):
        self.query_input.setDisabled(False)
        self.submit_button.setText('Submit')
        self.submit_button.clicked.disconnect()
        self.submit_button.clicked.connect(self.submit_query)
        self.image_path = None
        self.query_input.clear()
        self.clear_image()

    def add_chat_message(self, message, is_user=True):
        item = QListWidgetItem(message)
        item.setData(Qt.ItemDataRole.UserRole, is_user)
        self.chat_list.addItem(item)
        self.chat_list.scrollToBottom()

    def init_metadata(self):
        self.worker = WorkerThread(initialize_project_metadata)
        self.worker.update_signal.connect(self.update_chat)
        self.worker.start()

    def update_metadata(self):
        description, ok = QInputDialog.getText(
            self, 'Update Metadata', 'Enter metadata description:')
        if ok and description:
            self.worker = WorkerThread(
                update_metadata_with_claude, description)
            self.worker.update_signal.connect(self.update_chat)
            self.worker.start()

    def start_monitor(self):
        self.worker = WorkerThread(run_dev_server_with_monitoring)
        self.worker.update_signal.connect(self.update_chat)
        self.worker.start()


def main():
    app = QApplication(sys.argv)
    ex = DravidGUI()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
