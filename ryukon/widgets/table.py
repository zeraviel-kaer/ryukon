from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import struct
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
_LVS_REPORT        = 0x0001
_LVS_SHOWSELALWAYS = 0x0008
_LVS_FULLROWSELECT = 0x0020
_LVM_INSERTCOLUMNW = 0x1061
_LVM_INSERTITEMW   = 0x104D
_LVM_SETITEMW      = 0x104C
_LVM_DELETEALLITEMS = 0x1009
_LVM_SETEXTENDEDLISTVIEWSTYLE = 0x1036
_LVIF_TEXT         = 0x0001
_LVCF_FMT          = 0x0001
_LVCF_WIDTH        = 0x0002
_LVCF_TEXT         = 0x0004

_widget_counter = 9000

def _next_id() -> int:
    global _widget_counter
    _widget_counter += 1
    return _widget_counter


def _insert_column(hwnd, index: int, text: str, width: int) -> None:
    """Вставляет колонку через выделенную память процесса."""
    # Кодируем текст как UTF-16LE
    text_bytes = (text + "\0").encode("utf-16-le")
    text_len   = len(text_bytes)

    # LVCOLUMNW на 64-bit: mask(4) + fmt(4) + cx(4) + pad(4) + pszText(8) + cchTextMax(4) + iSubItem(4)
    # Выделяем буфер для текста + структуры
    buf_size = 256 * 2 + 64  # текст + структура
    buf      = (ctypes.c_byte * buf_size)()
    buf_addr = ctypes.addressof(buf)

    # Текст кладём в начало буфера
    ctypes.memmove(buf_addr, text_bytes, text_len)
    text_ptr = buf_addr

    # LVCOLUMNW структура идёт после текста (выровнена по 8)
    struct_offset = (text_len + 7) & ~7
    struct_addr   = buf_addr + struct_offset

    # Пакуем LVCOLUMNW вручную (64-bit layout)
    mask     = _LVCF_FMT | _LVCF_WIDTH | _LVCF_TEXT
    fmt      = 0
    cx       = width
    pszText  = text_ptr
    cchTextMax = len(text) + 1

    packed = struct.pack("IIiPiI",
        mask,        # UINT  mask
        fmt,         # int   fmt
        cx,          # int   cx  (но нужен pad перед pointer)
        pszText,     # void* pszText
        cchTextMax,  # int   cchTextMax
        0,           # int   iSubItem
    )
    ctypes.memmove(struct_addr, packed, len(packed))
    user32.SendMessageW(hwnd, _LVM_INSERTCOLUMNW, index, ctypes.c_void_p(struct_addr))


def _insert_item(hwnd, item_index: int, sub_index: int, text: str) -> int:
    """Вставляет строку или устанавливает текст ячейки."""
    text_bytes = (text + "\0").encode("utf-16-le")
    text_len   = len(text_bytes)

    buf_size = 256 * 2 + 128
    buf      = (ctypes.c_byte * buf_size)()
    buf_addr = ctypes.addressof(buf)
    ctypes.memmove(buf_addr, text_bytes, text_len)

    struct_offset = (text_len + 7) & ~7
    struct_addr   = buf_addr + struct_offset

    # LVITEMW 64-bit layout
    packed = struct.pack("IiiIIPiii",
        _LVIF_TEXT,   # mask   (UINT)
        item_index,   # iItem  (int)
        sub_index,    # iSubItem (int)
        0,            # state  (UINT)
        0,            # stateMask (UINT)
        buf_addr,     # pszText (pointer)
        len(text)+1,  # cchTextMax (int)
        -1,           # iImage (int)
        0,            # iIndent (int)
    )
    ctypes.memmove(struct_addr, packed, len(packed))

    if sub_index == 0:
        return user32.SendMessageW(hwnd, _LVM_INSERTITEMW, 0, ctypes.c_void_p(struct_addr))
    else:
        user32.SendMessageW(hwnd, _LVM_SETITEMW, 0, ctypes.c_void_p(struct_addr))
        return item_index


class Table:
    """Таблица с данными (ListView)."""

    def __init__(
        self,
        window:   Window,
        *,
        columns:  list[str]       = [],
        rows:     list[list[str]] = [],
        x:        int             = 0,
        y:        int             = 0,
        width:    int             = 400,
        height:   int             = 200,
        callback: Callable[..., Awaitable] | None = None,
    ) -> None:
        self._window   = window
        self._columns  = columns
        self._rows     = list(rows)
        self._x        = x
        self._y        = y
        self._width    = width
        self._height   = height
        self._callback = callback
        self._id       = _next_id()
        self._hwnd:    wt.HWND | None = None

    def _create(self, parent_hwnd: wt.HWND) -> None:
        ctypes.windll.comctl32.InitCommonControls()  # type: ignore
        hinstance = kernel32.GetModuleHandleW(None)
        self._hwnd = user32.CreateWindowExW(
            0, "SysListView32", "",
            _WS_CHILD | _WS_VISIBLE | _WS_BORDER | _WS_VSCROLL | _LVS_REPORT | _LVS_SHOWSELALWAYS,
            self._x, self._y, self._width, self._height,
            parent_hwnd, self._id, hinstance, None,
        )
        user32.SendMessageW(self._hwnd, _LVM_SETEXTENDEDLISTVIEWSTYLE, _LVS_FULLROWSELECT, _LVS_FULLROWSELECT)

        col_width = self._width // max(len(self._columns), 1)
        for i, col in enumerate(self._columns):
            _insert_column(self._hwnd, i, col, col_width)

        for row in self._rows:
            self._insert_row(row)

    def _insert_row(self, row: list[str]) -> None:
        if not row or not self._hwnd:
            return
        idx = _insert_item(self._hwnd, 999999, 0, str(row[0]))
        for col, text in enumerate(row[1:], start=1):
            _insert_item(self._hwnd, idx, col, str(text))

    def add_row(self, row: list[str]) -> None:
        """Добавляет строку в таблицу."""
        self._rows.append(row)
        if self._hwnd:
            self._insert_row(row)

    def clear(self) -> None:
        """Очищает все строки."""
        self._rows.clear()
        if self._hwnd:
            user32.SendMessageW(self._hwnd, _LVM_DELETEALLITEMS, 0, 0)

    def _on_command(self, wparam: int, lparam: int) -> None:
        pass