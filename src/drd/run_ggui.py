import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QScrollArea, QFrame
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QMargins


class ChatBubble(QFrame):
    def __init__(self, text, is_user=True):
        super().__init__()
        layout = QVBoxLayout(self)
        # Adjust padding inside the bubble
        layout.setContentsMargins(10, 5, 10, 5)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.label)

        self.setStyleSheet(
            f"background-color: {'#DCF8C6' if is_user else '#E2E2E2'}; "
            # Increased border radius and added horizontal margin
            "border-radius: 15px; margin: 5px 10px;"
        )
        self.label.setStyleSheet(
            "color: black; background-color: transparent;")


class ChatInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dravid Desktop")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Directory input
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit("/Users/vysakh/projects/drd")
        self.dir_input.setStyleSheet(
            "background-color: white; padding: 5px; border: 1px solid #ccc;")
        self.dir_button = QPushButton("Change Directory")
        self.dir_button.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px 10px; border: 1px solid #ccc;")
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_button)
        layout.addLayout(dir_layout)

        # Chat area
        chat_frame = QFrame()
        chat_frame.setStyleSheet(
            "background-color: #f0f0f0; border: 1px solid #ccc;")
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setSpacing(0)  # Remove spacing between bubbles
        self.chat_area = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_area)
        self.chat_layout.setSpacing(0)  # Remove spacing between bubbles
        self.chat_layout.addStretch()
        chat_layout.addWidget(self.chat_area)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(chat_frame)
        scroll_area.setStyleSheet("border: none;")
        layout.addWidget(scroll_area)

        # Message input
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Message Dravid...")
        self.message_input.setStyleSheet(
            "background-color: white; padding: 5px; border: 1px solid #ccc;")
        self.send_button = QPushButton("Submit")
        self.send_button.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 5px 10px; border: none;")
        self.image_button = QPushButton("Add Image")
        self.image_button.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px 10px; border: 1px solid #ccc;")
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.image_button)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Connect signals
        self.send_button.clicked.connect(self.send_message)
        self.message_input.returnPressed.connect(self.send_message)

    def send_message(self):
        message = self.message_input.text()
        if message:
            self.add_message(message, is_user=True)
            self.message_input.clear()
            # Here you would typically send the message to your AI and get a response
            self.add_message("This is a sample AI response.", is_user=False)

    def add_message(self, message, is_user=True):
        bubble = ChatBubble(message, is_user)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)


def main():
    app = QApplication(sys.argv)
    window = ChatInterface()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
