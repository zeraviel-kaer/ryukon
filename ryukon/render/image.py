from __future__ import annotations

import asyncio
import re
import time
import urllib.request

from ryukon.render import gdiplus
from ryukon.render.color import RColor
from ryukon.render.gdiplus import Graphics
from ryukon.render.nodes import RenderNode

_URL_RE = re.compile(r"^https?://", re.I)


class Image(RenderNode):
    """Картинка (PNG/JPG/BMP/GIF) — по пути к файлу или по URL.

    render.Image("assets/bg.png", fit="cover")
    render.Image("https://example.com/anim.gif")   # анимированный GIF проигрывается сам

    Подчиняется обычным CSS-свойствам узла: border-radius скругляет картинку
    (через обтравочный контур), opacity — её прозрачность. Если размер явно
    не задан в CSS (width/height), узел использует исходный размер картинки;
    в противном случае — растягивается по правилам box-модели, как любой
    другой виджет (в т.ч. может занять весь родительский блок).
    """

    tag = "Image"

    def __init__(self, src: str, *, fit: str = "cover", **kw) -> None:
        super().__init__(**kw)
        self.src   = src
        self.fit   = fit  # "cover" | "contain" | "stretch"
        self._bitmap        = None
        self._native_w       = 0.0
        self._native_h       = 0.0
        self._frame_count    = 1
        self._frame_delays: list[float] = []
        self._frame_index     = 0
        self._frame_started   = time.monotonic()
        self._load_started    = False

    # ── загрузка ────────────────────────────────────────────────────
    def _ensure_loaded(self) -> None:
        if self._load_started:
            return
        self._load_started = True
        if _URL_RE.match(self.src):
            try:
                asyncio.get_event_loop().create_task(self._load_url())
            except RuntimeError:
                pass
        else:
            bitmap = gdiplus.load_image_from_file(self.src)
            if bitmap:
                self._attach(bitmap)

    async def _load_url(self) -> None:
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(self.src, timeout=10).read()
            )
        except Exception:
            return
        bitmap = gdiplus.load_image_from_bytes(data)
        if bitmap:
            self._attach(bitmap)

    def _attach(self, bitmap) -> None:
        self._bitmap = bitmap
        self._native_w, self._native_h = gdiplus.get_image_size(bitmap)
        self._frame_count = gdiplus.get_frame_count(bitmap)
        if self._frame_count > 1:
            self._frame_delays = gdiplus.get_frame_delays(bitmap, self._frame_count)
            self._frame_started = time.monotonic()

    def __del__(self) -> None:
        # Best-effort: освобождаем GDI+ изображение, если узел был выброшен
        # (например, при пересборке дерева через use_render()).
        if self._bitmap is not None:
            gdiplus.dispose_image(self._bitmap)
            self._bitmap = None

    # ── размер по умолчанию — натуральный размер картинки ─────────────
    def preferred_width(self) -> float:
        if self.resolved.width:
            return self.resolved.width
        return self._native_w or 120

    def preferred_height(self, available_width: float) -> float:
        if self.resolved.height:
            return self.resolved.height
        return self._native_h or 80

    def is_animating(self) -> bool:
        return self._frame_count > 1

    def _advance_frame(self) -> None:
        if self._frame_count <= 1 or not self._frame_delays:
            return
        elapsed = time.monotonic() - self._frame_started
        if elapsed >= self._frame_delays[self._frame_index]:
            self._frame_index   = (self._frame_index + 1) % self._frame_count
            self._frame_started = time.monotonic()
            gdiplus.select_frame(self._bitmap, self._frame_index)

    def paint(self, g: Graphics) -> None:
        self._ensure_loaded()
        x, y, w, h = self.rect
        style = self.resolved
        if self._bitmap is not None and w > 0 and h > 0:
            self._advance_frame()
            g.draw_image(self._bitmap, x, y, w, h, self._native_w, self._native_h,
                         fit=self.fit, radius=style.radius, opacity=style.opacity)
        elif style.background and w > 0 and h > 0:
            # Заглушка цветом, пока картинка не загрузилась (особенно для URL).
            g.fill_round_rect(x, y, w, h, style.radius, style.background.argb)

        if style.border_width and style.border_color:
            g.stroke_round_rect(x, y, w, h, style.radius, style.border_color.argb, style.border_width)
        if "focused" in self.state:
            ring = (style.accent or RColor(91, 140, 255)).argb
            g.stroke_round_rect(x - 2, y - 2, w + 4, h + 4, style.radius + 2, ring, 2)
