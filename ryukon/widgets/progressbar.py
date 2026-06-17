from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32   # type: ignore
kernel32 = ctypes.windll.kernel32 # type: ignore

_WS_CHILD       = 0x40000000
_WS_VISIBLE     = 0x10000000
_PBS_SMOOTH     = 0x01   # плавное заполнение
_PBS_VERTICAL   = 0x04   # вертикальный
_PBM_SETRANGE   = 0x0401
_PBM_SETPOS     = 0x0402
_PBM_GETPOS     = 0x0408
_PBM_SETBARCOLOR = 0x0409
_PBM_SETBKCOLOR  = 0x2001

_widget_counter = 8000

def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


class ProgressBar:
    """Прогресс бар."""

    def __init__(
        self,
        window:   Window,
        *,
        min:      int  = 0,
        max:      int  = 100,
        value:    int  = 0,
        vertical: bool = False,
        x:        int  = 0,
        y:        int  = 0,
        width:    int  = 200,
        height:   int  = 20,
    ) -> None:
        self._window   = window
        self._min      = min
        self._max      = max
        self._value    = value
        self._vertical = vertical
        self._x        = x
        self._y        = y
        self._width    = width
        self._height   = height
        self._id       = _next_id()
        self._hwnd:    wt.HWND | None = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        ctypes.windll.comctl32.InitCommonControls()  # type: ignore
        hinstance = kernel32.GetModuleHandleW(None)
        style     = _WS_CHILD | _WS_VISIBLE | _PBS_SMOOTH
        if self._vertical:
            style |= _PBS_VERTICAL
        self._hwnd = user32.CreateWindowExW(
            0, "msctls_progress32", "",
            style,
            self._x, self._y, self._width, self._height,
            parent_hwnd, self._id, hinstance, None,
        )
        user32.SendMessageW(self._hwnd, _PBM_SETRANGE, 0, (self._max << 16) | self._min)
        user32.SendMessageW(self._hwnd, _PBM_SETPOS, self._value, 0)

    def _on_command(self, wparam: int, lparam: int) -> None:
        pass  # ProgressBar не генерирует события

    @property
    def value(self) -> int:
        if not self._hwnd:
            return self._value
        return user32.SendMessageW(self._hwnd, _PBM_GETPOS, 0, 0)

    @value.setter
    def value(self, val: int) -> None:
        self._value = val
        if self._hwnd:
            user32.SendMessageW(self._hwnd, _PBM_SETPOS, val, 0)