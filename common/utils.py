import sys
from pathlib import Path

def get_project_root() -> Path:
    """
    Возвращает корневую директорию проекта.
    Работает корректно как при запуске из исходников, так и в замороженном виде (PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        # Если приложение заморожено (PyInstaller)
        # sys._MEIPASS - это временная папка, куда распаковываются файлы
        # Но если мы хотим доступ к файлам, которые лежат РЯДОМ с exe (например, config),
        # то нужно использовать sys.executable
        
        # В данном случае, мы предполагаем, что config и data лежат рядом с exe
        # или внутри _MEIPASS, если мы их туда упаковали.
        
        # Стратегия:
        # 1. Если ресурсы упакованы внутрь (onefile/onedir с add-data), то они в sys._MEIPASS (для onefile) или sys.executable dir (для onedir).
        # 2. Если ресурсы внешние (config), то они рядом с exe.
        
        # Для универсальности, если мы ищем config, лучше искать рядом с exe.
        # Если мы ищем внутренние ресурсы, то _MEIPASS.
        
        # Но эта функция должна вернуть ROOT проекта.
        # В контексте этого проекта, config лежит в корне.
        
        # Вернем директорию, где лежит исполняемый файл.
        return Path(sys.executable).parent
    else:
        # Если запуск из исходников
        # common/utils.py -> common -> tmc_warehouse (root)
        return Path(__file__).parent.parent
