# Руководство по сборке .exe для Windows

## Предварительные требования

1.  **Компьютер с Windows 10/11**.
2.  **Python 3.12** (или новее).
    *   Скачать: [python.org](https://www.python.org/downloads/)
    *   **Важно**: При установке поставьте галочку "Add Python to PATH".
3.  **Git** (для скачивания кода).
    *   Скачать: [git-scm.com](https://git-scm.com/download/win)

## Пошаговая инструкция

### 1. Получение кода

Откройте командную строку (cmd) или PowerShell и выполните:

```bash
git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> tmc_warehouse
cd tmc_warehouse
```

### 2. Настройка окружения

Создайте виртуальное окружение и активируйте его:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Установка зависимостей

Установите необходимые библиотеки:

```bash
pip install -r requirements.txt
pip install pyinstaller
```

### 4. Сборка проекта

Запустите скрипт сборки:

```bash
python build.py
```

### 5. Результат

После успешного выполнения скрипта, в папке `dist/Release` появятся:

*   Папка `TMC_Client` (внутри `TMC_Client.exe`)
*   Папка `TMC_Server` (внутри `TMC_Server.exe`)
*   Папка `config` (файл конфигурации)
*   Папка `data` (для базы данных и файлов)

Вы можете скопировать всю папку `Release` на любой другой компьютер.
Запускать нужно сначала `TMC_Server.exe` (откроется консоль сервера), затем `TMC_Client.exe`.
