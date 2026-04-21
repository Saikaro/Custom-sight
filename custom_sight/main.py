import sys
import os
import logging

import keyboard
from PyQt5 import QtWidgets, QtCore, QtGui

from .constants import APP_DIR
from .config import (
    migrate_legacy_config, list_presets, preset_path,
    load_preset, save_preset, default_config, load_app_config,
)
from .system import (
    find_game_hwnd, make_window_borderless,
    change_display_resolution, restore_display_resolution,
)
from .stylesheet import get_stylesheet
from .overlay import CrosshairOverlay
from .main_window import MainWindow
from .rmb_listener import start_rmb_listener
from .widgets import SpinboxFocusFilter


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
    # Иконка лежит рядом с этим файлом (custom_sight/target.ico)
    # — работает и в dev-режиме, и в замороженном .exe
    _pkg_dir  = os.path.dirname(os.path.abspath(__file__))
    ico_path  = os.path.join(_pkg_dir, "target.ico")
    tray = QtWidgets.QSystemTrayIcon(QtGui.QIcon(ico_path) if os.path.exists(ico_path)
                                     else win.windowIcon(), app)
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
