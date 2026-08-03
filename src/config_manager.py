import json
import os
from typing import Any, Dict, Optional


SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")

DEFAULT_SETTINGS: Dict[str, Any] = {
    "provider": None,
    "model": None,
    "api_keys": {},
    "base_url": None,
    "local_depth": 3,
    "sound_enabled": True,
    "music_enabled": True,
    "animation_speed": 1.0,
    "ai_params": {
        "temperature": 0.1,
        "max_tokens": 10,
        "timeout": 30,
    },
}


def load_settings() -> Dict[str, Any]:
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Backwards compatibility migration
        if "api_key" in data and isinstance(data["api_key"], str) and data["api_key"]:
            prov = data.get("provider", "openai") or "openai"
            data.setdefault("api_keys", {})[prov] = data["api_key"]
            del data["api_key"]
            
        merged = DEFAULT_SETTINGS.copy()
        deep_merge(merged, data)
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> None:
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


def get_setting(key: str, default: Any = None) -> Any:
    settings = load_settings()
    return settings.get(key, default)