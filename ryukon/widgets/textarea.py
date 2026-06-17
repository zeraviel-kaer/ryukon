from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32   # type: ignore
kernel32 = ctypes.windll.kernel32 # type: ignore

_WS_CHILD       = 0x40000000
_WS_VISIBLE     = 0x10000000
_WS_BORDER      = 0x00800000
_WS_VSCROLL     = 0x00200000
_ES_MULTILINE   = 0x0004
_ES_AUTOVSCROLL = 0x0040
_ES_WANTRETURN  = 0x1000

_widget_counter = 7000

def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


class TextArea:
    """Многострочное текстовое поле."""

    def __init__(
        self,
        window:      Window,
        *,
        default:     str | None = None,
        placeholder: str | None = None,
        readonly:    bool       = False,
        x:           int        = 0,
        y:           int        = 0,
        width:       int        = 200,
        height:      int        = 100,
        callback:    Callable[..., Awaitable] | None = None,
    ) -> None:
        self._window      = window
        self._default     = default
        self._placeholder = placeholder
        self._readonly    = readonly
        self._x           = x
        self._y           = y
        self._width       = width
        self._height      = height
        self._callback    = callback
        self._id          = _next_id()
        self._hwnd:       wt.HWND | None = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        hinstance  = kernel32.GetModuleHandleW(None)
        style      = _WS_CHILD | _WS_VISIBLE | _WS_BORDER | _WS_VSCROLL | _ES_MULTILINE | _ES_AUTOVSCROLL | _ES_WANTRETURN
        if self._readonly:
            style |= 0x0800  # ES_READONLY
        self._hwnd = user32.CreateWindowExW(
            0, "EDIT", self._default or "",
            style,
            self._x, self._y, self._width, self._height,
            parent_hwnd, self._id, hinstance, None,
        )
        if self._placeholder and self._hwnd:
            user32.SendMessageW(self._hwnd, 0x1501, 1, self._placeholder)

    @property
    def value(self) -> str:
        if not self._hwnd:
            return ""
        length = user32.GetWindowTextLengthW(self._hwnd)
        buf    = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(self._hwnd, buf, length + 1)
        return buf.value

    @value.setter
    def value(self, text: str) -> None:
        if self._hwnd:
            user32.SetWindowTextW(self._hwnd, text)

    def _on_command(self, wparam: int, lparam: int) -> None:
        notif     = (wparam >> 16) & 0xFFFF
        EN_CHANGE = 0x0300
        if notif == EN_CHANGE and self._callback:
            asyncio.get_event_loop().create_task(
                self._callback(self._window, self.value)
            )