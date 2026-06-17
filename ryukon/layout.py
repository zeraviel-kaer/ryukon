from __future__ import annotations

import ctypes

user32: ctypes.WinDLL = ctypes.windll.user32  # type: ignore


class Layout:
    """Базовый класс layout."""

    auto_resize: bool = False

    def apply(self, widgets: list, window_width: int, window_height: int) -> None:
        raise NotImplementedError

    def _move(self, widget, x: int, y: int, width: int, height: int) -> None:
        """Перемещает и изменяет размер виджета — работает и до и после создания окна."""
        widget._x      = x
        widget._y      = y
        widget._width  = width
        widget._height = height
        if widget._hwnd:
            user32.MoveWindow(widget._hwnd, x, y, width, height, 1)


class VLayout(Layout):
    """Вертикальный layout — виджеты друг под другом.

    layout = ryukon.VLayout(padding=10, gap=8, auto_resize=True)
    """

    def __init__(
        self,
        *,
        padding:     int      = 10,
        gap:         int      = 8,
        width:       int | None = None,  # None = растянуть по ширине окна
        auto_resize: bool     = False,
    ) -> None:
        self.padding     = padding
        self.gap         = gap
        self.width       = width
        self.auto_resize = auto_resize

    def apply(self, widgets: list, window_width: int, window_height: int) -> None:
        y = self.padding
        for widget in widgets:
            if not getattr(widget, "_auto_layout", True):
                continue
            w = self.width if self.width is not None else (window_width - self.padding * 2)
            self._move(widget, self.padding, y, w, widget._height)
            y += widget._height + self.gap


class HLayout(Layout):
    """Горизонтальный layout — виджеты в ряд.

    layout = ryukon.HLayout(padding=10, gap=8, auto_resize=True)
    """

    def __init__(
        self,
        *,
        padding:     int      = 10,
        gap:         int      = 8,
        height:      int | None = None,  # None = не менять высоту
        auto_resize: bool     = False,
    ) -> None:
        self.padding     = padding
        self.gap         = gap
        self.height      = height
        self.auto_resize = auto_resize

    def apply(self, widgets: list, window_width: int, window_height: int) -> None:
        x = self.padding
        for widget in widgets:
            if not getattr(widget, "_auto_layout", True):
                continue
            h = self.height if self.height is not None else widget._height
            self._move(widget, x, self.padding, widget._width, h)
            x += widget._width + self.gap


class GridLayout(Layout):
    """Сеточный layout — виджеты по колонкам.

    layout = ryukon.GridLayout(columns=2, padding=10, gap=8, auto_resize=True)
    """

    def __init__(
        self,
        *,
        columns:     int  = 2,
        padding:     int  = 10,
        gap:         int  = 8,
        auto_resize: bool = False,
    ) -> None:
        self.columns     = columns
        self.padding     = padding
        self.gap         = gap
        self.auto_resize = auto_resize

    def apply(self, widgets: list, window_width: int, window_height: int) -> None:
        auto      = [w for w in widgets if getattr(w, "_auto_layout", True)]
        col_width = (window_width - self.padding * 2 - self.gap * (self.columns - 1)) // self.columns

        col = 0
        row = 0
        row_heights: dict[int, int] = {}

        for widget in auto:
            x = self.padding + col * (col_width + self.gap)
            y = self.padding + sum(
                row_heights.get(r, 0) + self.gap for r in range(row)
            )
            self._move(widget, x, y, col_width, widget._height)
            row_heights[row] = max(row_heights.get(row, 0), widget._height)
            col += 1
            if col >= self.columns:
                col  = 0
                row += 1