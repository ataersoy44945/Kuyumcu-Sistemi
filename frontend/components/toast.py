"""
Toast — pencerenin altında kısa süreli bildirim.
Kullanım:
    Toast.show_success(parent_window, "Ürün sepete eklendi")
    Toast.show_info(parent_window, "…")
    Toast.show_error(parent_window, "…")
"""

from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor

from frontend.styles.app_theme import Colors, Radius


class Toast(QWidget):
    """Ekranın alt-merkezinde belirip birkaç saniye sonra kaybolan bildirim."""

    _DURATION_MS = 2400   # görünür kalma süresi

    _VARIANTS = {
        "success": {"icon": "✓", "color": Colors.GREEN},
        "info":    {"icon": "●", "color": Colors.GOLD},
        "error":   {"icon": "✕", "color": Colors.RED},
    }

    def __init__(self, parent: QWidget, message: str, variant: str = "success"):
        super().__init__(parent)
        cfg = self._VARIANTS.get(variant, self._VARIANTS["info"])

        # Çerçevesiz, tıklama-geçirgen bir katman
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setStyleSheet(f"""
            QWidget#toastBody {{
                background: {Colors.BG_ELEVATED};
                border: 1px solid {cfg['color']}88;
                border-left: 3px solid {cfg['color']};
                border-radius: {Radius.MD};
            }}
            QLabel {{ background: transparent; border: none; }}
        """)

        body = QWidget(self)
        body.setObjectName("toastBody")
        lay = QHBoxLayout(body)
        lay.setContentsMargins(18, 12, 22, 12)
        lay.setSpacing(12)

        ico = QLabel(cfg["icon"])
        ico.setStyleSheet(
            f"color: {cfg['color']}; font-size: 16px; font-weight: 800;"
        )

        txt = QLabel(message)
        txt.setStyleSheet(
            f"color: {Colors.TEXT_H1}; font-size: 13px; font-weight: 600;"
        )

        lay.addWidget(ico)
        lay.addWidget(txt)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(body)

        # Yumuşak gölge
        shadow = QGraphicsDropShadowEffect(body)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        body.setGraphicsEffect(shadow)

        self.adjustSize()
        self._reposition(parent)

    # ── Konumlandırma & yaşam döngüsü ─────────────────────────

    def _reposition(self, parent: QWidget) -> None:
        # Parent penceresinin ekrandaki mutlak konumuna göre alt-merkeze yerleş
        try:
            g = parent.geometry()
            top_left = parent.mapToGlobal(parent.rect().topLeft())
            x = top_left.x() + (g.width() - self.width()) // 2
            y = top_left.y() + g.height() - self.height() - 48
            self.move(x, y)
        except Exception:
            pass

    def _start_fade(self) -> None:
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(350)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.finished.connect(self.close)
        self._anim.start()

    # ── Public API ────────────────────────────────────────────

    @classmethod
    def show_success(cls, parent: QWidget, message: str) -> "Toast":
        return cls._spawn(parent, message, "success")

    @classmethod
    def show_info(cls, parent: QWidget, message: str) -> "Toast":
        return cls._spawn(parent, message, "info")

    @classmethod
    def show_error(cls, parent: QWidget, message: str) -> "Toast":
        return cls._spawn(parent, message, "error")

    @classmethod
    def _spawn(cls, parent: QWidget, message: str, variant: str) -> "Toast":
        # Üst-düzey pencereyi bul (QDialog veya QMainWindow)
        top = parent.window() if parent else parent
        toast = cls(top, message, variant)
        toast.setWindowOpacity(0.0)
        toast.show()
        # Yumuşak giriş
        anim_in = QPropertyAnimation(toast, b"windowOpacity")
        anim_in.setDuration(180)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.start()
        toast._anim_in = anim_in  # referans tut
        # Süre dolunca fade out
        QTimer.singleShot(cls._DURATION_MS, toast._start_fade)
        return toast
