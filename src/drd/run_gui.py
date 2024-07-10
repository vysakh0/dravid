import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QFileDialog, QLabel, QListWidget, QListWidgetItem, QStyledItemDelegate,
                             QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QRegion


from drd import execute_claude_command, update_metadata_with_claude, initialize_project_metadata, run_dev_server_with_monitoring


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


class ChatBubbleWidget(QFrame):
    def __init__(self, text, is_user, image_path=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            background-color: transparent;
            border: none;
            padding: 5px;
        """)
        layout.addWidget(self.text_label)

        if image_path:
            image_label = QLabel()
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(
                200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
            layout.addWidget(image_label)

        self.setStyleSheet(f"""
            background-color: {'#DCF8C6' if is_user else '#FFFFFF'};
            border-radius: 10px;
        """)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Minimum)


class DravidGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.last_message = None

    def initUI(self):
        self.setWindowTitle('Dravid Desktop')
        self.setGeometry(100, 100, 800, 600)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Current directory display and change button
        dir_layout = QHBoxLayout()
        self.current_dir_label = QLabel(os.getcwd())
        dir_layout.addWidget(self.current_dir_label, stretch=1)
        change_dir_button = QPushButton("Change Directory")
        change_dir_button.setFixedSize(150, 30)
        change_dir_button.clicked.connect(self.change_directory)
        dir_layout.addWidget(change_dir_button)
        main_layout.addLayout(dir_layout)

        # Chat area
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 5px;
             }
        """)
        main_layout.addWidget(self.chat_list, stretch=1)

        # Query input area
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        query_layout.setContentsMargins(0, 0, 0, 0)
        query_layout.setSpacing(5)
        main_layout.addWidget(query_widget)

        # Image preview area with clear button
        self.image_preview_widget = QWidget()
        image_preview_layout = QHBoxLayout(self.image_preview_widget)
        image_preview_layout.setContentsMargins(0, 0, 0, 0)
        image_preview_layout.setSpacing(5)
        query_layout.addWidget(self.image_preview_widget)

        self.image_preview = QLabel()
        self.image_preview.setFixedSize(100, 100)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet(
            "border: 1px dashed #ccc; border-radius: 5px;")
        image_preview_layout.addWidget(self.image_preview)

        self.clear_image_button = QPushButton('x')
        self.clear_image_button.setFixedSize(20, 20)
        self.clear_image_button.clicked.connect(self.clear_image)
        self.clear_image_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        image_preview_layout.addWidget(
            self.clear_image_button, alignment=Qt.AlignmentFlag.AlignTop)
        image_preview_layout.addStretch()

        self.image_preview_widget.hide()  # Hide the entire widget initially

        # Input and buttons layout
        input_buttons_layout = QHBoxLayout()
        query_layout.addLayout(input_buttons_layout)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("Message Dravid...")
        self.query_input.setAcceptDrops(True)
        self.query_input.setFixedHeight(60)
        self.query_input.dragEnterEvent = self.dragEnterEvent
        self.query_input.dropEvent = self.dropEvent
        input_buttons_layout.addWidget(self.query_input)

        buttons_layout = QVBoxLayout()
        input_buttons_layout.addLayout(buttons_layout)

        self.add_image_button = QPushButton('Add Image')
        self.add_image_button.setFixedSize(100, 30)
        self.add_image_button.clicked.connect(self.open_file_dialog)
        buttons_layout.addWidget(self.add_image_button)

        self.submit_button = QPushButton('Submit')
        self.submit_button.setFixedSize(100, 30)
        self.submit_button.clicked.connect(self.submit_query)
        buttons_layout.addWidget(self.submit_button)

        self.image_path = None

        # Apply stylesheet
        self.setStyleSheet("""
            QLabel, QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

    def change_directory(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        if new_dir:
            os.chdir(new_dir)
            self.current_dir_label.setText(new_dir)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.image_path = file_path
            self.show_image_preview()

    def show_image_preview(self):
        if self.image_path:
            pixmap = QPixmap(self.image_path)
            scaled_pixmap = pixmap.scaled(
                100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_preview.setPixmap(scaled_pixmap)
            self.image_preview_widget.show()
            self.add_image_button.setDisabled(True)

    def clear_image(self):
        self.image_path = None
        self.image_preview.clear()
        self.image_preview_widget.hide()
        self.add_image_button.setDisabled(False)

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
                self.show_image_preview()
                break

    def add_chat_message(self, message, is_user=True):
        if message == self.last_message:
            return  # Don't add duplicate messages

        item = QListWidgetItem(self.chat_list)
        custom_widget = ChatBubbleWidget(
            message, is_user, self.image_path if is_user and self.image_path else None)
        item.setSizeHint(custom_widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, custom_widget)
        self.chat_list.scrollToBottom()
        self.last_message = message

    def submit_query(self):
        query = self.query_input.toPlainText().strip()
        if not query:
            return

        print("...ading query")
        self.add_chat_message(query, is_user=True)
        print("...added chat msg")
        self.query_input.clear()
        self.query_input.setDisabled(True)
        self.submit_button.setText('Stop')
        self.submit_button.clicked.disconnect()
        self.submit_button.clicked.connect(self.stop_execution)
        self.add_image_button.setDisabled(True)

        self.add_chat_message("sample response", is_user=None)
        # Clear the image preview
        self.clear_image()

        # # Start the worker thread
        # self.worker = WorkerThread(
        #     execute_claude_command, query, self.image_path, True)
        # self.worker.update_signal.connect(self.update_chat)
        # self.worker.finished_signal.connect(self.on_execution_finished)
        # self.worker.start()

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
        self.add_image_button.setDisabled(False)
        self.query_input.clear()


def main():
    app = QApplication(sys.argv)
    ex = DravidGUI()
    ex.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
