from PyQt5 import QtWidgets, QtCore, QtGui

from .constants import (
    ACCENT, ACCH, ACCL, TEXT, SUB, BORDER, BORDER2, RED, GREEN, BG, CARD, CARD2,
)


# ══════════════════════════════════════════════════════════════════════════════
#  Базовые виджеты
# ══════════════════════════════════════════════════════════════════════════════

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
        self.setContentsMargins(4, 0, 0, 0)

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        D  = 18
        ox = 3
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
    """Числовое поле ввода на базе QLineEdit."""

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

    def setDecimals(self, d):       self._decimals = int(d)
    def setRange(self, lo, hi):     self._min, self._max = float(lo), float(hi)
    def setSingleStep(self, s):     pass
    def setButtonSymbols(self, s):  pass
    def lineEdit(self):             return self

    def setSuffix(self, s):
        self._suffix = s
        if not self.hasFocus():
            self._show_display()

    def value(self):
        return self._value

    def setValue(self, v):
        self._value = round(max(self._min, min(self._max, float(v))), self._decimals)
        if not self.hasFocus():
            self._show_display()

    def _show_display(self):
        self.setText(f"{self._value:.{self._decimals}f}{self._suffix}")

    def _show_edit(self):
        self.setText(f"{self._value:.{self._decimals}f}")

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
            pass
        self._show_display()

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
    """Слайдер + поле ввода, синхронизированные между собой."""
    valueChanged = QtCore.pyqtSignal(float)

    def __init__(self, label, min_v, max_v, decimals=0, suffix="", parent=None):
        super().__init__(parent)
        self._scale    = 10 ** decimals
        self._decimals = decimals
        self._min      = float(min_v)
        self._max      = float(max_v)
        self._syncing  = False

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 2, 0, 5)
        root.setSpacing(4)

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
        self.spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)

        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(self.spinbox)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(
            int(round(min_v * self._scale)),
            int(round(max_v * self._scale))
        )

        root.addLayout(top)
        root.addWidget(self.slider)

        self.spinbox.setValue(min_v)

        self.slider.valueChanged.connect(self._from_slider)
        self.spinbox.valueChanged.connect(self._from_spinbox)

        _eff = QtWidgets.QGraphicsOpacityEffect(self)
        _eff.setOpacity(1.0)
        self.setGraphicsEffect(_eff)

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

    def value(self):
        return self.spinbox.value()

    def setValue(self, v):
        self._syncing = True
        raw = int(round(float(v) * self._scale))
        self.slider.setValue(raw)
        self.spinbox.setValue(float(v))
        self._syncing = False

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.slider.setEnabled(enabled)
        self.spinbox.setEnabled(enabled)
        effect = QtWidgets.QGraphicsOpacityEffect(self)
        effect.setOpacity(1.0 if enabled else 0.30)
        self.setGraphicsEffect(effect)


# ══════════════════════════════════════════════════════════════════════════════
#  Color Picker — внутренние виджеты
# ══════════════════════════════════════════════════════════════════════════════

class _Swatch(QtWidgets.QWidget):
    """Плашка предпросмотра цвета с шахматкой для альфа-канала."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QtGui.QColor(0, 0, 0)
        self.setFixedSize(56, 36)

    def set_color(self, c: QtGui.QColor):
        self._color = QtGui.QColor(c)
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        W, H, R = self.width(), self.height(), 7
        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(0, 0, W, H), R, R)
        p.setClipPath(path)
        cell = 9
        light = QtGui.QColor(185, 185, 185)
        dark  = QtGui.QColor(115, 115, 115)
        for col in range(W // cell + 2):
            for row in range(H // cell + 2):
                p.fillRect(col * cell, row * cell, cell, cell,
                           light if (col + row) % 2 == 0 else dark)
        p.fillRect(0, 0, W, H, self._color)
        p.setClipping(False)
        p.setPen(QtGui.QPen(QtGui.QColor(BORDER2), 1.0))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawRoundedRect(QtCore.QRectF(0.5, 0.5, W - 1, H - 1), R, R)


class _ColorSquare(QtWidgets.QWidget):
    """Квадрат насыщенность / яркость (HSV)."""
    positionChanged = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hue = 0
        self._s   = 255
        self._v   = 255
        self.setCursor(QtCore.Qt.CrossCursor)

    def set_hue(self, h: int):
        self._hue = max(0, min(359, h))
        self.update()

    def set_sv(self, s: int, v: int):
        self._s = max(0, min(255, s))
        self._v = max(0, min(255, v))
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        W, H = self.width(), self.height()

        gh = QtGui.QLinearGradient(0, 0, W, 0)
        gh.setColorAt(0, QtGui.QColor(255, 255, 255))
        gh.setColorAt(1, QtGui.QColor.fromHsv(self._hue, 255, 255))
        p.fillRect(0, 0, W, H, gh)

        gv = QtGui.QLinearGradient(0, 0, 0, H)
        gv.setColorAt(0, QtGui.QColor(0, 0, 0, 0))
        gv.setColorAt(1, QtGui.QColor(0, 0, 0, 255))
        p.fillRect(0, 0, W, H, gv)

        cx = int(self._s / 255 * W)
        cy = int((1.0 - self._v / 255) * H)
        p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 120), 1.5))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawEllipse(QtCore.QPoint(cx, cy), 7, 7)
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        p.drawEllipse(QtCore.QPoint(cx, cy), 6, 6)

    def _pick(self, pos):
        W, H = max(self.width(), 1), max(self.height(), 1)
        s = max(0, min(255, round(pos.x() / W * 255)))
        v = max(0, min(255, round((1 - pos.y() / H) * 255)))
        self._s, self._v = s, v
        self.update()
        self.positionChanged.emit(s, v)

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._pick(e.pos())

    def mouseMoveEvent(self, e):
        if e.buttons() & QtCore.Qt.LeftButton:
            self._pick(e.pos())


class _HueSlider(QtWidgets.QWidget):
    """Слайдер оттенка (радуга)."""
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def set_value(self, h: int):
        self._value = max(0, min(359, h))
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        W, H = self.width(), self.height()
        R = H // 2

        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(0, 0, W, H), R, R)
        p.setClipPath(path)

        grad = QtGui.QLinearGradient(0, 0, W, 0)
        for i in range(7):
            grad.setColorAt(i / 6, QtGui.QColor.fromHsv(i * 60, 255, 255))
        p.fillRect(0, 0, W, H, grad)

        p.setClipping(False)
        cx = R + int(self._value / 359 * (W - H))
        cy = H // 2
        p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 100), 1))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawEllipse(QtCore.QPoint(cx, cy), R - 1, R - 1)
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        p.drawEllipse(QtCore.QPoint(cx, cy), R - 2, R - 2)

    def _pick(self, x):
        W, H = self.width(), self.height()
        R = H // 2
        h = max(0, min(359, round((x - R) / max(W - H, 1) * 359)))
        self._value = h
        self.update()
        self.valueChanged.emit(h)

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._pick(e.pos().x())

    def mouseMoveEvent(self, e):
        if e.buttons() & QtCore.Qt.LeftButton:
            self._pick(e.pos().x())


class _AlphaSlider(QtWidgets.QWidget):
    """Слайдер прозрачности с шахматкой."""
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value      = 255
        self._base_color = QtGui.QColor(255, 0, 0)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def set_value(self, a: int):
        self._value = max(0, min(255, a))
        self.update()

    def set_color(self, c: QtGui.QColor):
        self._base_color = QtGui.QColor(c.red(), c.green(), c.blue())
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        W, H = self.width(), self.height()
        R = H // 2

        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(0, 0, W, H), R, R)
        p.setClipPath(path)

        cell  = R
        light = QtGui.QColor(185, 185, 185)
        dark  = QtGui.QColor(115, 115, 115)
        for col in range(W // cell + 2):
            for row in range(2):
                p.fillRect(col * cell, row * cell, cell, cell,
                           light if (col + row) % 2 == 0 else dark)

        c0 = QtGui.QColor(self._base_color); c0.setAlpha(0)
        c1 = QtGui.QColor(self._base_color); c1.setAlpha(255)
        grad = QtGui.QLinearGradient(0, 0, W, 0)
        grad.setColorAt(0, c0)
        grad.setColorAt(1, c1)
        p.fillRect(0, 0, W, H, grad)

        p.setClipping(False)
        cx = R + int(self._value / 255 * (W - H))
        cy = H // 2
        p.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 100), 1))
        p.setBrush(QtCore.Qt.NoBrush)
        p.drawEllipse(QtCore.QPoint(cx, cy), R - 1, R - 1)
        p.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 2))
        p.drawEllipse(QtCore.QPoint(cx, cy), R - 2, R - 2)

    def _pick(self, x):
        W, H = self.width(), self.height()
        R = H // 2
        a = max(0, min(255, round((x - R) / max(W - H, 1) * 255)))
        self._value = a
        self.update()
        self.valueChanged.emit(a)

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._pick(e.pos().x())

    def mouseMoveEvent(self, e):
        if e.buttons() & QtCore.Qt.LeftButton:
            self._pick(e.pos().x())


# ══════════════════════════════════════════════════════════════════════════════
#  Color Picker Dialog
# ══════════════════════════════════════════════════════════════════════════════

class ColorPickerDialog(QtWidgets.QDialog):
    """Кастомный тёмный пикер цвета."""

    _STYLE = f"""
        QFrame#CPCard {{
            background: {CARD};
            border-radius: 12px;
            border: 1px solid {BORDER2};
        }}
        QLabel {{
            color: {TEXT};
            background: transparent;
            border: none;
            font-size: 12px;
        }}
        QLineEdit {{
            background: {CARD2};
            border: 1px solid {BORDER};
            border-radius: 5px;
            color: {TEXT};
            padding: 3px 8px;
            font-size: 12px;
            font-family: monospace;
        }}
        QLineEdit:focus {{ border-color: {ACCENT}; }}
        QSpinBox {{
            background: {CARD2};
            border: 1px solid {BORDER};
            border-radius: 5px;
            color: {TEXT};
            padding: 2px 6px;
            font-size: 12px;
        }}
        QSpinBox:focus {{ border-color: {ACCENT}; }}
        QPushButton {{
            background: {CARD2};
            border: 1px solid {BORDER};
            border-radius: 6px;
            color: {TEXT};
            font-size: 12px;
            padding: 6px 16px;
        }}
        QPushButton:hover {{ border-color: {ACCENT}; color: {ACCL}; }}
    """

    def __init__(self, initial_color: QtGui.QColor = None, parent=None):
        super().__init__(parent, QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setModal(True)
        self._color     = QtGui.QColor(initial_color) if initial_color else QtGui.QColor(255, 0, 0, 255)
        self._old_color = QtGui.QColor(self._color)
        self._updating  = False
        self._drag_pos  = None
        self._setup_ui()
        self._load_color(self._color, initial=True)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        card = QtWidgets.QFrame()
        card.setObjectName("CPCard")
        card.setStyleSheet(self._STYLE)

        vlay = QtWidgets.QVBoxLayout(card)
        vlay.setContentsMargins(16, 12, 16, 16)
        vlay.setSpacing(12)

        # ── Заголовок ─────────────────────────────────────────────────────────
        tr = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Выбор цвета")
        title.setStyleSheet(f"color:{TEXT}; font-size:13px; font-weight:600;")
        close_btn = QtWidgets.QPushButton("✕")
        close_btn.setFixedSize(26, 22)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {SUB}; font-size: 13px; border-radius: 4px; padding: 0;
            }}
            QPushButton:hover {{ background: {RED}; color: white; }}
        """)
        close_btn.clicked.connect(self.reject)
        tr.addWidget(title)
        tr.addStretch()
        tr.addWidget(close_btn)
        vlay.addLayout(tr)

        # ── Тело ──────────────────────────────────────────────────────────────
        body = QtWidgets.QHBoxLayout()
        body.setSpacing(16)

        # Левый столбец: квадрат + слайдеры
        left = QtWidgets.QVBoxLayout()
        left.setSpacing(8)

        self._sq = _ColorSquare()
        self._sq.setFixedSize(215, 215)
        self._sq.positionChanged.connect(self._on_sv)
        left.addWidget(self._sq)

        def _sub_label(text):
            lbl = QtWidgets.QLabel(text)
            lbl.setStyleSheet(f"color:{SUB}; font-size:10px; letter-spacing:1px;")
            return lbl

        left.addWidget(_sub_label("ОТТЕНОК"))
        self._hue = _HueSlider()
        self._hue.setFixedHeight(22)
        self._hue.valueChanged.connect(self._on_hue)
        left.addWidget(self._hue)

        left.addWidget(_sub_label("ПРОЗРАЧНОСТЬ"))
        self._alpha = _AlphaSlider()
        self._alpha.setFixedHeight(22)
        self._alpha.valueChanged.connect(self._on_alpha)
        left.addWidget(self._alpha)
        left.addStretch()
        body.addLayout(left)

        # Правый столбец: превью + поля ввода
        right = QtWidgets.QVBoxLayout()
        right.setSpacing(10)

        right.addWidget(_sub_label("ДО / ПОСЛЕ"))
        sw_row = QtWidgets.QHBoxLayout()
        sw_row.setSpacing(5)
        self._sw_old = _Swatch()
        self._sw_new = _Swatch()
        sw_row.addWidget(self._sw_old)
        sw_row.addWidget(self._sw_new)
        sw_row.addStretch()
        right.addLayout(sw_row)

        right.addSpacing(4)

        hex_row = QtWidgets.QHBoxLayout()
        hex_lbl = QtWidgets.QLabel("HEX")
        hex_lbl.setFixedWidth(32)
        self._hex = QtWidgets.QLineEdit()
        self._hex.setFixedWidth(104)
        self._hex.setMaxLength(9)
        self._hex.editingFinished.connect(self._on_hex)
        hex_row.addWidget(hex_lbl)
        hex_row.addWidget(self._hex)
        hex_row.addStretch()
        right.addLayout(hex_row)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet(f"border: none; background: {BORDER2}; max-height: 1px;")
        right.addWidget(sep)

        self._ch_spins = {}
        for ch, color_hint in [("R", RED), ("G", GREEN), ("B", "#3b82f6"), ("A", SUB)]:
            row = QtWidgets.QHBoxLayout()
            lbl = QtWidgets.QLabel(ch)
            lbl.setFixedWidth(14)
            lbl.setStyleSheet(
                f"color:{color_hint}; font-weight:700; font-size:11px;"
            )
            sp = QtWidgets.QSpinBox()
            sp.setRange(0, 255)
            sp.setFixedWidth(62)
            sp.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            sp.valueChanged.connect(self._on_rgba)
            self._ch_spins[ch] = sp
            row.addWidget(lbl)
            row.addWidget(sp)
            row.addStretch()
            right.addLayout(row)

        right.addStretch()
        body.addLayout(right)
        vlay.addLayout(body)

        # ── Кнопки ────────────────────────────────────────────────────────────
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch()
        cancel = QtWidgets.QPushButton("Отмена")
        cancel.clicked.connect(self.reject)
        ok = QtWidgets.QPushButton("Применить")
        ok.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; border: none; border-radius: 6px;
                color: white; font-size: 12px; font-weight: 600; padding: 6px 22px;
            }}
            QPushButton:hover {{ background: {ACCH}; }}
        """)
        ok.clicked.connect(self.accept)
        btn_row.addWidget(cancel)
        btn_row.addSpacing(6)
        btn_row.addWidget(ok)
        vlay.addLayout(btn_row)

        outer.addWidget(card)

    # ── Вспомогательные методы ────────────────────────────────────────────────
    def _load_color(self, c: QtGui.QColor, initial=False):
        self._updating = True
        h = c.hsvHue() if c.hsvHue() >= 0 else 0
        s, v, a = c.hsvSaturation(), c.value(), c.alpha()
        self._sq.set_hue(h)
        self._sq.set_sv(s, v)
        self._hue.set_value(h)
        self._alpha.set_color(QtGui.QColor.fromHsv(h, s, v))
        self._alpha.set_value(a)
        self._sw_new.set_color(c)
        if initial:
            self._sw_old.set_color(c)
        self._sync_inputs(c)
        self._updating = False

    def _sync_inputs(self, c: QtGui.QColor):
        self._hex.setText(
            f"#{c.red():02X}{c.green():02X}{c.blue():02X}{c.alpha():02X}"
        )
        for ch, val in [("R", c.red()), ("G", c.green()),
                        ("B", c.blue()), ("A", c.alpha())]:
            self._ch_spins[ch].blockSignals(True)
            self._ch_spins[ch].setValue(val)
            self._ch_spins[ch].blockSignals(False)

    def _current_opaque(self) -> QtGui.QColor:
        return QtGui.QColor.fromHsv(self._hue._value, self._sq._s, self._sq._v)

    def _commit(self):
        c = QtGui.QColor.fromHsv(
            self._hue._value, self._sq._s, self._sq._v, self._alpha._value
        )
        self._color = c
        self._sw_new.set_color(c)
        self._sync_inputs(c)

    # ── Слоты ─────────────────────────────────────────────────────────────────
    def _on_sv(self, s, v):
        if not self._updating:
            self._commit()

    def _on_hue(self, h):
        if not self._updating:
            self._sq.set_hue(h)
            self._alpha.set_color(self._current_opaque())
            self._commit()

    def _on_alpha(self, a):
        if not self._updating:
            self._commit()

    def _on_hex(self):
        text = self._hex.text().strip().lstrip('#')
        if len(text) == 6:
            c = QtGui.QColor(f"#{text}")
            if c.isValid():
                c.setAlpha(self._color.alpha())
                self._color = c
                self._load_color(c)
        elif len(text) == 8:
            try:
                r, g, b, a = (int(text[i:i + 2], 16) for i in range(0, 8, 2))
                self._color = QtGui.QColor(r, g, b, a)
                self._load_color(self._color)
            except ValueError:
                pass

    def _on_rgba(self):
        if self._updating:
            return
        r = self._ch_spins["R"].value()
        g = self._ch_spins["G"].value()
        b = self._ch_spins["B"].value()
        a = self._ch_spins["A"].value()
        c = QtGui.QColor(r, g, b, a)
        self._color = c
        self._updating = True
        h = c.hsvHue() if c.hsvHue() >= 0 else self._hue._value
        self._sq.set_hue(h)
        self._sq.set_sv(c.hsvSaturation(), c.value())
        self._hue.set_value(h)
        self._alpha.set_color(QtGui.QColor(r, g, b))
        self._alpha.set_value(a)
        self._sw_new.set_color(c)
        self._hex.setText(f"#{r:02X}{g:02X}{b:02X}{a:02X}")
        self._updating = False

    # ── Перетаскивание окна ───────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == QtCore.Qt.LeftButton and self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)

    def selected_color(self) -> QtGui.QColor:
        return self._color


# ══════════════════════════════════════════════════════════════════════════════
#  ColorButton
# ══════════════════════════════════════════════════════════════════════════════

class ColorButton(QtWidgets.QPushButton):
    """Кнопка выбора цвета с превью-свотчем."""
    colorChanged = QtCore.pyqtSignal(QtGui.QColor)

    def __init__(self, text="", color=None, parent=None):
        super().__init__(text, parent)
        self._color = color or QtGui.QColor(255, 0, 0, 200)
        self._update_icon()
        self.clicked.connect(self._pick)

    def _pick(self):
        dlg = ColorPickerDialog(self._color, self)
        if dlg.exec_():
            self._color = dlg.selected_color()
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

        if self._color.alpha() < 240:
            painter.setClipPath(path)
            half = H // 2
            for dx in range(0, W, half * 2):
                painter.fillRect(dx,        0,    half, half, QtGui.QColor(190, 190, 190))
                painter.fillRect(dx + half, 0,    half, half, QtGui.QColor(130, 130, 130))
                painter.fillRect(dx,        half, half, half, QtGui.QColor(130, 130, 130))
                painter.fillRect(dx + half, half, half, half, QtGui.QColor(190, 190, 190))
            painter.setClipping(False)

        painter.fillPath(path, QtGui.QBrush(self._color))
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


# ══════════════════════════════════════════════════════════════════════════════
#  Title Bar
# ══════════════════════════════════════════════════════════════════════════════

class CustomTitleBar(QtWidgets.QWidget):
    def __init__(self, parent, title="App"):
        super().__init__(parent)
        self._parent = parent
        self.setFixedHeight(38)
        self.setAutoFillBackground(False)
        self.setAttribute(QtCore.Qt.WA_NoSystemBackground)
        self.setStyleSheet(f"background: transparent; border-bottom: 1px solid {BORDER};")

        lay = QtWidgets.QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 8, 0)

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


# ══════════════════════════════════════════════════════════════════════════════
#  Прочее
# ══════════════════════════════════════════════════════════════════════════════

class SpinboxFocusFilter(QtCore.QObject):
    """Снимает фокус с InstantSpinBox при клике на любой другой виджет."""

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            focused = QtWidgets.QApplication.focusWidget()
            if (isinstance(focused, InstantSpinBox)
                    and not isinstance(obj, InstantSpinBox)):
                focused.clearFocus()
        return False
