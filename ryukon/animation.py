from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Callable

user32 = ctypes.windll.user32  # type: ignore

# AnimateWindow флаги
AW_SLIDE      = 0x00040000
AW_BLEND      = 0x00080000  # плавное появление (fade)
AW_HIDE       = 0x00010000  # скрыть вместо показа
AW_HOR_POSITIVE = 0x00000001  # слева направо
AW_HOR_NEGATIVE = 0x00000002  # справа налево
AW_VER_POSITIVE = 0x00000004  # сверху вниз
AW_VER_NEGATIVE = 0x00000008  # снизу вверх
AW_CENTER     = 0x00000010  # из центра / в центр

# SetLayeredWindowAttributes
WS_EX_LAYERED = 0x00080000
GWL_EXSTYLE   = -20
LWA_ALPHA     = 0x00000002


def _set_layered(hwnd: wt.HWND, enabled: bool) -> None:
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if enabled:
        style |= WS_EX_LAYERED
    else:
        style &= ~WS_EX_LAYERED
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)


class Animation:
    """Анимации для окна.

    # Встроенные через AnimateWindow (быстро, одним вызовом):
    await Animation.fade_in(window, duration=200)
    await Animation.fade_out(window, duration=200)
    await Animation.slide_in(window, direction="left", duration=300)
    await Animation.slide_out(window, direction="right", duration=300)

    # Плавная анимация через таймер:
    await Animation.animate_opacity(window, from_=0.0, to=1.0, duration=0.5)
    await Animation.animate_size(window, to_width=600, to_height=400, duration=0.3)
    """

    @staticmethod
    async def fade_in(window, *, duration: int = 200) -> None:
        """Плавное появление окна."""
        if not window.hwnd:
            return
        user32.AnimateWindow(window.hwnd, duration, AW_BLEND)
        await asyncio.sleep(0)

    @staticmethod
    async def fade_out(window, *, duration: int = 200) -> None:
        """Плавное исчезновение окна."""
        if not window.hwnd:
            return
        user32.AnimateWindow(window.hwnd, duration, AW_BLEND | AW_HIDE)
        await asyncio.sleep(0)

    @staticmethod
    async def slide_in(
        window,
        *,
        direction: str = "left",   # "left", "right", "top", "bottom", "center"
        duration:  int = 300,
    ) -> None:
        """Окно въезжает со стороны."""
        if not window.hwnd:
            return
        flags = AW_SLIDE | {
            "left":   AW_HOR_POSITIVE,
            "right":  AW_HOR_NEGATIVE,
            "top":    AW_VER_POSITIVE,
            "bottom": AW_VER_NEGATIVE,
            "center": AW_CENTER,
        }.get(direction, AW_HOR_POSITIVE)
        user32.AnimateWindow(window.hwnd, duration, flags)
        await asyncio.sleep(0)

    @staticmethod
    async def slide_out(
        window,
        *,
        direction: str = "right",
        duration:  int = 300,
    ) -> None:
        """Окно уезжает в сторону."""
        if not window.hwnd:
            return
        flags = AW_SLIDE | AW_HIDE | {
            "left":   AW_HOR_NEGATIVE,
            "right":  AW_HOR_POSITIVE,
            "top":    AW_VER_NEGATIVE,
            "bottom": AW_VER_POSITIVE,
            "center": AW_CENTER,
        }.get(direction, AW_HOR_POSITIVE)
        user32.AnimateWindow(window.hwnd, duration, flags)
        await asyncio.sleep(0)

    @staticmethod
    async def animate_opacity(
        window,
        *,
        from_:    float = 0.0,   # 0.0 — прозрачный, 1.0 — непрозрачный
        to:       float = 1.0,
        duration: float = 0.5,   # секунды
        steps:    int   = 30,
    ) -> None:
        """Плавно меняет прозрачность окна."""
        if not window.hwnd:
            return
        _set_layered(window.hwnd, True)
        step_time  = duration / steps
        step_value = (to - from_) / steps
        current    = from_
        for _ in range(steps):
            alpha = max(0, min(255, int(current * 255)))
            user32.SetLayeredWindowAttributes(window.hwnd, 0, alpha, LWA_ALPHA)
            current += step_value
            await asyncio.sleep(step_time)
        # Финальное значение
        alpha = max(0, min(255, int(to * 255)))
        user32.SetLayeredWindowAttributes(window.hwnd, 0, alpha, LWA_ALPHA)
        # Раньше тут отключался WS_EX_LAYERED при to >= 1.0 — но если окно
        # независимо использует прозрачность где-то ещё (например, свой
        # слайдер), это сбрасывало её механизм. Оставляем layered включённым:
        # стоимость почти нулевая при alpha=255.

    @staticmethod
    async def animate_size(
        window,
        *,
        to_width:  int | None = None,
        to_height: int | None = None,
        duration:  float = 0.3,
        steps:     int   = 20,
    ) -> None:
        """Плавно меняет размер окна."""
        if not window.hwnd:
            return
        rect = wt.RECT()
        user32.GetWindowRect(window.hwnd, ctypes.byref(rect))
        from_w = rect.right  - rect.left
        from_h = rect.bottom - rect.top
        to_w   = to_width  if to_width  is not None else from_w
        to_h   = to_height if to_height is not None else from_h

        step_time = duration / steps
        dw        = (to_w - from_w) / steps
        dh        = (to_h - from_h) / steps
        cw, ch    = float(from_w), float(from_h)

        for _ in range(steps):
            cw += dw
            ch += dh
            user32.SetWindowPos(
                window.hwnd, None,
                rect.left, rect.top, int(cw), int(ch),
                0x0014,  # SWP_NOZORDER | SWP_NOACTIVATE
            )
            await asyncio.sleep(step_time)

        user32.SetWindowPos(
            window.hwnd, None,
            rect.left, rect.top, to_w, to_h,
            0x0014,
        )