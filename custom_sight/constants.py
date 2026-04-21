import sys
import os
import logging

# ==========================================
# ВЕРСИЯ 5.1
# ==========================================

GAME_WINDOW_NAMES = ["STALCRAFT: X", "STALCRAFT"]

# ---------- Пути ----------
def _get_app_dir():
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    # Поднимаемся на уровень выше пакета custom_sight/ к корню проекта
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


APP_DIR     = _get_app_dir()
DATA_DIR    = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "CustomSight")
PRESETS_DIR = os.path.join(DATA_DIR, "presets")
LOG_FILE    = os.path.join(DATA_DIR, "error.log")
PRESET_EXT  = ".json"
APP_CFG     = os.path.join(DATA_DIR, "app_config.json")

try:
    os.makedirs(DATA_DIR, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE, level=logging.ERROR,
        format="%(asctime)s %(levelname)s: %(message)s",
        encoding="utf-8"
    )
except Exception:
    pass

# ---------- Цветовая палитра ----------
BG      = "#0d0d0d"
CARD    = "#141414"
CARD2   = "#1c1c1c"
ACCENT  = "#7c3aed"
ACCH    = "#8b5cf6"
ACCL    = "#a78bfa"
TEXT    = "#f1f5f9"
SUB     = "#64748b"
BORDER  = "#232323"
BORDER2 = "#2c2c2c"
RED     = "#ef4444"
GREEN   = "#22c55e"

# ---------- WinAPI ----------
GWL_EXSTYLE       = -20
WS_EX_LAYERED     = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_NOACTIVATE  = 0x08000000
