from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

_WS_CHILD   = 0x40000000
_WS_VISIBLE = 0x10000000
_SS_LEFT    = 0x00000000
_SS_CENTER  = 0x00000001
_SS_RIGHT   = 0x00000002

_widget_counter = 3000

def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


class Label:
    """Текстовая метка."""

    def __init__(
        self,
        window: Window,
        *,
        text:   str = "",
        x:      int = 0,
        y:      int = 0,
        width:  int = 200,
        height: int = 20,
        align:  str = "left",  # "left", "center", "right"
    ) -> None:
        self._window = window
        self._text   = text
        self._x      = x
        self._y      = y
        self._width  = width
        self._height = height
        self._align  = {"left": _SS_LEFT, "center": _SS_CENTER, "right": _SS_RIGHT}.get(align, _SS_LEFT)
        self._id     = _next_id()
        self._hwnd:  wt.HWND | None = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        hinstance = kernel32.GetModuleHandleW(None)
        self._hwnd = user32.CreateWindowExW(
            0, "STATIC", self._text,
            _WS_CHILD | _WS_VISIBLE | self._align,
            self._x, self._y, self._width, self._height,
            parent_hwnd, self._id, hinstance, None,
        )

    def _on_command(self, wparam: int, lparam: int) -> None:
        pass  # Label не генерирует события

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = value
        if self._hwnd:
            user32.SetWindowTextW(self._hwnd, value)