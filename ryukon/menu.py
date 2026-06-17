from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable, Awaitable

user32 = ctypes.windll.user32  # type: ignore

MF_STRING    = 0x00000000
MF_SEPARATOR = 0x00000800
MF_POPUP     = 0x00000010
MF_GRAYED    = 0x00000001
MF_CHECKED   = 0x00000008
WM_COMMAND   = 0x0111
TPM_RETURNCMD = 0x0100
TPM_NONOTIFY  = 0x0080
TPM_RIGHTBUTTON = 0x0002

_id_counter = 10000

def _next_id() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter


class MenuItem:
    """Пункт меню."""

    def __init__(
        self,
        label:    str,
        *,
        callback: Callable[..., Awaitable] | None = None,
        shortcut: str | None = None,   # отображаемый shortcut "Ctrl+O"
        checked:  bool       = False,
        disabled: bool       = False,
        separator: bool      = False,
    ) -> None:
        self.label     = label
        self.callback  = callback
        self.shortcut  = shortcut
        self.checked   = checked
        self.disabled  = disabled
        self.separator = separator
        self.children: list[MenuItem] = []
        self._id       = _next_id()

    def add(self, item: MenuItem) -> MenuItem:
        """Добавляет дочерний пункт (создаёт подменю)."""
        self.children.append(item)
        return self


class Menu:
    """Строка меню окна.

    menu = ryukon.Menu()
    file = menu.add("Файл")
    file.add(ryukon.MenuItem("Открыть", callback=on_open, shortcut="Ctrl+O"))
    file.add(ryukon.MenuItem(separator=True))
    file.add(ryukon.MenuItem("Выход", callback=app.quit))
    window.set_menu(menu)
    """

    def __init__(self) -> None:
        self._items:   list[MenuItem] = []
        self._id_map:  dict[int, Callable] = {}
        self._hmenu:   wt.HMENU | None = None

    def add(self, label: str, *, callback: Callable | None = None) -> MenuItem:
        """Добавляет пункт верхнего уровня. Возвращает MenuItem для добавления дочерних."""
        item = MenuItem(label, callback=callback)
        self._items.append(item)
        return item

    def _build(self, hwnd: wt.HWND) -> None:
        """Создаёт меню и прикрепляет к окну."""
        self._hmenu = user32.CreateMenu()
        self._id_map.clear()

        for item in self._items:
            if item.children:
                submenu = self._build_submenu(item.children)
                user32.AppendMenuW(self._hmenu, MF_POPUP, submenu, item.label)
            else:
                self._append_item(self._hmenu, item)

        user32.SetMenu(hwnd, self._hmenu)
        user32.DrawMenuBar(hwnd)

    def _build_submenu(self, items: list[MenuItem]) -> wt.HMENU:
        hmenu = user32.CreatePopupMenu()
        for item in items:
            if item.children:
                submenu = self._build_submenu(item.children)
                user32.AppendMenuW(hmenu, MF_POPUP, submenu, item.label)
            else:
                self._append_item(hmenu, item)
        return hmenu

    def _append_item(self, hmenu: wt.HMENU, item: MenuItem) -> None:
        if item.separator:
            user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
            return

        flags = MF_STRING
        if item.disabled: flags |= MF_GRAYED
        if item.checked:  flags |= MF_CHECKED

        label = item.label
        if item.shortcut:
            label = f"{label}\t{item.shortcut}"

        user32.AppendMenuW(hmenu, flags, item._id, label)
        if item.callback:
            self._id_map[item._id] = item.callback

    def _on_command(self, item_id: int) -> None:
        cb = self._id_map.get(item_id)
        if cb:
            result = cb()
            if asyncio.iscoroutine(result):
                asyncio.get_event_loop().create_task(result)


class ContextMenu:
    """Контекстное меню (правая кнопка мыши).

    ctx = ryukon.ContextMenu()
    ctx.add(ryukon.MenuItem("Копировать", callback=on_copy))
    ctx.add(ryukon.MenuItem("Вставить",   callback=on_paste))
    window.set_context_menu(ctx)   # на всё окно
    # или на конкретный виджет — пока через window
    """

    def __init__(self) -> None:
        self._items:  list[MenuItem] = []
        self._id_map: dict[int, Callable] = {}

    def add(self, item: MenuItem) -> ContextMenu:
        self._items.append(item)
        return self

    def show(self, hwnd: wt.HWND) -> None:
        """Показывает меню в позиции курсора."""
        hmenu = user32.CreatePopupMenu()
        self._id_map.clear()

        for item in self._items:
            if item.separator:
                user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
                continue
            flags = MF_STRING
            if item.disabled: flags |= MF_GRAYED
            if item.checked:  flags |= MF_CHECKED
            user32.AppendMenuW(hmenu, flags, item._id, item.label)
            if item.callback:
                self._id_map[item._id] = item.callback

        pt = wt.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        user32.SetForegroundWindow(hwnd)
        cmd = user32.TrackPopupMenu(
            hmenu, TPM_RETURNCMD | TPM_NONOTIFY | TPM_RIGHTBUTTON,
            pt.x, pt.y, 0, hwnd, None,
        )
        user32.DestroyMenu(hmenu)

        if cmd:
            cb = self._id_map.get(cmd)
            if cb:
                result = cb()
                if asyncio.iscoroutine(result):
                    asyncio.get_event_loop().create_task(result)