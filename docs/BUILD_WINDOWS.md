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

### 4. Настройка OpenAI API ключа

**Важно**: Для работы OCR через OpenAI нужен API ключ.

#### Вариант 1: Файл .env (рекомендуется)

Создайте файл `.env` в корне проекта:

```bash
copy .env.example .env
```

Откройте `.env` в блокноте и вставьте ваш ключ:

```
OPENAI_API_KEY=sk-proj-ваш_ключ_здесь
```

**Где взять ключ**: https://platform.openai.com/api-keys

#### Вариант 2: Переменная окружения Windows

Альтернативно, можно установить переменную окружения в Windows:

```bash
setx OPENAI_API_KEY "sk-proj-ваш_ключ_здесь"
```

После этого перезапустите командную строку.

#### Вариант 3: Конфигурационный файл

Можно добавить ключ в `config/config.json`:

```json
"llm": {
    "provider": "openai",
    "api_key": "sk-proj-ваш_ключ_здесь",
    "model": "gpt-4o-mini",
    "base_url": "https://api.openai.com/v1"
}
```

⚠️ **Внимание**: При сборке через build.py файл `.env` НЕ попадет в exe (он в .gitignore). 
Поэтому для готового билда используйте **Вариант 3** (config.json) или **Вариант 2** (переменная окружения).

### 5. Сборка проекта

Запустите скрипт сборки:

```bash
python build.py
```

### 6. Результат

После успешного выполнения скрипта, в папке `dist/Release` появятся:

*   Папка `TMC_Client` (внутри `TMC_Client.exe`)
*   Папка `TMC_Server` (внутри `TMC_Server.exe`)
*   Папка `config` (файл конфигурации)
*   Папка `data` (для базы данных и файлов)

Вы можете скопировать всю папку `Release` на любой другой компьютер.
Запускать нужно сначала `TMC_Server.exe` (откроется консоль сервера), затем `TMC_Client.exe`.
