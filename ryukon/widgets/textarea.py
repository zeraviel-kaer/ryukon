from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32   # type: ignore
kernel32 = ctypes.windll.kernel32 # type: ignore
gdi32    = ctypes.windll.gdi32    # type: ignore

_WS_CHILD       = 0x40000000
_WS_VISIBLE     = 0x10000000
_WS_BORDER      = 0x00800000
_WS_VSCROLL     = 0x00200000
_ES_MULTILINE   = 0x0004
_ES_AUTOVSCROLL = 0x0040
_ES_WANTRETURN  = 0x1000
_ES_READONLY    = 0x0800
_WM_SETFOCUS    = 0x0007
_WM_KILLFOCUS   = 0x0008
_WM_SETFONT     = 0x0030
_COLOR_GRAYTEXT = 17

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM
)

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
        self._window        = window
        self._default       = default
        self._placeholder   = placeholder
        self._readonly      = readonly
        self._x             = x
        self._y             = y
        self._width         = width
        self._height        = height
        self._callback      = callback
        self._id            = _next_id()
        self._hwnd:         wt.HWND | None = None
        self._is_placeholder = False  # сейчас показывается плейсхолдер
        self._orig_proc     = None
        self._subclass_ref  = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        hinstance = kernel32.GetModuleHandleW(None)
        style     = _WS_CHILD | _WS_VISIBLE | _WS_BORDER | _WS_VSCROLL | _ES_MULTILINE | _ES_AUTOVSCROLL | _ES_WANTRETURN
        if self._readonly:
            style |= _ES_READONLY

        self._hwnd = user32.CreateWindowExW(
            0, "EDIT", "",
            style,
            self._x, self._y, self._width, self._height,
            parent_hwnd, self._id, hinstance, None,
        )

        # Показываем плейсхолдер если нет default
        if self._placeholder and not self._default:
            self._show_placeholder()
        elif self._default:
            user32.SetWindowTextW(self._hwnd, self._default)

        # Subclass чтобы перехватить WM_SETFOCUS / WM_KILLFOCUS
        if self._placeholder:
            self._subclass()

    def _show_placeholder(self) -> None:
        user32.SetWindowTextW(self._hwnd, self._placeholder)
        # Серый цвет через системный цвет текста
        gray = user32.GetSysColor(_COLOR_GRAYTEXT)
        # Просто ставим текст — цвет серый сделаем через subclass
        self._is_placeholder = True

    def _subclass(self) -> None:
        """Перехватываем WM_SETFOCUS и WM_KILLFOCUS через subclassing."""
        textarea = self

        def subclass_proc(hwnd, msg, wparam, lparam):
            if msg == _WM_SETFOCUS:
                # Получили фокус — убираем плейсхолдер
                if textarea._is_placeholder:
                    textarea._is_placeholder = False
                    user32.SetWindowTextW(hwnd, "")
            elif msg == _WM_KILLFOCUS:
                # Потеряли фокус — показываем плейсхолдер если поле пустое
                length = user32.GetWindowTextLengthW(hwnd)
                if length == 0 and textarea._placeholder:
                    textarea._show_placeholder()
            # Передаём остальное оригинальному обработчику
            return ctypes.windll.comctl32.DefSubclassProc(hwnd, msg, ctypes.c_longlong(wparam), ctypes.c_longlong(lparam))  # type: ignore

        self._subclass_ref = WNDPROC(subclass_proc)
        # SetWindowSubclass для безопасного subclassing
        ctypes.windll.comctl32.SetWindowSubclass(  # type: ignore
            self._hwnd, self._subclass_ref, self._id, 0
        )

    @property
    def value(self) -> str:
        if not self._hwnd or self._is_placeholder:
            return ""
        length = user32.GetWindowTextLengthW(self._hwnd)
        buf    = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(self._hwnd, buf, length + 1)
        return buf.value

    @value.setter
    def value(self, text: str) -> None:
        if self._hwnd:
            self._is_placeholder = False
            user32.SetWindowTextW(self._hwnd, text)

    def _on_command(self, wparam: int, lparam: int) -> None:
        notif     = (wparam >> 16) & 0xFFFF
        EN_CHANGE = 0x0300
        if notif == EN_CHANGE and self._callback and not self._is_placeholder:
            asyncio.get_event_loop().create_task(
                self._callback(self._window, self.value)
            )