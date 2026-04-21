import sys
import os
import json
import ctypes
import logging
import time
import re
import threading

import win32gui
import win32con
import win32api
from PyQt5 import QtWidgets, QtCore, QtGui
import keyboard
from pynput import mouse

# ==========================================
# ВЕРСИЯ 5.1
# ==========================================

GAME_WINDOW_NAMES = ["STALCRAFT: X", "STALCRAFT"]

# ---------- Пути ----------
def _get_app_dir():
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


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


# ==========================================
# СИСТЕМНЫЕ ФУНКЦИИ
# ==========================================

def find_game_hwnd():
    for name in GAME_WINDOW_NAMES:
        hwnd = win32gui.FindWindow(None, name)
        if hwnd:
            return hwnd
    return None


def get_foreground_hwnd():
    return ctypes.windll.user32.GetForegroundWindow()


def get_monitor_size():
    return (ctypes.windll.user32.GetSystemMetrics(0),
            ctypes.windll.user32.GetSystemMetrics(1))


def make_window_clickthrough(widget):
    try:
        hwnd = int(widget.winId())
        ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE,
            ex | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
        )
    except Exception as e:
        logging.error(f"make_window_clickthrough: {e}")


def get_available_resolutions():
    """Возвращает все доступные разрешения из Windows, не превышающие текущее разрешение монитора."""
    mon_w, mon_h = get_monitor_size()
    seen = set()
    i = 0
    while True:
        try:
            dm = win32api.EnumDisplaySettings(None, i)
            w, h = dm.PelsWidth, dm.PelsHeight
            if w >= 640 and h >= 480 and w <= mon_w and h <= mon_h:
                seen.add((w, h))
            i += 1
        except Exception:
            break
    result = sorted(seen, key=lambda r: (r[0] * r[1], r[0]), reverse=True)
    return result or [(mon_w, mon_h)]


# Нативное разрешение, кэшированное один раз при первом запросе.
# Это позволяет restore_display_resolution() сравнивать текущее
# разрешение с исходным без дополнительных обращений к API.
_NATIVE_RES: tuple[int, int] | None = None

def _get_native_res() -> tuple[int, int]:
    """Возвращает разрешение из реестра (то, что стоит «по умолчанию»)."""
    global _NATIVE_RES
    if _NATIVE_RES is None:
        try:
            # ENUM_REGISTRY_SETTINGS (-2) — настройки из реестра Windows,
            # не зависящие от текущего активного режима.
            dm = win32api.EnumDisplaySettings(None, win32con.ENUM_REGISTRY_SETTINGS)
            _NATIVE_RES = (int(dm.PelsWidth), int(dm.PelsHeight))
        except Exception as e:
            logging.error(f"_get_native_res: {e}")
            # Запасной вариант — текущее разрешение
            dm = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            _NATIVE_RES = (int(dm.PelsWidth), int(dm.PelsHeight))
    return _NATIVE_RES


def _apply_res_sync(width: int, height: int) -> bool:
    """Выполняет ChangeDisplaySettings синхронно (вызывается из потока)."""
    try:
        dm = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
        # Пропускаем вызов, если разрешение уже совпадает — экран не мигнет
        if int(dm.PelsWidth) == width and int(dm.PelsHeight) == height:
            return True
        dm.PelsWidth  = width
        dm.PelsHeight = height
        dm.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
        return win32api.ChangeDisplaySettings(dm, 0) == win32con.DISP_CHANGE_SUCCESSFUL
    except Exception as e:
        logging.error(f"change_display_resolution: {e}")
        return False


def change_display_resolution(width: int, height: int,
                              callback=None) -> None:
    """Меняет разрешение в отдельном потоке.

    callback(success: bool) вызывается после завершения смены.
    Благодаря потоку UI не зависает во время переключения.
    """
    def _worker():
        ok = _apply_res_sync(width, height)
        if callback:
            callback(ok)
    threading.Thread(target=_worker, daemon=True, name="res-change").start()


def restore_display_resolution(callback=None) -> None:
    """Восстанавливает разрешение из реестра Windows в отдельном потоке."""
    def _worker():
        try:
            nw, nh = _get_native_res()
            dm = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            # Пропускаем, если уже нативное — без лишнего мигания
            if int(dm.PelsWidth) == nw and int(dm.PelsHeight) == nh:
                if callback:
                    callback(True)
                return
            win32api.ChangeDisplaySettings(None, 0)
            if callback:
                callback(True)
        except Exception as e:
            logging.error(f"restore_display_resolution: {e}")
            if callback:
                callback(False)
    threading.Thread(target=_worker, daemon=True, name="res-restore").start()


def make_window_borderless(hwnd, tw=None, th=None):
    try:
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE,
                               style & ~win32con.WS_OVERLAPPEDWINDOW)
        w = tw or get_monitor_size()[0]
        h = th or get_monitor_size()[1]
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, w, h,
                              win32con.SWP_SHOWWINDOW)
    except Exception as e:
        logging.error(f"make_window_borderless: {e}")


def try_make_game_borderless(width=None, height=None):
    """Растягивает окно игры без изменения разрешения."""
    hwnd = find_game_hwnd()
    if hwnd:
        make_window_borderless(hwnd, width, height)
        return True
    return False


# ==========================================
# ПРЕСЕТЫ
# ==========================================

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


# ==========================================
# ТАБЛИЦА СТИЛЕЙ
# ==========================================

def get_stylesheet():
    return f"""
    * {{ font-family: 'Segoe UI', sans-serif; }}
    QWidget {{ font-size: 13px; color: {TEXT}; background: transparent; }}

    QGroupBox {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 10px;
        margin-top: 22px;
        padding: 12px 10px 10px 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 13px; top: 3px;
        color: {SUB};
        font-size: 10px;
        font-weight: bold;
        letter-spacing: 1.5px;
    }}

    QListWidget {{
        background: {BG};
        border: 1px solid {BORDER};
        border-radius: 8px;
        outline: none;
        padding: 4px;
    }}
    QListWidget::item {{
        padding: 7px 10px;
        border-radius: 5px;
        color: {SUB};
        margin: 1px 0;
    }}
    QListWidget::item:selected {{
        color: {ACCL};
        background: rgba(124,58,237,0.15);
        border: 1px solid rgba(124,58,237,0.3);
    }}
    QListWidget::item:hover:!selected {{
        background: {BORDER};
        color: {TEXT};
    }}

    QPushButton {{
        background: {CARD2};
        border: 1px solid {BORDER2};
        border-radius: 6px;
        padding: 5px 8px;
        color: {TEXT};
        font-size: 12px;
    }}
    QPushButton:hover {{ background: #222; border-color: #3a3a3a; }}
    QPushButton:pressed {{ background: {BG}; }}
    QPushButton:disabled {{ color: {SUB}; border-color: {BORDER}; background: {CARD}; }}

    QPushButton#AccentButton {{
        background: {ACCENT};
        border: none;
        color: white;
        font-weight: bold;
        font-size: 13px;
        border-radius: 7px;
        padding: 8px 16px;
    }}
    QPushButton#AccentButton:hover {{ background: {ACCH}; }}
    QPushButton#AccentButton:pressed {{ background: #6d28d9; }}
    QPushButton#AccentButton:disabled {{ background: rgba(124,58,237,0.30); color: rgba(255,255,255,0.30); }}

    QPushButton#DangerButton {{
        border: 1px solid rgba(239,68,68,0.4);
        color: {RED};
        background: transparent;
    }}
    QPushButton#DangerButton:hover {{
        background: rgba(239,68,68,0.1);
        border-color: {RED};
    }}
    QPushButton#DangerButton:disabled {{ color: rgba(239,68,68,0.28); border-color: rgba(239,68,68,0.14); }}

    QSlider::groove:horizontal {{
        height: 3px;
        background: {BORDER2};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {TEXT};
        border: 2px solid {BG};
        width: 14px;
        height: 14px;
        margin: -6px 0;
        border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{ background: {ACCL}; border-color: {ACCENT}; }}
    QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}

    QComboBox {{
        background: {BG};
        border: 1px solid {BORDER2};
        border-radius: 6px;
        padding: 5px 10px;
        color: {TEXT};
    }}
    QComboBox:focus {{ border-color: {ACCENT}; }}
    QComboBox:disabled {{ color: {SUB}; border-color: {BORDER}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        background: {CARD};
        border: 1px solid {BORDER2};
        selection-background-color: rgba(124,58,237,0.2);
        selection-color: {ACCL};
        padding: 4px;
        outline: none;
    }}

    QLabel {{ color: {TEXT}; }}
    QLabel#Sub {{ color: {SUB}; font-size: 11px; }}
    QLabel#Status {{ color: {ACCL}; font-weight: bold; font-size: 12px; }}

    QLineEdit#spinbox {{
        background: {CARD2};
        color: {TEXT};
        border: 1px solid {BORDER2};
        border-radius: 5px;
        padding: 2px 6px;
        font-size: 12px;
        selection-background-color: transparent;
        selection-color: {TEXT};
    }}
    QLineEdit#spinbox:focus {{
        border: 1px solid {ACCENT};
        background: {CARD};
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER2};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {SUB}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

    QMessageBox {{ background: {CARD}; }}
    QMessageBox QLabel {{ color: {TEXT}; }}
    QMessageBox QPushButton {{ min-width: 70px; }}

    QInputDialog {{ background: {CARD}; }}
    QInputDialog QLabel {{ color: {TEXT}; }}
    QInputDialog QLineEdit {{
        background: {BG};
        border: 1px solid {BORDER2};
        border-radius: 5px;
        padding: 5px 8px;
        color: {TEXT};
    }}
    QInputDialog QLineEdit:focus {{ border-color: {ACCENT}; }}
    """


# ==========================================
# UI-КОМПОНЕНТЫ
# ==========================================

class ToggleSwitch(QtWidgets.QCheckBox):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setFixedHeight(28)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        W, H = 38, 20
        x, y = 0, (self.height() - H) // 2

        enabled = self.isEnabled()
        checked = self.isChecked()

        if checked and enabled:
            track_c = QtGui.QColor(ACCENT)
        elif checked:
            track_c = QtGui.QColor(ACCENT).darker(160)
        else:
            track_c = QtGui.QColor(BORDER2)

        p.setBrush(track_c)
        p.setPen(QtCore.Qt.NoPen)
        p.drawRoundedRect(x, y, W, H, H // 2, H // 2)

        tx = x + W - (H - 4) - 2 if checked else x + 2
        p.setBrush(QtGui.QColor(0, 0, 0, 50))
        p.drawEllipse(tx + 1, y + 3, H - 4, H - 4)
        p.setBrush(QtGui.QColor("#ffffff" if enabled else "#888888"))
        p.drawEllipse(tx, y + 2, H - 4, H - 4)

        p.setPen(QtGui.QColor(TEXT if enabled else SUB))
        p.setFont(self.font())
        p.drawText(QtCore.QRect(W + 10, 0, self.width(), self.height()),
                   QtCore.Qt.AlignVCenter, self.text())


class ModernRadioButton(QtWidgets.QRadioButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setMinimumHeight(28)
        self.setMinimumWidth(110)
        # Добавляем левый отступ чтобы кружок не обрезался
        self.setContentsMargins(4, 0, 0, 0)

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        D  = 18
        ox = 3   # отступ слева чтобы кружок не обрезался
        y  = (self.height() - D) // 2
        checked = self.isChecked()

        p.setPen(QtGui.QPen(QtGui.QColor(ACCENT if checked else BORDER2), 2))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawEllipse(ox, y, D, D)
        if checked:
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QColor(ACCENT))
            p.drawEllipse(ox + 5, y + 5, D - 10, D - 10)

        p.setPen(QtGui.QColor(TEXT))
        p.setFont(self.font())
        p.drawText(QtCore.QRect(ox + D + 8, 0, self.width(), self.height()),
                   QtCore.Qt.AlignVCenter, self.text())


class InstantSpinBox(QtWidgets.QLineEdit):
    """Числовое поле ввода на базе QLineEdit.

    Заменяет QDoubleSpinBox, полностью избавляясь от его Windows-квирка
    «двойного клика»: QLineEdit активируется с первого клика нативно.

    Поведение:
    - При фокусе: показывает только число (суффикс скрыт), курсор в конец
    - При дефокусе / Enter: валидирует, обрезает до диапазона, показывает суффикс
    - Escape: откатывает изменения и снимает фокус
    """

    valueChanged = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min      = 0.0
        self._max      = 100.0
        self._decimals = 0
        self._value    = 0.0
        self._suffix   = ""
        self.setObjectName("spinbox")
        self.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)

    # ── Совместимость с QDoubleSpinBox API ─────────────────────────────────
    def setDecimals(self, d):       self._decimals = int(d)
    def setRange(self, lo, hi):     self._min, self._max = float(lo), float(hi)
    def setSingleStep(self, s):     pass
    def setButtonSymbols(self, s):  pass
    def lineEdit(self):             return self   # для SpinboxFocusFilter

    def setSuffix(self, s):
        self._suffix = s
        if not self.hasFocus():
            self._show_display()

    # ── Значение ───────────────────────────────────────────────────────────
    def value(self):
        return self._value

    def setValue(self, v):
        """Программная установка — сигнал не эмитируется."""
        self._value = round(
            max(self._min, min(self._max, float(v))), self._decimals)
        if not self.hasFocus():
            self._show_display()

    # ── Отображение ────────────────────────────────────────────────────────
    def _show_display(self):
        self.setText(f"{self._value:.{self._decimals}f}{self._suffix}")

    def _show_edit(self):
        self.setText(f"{self._value:.{self._decimals}f}")

    # ── Фиксация введённого значения ───────────────────────────────────────
    def _commit(self):
        text = self.text().strip()
        if self._suffix and text.endswith(self._suffix):
            text = text[:-len(self._suffix)].strip()
        try:
            v = float(text.replace(',', '.'))
            clamped = round(max(self._min, min(self._max, v)), self._decimals)
            if abs(clamped - self._value) > 10 ** -(self._decimals + 2):
                self._value = clamped
                self.valueChanged.emit(clamped)
            else:
                self._value = clamped
        except ValueError:
            pass        # невалидный ввод — возвращаем прежнее значение
        self._show_display()

    # ── События ────────────────────────────────────────────────────────────
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._show_edit()
        self.setCursorPosition(len(self.text()))

    def focusOutEvent(self, event):
        self._commit()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        k = event.key()
        if k == QtCore.Qt.Key_Escape:
            self._show_display()
            self.clearFocus()
            return
        if k in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            self._commit()
            self.clearFocus()
            return
        super().keyPressEvent(event)


class SliderRow(QtWidgets.QWidget):
    """Слайдер + поле ручного ввода, синхронизированные между собой.

    decimals=0  → целые числа (шаг 1)
    decimals=2  → до сотых  (шаг 0.01)
    decimals=3  → до тысячных (шаг 0.001)
    """
    valueChanged = QtCore.pyqtSignal(float)

    def __init__(self, label, min_v, max_v, decimals=0, suffix="", parent=None):
        super().__init__(parent)
        self._scale    = 10 ** decimals
        self._decimals = decimals
        self._min      = float(min_v)
        self._max      = float(max_v)
        self._syncing  = False   # защита от рекурсивных обновлений

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 2, 0, 5)
        root.setSpacing(4)

        # ── Верхняя строка: подпись + поле ввода ──────────────────────────
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(6)

        lbl = QtWidgets.QLabel(label)

        self.spinbox = InstantSpinBox()
        self.spinbox.setDecimals(decimals)
        self.spinbox.setRange(min_v, max_v)
        self.spinbox.setSingleStep(max(1.0 / self._scale, 0.001))
        self.spinbox.setSuffix(suffix)
        self.spinbox.setAlignment(QtCore.Qt.AlignRight)
        self.spinbox.setFixedWidth(82)
        self.spinbox.setFocusPolicy(QtCore.Qt.ClickFocus)
        # Убираем стрелки — управление только через слайдер или клавиатуру
        self.spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(self.spinbox)

        # ── Ползунок ──────────────────────────────────────────────────────
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(
            int(round(min_v * self._scale)),
            int(round(max_v * self._scale))
        )

        root.addLayout(top)
        root.addWidget(self.slider)

        # Инициализируем значение
        self.spinbox.setValue(min_v)

        # Сигналы
        self.slider.valueChanged.connect(self._from_slider)
        self.spinbox.valueChanged.connect(self._from_spinbox)

        # Начальный эффект прозрачности (enabled по умолчанию)
        _eff = QtWidgets.QGraphicsOpacityEffect(self)
        _eff.setOpacity(1.0)
        self.setGraphicsEffect(_eff)

    # ── Внутренняя синхронизация ───────────────────────────────────────────

    def _from_slider(self, raw):
        if self._syncing:
            return
        v = raw / self._scale
        self._syncing = True
        self.spinbox.setValue(v)
        self._syncing = False
        self.valueChanged.emit(v)

    def _from_spinbox(self, v):
        if self._syncing:
            return
        raw = int(round(v * self._scale))
        self._syncing = True
        self.slider.setValue(raw)
        self._syncing = False
        self.valueChanged.emit(v)

    # ── Публичный API ──────────────────────────────────────────────────────

    def value(self):
        return self.spinbox.value()

    def setValue(self, v):
        """Программная установка значения без эмиссии valueChanged."""
        self._syncing = True
        raw = int(round(float(v) * self._scale))
        self.slider.setValue(raw)
        self.spinbox.setValue(float(v))
        self._syncing = False

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.slider.setEnabled(enabled)
        self.spinbox.setEnabled(enabled)
        # Полупрозрачность для визуализации недоступности
        effect = QtWidgets.QGraphicsOpacityEffect(self)
        effect.setOpacity(1.0 if enabled else 0.30)
        self.setGraphicsEffect(effect)


class ColorButton(QtWidgets.QPushButton):
    """Кнопка выбора цвета с превью-свотчем и поддержкой альфа-канала."""
    colorChanged = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, text="", color=None, parent=None):
        super().__init__(text, parent)
        self._color = color or QtGui.QColor(255, 0, 0, 200)
        self._update_icon()
        self.clicked.connect(self._pick)

    def _pick(self):
        dlg = QtWidgets.QColorDialog(self._color, self)
        dlg.setOption(QtWidgets.QColorDialog.ShowAlphaChannel, True)
        if dlg.exec_():
            self._color = dlg.currentColor()
            self._update_icon()
            self.colorChanged.emit(self._color)

    def _make_swatch(self):
        W, H, R = 28, 16, 4
        pm = QtGui.QPixmap(W, H)
        pm.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pm)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(0, 0, W, H), R, R)

        # Шахматный фон для прозрачности
        if self._color.alpha() < 240:
            painter.setClipPath(path)
            half = H // 2
            for dx in range(0, W, half * 2):
                painter.fillRect(dx, 0,    half, half, QtGui.QColor(190, 190, 190))
                painter.fillRect(dx + half, 0,    half, half, QtGui.QColor(130, 130, 130))
                painter.fillRect(dx, half, half, half, QtGui.QColor(130, 130, 130))
                painter.fillRect(dx + half, half, half, half, QtGui.QColor(190, 190, 190))
            painter.setClipping(False)

        painter.fillPath(path, QtGui.QBrush(self._color))
        # Тонкая обводка в цвет темы, не чёрная
        pen_col = QtGui.QColor(BORDER2)
        pen_col.setAlpha(180)
        painter.strokePath(path, QtGui.QPen(pen_col, 1))
        painter.end()
        return pm

    def _update_icon(self):
        self.setIcon(QtGui.QIcon(self._make_swatch()))
        self.setIconSize(QtCore.QSize(28, 16))

    def color(self):
        return self._color

    def setColor(self, c: QtGui.QColor):
        self._color = c
        self._update_icon()


class CustomTitleBar(QtWidgets.QWidget):
    def __init__(self, parent, title="App"):
        super().__init__(parent)
        self._parent = parent
        self.setFixedHeight(38)
        # Прозрачный фон — RoundedPanel рисует за нас BG через paintEvent
        self.setAutoFillBackground(False)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.setStyleSheet(f"background: transparent; border-bottom: 1px solid {BORDER};")

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 8, 0)

        dot_widget = QtWidgets.QWidget()
        dot_lay = QtWidgets.QHBoxLayout(dot_widget)
        dot_lay.setContentsMargins(0, 0, 10, 0)
        dot_lay.setSpacing(7)
        for col in [RED, "#f59e0b", GREEN]:
            dot = QtWidgets.QLabel()
            dot.setFixedSize(11, 11)
            dot.setStyleSheet(
                f"background: {col}; border-radius: 5px;"
                f"min-width: 11px; min-height: 11px; border: none;"
            )
            dot_lay.addWidget(dot)
        lay.addWidget(dot_widget)

        lbl = QtWidgets.QLabel(title)
        lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 600;"
            f"letter-spacing: 0.3px; border: none;"
        )
        lay.addWidget(lbl)
        lay.addStretch()

        for sym, slot, hcol in [("—", parent.showMinimized, BORDER2),
                                 ("✕", parent.close, RED)]:
            btn = QtWidgets.QPushButton(sym)
            btn.setFixedSize(32, 28)
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; border: none; border-radius: 5px;"
                f"color: {SUB}; font-size: 14px; }}"
                f"QPushButton:hover {{ background: {hcol}; color: white; }}"
            )
            btn.clicked.connect(slot)
            lay.addWidget(btn)

        self._start = None

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._start = e.globalPos()

    def mouseMoveEvent(self, e):
        if e.buttons() == QtCore.Qt.LeftButton and self._start:
            self._parent.move(self._parent.pos() + e.globalPos() - self._start)
            self._start = e.globalPos()




# ==========================================
# ОВЕРЛЕЙ ПРИЦЕЛА
# ==========================================

class CrosshairOverlay(QtWidgets.QWidget):
    visibility_signal = QtCore.pyqtSignal(bool)

    def __init__(self, cfg):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        w, h = get_monitor_size()
        self.setGeometry(0, 0, w, h)

        d = default_config()
        self.mode                = cfg.get("mode",                 d["mode"])
        self.color               = QtGui.QColor(*cfg.get("color",          d["color"]))
        self.line_length         = float(cfg.get("line_length",    d["line_length"]))
        self.line_thickness      = float(cfg.get("line_thickness", d["line_thickness"]))
        self.gap                 = float(cfg.get("gap",            d["gap"]))
        self.draw_circle         = cfg.get("draw_circle",          d["draw_circle"])
        self.circle_radius       = float(cfg.get("circle_radius",  d["circle_radius"]))
        self.outline_thickness   = float(cfg.get("outline_thickness", d["outline_thickness"]))
        self.outline_color       = QtGui.QColor(*cfg.get("outline_color",  d["outline_color"]))
        self.dot_radius          = float(cfg.get("dot_radius",     d["dot_radius"]))
        self.dot_outline_thickness = float(cfg.get("dot_outline_thickness", d["dot_outline_thickness"]))
        self.rmb_hide_enabled    = cfg.get("rmb_hide_enabled",     d["rmb_hide_enabled"])
        self.rmb_threshold       = float(cfg.get("rmb_threshold",  d["rmb_threshold"]))
        self.auto_stretch_game   = cfg.get("auto_stretch_game",    d["auto_stretch_game"])
        self.custom_res_enabled  = cfg.get("custom_res_enabled",   d["custom_res_enabled"])
        self.custom_res_width    = cfg.get("custom_res_width",     d["custom_res_width"])
        self.custom_res_height   = cfg.get("custom_res_height",    d["custom_res_height"])

        self.visibility_signal.connect(self._set_visible)
        make_window_clickthrough(self)
        self.show()

        self._size_timer = QtCore.QTimer(self)
        self._size_timer.timeout.connect(self._check_size)
        self._size_timer.start(2000)

    def _check_size(self):
        w, h = get_monitor_size()
        if self.width() != w or self.height() != h:
            self.setGeometry(0, 0, w, h)

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        cx = self.width()  / 2.0
        cy = self.height() / 2.0

        if self.mode == "cross":
            ln = self.line_length
            if self.outline_thickness > 0:
                pen = QtGui.QPen(self.outline_color)
                pen.setWidthF(max(0.5, self.line_thickness + 2.0 * self.outline_thickness))
                pen.setCapStyle(QtCore.Qt.RoundCap)
                p.setPen(pen)
                self._draw_lines(p, cx, cy, ln)
            pen = QtGui.QPen(self.color)
            pen.setWidthF(max(0.5, self.line_thickness))
            pen.setCapStyle(QtCore.Qt.RoundCap)
            p.setPen(pen)
            self._draw_lines(p, cx, cy, ln)
            if self.draw_circle:
                p.setBrush(QtCore.Qt.NoBrush)
                p.drawEllipse(QtCore.QPointF(cx, cy),
                              self.circle_radius, self.circle_radius)
        else:
            r = self.dot_radius
            if self.dot_outline_thickness > 0:
                p.setPen(QtGui.QPen(self.outline_color, self.dot_outline_thickness))
                p.setBrush(QtCore.Qt.NoBrush)
                p.drawEllipse(QtCore.QPointF(cx, cy), r, r)
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(self.color)
            p.drawEllipse(QtCore.QPointF(cx, cy), r, r)

    def _draw_lines(self, p, x, y, l):
        g = self.gap
        if l > 0:
            p.drawLine(QtCore.QLineF(x,     y - g,     x,     y - g - l))
            p.drawLine(QtCore.QLineF(x,     y + g,     x,     y + g + l))
            p.drawLine(QtCore.QLineF(x - g, y,         x - g - l, y))
            p.drawLine(QtCore.QLineF(x + g, y,         x + g + l, y))

    def to_config(self):
        return {
            "mode":                  self.mode,
            "color":                 list(self.color.getRgb()),
            "line_length":           round(self.line_length, 3),
            "line_thickness":        round(self.line_thickness, 3),
            "gap":                   round(self.gap, 3),
            "draw_circle":           self.draw_circle,
            "circle_radius":         round(self.circle_radius, 3),
            "outline_thickness":     round(self.outline_thickness, 3),
            "outline_color":         list(self.outline_color.getRgb()),
            "dot_radius":            round(self.dot_radius, 3),
            "dot_outline_thickness": round(self.dot_outline_thickness, 3),
            "rmb_hide_enabled":      self.rmb_hide_enabled,
            "rmb_threshold":         round(self.rmb_threshold, 3),
            "auto_stretch_game":     self.auto_stretch_game,
            "custom_res_enabled":    self.custom_res_enabled,
            "custom_res_width":      self.custom_res_width,
            "custom_res_height":     self.custom_res_height,
        }

    @QtCore.pyqtSlot(bool)
    def _set_visible(self, v):
        if v:
            self.show()
            make_window_clickthrough(self)
        else:
            self.hide()


# ==========================================
# ОКНО НАСТРОЕК
# ==========================================

class SettingsWindow(QtWidgets.QWidget):
    # Сигналы для безопасного общения с потоками (keyboard, threading)
    _key_captured      = QtCore.pyqtSignal(str)   # имя горячей клавиши из потока захвата
    _toggle_res_signal = QtCore.pyqtSignal()       # переключить разрешение из потока keyboard

    def __init__(self, overlay, initial_preset):
        super().__init__()
        self.overlay        = overlay
        self.current_preset = initial_preset
        self._loading       = False
        self._resolutions   = get_available_resolutions()
        self.setAutoFillBackground(False)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)

        # Мониторинг игры
        self._res_applied = False  # применено ли кастомное разрешение сейчас
        self._game_timer  = QtCore.QTimer(self)
        self._game_timer.timeout.connect(self._tick)

        # Горячая клавиша переключения разрешения
        self._res_hotkey = ""     # строка вида "f9" или "ctrl+f8"
        self._binding    = False  # True пока ждём нажатие от пользователя
        self._key_captured.connect(self._on_key_captured)
        self._toggle_res_signal.connect(self._toggle_res_hotkey)

        self._setup_ui()
        self.refresh_presets()
        cfg = load_preset(self.current_preset) if self.current_preset else None
        if cfg:
            self.apply_config(cfg)

    # ──────────────────────────────────────
    # Построение UI
    # ──────────────────────────────────────
    def _setup_ui(self):
        root = QtWidgets.QHBoxLayout(self)
        root.setContentsMargins(15, 15, 15, 15)
        root.setSpacing(14)

        # ══ БОКОВАЯ ПАНЕЛЬ ══
        sidebar = QtWidgets.QWidget()
        sidebar.setFixedWidth(215)
        sb = QtWidgets.QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(10)

        pg = QtWidgets.QGroupBox("ПРЕСЕТЫ")
        pl = QtWidgets.QVBoxLayout(pg)
        pl.setSpacing(7)
        self.preset_list = QtWidgets.QListWidget()
        self.preset_list.setMinimumHeight(120)
        pl.addWidget(self.preset_list)

        btn_grid = QtWidgets.QGridLayout()
        btn_grid.setSpacing(5)
        self.b_load = QtWidgets.QPushButton("Загрузить")
        self.b_save = QtWidgets.QPushButton("Сохранить")
        self.b_ren  = QtWidgets.QPushButton("Переим.")   # укороченный текст — влазит
        self.b_del  = QtWidgets.QPushButton("Удалить")
        self.b_del.setObjectName("DangerButton")
        btn_grid.addWidget(self.b_load, 0, 0)
        btn_grid.addWidget(self.b_save, 0, 1)
        btn_grid.addWidget(self.b_ren,  1, 0)
        btn_grid.addWidget(self.b_del,  1, 1)
        pl.addLayout(btn_grid)
        sb.addWidget(pg)

        cg = QtWidgets.QGroupBox("ЦВЕТ ПРИЦЕЛА")
        cl = QtWidgets.QVBoxLayout(cg)
        cl.setSpacing(7)
        self.b_mc = ColorButton("Основной цвет",  self.overlay.color)
        self.b_oc = ColorButton("Цвет обводки",   self.overlay.outline_color)
        cl.addWidget(self.b_mc)
        cl.addWidget(self.b_oc)
        sb.addWidget(cg)
        sb.addStretch()
        root.addWidget(sidebar)

        # ══ ПРАВАЯ ЧАСТЬ ══
        right = QtWidgets.QVBoxLayout()
        right.setSpacing(10)

        # Режим прицела
        mode_row = QtWidgets.QHBoxLayout()
        lbl_m = QtWidgets.QLabel("РЕЖИМ ПРИЦЕЛА")
        lbl_m.setObjectName("Sub")
        lbl_m.setStyleSheet(
            f"color: {SUB}; font-size: 10px; font-weight: bold; letter-spacing: 1.5px;"
        )
        self.rb_cr = ModernRadioButton("✛  Крестик")
        self.rb_dt = ModernRadioButton("●  Точка")
        self.rb_cr.setChecked(True)
        mode_row.addWidget(lbl_m)
        mode_row.addStretch()
        mode_row.addWidget(self.rb_cr)
        mode_row.addSpacing(16)
        mode_row.addWidget(self.rb_dt)
        right.addLayout(mode_row)

        # Два столбца настроек
        cols = QtWidgets.QHBoxLayout()
        cols.setSpacing(14)

        # ── Столбец 1: Параметры (все значения до тысячных) ──
        c1 = QtWidgets.QVBoxLayout()
        c1.setSpacing(0)
        params = QtWidgets.QGroupBox("ПАРАМЕТРЫ")
        pp = QtWidgets.QVBoxLayout(params)
        pp.setSpacing(0)
        pp.setContentsMargins(10, 12, 10, 10)
        self.sl_len   = SliderRow("Длина линий",          0,    100,  decimals=3)
        self.sl_thick = SliderRow("Толщина линий",        0.1,  20.0, decimals=3)
        self.sl_gap   = SliderRow("Отступ от центра",     0,    50,   decimals=3)
        self.sl_oth   = SliderRow("Толщина обводки",      0,    10,   decimals=3)
        self.sl_dr    = SliderRow("Радиус точки",         0.1,  50,   decimals=3)
        self.sl_cr    = SliderRow("Радиус окружности",    0.1,  80,   decimals=3)
        for sl in [self.sl_len, self.sl_thick, self.sl_gap,
                   self.sl_oth, self.sl_dr, self.sl_cr]:
            pp.addWidget(sl)
        c1.addWidget(params)
        c1.addStretch()
        cols.addLayout(c1, 1)

        # ── Столбец 2: Функции + Экран ──
        c2 = QtWidgets.QVBoxLayout()
        c2.setSpacing(10)

        funcs = QtWidgets.QGroupBox("ФУНКЦИИ")
        fl = QtWidgets.QVBoxLayout(funcs)
        fl.setSpacing(7)
        fl.setContentsMargins(10, 12, 10, 10)
        self.chk_c   = ToggleSwitch("Окружность вокруг прицела")
        self.chk_rmb = ToggleSwitch("Скрывать при прицеливании (ПКМ)")
        self.sl_rmb  = SliderRow("Задержка скрытия", 0.05, 2.0,
                                 decimals=2, suffix=" с")
        fl.addWidget(self.chk_c)
        fl.addWidget(self.chk_rmb)
        fl.addWidget(self.sl_rmb)
        c2.addWidget(funcs)

        screen = QtWidgets.QGroupBox("ЭКРАН")
        sl3 = QtWidgets.QVBoxLayout(screen)
        sl3.setSpacing(8)
        sl3.setContentsMargins(10, 12, 10, 10)
        self.chk_res  = ToggleSwitch("Кастомное разрешение")

        # Всё, что зависит от chk_res, собирается в один контейнер
        self._res_sub_group = QtWidgets.QWidget()
        _sub = QtWidgets.QVBoxLayout(self._res_sub_group)
        _sub.setContentsMargins(0, 0, 0, 0)
        _sub.setSpacing(8)

        self.chk_auto = ToggleSwitch("Авто-растяжение при запуске")
        _sub.addWidget(self.chk_auto)

        res_row = QtWidgets.QHBoxLayout()
        res_lbl = QtWidgets.QLabel("Разрешение:")
        res_lbl.setObjectName("Sub")
        self.cb_res = QtWidgets.QComboBox()
        for w, h in self._resolutions:
            self.cb_res.addItem(f"{w} × {h}")
        res_row.addWidget(res_lbl)
        res_row.addWidget(self.cb_res, 1)
        _sub.addLayout(res_row)

        # ── Горячая клавиша переключения разрешения ──────────────────────
        hk_lbl = QtWidgets.QLabel("Клавиша переключения:")
        hk_lbl.setObjectName("Sub")

        self.b_hk = QtWidgets.QPushButton("Не задана")
        self.b_hk.setFixedHeight(26)
        self.b_hk.setMinimumWidth(90)
        self.b_hk.setToolTip(
            "Нажмите, чтобы назначить горячую клавишу.\n"
            "Поддерживаются комбинации: Ctrl+F9, F5 и т.д.\n"
            "Клавиша мгновенно переключает разрешение."
        )

        self.b_hk_clr = QtWidgets.QPushButton("✕")
        self.b_hk_clr.setFixedSize(26, 26)
        self.b_hk_clr.setObjectName("DangerButton")
        self.b_hk_clr.setToolTip("Убрать привязку")

        hk_row = QtWidgets.QHBoxLayout()
        hk_row.setSpacing(4)
        hk_row.addWidget(hk_lbl)
        hk_row.addStretch()
        hk_row.addWidget(self.b_hk)
        hk_row.addWidget(self.b_hk_clr)
        _sub.addLayout(hk_row)
        # ─────────────────────────────────────────────────────────────────

        action_row = QtWidgets.QHBoxLayout()
        self.b_res = QtWidgets.QPushButton("Сбросить разрешение")
        self.b_res.setObjectName("DangerButton")
        self.b_res.setFixedHeight(36)
        self.b_str = QtWidgets.QPushButton("РАСТЯНУТЬ ИГРУ")
        self.b_str.setObjectName("AccentButton")
        self.b_str.setFixedHeight(36)
        action_row.addWidget(self.b_res)
        action_row.addWidget(self.b_str)
        _sub.addLayout(action_row)

        # Эффект прозрачности для визуальной блокировки sub-group
        self._res_sub_opacity = QtWidgets.QGraphicsOpacityEffect(self._res_sub_group)
        self._res_sub_opacity.setOpacity(1.0)
        self._res_sub_group.setGraphicsEffect(self._res_sub_opacity)

        sl3.addWidget(self.chk_res)
        sl3.addWidget(self._res_sub_group)
        c2.addWidget(screen)
        c2.addStretch()
        cols.addLayout(c2, 1)

        right.addLayout(cols)

        # Статус
        self.lbl_st = QtWidgets.QLabel("")
        self.lbl_st.setObjectName("Status")
        self.lbl_st.setAlignment(QtCore.Qt.AlignCenter)
        right.addWidget(self.lbl_st)

        root.addLayout(right, 1)

        # ══ ПОДКЛЮЧЕНИЕ СИГНАЛОВ ══
        self.b_load.clicked.connect(self._do_load)
        self.b_save.clicked.connect(self._do_save)
        self.b_ren.clicked.connect(self._do_ren)
        self.b_del.clicked.connect(self._do_del)
        self.b_mc.colorChanged.connect(self._on_main_color)
        self.b_oc.colorChanged.connect(self._on_outline_color)

        self.rb_cr.toggled.connect(self.update_live)
        self.rb_dt.toggled.connect(self.update_live)
        for sl in [self.sl_len, self.sl_thick, self.sl_gap, self.sl_oth,
                   self.sl_dr, self.sl_cr, self.sl_rmb]:
            sl.valueChanged.connect(self.update_live)
        for chk in [self.chk_c, self.chk_rmb, self.chk_auto, self.chk_res]:
            chk.stateChanged.connect(self.update_live)
        self.cb_res.currentIndexChanged.connect(self.update_live)

        self.b_str.clicked.connect(self._do_stretch)
        self.b_res.clicked.connect(self._do_restore)
        self.b_hk.clicked.connect(self._start_key_capture)
        self.b_hk_clr.clicked.connect(self._clear_res_hotkey)

        # Начальные состояния вычисляются по текущим значениям виджетов
        self._update_enabled_states()

    # ──────────────────────────────────────
    # Управление активностью виджетов
    # ──────────────────────────────────────
    def _update_enabled_states(self):
        """Синхронизирует enabled/opacity всех контролов с текущим режимом и переключателями."""
        is_cross   = self.rb_cr.isChecked()
        custom_res = self.chk_res.isChecked()

        # Параметры, специфичные для режима «крестик»
        self.sl_len.setEnabled(is_cross)
        self.sl_thick.setEnabled(is_cross)
        self.sl_gap.setEnabled(is_cross)
        self.chk_c.setEnabled(is_cross)
        self.sl_cr.setEnabled(is_cross and self.chk_c.isChecked())

        # Параметры, специфичные для режима «точка»
        self.sl_dr.setEnabled(not is_cross)

        # Задержка скрытия при ПКМ
        self.sl_rmb.setEnabled(self.chk_rmb.isChecked())

        # Блок «Экран» — всё содержимое sub-group зависит от «Кастомное разрешение»
        self._res_sub_group.setEnabled(custom_res)
        self._res_sub_opacity.setOpacity(1.0 if custom_res else 0.35)

        # Кнопка горячей клавиши дополнительно блокируется во время захвата
        self.b_hk.setEnabled(custom_res and not self._binding)

    # ──────────────────────────────────────
    # Мониторинг закрытия игры
    # ──────────────────────────────────────
    def _tick(self):
        """Вызывается каждые 2 с. Следит только за закрытием игры."""
        if find_game_hwnd():
            return
        # Игра закрылась — сбрасываем разрешение
        if self._res_applied:
            self._res_applied = False
            restore_display_resolution()
        self._game_timer.stop()
        self.status("Игра закрыта — разрешение сброшено")

    # ──────────────────────────────────────
    # Пресеты
    # ──────────────────────────────────────
    def refresh_presets(self):
        self.preset_list.clear()
        for name in list_presets():
            item = QtWidgets.QListWidgetItem(name)
            if name == self.current_preset:
                item.setForeground(QtGui.QColor(ACCL))
            self.preset_list.addItem(item)

    def _do_load(self):
        item = self.preset_list.currentItem()
        if not item:
            return
        cfg = load_preset(item.text())
        if cfg is None:
            self.status("Не удалось загрузить пресет")
            return
        self.current_preset = item.text()
        self.apply_config(cfg)
        self.refresh_presets()
        self.status(f"Загружено: {item.text()}")

    def _do_save(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Сохранить пресет", "Имя:")
        if ok and name:
            n = sanitize(name)
            if save_preset(n, self.overlay.to_config()):
                self.current_preset = n
                self.refresh_presets()
                self.status(f"Сохранено: {n}")
            else:
                self.status("Ошибка при сохранении")

    def _do_ren(self):
        item = self.preset_list.currentItem()
        if not item:
            return
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Переименовать пресет", "Новое имя:", text=item.text()
        )
        if ok and new_name:
            new_n = sanitize(new_name)
            if rename_preset(item.text(), new_n):
                if self.current_preset == item.text():
                    self.current_preset = new_n
                self.refresh_presets()

    def _do_del(self):
        item = self.preset_list.currentItem()
        if not item:
            return
        reply = QtWidgets.QMessageBox.question(
            self, "Удалить пресет",
            f'Удалить пресет «{item.text()}»?\nЭто действие необратимо.',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            delete_preset(item.text())
            if self.current_preset == item.text():
                self.current_preset = None
            self.refresh_presets()

    def _on_main_color(self, c):
        if not self._loading:
            self.overlay.color = c
            self.overlay.update()
            self._autosave()

    def _on_outline_color(self, c):
        if not self._loading:
            self.overlay.outline_color = c
            self.overlay.update()
            self._autosave()

    # ──────────────────────────────────────
    # Живое обновление
    # ──────────────────────────────────────
    def update_live(self):
        if self._loading:
            return
        o = self.overlay
        o.mode             = "cross" if self.rb_cr.isChecked() else "dot"
        o.line_length      = self.sl_len.value()
        o.line_thickness   = self.sl_thick.value()
        o.gap              = self.sl_gap.value()
        o.outline_thickness = self.sl_oth.value()
        o.dot_radius       = self.sl_dr.value()
        o.circle_radius    = self.sl_cr.value()
        o.draw_circle      = self.chk_c.isChecked()
        o.rmb_hide_enabled = self.chk_rmb.isChecked()
        o.rmb_threshold    = self.sl_rmb.value()
        o.auto_stretch_game = self.chk_auto.isChecked()
        o.custom_res_enabled = self.chk_res.isChecked()

        idx = self.cb_res.currentIndex()
        if 0 <= idx < len(self._resolutions):
            o.custom_res_width, o.custom_res_height = self._resolutions[idx]

        self._update_enabled_states()

        o.update()
        self._autosave()

    def apply_config(self, cfg):
        if cfg is None:
            return
        self._loading = True
        try:
            o = self.overlay
            d = default_config()
            o.mode               = cfg.get("mode",               d["mode"])
            o.color              = QtGui.QColor(*cfg.get("color",          d["color"]))
            o.line_length        = float(cfg.get("line_length",   d["line_length"]))
            o.line_thickness     = float(cfg.get("line_thickness", d["line_thickness"]))
            o.gap                = float(cfg.get("gap",            d["gap"]))
            o.draw_circle        = cfg.get("draw_circle",        d["draw_circle"])
            o.circle_radius      = float(cfg.get("circle_radius", d["circle_radius"]))
            o.outline_thickness  = float(cfg.get("outline_thickness", d["outline_thickness"]))
            o.outline_color      = QtGui.QColor(*cfg.get("outline_color",  d["outline_color"]))
            o.dot_radius         = float(cfg.get("dot_radius",    d["dot_radius"]))
            o.dot_outline_thickness = float(cfg.get("dot_outline_thickness", d["dot_outline_thickness"]))
            o.rmb_hide_enabled   = cfg.get("rmb_hide_enabled",   d["rmb_hide_enabled"])
            o.rmb_threshold      = float(cfg.get("rmb_threshold", d["rmb_threshold"]))
            o.auto_stretch_game  = cfg.get("auto_stretch_game",  d["auto_stretch_game"])
            o.custom_res_enabled = cfg.get("custom_res_enabled", d["custom_res_enabled"])
            o.custom_res_width   = cfg.get("custom_res_width",   d["custom_res_width"])
            o.custom_res_height  = cfg.get("custom_res_height",  d["custom_res_height"])

            self.rb_cr.setChecked(o.mode == "cross")
            self.rb_dt.setChecked(o.mode != "cross")
            self.sl_len.setValue(o.line_length)
            self.sl_thick.setValue(o.line_thickness)
            self.sl_gap.setValue(o.gap)
            self.sl_oth.setValue(o.outline_thickness)
            self.sl_dr.setValue(o.dot_radius)
            self.sl_cr.setValue(o.circle_radius)
            self.sl_rmb.setValue(o.rmb_threshold)
            self.chk_c.setChecked(o.draw_circle)
            self.chk_rmb.setChecked(o.rmb_hide_enabled)
            self.chk_auto.setChecked(o.auto_stretch_game)
            self.chk_res.setChecked(o.custom_res_enabled)
            self.b_mc.setColor(o.color)
            self.b_oc.setColor(o.outline_color)
            self._set_res_combo(o.custom_res_width, o.custom_res_height)

            self._update_enabled_states()

            o.update()
        finally:
            self._loading = False

    def _set_res_combo(self, w, h):
        for i, (rw, rh) in enumerate(self._resolutions):
            if rw == w and rh == h:
                self.cb_res.setCurrentIndex(i)
                return
        if self._resolutions:
            best = min(
                range(len(self._resolutions)),
                key=lambda i: abs(self._resolutions[i][0] - w) + abs(self._resolutions[i][1] - h)
            )
            self.cb_res.setCurrentIndex(best)

    def _autosave(self):
        if self.current_preset:
            save_preset(self.current_preset, self.overlay.to_config())

    def status(self, text):
        self.lbl_st.setText(text)
        QtCore.QTimer.singleShot(3500, lambda: self.lbl_st.setText(""))

    # ──────────────────────────────────────
    # Управление экраном
    # ──────────────────────────────────────
    def _do_stretch(self):
        hwnd = find_game_hwnd()
        if not hwnd:
            names = " / ".join(f'«{n}»' for n in GAME_WINDOW_NAMES)
            self.status(f"Окно {names} не найдено")
            return

        make_window_borderless(hwnd)

        if self.chk_res.isChecked():
            idx = self.cb_res.currentIndex()
            w, h = (self._resolutions[idx]
                    if 0 <= idx < len(self._resolutions)
                    else get_monitor_size())
            self.overlay.custom_res_width  = w
            self.overlay.custom_res_height = h

            # Применяем разрешение сразу, без слежения за фокусом
            self._res_applied = True
            def _on_stretch(ok, _w=w, _h=h):
                if not ok:
                    self._res_applied = False
                    self.status(f"Не удалось применить разрешение {_w}×{_h}")
            change_display_resolution(w, h, callback=_on_stretch)
            self.status(f"Растянуто: {w} × {h}")
        else:
            self.status("Окно растянуто")

        # Следим только за закрытием игры
        self._game_timer.start(2000)

    def _do_restore(self):
        self._game_timer.stop()
        if self._res_applied:
            self._res_applied = False
            restore_display_resolution()
        self.status("Разрешение сброшено")

    # ──────────────────────────────────────────────────────────────────────
    # Горячая клавиша переключения разрешения
    # ──────────────────────────────────────────────────────────────────────

    def _start_key_capture(self):
        """Входит в режим ожидания нажатия для привязки горячей клавиши."""
        if self._binding:
            return
        self._binding = True
        self.b_hk.setText("Нажмите клавишу…")
        self.b_hk.setEnabled(False)
        threading.Thread(target=self._capture_key_thread, daemon=True,
                         name="hk-capture").start()

    def _capture_key_thread(self):
        """Блокирует поток до первого нажатия. Поддерживает комбинации."""
        try:
            # read_hotkey ждёт отпускания всех клавиш и возвращает
            # строку вида "f9", "ctrl+f8", "shift+f2" и т.д.
            key = keyboard.read_hotkey(suppress=False)
            self._key_captured.emit(key.lower())
        except Exception as e:
            logging.error(f"_capture_key_thread: {e}")
            self._key_captured.emit("")

    def _on_key_captured(self, key_str: str):
        """Вызывается в Qt-потоке после захвата клавиши."""
        self._binding = False
        if not key_str:
            # Ошибка захвата — восстанавливаем предыдущий текст
            self.b_hk.setText(self._res_hotkey.upper() if self._res_hotkey else "Не задана")
        else:
            self._set_res_hotkey(key_str)
            self.status(f"Горячая клавиша: {key_str.upper()}")
        # Восстанавливаем корректные состояния (b_hk, sub-group и т.д.)
        self._update_enabled_states()

    def _set_res_hotkey(self, key_str: str):
        """Снимает старую привязку, регистрирует новую, сохраняет в конфиг."""
        # Снять предыдущую привязку
        if self._res_hotkey:
            try:
                keyboard.remove_hotkey(self._res_hotkey)
            except Exception:
                pass
        self._res_hotkey = key_str
        if key_str:
            try:
                keyboard.add_hotkey(
                    key_str,
                    lambda: self._toggle_res_signal.emit(),
                    suppress=False
                )
                self.b_hk.setText(key_str.upper())
            except Exception as e:
                logging.error(f"_set_res_hotkey: {e}")
                self.b_hk.setText("Ошибка!")
                self._res_hotkey = ""
        else:
            self.b_hk.setText("Не задана")
        # Сохраняем в файл конфига приложения
        cfg = load_app_config()
        cfg["res_hotkey"] = self._res_hotkey
        save_app_config(cfg)

    def _clear_res_hotkey(self):
        """Убирает привязку горячей клавиши."""
        self._set_res_hotkey("")
        self.status("Горячая клавиша снята")

    def _toggle_res_hotkey(self):
        """Переключает разрешение по горячей клавише (вызывается через сигнал)."""
        if not self._game_timer.isActive() or not self.overlay.custom_res_enabled:
            self.status("Сначала нажмите «РАСТЯНУТЬ ИГРУ»")
            return
        if self._res_applied:
            self._res_applied = False
            restore_display_resolution()
            self.status("Разрешение: нативное ↩")
        else:
            w, h = self.overlay.custom_res_width, self.overlay.custom_res_height
            self._res_applied = True
            change_display_resolution(w, h)
            self.status(f"Разрешение: {w}×{h} ↗")


# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================

class MainWindow(QtWidgets.QMainWindow):
    """Главное окно.

    Фон и тень рисуются в paintEvent самого QMainWindow — до дочерних
    виджетов. Дочерние виджеты не достают до угловых пикселей
    (layout contentMargins > corner radius), поэтому углы чисто прозрачны
    без setMask и без QGraphicsDropShadowEffect.
    """
    _M = 13   # отступ: угловые пиксели (radius=12) не перекроются детьми
    _R = 12   # радиус скругления

    def __init__(self, overlay, initial_preset):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.resize(920, 610)

        # Прозрачный контейнер — фон рисует paintEvent окна, не сам виджет
        central = QtWidgets.QWidget()
        central.setAutoFillBackground(False)
        central.setAttribute(QtCore.Qt.WA_NoSystemBackground)

        layout = QtWidgets.QVBoxLayout(central)
        # Отступ _M: дочерние виджеты начинаются ПОСЛЕ угловой зоны (12px)
        layout.setContentsMargins(self._M, self._M, self._M, self._M)
        layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self, "Custom Crosshair  ·  STALCRAFT: X")
        self.settings  = SettingsWindow(overlay, initial_preset)
        layout.addWidget(self.title_bar)
        layout.addWidget(self.settings)

        self.setCentralWidget(central)

    def paintEvent(self, event):
        """Рисует тень и скруглённый фон ДО дочерних виджетов."""
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        M, R = self._M, self._R
        cr = QtCore.QRectF(self.rect()).adjusted(M, M, -M, -M)
        p.setBrush(QtGui.QColor(BG))
        p.setPen(QtGui.QPen(QtGui.QColor(BORDER), 1.0))
        p.drawRoundedRect(cr.adjusted(0.5, 0.5, -0.5, -0.5), R, R)

    def closeEvent(self, event):
        event.ignore()
        self.hide()


# ==========================================
# СЛУШАТЕЛЬ ПКМ
# ==========================================

def start_rmb_listener(overlay):
    lock  = threading.Lock()
    state = {"pressed": False, "timer": None, "hidden": False}

    def hide_task():
        with lock:
            if state["pressed"] and overlay.rmb_hide_enabled:
                try:
                    overlay.visibility_signal.emit(False)
                except Exception as e:
                    logging.error(f"hide_task: {e}")
                state["hidden"] = True
            state["timer"] = None

    def on_click(x, y, btn, pressed):
        if btn != mouse.Button.right:
            return
        with lock:
            if pressed:
                state["pressed"] = True
                if not overlay.rmb_hide_enabled:
                    if state["timer"]:
                        state["timer"].cancel()
                        state["timer"] = None
                    state["hidden"] = False
                    overlay.visibility_signal.emit(True)
                    return
                if state["timer"]:
                    state["timer"].cancel()
                t = threading.Timer(overlay.rmb_threshold, hide_task)
                t.daemon = True
                t.start()
                state["timer"] = t
            else:
                state["pressed"] = False
                if state["timer"]:
                    state["timer"].cancel()
                    state["timer"] = None
                if state["hidden"]:
                    overlay.visibility_signal.emit(True)
                state["hidden"] = False

    listener = mouse.Listener(on_click=on_click)
    listener.daemon = True
    listener.start()
    return listener


# ==========================================
# ==========================================
# EVENT FILTER: снятие фокуса со спинбокса
# ==========================================

class SpinboxFocusFilter(QtCore.QObject):
    """Снимает фокус с InstantSpinBox при клике на любой другой виджет."""

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            focused = QtWidgets.QApplication.focusWidget()
            if (isinstance(focused, InstantSpinBox)
                    and not isinstance(obj, InstantSpinBox)):
                focused.clearFocus()   # вызовет focusOutEvent → _commit()
        return False


# ==========================================
# ТОЧКА ВХОДА
# ==========================================

def main():
    migrate_legacy_config()

    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(get_stylesheet())
    app.setQuitOnLastWindowClosed(False)

    _spinbox_filter = SpinboxFocusFilter()
    app.installEventFilter(_spinbox_filter)

    presets = list_presets()
    init_p  = "default" if "default" in presets else (presets[0] if presets else "default")
    if init_p == "default" and not os.path.exists(preset_path("default")):
        save_preset("default", default_config())

    cfg     = load_preset(init_p) or default_config()
    overlay = CrosshairOverlay(cfg)
    win     = MainWindow(overlay, init_p)
    win.show()

    # Трей
    tray = QtWidgets.QSystemTrayIcon(win.windowIcon(), app)
    ico_path = os.path.join(APP_DIR, "target.ico")
    if os.path.exists(ico_path):
        tray.setIcon(QtGui.QIcon(ico_path))

    menu = QtWidgets.QMenu()
    menu.addAction(
        "Показать/Скрыть прицел",
        lambda: overlay.visibility_signal.emit(not overlay.isVisible())
    )
    menu.addAction("Настройки", win.showNormal)
    menu.addSeparator()
    menu.addAction("Сбросить разрешение", restore_display_resolution)

    def do_exit():
        restore_display_resolution()
        app.quit()

    menu.addAction("Выход", do_exit)
    tray.setContextMenu(menu)
    tray.show()
    tray.activated.connect(lambda r: win.showNormal() if r == 3 else None)

    # Авто-растяжение при старте
    if overlay.auto_stretch_game:
        hwnd = find_game_hwnd()
        if hwnd:
            make_window_borderless(hwnd)
            if overlay.custom_res_enabled:
                win.settings._res_applied = True
                change_display_resolution(overlay.custom_res_width,
                                          overlay.custom_res_height)
            # Следим только за закрытием игры
            win.settings._game_timer.start(2000)
            win.settings.status("Авто-запуск: окно растянуто")

    # Горячая клавиша показа/скрытия оверлея
    try:
        keyboard.add_hotkey(
            "ctrl+shift+h",
            lambda: overlay.visibility_signal.emit(not overlay.isVisible())
        )
    except Exception as e:
        logging.error(f"hotkey registration: {e}")

    # Восстанавливаем сохранённую горячую клавишу переключения разрешения
    saved_hk = load_app_config().get("res_hotkey", "")
    if saved_hk:
        win.settings._set_res_hotkey(saved_hk)

    start_rmb_listener(overlay)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
