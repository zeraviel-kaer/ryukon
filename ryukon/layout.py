from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

_UNSET = object()  # sentinel — отличаем "не задано" от 0


class Layout:
    """Базовый класс layout."""

    def apply(self, widgets: list, window_width: int, window_height: int) -> None:
        raise NotImplementedError


class VLayout(Layout):
    """Вертикальный layout — виджеты друг под другом.

    layout = ryukon.VLayout(padding=10, gap=8)
    """

    def __init__(
        self,
        *,
        padding: int = 10,  # отступ от краёв окна
        gap:     int = 8,   # расстояние между виджетами
        width:   int | None = None,  # ширина виджетов, None = растянуть по окну
    ) -> None:
        self.padding = padding
        self.gap     = gap
        self.width   = width

    def apply(self, widgets: list, window_width: int, window_height: int) -> None:
        y = self.padding
        for widget in widgets:
            # Пропускаем виджеты с явно заданными координатами
            if not getattr(widget, "_auto_layout", True):
                continue
            w = self.width if self.width is not None else (window_width - self.padding * 2)
            widget._x = self.padding
            widget._y = y
            widget._width = w
            y += widget._height + self.gap


class HLayout(Layout):
    """Горизонтальный layout — виджеты в ряд.

    layout = ryukon.HLayout(padding=10, gap=8)
    """

    def __init__(
        self,
        *,
        padding: int = 10,
        gap:     int = 8,
        height:  int | None = None,  # высота виджетов, None = не менять
    ) -> None:
        self.padding = padding
        self.gap     = gap
        self.height  = height

    def apply(self, widgets: list, window_width: int, window_height: int) -> None:
        x = self.padding
        for widget in widgets:
            if not getattr(widget, "_auto_layout", True):
                continue
            if self.height is not None:
                widget._height = self.height
            widget._x = x
            widget._y = self.padding
            x += widget._width + self.gap


class GridLayout(Layout):
    """Сеточный layout — виджеты по колонкам.

    layout = ryukon.GridLayout(columns=2, padding=10, gap=8)
    """

    def __init__(
        self,
        *,
        columns: int = 2,
        padding: int = 10,
        gap:     int = 8,
    ) -> None:
        self.columns = columns
        self.padding = padding
        self.gap     = gap

    def apply(self, widgets: list, window_width: int, window_height: int) -> None:
        auto = [w for w in widgets if getattr(w, "_auto_layout", True)]
        col_width = (window_width - self.padding * 2 - self.gap * (self.columns - 1)) // self.columns

        col = 0
        row = 0
        row_heights: dict[int, int] = {}  # максимальная высота в каждой строке

        for widget in auto:
            widget._x     = self.padding + col * (col_width + self.gap)
            widget._y     = self.padding + sum(
                row_heights.get(r, 0) + self.gap for r in range(row)
            )
            widget._width = col_width
            row_heights[row] = max(row_heights.get(row, 0), widget._height)
            col += 1
            if col >= self.columns:
                col  = 0
                row += 1