from __future__ import annotations

import time
from dataclasses import replace

from ryukon.render.color import RColor
from ryukon.render.cssx import BoxStyle
from ryukon.render.gdiplus import Graphics, argb


def _lerp_color(a: RColor | None, b: RColor | None, t: float) -> RColor | None:
    if a is None and b is None:
        return None
    a = a or RColor(0, 0, 0, 0)
    b = b or RColor(0, 0, 0, 0)
    return RColor(
        int(a.r + (b.r - a.r) * t),
        int(a.g + (b.g - a.g) * t),
        int(a.b + (b.b - a.b) * t),
        int(a.a + (b.a - a.a) * t),
    )


def draw_box(g: Graphics, rect: tuple, style: BoxStyle, *, focused: bool = False) -> None:
    """Рисует фон/рамку/тень прямоугольника узла — общая часть для всех виджетов."""
    x, y, w, h = rect
    if w <= 0 or h <= 0 or style.opacity <= 0:
        return

    if style.shadow:
        dx, dy, blur, color = style.shadow
        steps = max(1, blur // 4)
        for i in range(steps, 0, -1):
            alpha = int(color.a * (i / steps) * 0.30)
            expand = i * 2
            g.fill_round_rect(
                x + dx - expand / 2, y + dy - expand / 2,
                w + expand, h + expand,
                style.radius + expand / 2,
                argb(color.r, color.g, color.b, alpha),
            )

    if style.background:
        g.fill_round_rect(x, y, w, h, style.radius, style.background.argb)

    if style.border_width and style.border_color:
        g.stroke_round_rect(x, y, w, h, style.radius, style.border_color.argb, style.border_width)

    if focused:
        ring = (style.accent or RColor(91, 140, 255)).argb
        g.stroke_round_rect(x - 2, y - 2, w + 4, h + 4, style.radius + 2, ring, 2)


class RenderNode:
    """Базовый узел дерева рендера."""

    tag = "Node"

    def __init__(self, *, id: str | None = None, classes: list[str] | None = None) -> None:
        self.id       = id
        self.classes  = set(classes or [])
        self.parent: RenderNode | None = None
        self.children: list[RenderNode] = []
        self.resolved = BoxStyle()
        self.rect     = (0, 0, 0, 0)  # x, y, w, h — заполняется при layout()
        self.state: set[str] = set()  # "hover", "pressed", "checked", "focused"
        self._anim_from:  BoxStyle | None = None
        self._anim_start: float | None    = None

    def add(self, *children: "RenderNode") -> "RenderNode":
        for child in children:
            child.parent = self
            self.children.append(child)
        return self

    def content_rect(self) -> tuple[float, float, float, float]:
        x, y, w, h = self.rect
        t, r, b, l = self.resolved.padding
        return (x + l, y + t, max(0.0, w - l - r), max(0.0, h - t - b))

    def preferred_height(self, available_width: float) -> float:
        return self.resolved.height or 24

    def preferred_width(self) -> float:
        return self.resolved.width or 120

    def layout(self, x: float, y: float, w: float, h: float) -> None:
        self.rect = (x, y, w, h)

    def apply_style(self, new_style: BoxStyle) -> bool:
        """Применяет посчитанный CSS-стиль; если задан transition — запускает
        плавный переход цветов. Возвращает True, если переход активен (нужно
        продолжать цикл анимации и перерисовывать кадры)."""
        if new_style.transition > 0:
            self._anim_from  = self.display_style()
            self._anim_start = time.monotonic()
        else:
            self._anim_start = None
        self.resolved = new_style
        return self._anim_start is not None

    def display_style(self) -> BoxStyle:
        """Стиль для текущего кадра — с учётом анимации перехода, если она идёт."""
        if self._anim_start is None or self.resolved.transition <= 0 or self._anim_from is None:
            return self.resolved
        t = (time.monotonic() - self._anim_start) / self.resolved.transition
        if t >= 1.0:
            self._anim_start = None
            return self.resolved
        style = replace(self.resolved)
        style.background   = _lerp_color(self._anim_from.background, self.resolved.background, t)
        style.border_color = _lerp_color(self._anim_from.border_color, self.resolved.border_color, t)
        style.color         = _lerp_color(self._anim_from.color, self.resolved.color, t)
        style.accent         = _lerp_color(self._anim_from.accent, self.resolved.accent, t)
        return style

    def is_animating(self) -> bool:
        return self._anim_start is not None

    def paint(self, g: Graphics) -> None:
        draw_box(g, self.rect, self.display_style(), focused="focused" in self.state)

    def hit_test(self, px: float, py: float) -> bool:
        x, y, w, h = self.rect
        return x <= px < x + w and y <= py < y + h

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


def _main_size(child: RenderNode, main_is_x: bool, cross_avail: float) -> float:
    if main_is_x:
        return child.resolved.width or child.preferred_width()
    return child.resolved.height or child.preferred_height(cross_avail)


def _cross_offset(container_cross: float, item_cross: float, align: str) -> float:
    extra = container_cross - item_cross
    if align == "center":
        return max(0.0, extra / 2)
    if align == "end":
        return max(0.0, extra)
    return 0.0


def _layout_axis(children: list[RenderNode], cx: float, cy: float, cw: float, ch: float,
                  gap: float, main_is_x: bool, justify: str, align: str) -> None:
    if not children:
        return
    # cross_avail — это ширина для preferred_height() (когда стек вертикальный)
    # или высота для preferred_width() (когда стек горизонтальный), т.е. ОБРАТНО
    # главной оси. Перепутанные местами cw/ch здесь — именно та причина, по которой
    # карточка резервирует высоту по одной ширине, а реально кладёт контент по другой.
    cross_avail     = ch if main_is_x else cw
    container_main  = cw if main_is_x else ch
    base_sizes      = [_main_size(c, main_is_x, cross_avail) for c in children]
    n               = len(children)
    total_base      = sum(base_sizes) + gap * (n - 1)
    leftover        = container_main - total_base
    grows           = [c.resolved.grow for c in children]
    total_grow      = sum(grows)
    sizes           = list(base_sizes)
    extra_gap       = 0.0
    start_offset    = 0.0

    if leftover > 0 and total_grow > 0:
        for i, g_ in enumerate(grows):
            if g_ > 0:
                sizes[i] += leftover * (g_ / total_grow)
    elif leftover > 0:
        if justify == "center":
            start_offset = leftover / 2
        elif justify == "end":
            start_offset = leftover
        elif justify == "between" and n > 1:
            extra_gap = leftover / (n - 1)

    pos = (cx if main_is_x else cy) + start_offset
    for child, size_main in zip(children, sizes):
        if main_is_x:
            cross_size = child.resolved.height or (ch if align == "stretch" else child.preferred_height(size_main))
            cross_pos  = cy + _cross_offset(ch, cross_size, align)
            child.layout(pos, cross_pos, size_main, cross_size)
        else:
            cross_size = child.resolved.width or (cw if align == "stretch" else child.preferred_width())
            cross_pos  = cx + _cross_offset(cw, cross_size, align)
            child.layout(cross_pos, pos, cross_size, size_main)
        pos += size_main + gap + extra_gap


def _wrap_rows(children: list[RenderNode], cw: float, gap: float) -> list[list[RenderNode]]:
    rows: list[list[RenderNode]] = []
    current: list[RenderNode]    = []
    current_w = 0.0
    for child in children:
        w = child.resolved.width or child.preferred_width()
        add_w = w if not current else w + gap
        if current and current_w + add_w > cw:
            rows.append(current)
            current, current_w = [child], w
        else:
            current.append(child)
            current_w += add_w
    if current:
        rows.append(current)
    return rows


class Panel(RenderNode):
    """Контейнер с упрощённой flex-раскладкой: vertical/horizontal,
    wrap, justify-content, align-items, flex-grow у детей."""

    tag = "Panel"

    def __init__(self, *, direction: str = "vertical", background_image=None,
                 image_fit: str = "cover", **kw) -> None:
        super().__init__(**kw)
        self.direction = direction
        if isinstance(background_image, str):
            from ryukon.render.image import Image
            background_image = Image(background_image, fit=image_fit)
        self.background_image = background_image

    def preferred_height(self, available_width: float) -> float:
        if self.resolved.height:
            return self.resolved.height
        t, r, b, l = self.resolved.padding
        inner_w = max(0.0, available_width - l - r)
        if self.direction == "horizontal":
            if self.resolved.wrap:
                rows = _wrap_rows(self.children, inner_w, self.resolved.gap)
                total = t + b
                for i, row in enumerate(rows):
                    row_h = max((c.resolved.height or c.preferred_height(inner_w)) for c in row)
                    total += row_h + (self.resolved.gap if i > 0 else 0)
                return total
            heights = [c.resolved.height or c.preferred_height(inner_w) for c in self.children] or [0]
            return t + b + max(heights)
        total = t + b
        for i, child in enumerate(self.children):
            total += child.resolved.height or child.preferred_height(inner_w)
            if i > 0:
                total += self.resolved.gap
        return total

    def layout(self, x: float, y: float, w: float, h: float) -> None:
        self.rect = (x, y, w, h)
        if self.background_image is not None:
            # Фон-картинка всегда растягивается на весь блок панели —
            # вместе с её размером при ресайзе окна/контейнера.
            self.background_image.layout(x, y, w, h)
        cx, cy, cw, ch = self.content_rect()
        gap       = self.resolved.gap
        main_is_x = self.direction == "horizontal"

        if main_is_x and self.resolved.wrap:
            rows  = _wrap_rows(self.children, cw, gap)
            row_y = cy
            for row in rows:
                row_h = max((c.resolved.height or c.preferred_height(cw)) for c in row)
                _layout_axis(row, cx, row_y, cw, row_h, gap, True, self.resolved.justify, self.resolved.align)
                row_y += row_h + gap
        else:
            _layout_axis(self.children, cx, cy, cw, ch, gap, main_is_x, self.resolved.justify, self.resolved.align)

    def is_animating(self) -> bool:
        return super().is_animating() or (self.background_image is not None and self.background_image.is_animating())

    def paint(self, g: Graphics) -> None:
        style = self.display_style()
        x, y, w, h = self.rect
        if style.shadow and w > 0 and h > 0:
            draw_box(g, self.rect, replace(style, background=None, border_width=0))
        if self.background_image is not None:
            self.background_image.resolved = replace(style, opacity=style.opacity)
            self.background_image.paint(g)
        elif style.background:
            g.fill_round_rect(x, y, w, h, style.radius, style.background.argb)
        if style.border_width and style.border_color:
            g.stroke_round_rect(x, y, w, h, style.radius, style.border_color.argb, style.border_width)
        if "focused" in self.state:
            ring = (style.accent or RColor(91, 140, 255)).argb
            g.stroke_round_rect(x - 2, y - 2, w + 4, h + 4, style.radius + 2, ring, 2)
        for child in self.children:
            child.paint(g)


class Label(RenderNode):
    tag = "Label"

    def __init__(self, text: str, **kw) -> None:
        super().__init__(**kw)
        self.text = text

    def preferred_height(self, available_width: float) -> float:
        return self.resolved.height or 22

    def paint(self, g: Graphics) -> None:
        style = self.display_style()
        draw_box(g, self.rect, style, focused="focused" in self.state)
        x, y, w, h = self.content_rect()
        color = style.color or RColor(220, 220, 220)
        g.draw_text(
            self.text, x, y, w, h,
            family=style.font_family, size=style.font_size,
            bold=style.font_bold, italic=style.font_italic,
            color=color.argb, align=style.text_align,
        )


class Button(RenderNode):
    tag = "Button"

    def __init__(self, text: str, *, onclick=None, **kw) -> None:
        super().__init__(**kw)
        self.text    = text
        self.onclick = onclick

    def preferred_height(self, available_width: float) -> float:
        return self.resolved.height or 36

    def preferred_width(self) -> float:
        return self.resolved.width or max(100, len(self.text) * 9 + 40)

    def paint(self, g: Graphics) -> None:
        style = self.display_style()
        draw_box(g, self.rect, style, focused="focused" in self.state)
        x, y, w, h = self.rect
        color = style.color or RColor(255, 255, 255)
        g.draw_text(
            self.text, x, y, w, h,
            family=style.font_family, size=style.font_size,
            bold=style.font_bold, italic=style.font_italic,
            color=color.argb, align=style.text_align,
        )


class Checkbox(RenderNode):
    tag = "Checkbox"
    BOX = 18

    def __init__(self, text: str, *, checked: bool = False, onchange=None, **kw) -> None:
        super().__init__(**kw)
        self.text     = text
        self.checked  = checked
        self.onchange = onchange
        if checked:
            self.state.add("checked")

    def preferred_height(self, available_width: float) -> float:
        return self.resolved.height or 24

    def toggle(self) -> None:
        self.checked = not self.checked
        if self.checked:
            self.state.add("checked")
        else:
            self.state.discard("checked")

    def paint(self, g: Graphics) -> None:
        x, y, w, h = self.rect
        style = self.display_style()
        box   = self.BOX
        bx, by = x, y + (h - box) / 2

        bg = style.background or RColor(45, 45, 48)
        rad = min(style.radius, 6)
        g.fill_round_rect(bx, by, box, box, rad, bg.argb)
        if style.border_width and style.border_color:
            g.stroke_round_rect(bx, by, box, box, rad, style.border_color.argb, style.border_width)
        if "focused" in self.state:
            ring = (style.accent or RColor(91, 140, 255)).argb
            g.stroke_round_rect(bx - 2, by - 2, box + 4, box + 4, rad + 2, ring, 2)

        if self.checked:
            accent = style.accent or RColor(0, 120, 212)
            g.fill_round_rect(bx + 3, by + 3, box - 6, box - 6, max(0, rad - 2), accent.argb)

        text_color = style.color or RColor(220, 220, 220)
        g.draw_text(
            self.text, x + box + 10, y, w - box - 10, h,
            family=style.font_family, size=style.font_size,
            bold=style.font_bold, italic=style.font_italic,
            color=text_color.argb, align="left",
        )


class ProgressBar(RenderNode):
    tag = "ProgressBar"

    def __init__(self, *, min: int = 0, max: int = 100, value: int = 0, **kw) -> None:
        super().__init__(**kw)
        self.min   = min
        self.max   = max
        self.value = value

    def preferred_height(self, available_width: float) -> float:
        return self.resolved.height or 14

    def paint(self, g: Graphics) -> None:
        style = self.display_style()
        draw_box(g, self.rect, style, focused="focused" in self.state)
        x, y, w, h = self.rect
        span  = (self.max - self.min) or 1
        frac  = max(0.0, min(1.0, (self.value - self.min) / span))
        fill_w = w * frac
        if fill_w > 1:
            accent = style.accent or RColor(0, 120, 212)
            g.fill_round_rect(x, y, fill_w, h, style.radius, accent.argb)


class Slider(RenderNode):
    tag   = "Slider"
    THUMB = 16

    def __init__(self, *, min: int = 0, max: int = 100, value: int = 0, onchange=None, **kw) -> None:
        super().__init__(**kw)
        self.min      = min
        self.max      = max
        self.value    = value
        self.onchange = onchange

    def preferred_height(self, available_width: float) -> float:
        return self.resolved.height or 28

    def value_from_x(self, px: float) -> float:
        x, y, w, h = self.rect
        span = (self.max - self.min) or 1
        frac = max(0.0, min(1.0, (px - x - self.THUMB / 2) / max(1, w - self.THUMB)))
        return self.min + frac * span

    def thumb_x(self) -> float:
        x, y, w, h = self.rect
        span = (self.max - self.min) or 1
        frac = (self.value - self.min) / span
        return x + frac * (w - self.THUMB)

    def step(self, delta: float) -> None:
        span = (self.max - self.min) or 1
        self.value = max(self.min, min(self.max, self.value + delta * max(1, span / 100)))

    def paint(self, g: Graphics) -> None:
        x, y, w, h = self.rect
        style    = self.display_style()
        track_h  = 6
        ty       = y + (h - track_h) / 2
        track_bg = style.background or RColor(60, 60, 60)
        g.fill_round_rect(x, ty, w, track_h, track_h / 2, track_bg.argb)

        accent = style.accent or RColor(0, 120, 212)
        tx     = self.thumb_x()
        fill_w = max(0.0, tx + self.THUMB / 2 - x)
        g.fill_round_rect(x, ty, fill_w, track_h, track_h / 2, accent.argb)

        thumb_y = y + (h - self.THUMB) / 2
        g.fill_ellipse(tx, thumb_y, self.THUMB, self.THUMB, RColor(255, 255, 255).argb)
        g.stroke_round_rect(tx, thumb_y, self.THUMB, self.THUMB, self.THUMB / 2, accent.argb, 2)
        if "focused" in self.state:
            g.stroke_round_rect(x - 2, y - 2, w + 4, h + 4, 6, accent.argb, 2)


class NativeSlot(RenderNode):
    """Резервирует место и рисует фон-«карточку» под настоящим Win32-виджетом
    (Input/TextArea/Dropdown/Table), который двигает Surface поверх неё."""

    tag = "NativeSlot"

    def __init__(self, widget_name: str, *, height: int = 30, **kw) -> None:
        super().__init__(**kw)
        self.widget_name      = widget_name
        self._default_height  = height

    def preferred_height(self, available_width: float) -> float:
        return self.resolved.height or self._default_height

    def paint(self, g: Graphics) -> None:
        draw_box(g, self.rect, self.display_style(), focused="focused" in self.state)
