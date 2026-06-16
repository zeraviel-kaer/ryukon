from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

_WS_CHILD    = 0x40000000
_WS_VISIBLE  = 0x10000000
_BS_CHECKBOX = 0x00000002
_BS_AUTOCHECKBOX = 0x00000003
_BM_GETCHECK = 0x00F0
_BM_SETCHECK = 0x00F1
_BST_CHECKED = 0x0001

_widget_counter = 4000

def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


class Checkbox:
    """Чекбокс."""

    def __init__(
        self,
        window:   Window,
        *,
        label:    str  = "",
        checked:  bool = False,  # начальное состояние
        x:        int  = 0,
        y:        int  = 0,
        width:    int  = 150,
        height:   int  = 25,
        callback: Callable[..., Awaitable] | None = None,
    ) -> None:
        self._window   = window
        self._label    = label
        self._checked  = checked
        self._x        = x
        self._y        = y
        self._width    = width
        self._height   = height
        self._callback = callback
        self._id       = _next_id()
        self._hwnd:    wt.HWND | None = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        hinstance  = kernel32.GetModuleHandleW(None)
        self._hwnd = user32.CreateWindowExW(
            0, "BUTTON", self._label,
            _WS_CHILD | _WS_VISIBLE | _BS_AUTOCHECKBOX,
            self._x, self._y, self._width, self._height,
            parent_hwnd, self._id, hinstance, None,
        )
        if self._checked and self._hwnd:
            user32.SendMessageW(self._hwnd, _BM_SETCHECK, _BST_CHECKED, 0)

    def _on_command(self, wparam: int, lparam: int) -> None:
        if self._callback:
            asyncio.get_event_loop().create_task(
                self._callback(self._window, self.checked)
            )

    @property
    def checked(self) -> bool:
        if not self._hwnd:
            return self._checked
        return bool(user32.SendMessageW(self._hwnd, _BM_GETCHECK, 0, 0))