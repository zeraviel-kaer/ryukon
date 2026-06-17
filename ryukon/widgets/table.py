from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable, TYPE_CHECKING

if TYPE_CHECKING:
    from ryukon.window import Window

user32   = ctypes.windll.user32   # type: ignore
kernel32 = ctypes.windll.kernel32 # type: ignore

_WS_CHILD          = 0x40000000
_WS_VISIBLE        = 0x10000000
_WS_BORDER         = 0x00800000
_WS_VSCROLL        = 0x00200000
_WS_HSCROLL        = 0x00100000
_LVS_REPORT        = 0x0001
_LVS_SHOWSELALWAYS = 0x0008
_LVS_FULLROWSELECT = 0x0020

_LVM_INSERTCOLUMN   = 0x101B
_LVM_INSERTITEM     = 0x104D
_LVM_SETITEM        = 0x104C
_LVM_DELETEALLITEMS = 0x1009

_LVN_ITEMCHANGED = -101
_WM_NOTIFY       = 0x004E

_LVIF_TEXT = 0x0001

_widget_counter = 9000


def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


class LVCOLUMN(ctypes.Structure):
    _fields_ = [
        ("mask", wt.UINT),
        ("fmt", ctypes.c_int),
        ("cx", ctypes.c_int),
        ("pszText", wt.LPWSTR),
        ("cchTextMax", ctypes.c_int),
        ("iSubItem", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("iOrder", ctypes.c_int),
        ("cxMin", ctypes.c_int),
        ("cxDefault", ctypes.c_int),
        ("cxIdeal", ctypes.c_int),
    ]


class LVITEM(ctypes.Structure):
    _fields_ = [
        ("mask", wt.UINT),
        ("iItem", ctypes.c_int),
        ("iSubItem", ctypes.c_int),
        ("state", wt.UINT),
        ("stateMask", wt.UINT),
        ("pszText", wt.LPWSTR),
        ("cchTextMax", ctypes.c_int),
        ("iImage", ctypes.c_int),
        ("lParam", wt.LPARAM),
        ("iIndent", ctypes.c_int),
        ("iGroupId", ctypes.c_int),
        ("cColumns", wt.UINT),
        ("puColumns", ctypes.c_void_p),
        ("piColFmt", ctypes.c_void_p),
        ("iGroup", ctypes.c_int),
    ]


class Table:
    """Таблица с данными (ListView)."""

    def __init__(
        self,
        window: Window,
        *,
        columns: list[str] = [],
        rows: list[list[str]] = [],
        x: int = 0,
        y: int = 0,
        width: int = 400,
        height: int = 200,
        callback: Callable[..., Awaitable] | None = None,
    ) -> None:
        self._window = window
        self._columns = columns
        self._rows = list(rows)
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._callback = callback
        self._id = _next_id()
        self._hwnd: wt.HWND | None = None

        # ВАЖНО: храним буферы строк
        self._buffers: list[ctypes.Array] = []

    def _create(self, parent_hwnd: wt.HWND) -> None:
        ctypes.windll.comctl32.InitCommonControls()

        hinstance = kernel32.GetModuleHandleW(None)

        self._hwnd = user32.CreateWindowExW(
            0,
            "SysListView32",
            "",
            _WS_CHILD
            | _WS_VISIBLE
            | _WS_BORDER
            | _WS_VSCROLL
            | _LVS_REPORT
            | _LVS_SHOWSELALWAYS,
            self._x,
            self._y,
            self._width,
            self._height,
            parent_hwnd,
            self._id,
            hinstance,
            None,
        )

        _LVM_SETEXTENDEDLISTVIEWSTYLE = 0x1036

        user32.SendMessageW(
            self._hwnd,
            _LVM_SETEXTENDEDLISTVIEWSTYLE,
            _LVS_FULLROWSELECT,
            _LVS_FULLROWSELECT,
        )

        col_width = self._width // max(len(self._columns), 1)

        for i, col in enumerate(self._columns):
            buf = ctypes.create_unicode_buffer(str(col), 256)
            self._buffers.append(buf)

            lvc = LVCOLUMN()
            lvc.mask = 0x0007
            lvc.cx = col_width
            lvc.pszText = ctypes.cast(buf, wt.LPWSTR)

            user32.SendMessageW(
                self._hwnd,
                _LVM_INSERTCOLUMN,
                i,
                ctypes.byref(lvc),
            )

        for row in self._rows:
            self._insert_row(row)

    def _insert_row(self, row: list[str]) -> None:
        if not row:
            return

        first_buf = ctypes.create_unicode_buffer(str(row[0]))
        self._buffers.append(first_buf)

        lvi = LVITEM()
        lvi.mask = _LVIF_TEXT
        lvi.iItem = 999999
        lvi.iSubItem = 0
        lvi.pszText = ctypes.cast(first_buf, wt.LPWSTR)

        idx = user32.SendMessageW(
            self._hwnd,
            _LVM_INSERTITEM,
            0,
            ctypes.byref(lvi),
        )

        for col, text in enumerate(row[1:], start=1):
            buf = ctypes.create_unicode_buffer(str(text))
            self._buffers.append(buf)

            lvi2 = LVITEM()
            lvi2.mask = _LVIF_TEXT
            lvi2.iItem = idx
            lvi2.iSubItem = col
            lvi2.pszText = ctypes.cast(buf, wt.LPWSTR)

            user32.SendMessageW(
                self._hwnd,
                _LVM_SETITEM,
                0,
                ctypes.byref(lvi2),
            )

    def add_row(self, row: list[str]) -> None:
        self._rows.append(row)

        if self._hwnd:
            self._insert_row(row)

    def clear(self) -> None:
        self._rows.clear()
        self._buffers.clear()

        if self._hwnd:
            user32.SendMessageW(
                self._hwnd,
                _LVM_DELETEALLITEMS,
                0,
                0,
            )

    def _on_command(self, wparam: int, lparam: int) -> None:
        pass