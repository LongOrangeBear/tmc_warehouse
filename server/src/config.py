"""Загрузка конфигурации сервера."""
import json
from pathlib import Path
from typing import Any, Dict

_config: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    """Загрузить конфиг из config/config.json."""
    global _config
    if _config:
        return _config
    
    # Путь относительно корня проекта
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "config.json"
    
    if not config_path.exists():
        # Fallback for different running contexts, try absolute path based on known structure
        # Assuming we are in /home/meow/work/tmc_warehouse/server/src/
        possible_path = Path("/home/meow/work/tmc_warehouse/config/config.json")
        if possible_path.exists():
            config_path = possible_path
        else:
             raise FileNotFoundError(f"Config not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        _config = json.load(f)
    
    return _config

def get_config() -> Dict[str, Any]:
    """Получить загруженный конфиг."""
    if not _config:
        return load_config()
    return _config
