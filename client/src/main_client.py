"""Точка входа клиента."""
import sys
import logging
from PySide6.QtWidgets import QApplication

from client.src.ui.main_window import MainWindow

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Запустить клиентское приложение."""
    app = QApplication(sys.argv)
    app.setApplicationName("TMC Warehouse")
    app.setOrganizationName("TMC")
    
    window = MainWindow()
    window.show()
    
    logger.info("Client application started")
    
    # Глобальный обработчик исключений
    def exception_hook(exctype, value, traceback):
        logger.critical("Unhandled exception", exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
        
    sys.excepthook = exception_hook
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
