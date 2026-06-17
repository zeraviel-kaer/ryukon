from __future__ import annotations

import re


class RColor:
    """Цвет с альфа-каналом для движка рендера."""

    __slots__ = ("r", "g", "b", "a")

    def __init__(self, r: int, g: int, b: int, a: int = 255) -> None:
        self.r, self.g, self.b, self.a = r, g, b, a

    @property
    def argb(self) -> int:
        from ryukon.render.gdiplus import argb
        return argb(self.r, self.g, self.b, self.a)

    def with_alpha(self, a: int) -> "RColor":
        return RColor(self.r, self.g, self.b, a)

    def __repr__(self) -> str:
        return f"RColor({self.r},{self.g},{self.b},{self.a})"


def parse_color(value: str) -> RColor | None:
    value = value.strip()
    if value.startswith("#"):
        hex_str = value.lstrip("#")
        try:
            if len(hex_str) == 6:
                return RColor(int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
            if len(hex_str) == 8:
                return RColor(int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16))
            if len(hex_str) == 3:
                return RColor(int(hex_str[0] * 2, 16), int(hex_str[1] * 2, 16), int(hex_str[2] * 2, 16))
        except ValueError:
            return None
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)", value)
    if m:
        a = m.group(4)
        alpha = int(float(a) * 255) if a else 255
        return RColor(int(m.group(1)), int(m.group(2)), int(m.group(3)), alpha)
    return None
