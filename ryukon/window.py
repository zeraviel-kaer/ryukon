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
WM_CTLCOLORSTATIC    = 0x0138
WM_CTLCOLOREDIT      = 0x0133
WM_CTLCOLORBTN       = 0x0135
WM_CTLCOLORLISTBOX   = 0x0134
COLOR_WINDOW         = 5
IMAGE_ICON           = 1
LR_LOADFROMFILE      = 0x0010
LR_DEFAULTSIZE       = 0x0040
ICON_SMALL           = 0
ICON_BIG             = 1
WM_RBUTTONUP         = 0x0205

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM
)

user32   = ctypes.windll.user32   # type: ignore
kernel32 = ctypes.windll.kernel32 # type: ignore
gdi32    = ctypes.windll.gdi32    # type: ignore


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
    """Базовое окно Ryukon."""

    _title:      str        = "Ryukon Window"
    _width:      int        = 800
    _height:     int        = 600
    _icon:       str | None = None
    _resizable:  bool       = True
    _min_width:  int | None = None
    _min_height: int | None = None
    _max_width:  int | None = None
    _max_height: int | None = None
    _center:     bool       = False
    _is_main:    bool       = True   # False для дочерних окон
    _modal:      bool       = False  # блокирует родителя пока открыто

    def __init__(self, app: App) -> None:
        self._app         = app
        self._hwnd:       wt.HWND | None = None
        self._widgets:    list            = []
        self._scrollers:  list            = []
        self._wndproc_ref                 = None
        self._bg_brush                    = None  # кисть для фона окна
        self._parent:     object | None   = None   # родительское окно
        self._menu        = None  # строка меню
        self._context_menu = None  # контекстное меню

    def _create(self) -> None:
        hinstance  = kernel32.GetModuleHandleW(None)
        class_name = f"Ryukon_{id(self)}"

        def wnd_proc(hwnd, msg, wparam, lparam):
            return self._dispatch(hwnd, msg, wparam, lparam)

        self._wndproc_ref = WNDPROC(wnd_proc)

        # Стиль окна
        style_obj = getattr(self.__class__, "style", None)
        if style_obj and style_obj.bg:
            bg_brush = gdi32.CreateSolidBrush(style_obj.bg.colorref)
        else:
            bg_brush = ctypes.cast(ctypes.c_void_p(COLOR_WINDOW + 1), wt.HBRUSH)
        self._bg_brush = bg_brush

        wc = WNDCLASSEX()
        wc.cbSize        = ctypes.sizeof(WNDCLASSEX)
        wc.style         = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc   = self._wndproc_ref
        wc.hInstance     = hinstance
        wc.hbrBackground = bg_brush
        wc.lpszClassName = class_name
        wc.hCursor       = user32.LoadCursorW(None, ctypes.c_wchar_p(32512))

        if not user32.RegisterClassExW(ctypes.byref(wc)):
            raise RuntimeError(f"RegisterClassEx failed: {kernel32.GetLastError()}")

        if self._resizable:
            style = WS_OVERLAPPEDWINDOW | WS_VISIBLE
        else:
            style = WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX | WS_VISIBLE

        x = CW_USEDEFAULT
        y = CW_USEDEFAULT
        if self._center:
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            x  = (sw - self._width)  // 2
            y  = (sh - self._height) // 2

        self._hwnd = user32.CreateWindowExW(
            0, class_name, self._title,
            style, x, y, self._width, self._height,
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

        # Строим меню если задано
        if self._menu:
            self._menu._build(self._hwnd)

        for widget in self._widgets:
            widget._create(self._hwnd)
            # Применяем стиль виджета если есть
            w_style = getattr(widget, "style", None) or style_obj
            if w_style:
                w_style.apply_to_widget(widget._hwnd)

    def _dispatch(self, hwnd, msg, wparam, lparam) -> int:
        # Цвет фона и текста для дочерних виджетов
        if msg in (WM_CTLCOLORSTATIC, WM_CTLCOLOREDIT, WM_CTLCOLORBTN, WM_CTLCOLORLISTBOX):
            style_obj = getattr(self.__class__, "style", None)
            if style_obj:
                hdc = ctypes.cast(wparam, wt.HDC)
                if style_obj.fg:
                    gdi32.SetTextColor(hdc, style_obj.fg.colorref)
                if style_obj.bg:
                    gdi32.SetBkColor(hdc, style_obj.bg.colorref)
                    return ctypes.cast(self._bg_brush, ctypes.c_void_p).value or 0
            return user32.DefWindowProcW(hwnd, msg, ctypes.c_longlong(wparam), ctypes.c_longlong(lparam))

        if msg == WM_DESTROY:
            # PostQuitMessage только для главного окна
            if self._is_main:
                user32.PostQuitMessage(0)
            return 0

        if msg == WM_CLOSE:
            loop = asyncio.get_event_loop()
            async def _do_close():
                # Проверяем on_close если переопределён в подклассе
                if 'on_close' in type(self).__dict__:
                    result = await self.on_close()
                    if result is False:
                        return
                # Разблокируем родителя если модалка
                if self._modal and self._parent and self._parent._hwnd:
                    user32.EnableWindow(self._parent._hwnd, 1)
                    user32.SetForegroundWindow(self._parent._hwnd)
                # Останавливаем таймеры окна
                for attr in vars(self).values():
                    from ryukon.timer import Timer
                    if isinstance(attr, Timer):
                        attr.stop()
                # Убираем из активных окон
                if self in self._app._active_windows:
                    self._app._active_windows.remove(self)
                user32.DestroyWindow(hwnd)
                # Останавливаем приложение только если главное окно
                if self._is_main:
                    self._app._stop()
            loop.create_task(_do_close())
            return 0

        if msg == WM_RBUTTONUP:
            if self._context_menu:
                self._context_menu.show(hwnd)
            return 0

        if msg == WM_COMMAND:
            ctrl_id = wparam & 0xFFFF
            # Пункты меню имеют HIWORD(wparam) == 0
            if (wparam >> 16) == 0 and self._menu:
                self._menu._on_command(ctrl_id)
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

        if msg == WM_SIZE:
            w = lparam & 0xFFFF
            h = (lparam >> 16) & 0xFFFF
            if w > 0 and h > 0:
                layout = getattr(self.__class__, "layout", None)
                if layout is not None and getattr(layout, "auto_resize", False):
                    layout.apply(self._widgets, w, h)
                if hasattr(self, 'on_resize'):
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

    def load_style(self, css: str) -> None:
        """Применяет стили из CSS строки."""
        """
        self.load_style(
            Window { background: #1e1e1e; color: #ffffff; font-size: 11; }
            Button { background: #0078d4; color: #ffffff; }
        )
        """
        from ryukon import css as css_module
        self._apply_styles(css_module.parse(css))

    def load_style_file(self, path: str) -> None:
        """Применяет стили из .rcss файла.

        self.load_style_file("styles/dark.rcss")
        """
        from ryukon import css as css_module
        self._apply_styles(css_module.load(path))

    def _apply_styles(self, styles: dict) -> None:
        from ryukon.widgets.button      import Button
        from ryukon.widgets.input       import Input
        from ryukon.widgets.label       import Label
        from ryukon.widgets.checkbox    import Checkbox
        from ryukon.widgets.dropdown    import Dropdown
        from ryukon.widgets.slider      import Slider
        from ryukon.widgets.textarea    import TextArea
        from ryukon.widgets.progressbar import ProgressBar
        from ryukon.widgets.table       import Table

        _widget_map = {
            "button":      Button,
            "input":       Input,
            "label":       Label,
            "checkbox":    Checkbox,
            "dropdown":    Dropdown,
            "slider":      Slider,
            "textarea":    TextArea,
            "progressbar": ProgressBar,
            "table":       Table,
        }

        # Стиль окна
        win_style = styles.get("window")
        if win_style:
            self.__class__.style = win_style
            if self._hwnd and win_style.bg:
                brush = gdi32.CreateSolidBrush(win_style.bg.colorref)
                self._bg_brush = brush
                user32.InvalidateRect(self._hwnd, None, 1)

        # Стили виджетов
        for selector, cls in _widget_map.items():
            widget_style = styles.get(selector)
            if not widget_style:
                continue
            for widget in self._widgets:
                if isinstance(widget, cls):
                    widget.style = widget_style
                    if widget._hwnd:
                        widget_style.apply_to_widget(widget._hwnd)

    def set_menu(self, menu) -> None:
        """Устанавливает строку меню окна."""
        self._menu = menu
        if self._hwnd:
            menu._build(self._hwnd)

    def set_context_menu(self, ctx) -> None:
        """Устанавливает контекстное меню (правая кнопка на окне)."""
        self._context_menu = ctx

    def open_window(self, window_cls, *, modal: bool = False) -> None:
        """Открывает дочернее окно.

        self.open_window(SettingsWindow)
        self.open_window(SettingsWindow, modal=True)  # блокирует текущее окно
        """
        win             = window_cls(self._app)
        win._is_main    = False
        win._parent     = self
        win._modal      = modal
        win._create()
        self._app._active_windows.append(win)
        # Блокируем родителя если модалка
        if modal and self._hwnd:
            user32.EnableWindow(self._hwnd, 0)
        asyncio.get_event_loop().create_task(win.on_ready())