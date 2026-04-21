import threading
import logging

import keyboard
from PyQt5 import QtWidgets, QtCore, QtGui

from .constants import GAME_WINDOW_NAMES, SUB, ACCL
from .config import (
    load_preset, save_preset, list_presets, delete_preset, rename_preset,
    sanitize, load_app_config, save_app_config, default_config,
)
from .system import (
    get_available_resolutions, find_game_hwnd, make_window_borderless,
    get_monitor_size, change_display_resolution, restore_display_resolution,
)
from .widgets import (
    ToggleSwitch, ModernRadioButton, SliderRow, ColorButton,
)


class SettingsWindow(QtWidgets.QWidget):
    # Сигналы для безопасного общения с потоками (keyboard, threading)
    _key_captured      = QtCore.pyqtSignal(str)
    _toggle_res_signal = QtCore.pyqtSignal()

    def __init__(self, overlay, initial_preset):
        super().__init__()
        self.overlay        = overlay
        self.current_preset = initial_preset
        self._loading       = False
        self._resolutions   = get_available_resolutions()
        self.setAutoFillBackground(False)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)

        self._res_applied = False
        self._game_timer  = QtCore.QTimer(self)
        self._game_timer.timeout.connect(self._tick)

        self._res_hotkey = ""
        self._binding    = False
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
        self.b_ren  = QtWidgets.QPushButton("Переим.")
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

        cols = QtWidgets.QHBoxLayout()
        cols.setSpacing(14)

        # ── Столбец 1: Параметры ──
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

        self._res_sub_opacity = QtWidgets.QGraphicsOpacityEffect(self._res_sub_group)
        self._res_sub_opacity.setOpacity(1.0)
        self._res_sub_group.setGraphicsEffect(self._res_sub_opacity)

        sl3.addWidget(self.chk_res)
        sl3.addWidget(self._res_sub_group)
        c2.addWidget(screen)
        c2.addStretch()
        cols.addLayout(c2, 1)

        right.addLayout(cols)

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
        if find_game_hwnd():
            return
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

            self._res_applied = True
            def _on_stretch(ok, _w=w, _h=h):
                if not ok:
                    self._res_applied = False
                    self.status(f"Не удалось применить разрешение {_w}×{_h}")
            change_display_resolution(w, h, callback=_on_stretch)
            self.status(f"Растянуто: {w} × {h}")
        else:
            self.status("Окно растянуто")

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
        if self._binding:
            return
        self._binding = True
        self.b_hk.setText("Нажмите клавишу…")
        self.b_hk.setEnabled(False)
        threading.Thread(target=self._capture_key_thread, daemon=True,
                         name="hk-capture").start()

    def _capture_key_thread(self):
        try:
            key = keyboard.read_hotkey(suppress=False)
            self._key_captured.emit(key.lower())
        except Exception as e:
            logging.error(f"_capture_key_thread: {e}")
            self._key_captured.emit("")

    def _on_key_captured(self, key_str: str):
        self._binding = False
        if not key_str:
            self.b_hk.setText(self._res_hotkey.upper() if self._res_hotkey else "Не задана")
        else:
            self._set_res_hotkey(key_str)
            self.status(f"Горячая клавиша: {key_str.upper()}")
        self._update_enabled_states()

    def _set_res_hotkey(self, key_str: str):
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
        cfg = load_app_config()
        cfg["res_hotkey"] = self._res_hotkey
        save_app_config(cfg)

    def _clear_res_hotkey(self):
        self._set_res_hotkey("")
        self.status("Горячая клавиша снята")

    def _toggle_res_hotkey(self):
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
