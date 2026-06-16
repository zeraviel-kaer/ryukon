from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.app import App

# ── WinAPI константы ────────────────────────────────────────
WS_OVERLAPPEDWINDOW  = 0x00CF0000
WS_CAPTION           = 0x00C00000
WS_SYSMENU           = 0x00080000
WS_MINIMIZEBOX       = 0x00020000
WS_VISIBLE           = 0x10000000
CS_HREDRAW           = 0x0002
CS_VREDRAW           = 0x0001
CW_USEDEFAULT        = 0x80000000
SW_SHOW              = 5
WM_DESTROY           = 0x0002
WM_CLOSE             = 0x0010
WM_COMMAND           = 0x0111
WM_HSCROLL           = 0x0114
WM_VSCROLL           = 0x0115
WM_SIZE              = 0x0005
WM_GETMINMAXINFO     = 0x0024
WM_SETICON           = 0x0080
COLOR_WINDOW         = 5
IMAGE_ICON           = 1
LR_LOADFROMFILE      = 0x0010
LR_DEFAULTSIZE       = 0x0040
ICON_SMALL           = 0
ICON_BIG             = 1

# ── WinAPI типы ─────────────────────────────────────────────
WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM
)

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class WNDCLASSEX(ctypes.Structure):
    _fields_ = [
        ("cbSize",        wt.UINT),
        ("style",         wt.UINT),
        ("lpfnWndProc",   WNDPROC),
        ("cbClsExtra",    ctypes.c_int),
        ("cbWndExtra",    ctypes.c_int),
        ("hInstance",     wt.HINSTANCE),
        ("hIcon",         wt.HICON),
        ("hCursor",       wt.HANDLE),
        ("hbrBackground", wt.HBRUSH),
        ("lpszMenuName",  wt.LPCWSTR),
        ("lpszClassName", wt.LPCWSTR),
        ("hIconSm",       wt.HICON),
    ]


class MINMAXINFO(ctypes.Structure):
    _fields_ = [
        ("ptReserved",     wt.POINT),
        ("ptMaxSize",      wt.POINT),
        ("ptMaxPosition",  wt.POINT),
        ("ptMinTrackSize", wt.POINT),
        ("ptMaxTrackSize", wt.POINT),
    ]


class Window:
    """Базовое окно Ryukon. Наследуйся и вешай декораторы виджетов."""

    _title:      str        = "Ryukon Window"
    _width:      int        = 800
    _height:     int        = 600
    _icon:       str | None = None
    _resizable:  bool       = True
    _min_width:  int | None = None
    _min_height: int | None = None
    _max_width:  int | None = None
    _max_height: int | None = None
    _center:     bool       = False  # центрировать на экране при запуске

    def __init__(self, app: App) -> None:
        self._app          = app
        self._hwnd:        wt.HWND | None = None
        self._widgets:     list            = []
        self._scrollers:   list            = []  # виджеты с scroll событиями (Slider)
        self._wndproc_ref                  = None

    # --- Внутреннее создание окна ---

    def _create(self) -> None:
        hinstance  = kernel32.GetModuleHandleW(None)
        class_name = f"Ryukon_{id(self)}"

        def wnd_proc(hwnd, msg, wparam, lparam):
            return self._dispatch(hwnd, msg, wparam, lparam)

        self._wndproc_ref = WNDPROC(wnd_proc)

        wc = WNDCLASSEX()
        wc.cbSize        = ctypes.sizeof(WNDCLASSEX)
        wc.style         = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc   = self._wndproc_ref
        wc.hInstance     = hinstance
        wc.hbrBackground = ctypes.cast(
            ctypes.c_void_p(COLOR_WINDOW + 1), wt.HBRUSH
        )
        wc.lpszClassName = class_name
        wc.hCursor       = user32.LoadCursorW(None, ctypes.c_wchar_p(32512))

        if not user32.RegisterClassExW(ctypes.byref(wc)):
            raise RuntimeError(f"RegisterClassEx failed: {kernel32.GetLastError()}")

        if self._resizable:
            style = WS_OVERLAPPEDWINDOW | WS_VISIBLE
        else:
            style = WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX | WS_VISIBLE

        # Вычисляем позицию для центрирования
        x = CW_USEDEFAULT
        y = CW_USEDEFAULT
        if self._center:
            sw = user32.GetSystemMetrics(0)  # ширина экрана
            sh = user32.GetSystemMetrics(1)  # высота экрана
            x  = (sw - self._width)  // 2
            y  = (sh - self._height) // 2

        self._hwnd = user32.CreateWindowExW(
            0, class_name, self._title,
            style, x, y,
            self._width, self._height,
            None, None, hinstance, None,
        )

        if not self._hwnd:
            raise RuntimeError(f"CreateWindowEx failed: {kernel32.GetLastError()}")

        if self._icon:
            hicon = user32.LoadImageW(
                None, self._icon, IMAGE_ICON,
                0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE,
            )
            if hicon:
                user32.SendMessageW(self._hwnd, WM_SETICON, ICON_BIG,   hicon)
                user32.SendMessageW(self._hwnd, WM_SETICON, ICON_SMALL, hicon)

        user32.ShowWindow(self._hwnd, SW_SHOW)
        user32.UpdateWindow(self._hwnd)

        for widget in self._widgets:
            widget._create(self._hwnd)

    def _dispatch(self, hwnd, msg, wparam, lparam) -> int:
        """Диспетчер WinAPI сообщений."""
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0

        if msg == WM_CLOSE:
            loop = asyncio.get_event_loop()
            if hasattr(self, 'on_close'):
                async def _try_close():
                    if await self.on_close() is not False:
                        self._app._stop()
                        user32.DestroyWindow(hwnd)
                loop.create_task(_try_close())
            else:
                loop.call_soon_threadsafe(self._app._stop)
                user32.DestroyWindow(hwnd)
            return 0

        if msg == WM_COMMAND:
            ctrl_id = wparam & 0xFFFF
            for widget in self._widgets:
                if getattr(widget, "_id", None) == ctrl_id:
                    widget._on_command(wparam, lparam)
                    break

        if msg in (WM_HSCROLL, WM_VSCROLL):
            hwnd_ctrl = ctypes.cast(lparam, wt.HWND)
            for scroller in self._scrollers:
                if scroller._hwnd == hwnd_ctrl:
                    scroller._on_scroll()
                    break

        if msg == WM_SIZE and hasattr(self, 'on_resize'):
            w = lparam & 0xFFFF
            h = (lparam >> 16) & 0xFFFF
            asyncio.get_event_loop().create_task(self.on_resize(w, h))

        if msg == WM_GETMINMAXINFO:
            if any(v is not None for v in (self._min_width, self._min_height, self._max_width, self._max_height)):
                info = ctypes.cast(lparam, ctypes.POINTER(MINMAXINFO)).contents
                if self._min_width  is not None: info.ptMinTrackSize.x = self._min_width
                if self._min_height is not None: info.ptMinTrackSize.y = self._min_height
                if self._max_width  is not None: info.ptMaxTrackSize.x = self._max_width
                if self._max_height is not None: info.ptMaxTrackSize.y = self._max_height
            return 0

        return user32.DefWindowProcW(
            hwnd, msg,
            ctypes.c_longlong(wparam),
            ctypes.c_longlong(lparam),
        )

    def _register_widget(self, widget) -> None:
        self._widgets.append(widget)

    def _register_scroll(self, widget) -> None:
        self._scrollers.append(widget)

    # --- Публичное API ---

    @property
    def hwnd(self) -> wt.HWND | None:
        return self._hwnd

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        if self._hwnd:
            user32.SetWindowTextW(self._hwnd, value)

    def get(self, name: str):
        """Возвращает виджет по имени метода."""
        for widget in self._widgets:
            if getattr(widget, "_name", None) == name:
                return widget
        return None

    async def on_ready(self) -> None:
        """Вызывается когда окно создано."""

    # on_resize(w, h) и on_close() — переопределяются в подклассе при необходимости