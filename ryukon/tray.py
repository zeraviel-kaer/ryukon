from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable

user32   = ctypes.windll.user32   # type: ignore
shell32  = ctypes.windll.shell32  # type: ignore
kernel32 = ctypes.windll.kernel32 # type: ignore

WM_APP          = 0x8000
WM_TRAY         = WM_APP + 1
NIM_ADD         = 0x00
NIM_DELETE      = 0x02
NIM_MODIFY      = 0x01
NIF_ICON        = 0x00000002
NIF_MESSAGE     = 0x00000001
NIF_TIP         = 0x00000004
NIF_INFO        = 0x00000010
WM_RBUTTONUP    = 0x0205
WM_LBUTTONUP    = 0x0202
IMAGE_ICON      = 1
LR_LOADFROMFILE = 0x0010
LR_DEFAULTSIZE  = 0x0040
NIIF_INFO       = 0x00000001
NIIF_WARNING    = 0x00000002
NIIF_ERROR      = 0x00000003

MF_STRING   = 0x00000000
MF_SEPARATOR = 0x00000800
TPM_RETURNCMD = 0x0100
TPM_NONOTIFY  = 0x0080


class NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize",            wt.DWORD),
        ("hWnd",              wt.HWND),
        ("uID",               wt.UINT),
        ("uFlags",            wt.UINT),
        ("uCallbackMessage",  wt.UINT),
        ("hIcon",             wt.HICON),
        ("szTip",             ctypes.c_wchar * 128),
        ("dwState",           wt.DWORD),
        ("dwStateMask",       wt.DWORD),
        ("szInfo",            ctypes.c_wchar * 256),
        ("uTimeout",          wt.UINT),
        ("szInfoTitle",       ctypes.c_wchar * 64),
        ("dwInfoFlags",       wt.DWORD),
    ]


class TrayMenuItem:
    def __init__(self, label: str, callback: Callable | None = None, separator: bool = False):
        self.label     = label
        self.callback  = callback
        self.separator = separator


class Tray:
    """Иконка в системном трее.

    tray = ryukon.Tray(
        icon="icon.ico",
        tooltip="Моё приложение",
        on_click=lambda: print("клик"),
    )
    tray.add_item("Открыть", callback=open_window)
    tray.add_separator()
    tray.add_item("Выход", callback=app.quit)
    """

    def __init__(
        self,
        *,
        icon:     str | None = None,
        tooltip:  str        = "",
        on_click: Callable[..., Awaitable] | None = None,
    ) -> None:
        self._icon     = icon
        self._tooltip  = tooltip
        self._on_click = on_click
        self._items:   list[TrayMenuItem] = []
        self._hwnd:    wt.HWND | None = None
        self._hicon                   = None
        self._nid:     NOTIFYICONDATA | None = None
        self._wndproc_ref             = None
        self._id       = 1

    def add_item(self, label: str, *, callback: Callable | None = None) -> None:
        self._items.append(TrayMenuItem(label, callback))

    def add_separator(self) -> None:
        self._items.append(TrayMenuItem("", separator=True))

    def _create(self) -> None:
        from ryukon.window import WNDPROC, WNDCLASSEX, CS_HREDRAW, CS_VREDRAW, COLOR_WINDOW

        hinstance  = kernel32.GetModuleHandleW(None)
        class_name = f"RyukonTray_{id(self)}"

        def wnd_proc(hwnd, msg, wparam, lparam):
            return self._dispatch(hwnd, msg, wparam, lparam)

        self._wndproc_ref = WNDPROC(wnd_proc)

        wc = WNDCLASSEX()
        wc.cbSize        = ctypes.sizeof(WNDCLASSEX)
        wc.style         = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc   = self._wndproc_ref
        wc.hInstance     = hinstance
        wc.hbrBackground = ctypes.cast(ctypes.c_void_p(COLOR_WINDOW + 1), wt.HBRUSH)
        wc.lpszClassName = class_name
        user32.RegisterClassExW(ctypes.byref(wc))

        # Невидимое окно для приёма сообщений трея
        self._hwnd = user32.CreateWindowExW(
            0, class_name, "", 0,
            0, 0, 0, 0,
            None, None, hinstance, None,
        )

        if self._icon:
            self._hicon = user32.LoadImageW(
                None, self._icon, IMAGE_ICON,
                0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE,
            )
        if not self._hicon:
            self._hicon = user32.LoadIconW(None, ctypes.c_wchar_p(32512))  # стандартная иконка

        nid = NOTIFYICONDATA()
        nid.cbSize           = ctypes.sizeof(NOTIFYICONDATA)
        nid.hWnd             = self._hwnd
        nid.uID              = self._id
        nid.uFlags           = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon            = self._hicon
        nid.szTip            = self._tooltip[:127]
        self._nid = nid
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

    def _dispatch(self, hwnd, msg, wparam, lparam) -> int:
        if msg == WM_TRAY:
            event = lparam & 0xFFFF
            if event == WM_LBUTTONUP and self._on_click:
                asyncio.get_event_loop().create_task(self._on_click())
            if event == WM_RBUTTONUP and self._items:
                self._show_menu()
        return user32.DefWindowProcW(hwnd, msg, ctypes.c_longlong(wparam), ctypes.c_longlong(lparam))

    def _show_menu(self) -> None:
        hmenu = user32.CreatePopupMenu()
        for i, item in enumerate(self._items):
            if item.separator:
                user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
            else:
                user32.AppendMenuW(hmenu, MF_STRING, i + 1, item.label)

        pt = wt.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        user32.SetForegroundWindow(self._hwnd)
        cmd = user32.TrackPopupMenu(
            hmenu, TPM_RETURNCMD | TPM_NONOTIFY,
            pt.x, pt.y, 0, self._hwnd, None,
        )
        user32.DestroyMenu(hmenu)

        if cmd and 1 <= cmd <= len(self._items):
            item = self._items[cmd - 1]
            if item.callback:
                result = item.callback()
                if asyncio.iscoroutine(result):
                    asyncio.get_event_loop().create_task(result)

    def remove(self) -> None:
        """Убирает иконку из трея."""
        if self._nid and self._hwnd:
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))

    def update_tooltip(self, tooltip: str) -> None:
        """Обновляет подсказку иконки."""
        if self._nid:
            self._nid.szTip = tooltip[:127]
            shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid))