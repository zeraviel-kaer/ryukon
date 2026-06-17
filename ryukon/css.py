from __future__ import annotations

import re
from ryukon.style import Style, Font, Color


# Поддерживаемые свойства
_PROPS = {
    "background", "background-color",
    "color",
    "font-family",
    "font-size",
    "font-weight",
    "font-style",
    "border-radius",
}

# Карта селекторов → имена классов ryukon
_SELECTOR_MAP = {
    "window":      "Window",
    "button":      "Button",
    "input":       "Input",
    "label":       "Label",
    "checkbox":    "Checkbox",
    "dropdown":    "Dropdown",
    "slider":      "Slider",
    "textarea":    "TextArea",
    "progressbar": "ProgressBar",
    "table":       "Table",
}


def _parse_color(value: str) -> Color | None:
    value = value.strip()
    if value.startswith("#"):
        try:
            return Color.from_hex(value)
        except Exception:
            return None
    # rgb(r, g, b)
    m = re.match(r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)", value)
    if m:
        return Color(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def _parse_block(props: dict[str, str]) -> Style:
    """Парсит словарь CSS свойств в объект Style."""
    bg   = None
    fg   = None
    font_family = "Segoe UI"
    font_size   = 10
    font_bold   = False
    font_italic = False
    has_font    = False
    radius      = None

    for key, value in props.items():
        key   = key.strip().lower()
        value = value.strip()

        if key in ("background", "background-color"):
            bg = _parse_color(value)

        elif key == "color":
            fg = _parse_color(value)

        elif key == "font-family":
            font_family = value.strip("'\"")
            has_font    = True

        elif key == "font-size":
            try:
                font_size = int(re.sub(r"[^\d]", "", value))
                has_font  = True
            except ValueError:
                pass

        elif key == "font-weight":
            font_bold = value.lower() in ("bold", "700", "800", "900")
            has_font  = True

        elif key == "font-style":
            font_italic = value.lower() == "italic"
            has_font    = True

        elif key == "border-radius":
            try:
                radius = int(re.sub(r"[^\d]", "", value))
            except ValueError:
                pass

    font = Font(family=font_family, size=font_size, bold=font_bold, italic=font_italic) if has_font else None
    return Style(font=font, bg=bg, fg=fg, radius=radius)


def parse(css: str) -> dict[str, Style]:
    """Парсит CSS строку. Возвращает словарь {selector: Style}.

    styles = ryukon.css.parse('''
        Window {
            background: #1e1e1e;
            color: #ffffff;
            font-family: Segoe UI;
            font-size: 11;
        }
        Button {
            background: #0078d4;
            color: #ffffff;
        }
    ''')
    """
    result: dict[str, Style] = {}

    # Убираем комментарии /* ... */
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)

    # Ищем блоки: selector { props }
    for match in re.finditer(r"([^{]+)\{([^}]*)\}", css):
        selectors = [s.strip().lower() for s in match.group(1).split(",")]
        block     = match.group(2)

        # Парсим свойства
        props: dict[str, str] = {}
        for line in block.split(";"):
            if ":" in line:
                k, _, v = line.partition(":")
                props[k.strip()] = v.strip()

        style = _parse_block(props)

        for selector in selectors:
            result[selector] = style

    return result


def load(path: str) -> dict[str, Style]:
    """Загружает CSS из файла .rcss.

    styles = ryukon.css.load("styles/dark.rcss")
    """
    with open(path, encoding="utf-8") as f:
        return parse(f.read())