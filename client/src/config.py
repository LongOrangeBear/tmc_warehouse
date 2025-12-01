"""Загрузка конфигурации клиента."""
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
    # client/src/config.py -> client/src -> client -> tmc_warehouse -> config/config.json
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "config.json"
    
    if not config_path.exists():
        # Fallback for different running contexts
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

def save_config(new_config: Dict[str, Any]):
    """Сохранить конфиг в файл."""
    global _config
    _config = new_config
    
    config_path = Path(__file__).parent.parent.parent.parent / "config" / "config.json"
    if not config_path.exists():
         config_path = Path("/home/meow/work/tmc_warehouse/config/config.json")
         
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(_config, f, indent=4, ensure_ascii=False)
