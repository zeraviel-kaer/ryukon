from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

_WS_CHILD       = 0x40000000
_WS_VISIBLE     = 0x10000000
_WS_BORDER      = 0x00800000
_ES_AUTOHSCROLL = 0x0080
_EM_SETCUEBANNER = 0x1501  # фантомный текст

_widget_counter = 2000


def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


class Input:
    """Текстовый инпут WinAPI."""

    def __init__(
        self,
        window:      Window,
        *,
        placeholder: str | None = None,  # фантомный текст, исчезает при вводе
        default:     str | None = None,  # реальный текст по умолчанию
        x:           int = 0,
        y:           int = 0,
        width:       int = 200,
        height:      int = 25,
        callback:    Callable[..., Awaitable] | None = None,
    ) -> None:
        self._window      = window
        self._placeholder = placeholder
        self._default     = default
        self._x           = x
        self._y           = y
        self._width       = width
        self._height      = height
        self._callback    = callback
        self._id          = _next_id()
        self._hwnd:       wt.HWND | None = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        hinstance = kernel32.GetModuleHandleW(None)
        self._hwnd = user32.CreateWindowExW(
            0, "EDIT", self._default or "",
            _WS_CHILD | _WS_VISIBLE | _WS_BORDER | _ES_AUTOHSCROLL,
            self._x, self._y, self._width, self._height,
            parent_hwnd, self._id, hinstance, None,
        )

        # Устанавливаем фантомный текст если передан
        if self._placeholder and self._hwnd:
            user32.SendMessageW(
                self._hwnd, _EM_SETCUEBANNER,
                1,  # 1 = показывать даже когда инпут в фокусе
                self._placeholder,
            )

    @property
    def value(self) -> str:
        if not self._hwnd:
            return ""
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(self._hwnd, buf, 256)
        return buf.value

    @value.setter
    def value(self, text: str) -> None:
        if self._hwnd:
            user32.SetWindowTextW(self._hwnd, text)

    def _on_command(self, wparam: int, lparam: int) -> None:
        notif    = (wparam >> 16) & 0xFFFF
        EN_CHANGE = 0x0300
        if notif == EN_CHANGE and self._callback:
            asyncio.get_event_loop().create_task(
                self._callback(self._window, self.value)
            )