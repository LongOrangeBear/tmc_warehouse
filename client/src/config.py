"""Загрузка конфигурации клиента."""
import json
import sys
from pathlib import Path
from typing import Any, Dict

_config: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    """Загрузить конфиг из config/config.json."""
    global _config
    if _config:
        return _config
    
    # Путь относительно корня проекта
    # Путь относительно корня проекта
    from common.utils import get_project_root
    project_root = get_project_root()
    config_path = project_root / "config" / "config.json"
    
    if not config_path.exists():
        # Fallback: try to find in _MEIPASS if bundled
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
             bundled_path = Path(sys._MEIPASS) / "config" / "config.json"
             if bundled_path.exists():
                 config_path = bundled_path
             else:
                 # Last resort: try absolute path (dev only)
                 possible_path = Path("/home/meow/work/tmc_warehouse/config/config.json")
                 if possible_path.exists():
                     config_path = possible_path
                 else:
                     raise FileNotFoundError(f"Config not found at {config_path} or bundled path")
        else:
             # Last resort: try absolute path (dev only)
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
    
    from common.utils import get_project_root
    project_root = get_project_root()
    config_path = project_root / "config" / "config.json"
    if not config_path.exists():
         config_path = Path("/home/meow/work/tmc_warehouse/config/config.json")
         
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(_config, f, indent=4, ensure_ascii=False)
