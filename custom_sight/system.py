import ctypes
import logging
import threading

import win32gui
import win32con
import win32api

from .constants import (
    GAME_WINDOW_NAMES,
    GWL_EXSTYLE, WS_EX_LAYERED, WS_EX_TRANSPARENT, WS_EX_NOACTIVATE,
)


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
_NATIVE_RES: tuple[int, int] | None = None


def _get_native_res() -> tuple[int, int]:
    """Возвращает разрешение из реестра (то, что стоит «по умолчанию»)."""
    global _NATIVE_RES
    if _NATIVE_RES is None:
        try:
            dm = win32api.EnumDisplaySettings(None, win32con.ENUM_REGISTRY_SETTINGS)
            _NATIVE_RES = (int(dm.PelsWidth), int(dm.PelsHeight))
        except Exception as e:
            logging.error(f"_get_native_res: {e}")
            dm = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            _NATIVE_RES = (int(dm.PelsWidth), int(dm.PelsHeight))
    return _NATIVE_RES


def _apply_res_sync(width: int, height: int) -> bool:
    """Выполняет ChangeDisplaySettings синхронно (вызывается из потока)."""
    try:
        dm = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
        if int(dm.PelsWidth) == width and int(dm.PelsHeight) == height:
            return True
        dm.PelsWidth  = width
        dm.PelsHeight = height
        dm.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT
        return win32api.ChangeDisplaySettings(dm, 0) == win32con.DISP_CHANGE_SUCCESSFUL
    except Exception as e:
        logging.error(f"change_display_resolution: {e}")
        return False


def change_display_resolution(width: int, height: int, callback=None) -> None:
    """Меняет разрешение в отдельном потоке."""
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
