from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

user32   = ctypes.windll.user32    # type: ignore
gdi32    = ctypes.windll.gdi32     # type: ignore
kernel32 = ctypes.windll.kernel32  # type: ignore

DEFAULT_CHARSET  = 1
OUT_DEFAULT_PREC = 0
CLIP_DEFAULT_PREC = 0
ANTIALIASED_QUALITY = 4
FF_DONTCARE = 0
FW_NORMAL   = 400
FW_BOLD     = 700


class Font:
    """Шрифт для виджетов.

    font = ryukon.Font(family="Segoe UI", size=12, bold=False)
    """

    def __init__(
        self,
        *,
        family: str  = "Segoe UI",
        size:   int  = 10,
        bold:   bool = False,
        italic: bool = False,
    ) -> None:
        self.family = family
        self.size   = size
        self.bold   = bold
        self.italic = italic
        self._hfont = None

    def _build(self):
        if self._hfont:
            return self._hfont
        # Конвертируем pt → логические единицы
        hdc        = user32.GetDC(None)
        dpi        = gdi32.GetDeviceCaps(hdc, 90)  # LOGPIXELSY
        user32.ReleaseDC(None, hdc)
        height     = -(self.size * dpi // 72)
        self._hfont = gdi32.CreateFontW(
            height, 0, 0, 0,
            FW_BOLD if self.bold else FW_NORMAL,
            int(self.italic), 0, 0,
            DEFAULT_CHARSET, OUT_DEFAULT_PREC, CLIP_DEFAULT_PREC,
            ANTIALIASED_QUALITY, FF_DONTCARE,
            self.family,
        )
        return self._hfont

    def apply(self, hwnd) -> None:
        """Применяет шрифт к виджету."""
        hfont = self._build()
        if hfont and hwnd:
            user32.SendMessageW(hwnd, 0x0030, hfont, 1)  # WM_SETFONT


class Color:
    """Цвет в формате RGB.

    Color(255, 0, 0)      # красный
    Color.from_hex("#ff0000")
    """

    def __init__(self, r: int, g: int, b: int) -> None:
        self.r = r
        self.g = g
        self.b = b

    @classmethod
    def from_hex(cls, hex_str: str) -> Color:
        hex_str = hex_str.lstrip("#")
        return cls(
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16),
        )

    @property
    def colorref(self) -> int:
        """COLORREF для WinAPI — BGR порядок."""
        return self.r | (self.g << 8) | (self.b << 16)


class Style:
    """Стиль для окна или виджета.

    style = ryukon.Style(
        font=ryukon.Font(family="Segoe UI", size=11),
        bg=ryukon.Color.from_hex("#ffffff"),
        fg=ryukon.Color.from_hex("#000000"),
    )
    """

    def __init__(
        self,
        *,
        font: Font  | None = None,
        bg:   Color | None = None,  # цвет фона
        fg:   Color | None = None,  # цвет текста
    ) -> None:
        self.font = font
        self.bg   = bg
        self.fg   = fg

    def apply_to_widget(self, hwnd) -> None:
        if self.font and hwnd:
            self.font.apply(hwnd)