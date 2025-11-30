import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("TMC Warehouse (demo skeleton)")

        btn_accept = QPushButton("Принять ТМЦ на склад")
        btn_history = QPushButton("История приёмок")
        btn_settings = QPushButton("Настройки")

        layout = QVBoxLayout()
        layout.addWidget(btn_accept)
        layout.addWidget(btn_history)
        layout.addWidget(btn_settings)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        btn_accept.clicked.connect(self.on_accept)
        btn_history.clicked.connect(self.on_history)
        btn_settings.clicked.connect(self.on_settings)

    def on_accept(self) -> None:
        QMessageBox.information(self, "Действие", "Здесь будет сценарий приёмки ТМЦ.")

    def on_history(self) -> None:
        QMessageBox.information(self, "Действие", "Здесь будет история приёмок.")

    def on_settings(self) -> None:
        QMessageBox.information(self, "Действие", "Здесь будут настройки.")

def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
