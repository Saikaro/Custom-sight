from PyQt5 import QtWidgets, QtCore, QtGui

from .system import get_monitor_size, make_window_clickthrough
from .config import default_config


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
