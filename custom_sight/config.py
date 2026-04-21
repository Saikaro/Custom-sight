import os
import re
import json
import logging

from .constants import APP_DIR, DATA_DIR, PRESETS_DIR, APP_CFG, PRESET_EXT


def ensure_presets_dir():
    try:
        os.makedirs(PRESETS_DIR, exist_ok=True)
    except Exception as e:
        logging.error(f"ensure_presets_dir: {e}")


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(name).strip())[:80] or "preset"


def preset_path(name):
    return os.path.join(PRESETS_DIR, f"{name}{PRESET_EXT}")


def list_presets():
    ensure_presets_dir()
    try:
        return sorted(
            [f[:-len(PRESET_EXT)] for f in os.listdir(PRESETS_DIR)
             if f.lower().endswith(PRESET_EXT)],
            key=str.lower
        )
    except Exception as e:
        logging.error(f"list_presets: {e}")
        return []


def default_config():
    return {
        "mode":                  "cross",
        "color":                 [255, 0, 0, 200],
        "line_length":           20.0,
        "line_thickness":        3.0,
        "gap":                   6.0,
        "draw_circle":           False,
        "circle_radius":         10.0,
        "outline_thickness":     1.0,
        "outline_color":         [0, 0, 0, 200],
        "dot_radius":            5.0,
        "dot_outline_thickness": 1.0,
        "rmb_hide_enabled":      True,
        "rmb_threshold":         0.20,
        "auto_stretch_game":     False,
        "custom_res_enabled":    False,
        "custom_res_width":      1440,
        "custom_res_height":     1080,
    }


def load_app_config() -> dict:
    try:
        with open(APP_CFG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_app_config(cfg: dict):
    try:
        with open(APP_CFG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"save_app_config: {e}")


def load_preset(name):
    p = preset_path(name)
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in default_config().items():
            cfg.setdefault(k, v)
        return cfg
    except Exception as e:
        logging.error(f"load_preset({name}): {e}")
        return None


def save_preset(name, cfg):
    ensure_presets_dir()
    try:
        with open(preset_path(name), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as e:
        logging.error(f"save_preset({name}): {e}")
        return False


def delete_preset(name):
    try:
        os.remove(preset_path(name))
        return True
    except Exception as e:
        logging.error(f"delete_preset({name}): {e}")
        return False


def rename_preset(old, new):
    try:
        os.replace(preset_path(old), preset_path(new))
        return True
    except Exception as e:
        logging.error(f"rename_preset: {e}")
        return False


def migrate_legacy_config():
    ensure_presets_dir()
    if os.path.exists(preset_path("default")):
        return
    legacy = os.path.join(APP_DIR, "crosshair_config.json")
    try:
        if os.path.exists(legacy):
            with open(legacy, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in default_config().items():
                cfg.setdefault(k, v)
            save_preset("default", cfg)
            return
    except Exception as e:
        logging.error(f"migrate_legacy_config: {e}")
    save_preset("default", default_config())
