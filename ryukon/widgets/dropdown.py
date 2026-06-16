from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

_WS_CHILD      = 0x40000000
_WS_VISIBLE    = 0x10000000
_CBS_DROPDOWNLIST = 0x0003  # только выбор, без ввода
_WS_VSCROLL    = 0x00200000
_CB_ADDSTRING  = 0x0143
_CB_SETCURSEL  = 0x014E
_CB_GETCURSEL  = 0x0147
_CB_GETLBTEXT  = 0x0148
_CB_GETLBTEXTLEN = 0x0149
_CBN_SELCHANGE = 0x0001

_widget_counter = 5000

def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


class Dropdown:
    """Выпадающий список."""

    def __init__(
        self,
        window:   Window,
        *,
        options:  list[str] = [],
        default:  int       = 0,   # индекс выбранного по умолчанию
        x:        int       = 0,
        y:        int       = 0,
        width:    int       = 200,
        height:   int       = 25,
        callback: Callable[..., Awaitable] | None = None,
    ) -> None:
        self._window   = window
        self._options  = options
        self._default  = default
        self._x        = x
        self._y        = y
        self._width    = width
        self._height   = height
        self._callback = callback
        self._id       = _next_id()
        self._hwnd:    wt.HWND | None = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        hinstance  = kernel32.GetModuleHandleW(None)
        # height передаём большим — WinAPI использует его как высоту развёрнутого списка
        self._hwnd = user32.CreateWindowExW(
            0, "COMBOBOX", "",
            _WS_CHILD | _WS_VISIBLE | _CBS_DROPDOWNLIST | _WS_VSCROLL,
            self._x, self._y, self._width, self._height * (len(self._options) + 1),
            parent_hwnd, self._id, hinstance, None,
        )
        for option in self._options:
            user32.SendMessageW(self._hwnd, _CB_ADDSTRING, 0, option)
        if self._options:
            user32.SendMessageW(self._hwnd, _CB_SETCURSEL, self._default, 0)

    def _on_command(self, wparam: int, lparam: int) -> None:
        notif = (wparam >> 16) & 0xFFFF
        if notif == _CBN_SELCHANGE and self._callback:
            asyncio.get_event_loop().create_task(
                self._callback(self._window, self.value, self.index)
            )

    @property
    def index(self) -> int:
        if not self._hwnd:
            return -1
        return user32.SendMessageW(self._hwnd, _CB_GETCURSEL, 0, 0)

    @property
    def value(self) -> str | None:
        idx = self.index
        if idx < 0 or not self._hwnd:
            return None
        length = user32.SendMessageW(self._hwnd, _CB_GETLBTEXTLEN, idx, 0)
        buf    = ctypes.create_unicode_buffer(length + 1)
        user32.SendMessageW(self._hwnd, _CB_GETLBTEXT, idx, buf)
        return buf.value