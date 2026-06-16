from __future__ import annotations

import ctypes.wintypes as wt


class Event:
    """Базовый класс события."""
    pass


class ClickEvent(Event):
    """Событие нажатия кнопки."""

    def __init__(self, widget_id: int) -> None:
        self.widget_id = widget_id


class ChangeEvent(Event):
    """Событие изменения значения виджета."""

    def __init__(self, widget_id: int, value: str) -> None:
        self.widget_id = widget_id
        self.value     = value