from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable

user32 = ctypes.windll.user32  # type: ignore

WM_HOTKEY   = 0x0312
MOD_ALT     = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT   = 0x0004
MOD_WIN     = 0x0008

VK = {
    "F1": 0x70,  "F2": 0x71,  "F3": 0x72,  "F4": 0x73,
    "F5": 0x74,  "F6": 0x75,  "F7": 0x76,  "F8": 0x77,
    "F9": 0x78,  "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "ENTER": 0x0D, "ESC": 0x1B, "SPACE": 0x20,
    "TAB": 0x09, "BACKSPACE": 0x08, "DELETE": 0x2E,
    "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
    "HOME": 0x24, "END": 0x23, "PGUP": 0x21, "PGDN": 0x22,
}


class HotkeyManager:
    """Менеджер глобальных горячих клавиш.

    hotkeys = ryukon.HotkeyManager()
    hotkeys.register("CTRL+SHIFT+O", callback=open_window)
    app.set_hotkeys(hotkeys)
    """

    def __init__(self) -> None:
        self._hotkeys:    dict[int, Callable] = {}
        self._pending:    dict[int, tuple]    = {}  # до создания окна
        self._next_id     = 1
        self._hwnd:       wt.HWND | None = None
        self._wndproc_ref = None

    def _create(self) -> None:
        from ryukon.window import WNDPROC, WNDCLASSEX, CS_HREDRAW, CS_VREDRAW, COLOR_WINDOW

        hinstance  = ctypes.windll.kernel32.GetModuleHandleW(None)  # type: ignore
        class_name = f"RyukonHotkey_{id(self)}"

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == WM_HOTKEY and wparam in self._hotkeys:
                cb = self._hotkeys[wparam]
                result = cb()
                if asyncio.iscoroutine(result):
                    asyncio.get_event_loop().create_task(result)
            return user32.DefWindowProcW(hwnd, msg, ctypes.c_longlong(wparam), ctypes.c_longlong(lparam))

        self._wndproc_ref = WNDPROC(wnd_proc)

        wc = WNDCLASSEX()
        wc.cbSize        = ctypes.sizeof(WNDCLASSEX)
        wc.style         = CS_HREDRAW | CS_VREDRAW
        wc.lpfnWndProc   = self._wndproc_ref
        wc.hInstance     = hinstance
        wc.hbrBackground = ctypes.cast(ctypes.c_void_p(COLOR_WINDOW + 1), wt.HBRUSH)
        wc.lpszClassName = class_name
        user32.RegisterClassExW(ctypes.byref(wc))

        self._hwnd = user32.CreateWindowExW(
            0, class_name, "", 0,
            0, 0, 0, 0,
            None, None, hinstance, None,
        )

    def register(self, hotkey: str, *, callback: Callable[..., Awaitable]) -> int:
        """Регистрирует горячую клавишу.

        hotkeys.register("CTRL+SHIFT+O", callback=my_func)
        """
        mods, vk = self._parse(hotkey)
        hid      = self._next_id
        self._next_id += 1
        if self._hwnd:
            user32.RegisterHotKey(self._hwnd, hid, mods, vk)
            self._hotkeys[hid] = callback
        else:
            self._pending[hid] = (mods, vk, callback)
        return hid

    def unregister(self, hotkey_id: int) -> None:
        """Отменяет регистрацию горячей клавиши."""
        if self._hwnd:
            user32.UnregisterHotKey(self._hwnd, hotkey_id)
        self._hotkeys.pop(hotkey_id, None)
        self._pending.pop(hotkey_id, None)

    def _parse(self, hotkey: str) -> tuple[int, int]:
        parts = [p.strip().upper() for p in hotkey.split("+")]
        mods  = 0
        vk    = 0
        for part in parts:
            if   part == "CTRL":  mods |= MOD_CONTROL
            elif part == "ALT":   mods |= MOD_ALT
            elif part == "SHIFT": mods |= MOD_SHIFT
            elif part == "WIN":   mods |= MOD_WIN
            elif part in VK:      vk = VK[part]
            elif len(part) == 1:  vk = ord(part)
        return mods, vk