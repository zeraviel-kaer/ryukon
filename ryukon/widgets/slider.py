from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

_WS_CHILD        = 0x40000000
_WS_VISIBLE      = 0x10000000
_TBS_HORZ        = 0x0000  # горизонтальный
_TBS_VERT        = 0x0002  # вертикальный
_TBS_AUTOTICKS   = 0x0001  # деления
_TBM_SETRANGE    = 0x0406
_TBM_SETPOS      = 0x0405
_TBM_GETPOS      = 0x0400
_WM_HSCROLL      = 0x0114
_WM_VSCROLL      = 0x0115

_widget_counter = 6000

def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


class Slider:
    """Ползунок (trackbar)."""

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
        height:   int  = 30,
        callback: Callable[..., Awaitable] | None = None,
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
        self._callback = callback
        self._id       = _next_id()
        self._hwnd:    wt.HWND | None = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        # Trackbar требует загрузки commctrl
        ctypes.windll.comctl32.InitCommonControls()
        hinstance  = kernel32.GetModuleHandleW(None)
        orient     = _TBS_VERT if self._vertical else _TBS_HORZ
        self._hwnd = user32.CreateWindowExW(
            0, "msctls_trackbar32", "",
            _WS_CHILD | _WS_VISIBLE | _TBS_AUTOTICKS | orient,
            self._x, self._y, self._width, self._height,
            parent_hwnd, self._id, hinstance, None,
        )
        user32.SendMessageW(self._hwnd, _TBM_SETRANGE, 1, (self._max << 16) | self._min)
        user32.SendMessageW(self._hwnd, _TBM_SETPOS,   1, self._value)

        # Регистрируем окно для перехвата WM_HSCROLL/WM_VSCROLL
        self._window._register_scroll(self)

    def _on_scroll(self) -> None:
        if self._callback:
            asyncio.get_event_loop().create_task(
                self._callback(self._window, self.value)
            )

    def _on_command(self, wparam: int, lparam: int) -> None:
        pass  # Slider использует scroll события, не command

    @property
    def value(self) -> int:
        if not self._hwnd:
            return self._value
        return user32.SendMessageW(self._hwnd, _TBM_GETPOS, 0, 0)