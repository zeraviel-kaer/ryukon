from __future__ import annotations

import re
from dataclasses import dataclass, replace

from ryukon.render.color import RColor, parse_color


@dataclass
class BoxStyle:
    background:   RColor | None = None
    accent:       RColor | None = None   # цвет заливки (прогрессбар/слайдер)
    color:        RColor | None = None   # цвет текста
    border_color: RColor | None = None
    border_width: int = 0
    radius:       int = 0
    padding:      tuple[int, int, int, int] = (0, 0, 0, 0)  # top, right, bottom, left
    margin:       tuple[int, int, int, int] = (0, 0, 0, 0)
    gap:          int = 8
    font_family:  str = "Segoe UI"
    font_size:    int = 11
    font_bold:    bool = False
    font_italic:  bool = False
    width:        int | None = None
    height:       int | None = None
    text_align:   str = "center"
    shadow:       tuple[int, int, int, RColor] | None = None  # dx, dy, blur, color
    opacity:      float = 1.0

    # flex-подобная раскладка для Panel
    wrap:    bool = False
    justify: str  = "start"    # start, center, end, between
    align:   str  = "stretch"  # start, center, end, stretch
    grow:    float = 0.0       # вес растяжения этого узла внутри Panel-родителя

    # анимация при смене состояния (hover/pressed/focused), секунды
    transition: float = 0.0


def scale_style(style: BoxStyle, scale: float) -> BoxStyle:
    """Масштабирует пиксельные поля стиля под DPI монитора (96 DPI = 1.0)."""
    if scale == 1.0:
        return style
    out = replace(style)
    t, r, b, l   = style.padding
    mt, mr, mb, ml = style.margin
    out.padding      = (round(t * scale), round(r * scale), round(b * scale), round(l * scale))
    out.margin        = (round(mt * scale), round(mr * scale), round(mb * scale), round(ml * scale))
    out.gap           = round(style.gap * scale)
    out.radius        = round(style.radius * scale)
    out.border_width = round(style.border_width * scale)
    out.font_size      = max(1, round(style.font_size * scale))
    out.width          = round(style.width * scale) if style.width is not None else None
    out.height         = round(style.height * scale) if style.height is not None else None
    if style.shadow:
        dx, dy, blur, color = style.shadow
        out.shadow = (round(dx * scale), round(dy * scale), round(blur * scale), color)
    return out


def _parse_edges(value: str) -> tuple[int, int, int, int]:
    parts = [int(re.sub(r"[^\d-]", "", p)) for p in value.split() if re.search(r"\d", p)]
    if len(parts) == 1:
        t = r = b = l = parts[0]
    elif len(parts) == 2:
        t = b = parts[0]
        r = l = parts[1]
    elif len(parts) == 4:
        t, r, b, l = parts
    else:
        t = r = b = l = 0
    return (t, r, b, l)


def _parse_int(value: str, default: int = 0) -> int:
    m = re.search(r"-?\d+", value)
    return int(m.group()) if m else default


_PROP_HANDLERS = {}


def _prop(name):
    def deco(fn):
        _PROP_HANDLERS[name] = fn
        return fn
    return deco


@_prop("background")
@_prop("background-color")
def _h_background(style: BoxStyle, value: str) -> None:
    c = parse_color(value)
    if c:
        style.background = c


@_prop("accent-color")
def _h_accent(style: BoxStyle, value: str) -> None:
    c = parse_color(value)
    if c:
        style.accent = c


@_prop("color")
def _h_color(style: BoxStyle, value: str) -> None:
    c = parse_color(value)
    if c:
        style.color = c


@_prop("border-color")
def _h_border_color(style: BoxStyle, value: str) -> None:
    c = parse_color(value)
    if c:
        style.border_color = c


@_prop("border-width")
def _h_border_width(style: BoxStyle, value: str) -> None:
    style.border_width = _parse_int(value)


@_prop("border")
def _h_border(style: BoxStyle, value: str) -> None:
    tokens = value.split()
    for tok in tokens:
        if re.match(r"^\d+(px)?$", tok):
            style.border_width = _parse_int(tok)
        elif tok.startswith("#") or tok.startswith("rgb"):
            c = parse_color(tok)
            if c:
                style.border_color = c


@_prop("border-radius")
def _h_radius(style: BoxStyle, value: str) -> None:
    style.radius = _parse_int(value)


@_prop("padding")
def _h_padding(style: BoxStyle, value: str) -> None:
    style.padding = _parse_edges(value)


@_prop("margin")
def _h_margin(style: BoxStyle, value: str) -> None:
    style.margin = _parse_edges(value)


@_prop("gap")
def _h_gap(style: BoxStyle, value: str) -> None:
    style.gap = _parse_int(value)


@_prop("width")
def _h_width(style: BoxStyle, value: str) -> None:
    style.width = _parse_int(value)


@_prop("height")
def _h_height(style: BoxStyle, value: str) -> None:
    style.height = _parse_int(value)


@_prop("text-align")
def _h_text_align(style: BoxStyle, value: str) -> None:
    if value.strip().lower() in ("left", "center", "right"):
        style.text_align = value.strip().lower()


@_prop("font-family")
def _h_font_family(style: BoxStyle, value: str) -> None:
    style.font_family = value.strip("'\"")


@_prop("font-size")
def _h_font_size(style: BoxStyle, value: str) -> None:
    style.font_size = _parse_int(value, style.font_size)


@_prop("font-weight")
def _h_font_weight(style: BoxStyle, value: str) -> None:
    style.font_bold = value.strip().lower() in ("bold", "700", "800", "900")


@_prop("font-style")
def _h_font_style(style: BoxStyle, value: str) -> None:
    style.font_italic = value.strip().lower() == "italic"


@_prop("opacity")
def _h_opacity(style: BoxStyle, value: str) -> None:
    try:
        style.opacity = max(0.0, min(1.0, float(value)))
    except ValueError:
        pass


@_prop("flex-wrap")
def _h_wrap(style: BoxStyle, value: str) -> None:
    style.wrap = value.strip().lower() in ("wrap", "true", "1")


@_prop("justify-content")
def _h_justify(style: BoxStyle, value: str) -> None:
    v = value.strip().lower()
    if v in ("start", "center", "end", "between"):
        style.justify = v
    elif v == "flex-start":
        style.justify = "start"
    elif v == "flex-end":
        style.justify = "end"
    elif v == "space-between":
        style.justify = "between"


@_prop("align-items")
def _h_align(style: BoxStyle, value: str) -> None:
    v = value.strip().lower()
    if v in ("start", "center", "end", "stretch"):
        style.align = v
    elif v == "flex-start":
        style.align = "start"
    elif v == "flex-end":
        style.align = "end"


@_prop("flex-grow")
def _h_grow(style: BoxStyle, value: str) -> None:
    try:
        style.grow = float(value)
    except ValueError:
        pass


@_prop("transition")
def _h_transition(style: BoxStyle, value: str) -> None:
    m = re.search(r"([\d.]+)\s*(ms|s)?", value)
    if not m:
        return
    num = float(m.group(1))
    style.transition = num / 1000.0 if m.group(2) == "ms" else num


@_prop("box-shadow")
def _h_shadow(style: BoxStyle, value: str) -> None:
    tokens = value.split()
    nums = [t for t in tokens if re.match(r"^-?\d+$", t)]
    color_tok = next((t for t in tokens if t.startswith("#") or t.startswith("rgb")), "#00000066")
    if len(nums) >= 3:
        dx, dy, blur = int(nums[0]), int(nums[1]), int(nums[2])
        color = parse_color(color_tok) or RColor(0, 0, 0, 100)
        style.shadow = (dx, dy, blur, color)


@dataclass
class Rule:
    type_name: str | None
    classes:   tuple[str, ...]
    id_name:   str | None
    pseudo:    str | None
    props:     dict
    order:     int

    @property
    def specificity(self) -> tuple[int, int, int]:
        class_weight = len(self.classes) + (1 if self.pseudo else 0)
        return (1 if self.id_name else 0, class_weight, 1 if self.type_name else 0)


_SELECTOR_RE = re.compile(
    r"^(?P<type>[A-Za-z_][A-Za-z0-9_]*|\*)?"
    r"(?P<classes>(?:\.[A-Za-z0-9_-]+)*)"
    r"(?:#(?P<id>[A-Za-z0-9_-]+))?"
    r"(?::(?P<pseudo>[A-Za-z-]+))?$"
)


def _parse_selector(sel: str, props: dict, order: int) -> Rule | None:
    sel = sel.strip()
    m = _SELECTOR_RE.match(sel)
    if not m:
        return None
    type_name = m.group("type")
    if type_name == "*":
        type_name = None
    classes = tuple(c for c in m.group("classes").split(".") if c) if m.group("classes") else ()
    return Rule(type_name, classes, m.group("id"), m.group("pseudo"), props, order)


class StyleSheet:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = sorted(rules, key=lambda r: (r.specificity, r.order))

    def resolve(self, node) -> BoxStyle:
        """Считает итоговый BoxStyle для узла с учётом состояния (hover/pressed/checked)."""
        style = BoxStyle()
        for rule in self.rules:
            if rule.type_name and rule.type_name != node.tag:
                continue
            if rule.classes and not set(rule.classes).issubset(node.classes):
                continue
            if rule.id_name and rule.id_name != node.id:
                continue
            if rule.pseudo and rule.pseudo not in node.state:
                continue
            for key, value in rule.props.items():
                handler = _PROP_HANDLERS.get(key)
                if handler:
                    handler(style, value)
        return style


def parse(css_text: str) -> StyleSheet:
    css_text = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)
    rules: list[Rule] = []
    order = 0
    for match in re.finditer(r"([^{}]+)\{([^}]*)\}", css_text):
        selectors = [s.strip() for s in match.group(1).split(",") if s.strip()]
        block     = match.group(2)
        props: dict[str, str] = {}
        for line in block.split(";"):
            if ":" in line:
                k, _, v = line.partition(":")
                props[k.strip().lower()] = v.strip()
        for sel in selectors:
            rule = _parse_selector(sel, props, order)
            if rule:
                rules.append(rule)
            order += 1
    return StyleSheet(rules)


def load(path: str) -> StyleSheet:
    with open(path, encoding="utf-8") as f:
        return parse(f.read())
