from PyQt5 import QtWidgets, QtCore, QtGui

from .constants import (
    ACCENT, ACCL, TEXT, SUB, BORDER, BORDER2, RED, GREEN, BG, CARD, CARD2,
)


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
    def lineEdit(self):             return self

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
            pass
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


class SpinboxFocusFilter(QtCore.QObject):
    """Снимает фокус с InstantSpinBox при клике на любой другой виджет."""

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            focused = QtWidgets.QApplication.focusWidget()
            if (isinstance(focused, InstantSpinBox)
                    and not isinstance(obj, InstantSpinBox)):
                focused.clearFocus()
        return False
