from PyQt5 import QtWidgets, QtCore, QtGui

from .constants import BG, BORDER
from .widgets import CustomTitleBar
from .settings_window import SettingsWindow


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

        central = QtWidgets.QWidget()
        central.setAutoFillBackground(False)
        central.setAttribute(QtCore.Qt.WA_NoSystemBackground)

        layout = QtWidgets.QVBoxLayout(central)
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
