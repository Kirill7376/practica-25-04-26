import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def get_db_mode() -> str:
    """Возвращает 'orm' или 'native'."""
    if not os.path.exists(CONFIG_PATH):
        # Если файла нет, создаём с orm по умолчанию
        set_db_mode("orm")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("db_mode", "orm")

def set_db_mode(mode: str) -> None:
    """Устанавливает режим: 'orm' или 'native'."""
    if mode not in ("orm", "native"):
        raise ValueError("mode must be 'orm' or 'native'")
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"db_mode": mode}, f, indent=2)