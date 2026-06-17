from __future__ import annotations

import asyncio
import ctypes
import ctypes.wintypes as wt

from ryukon.render.gdiplus import Graphics
from ryukon.render.nodes import Button, Checkbox, NativeSlot, RenderNode, Slider
from ryukon.render.cssx import StyleSheet, scale_style

user32 = ctypes.windll.user32  # type: ignore
gdi32  = ctypes.windll.gdi32   # type: ignore

SRCCOPY = 0x00CC0020
ANIM_FPS = 60

# Хендлы — указатели; без явного restype/argtypes ctypes по умолчанию считает
# их 32-битным int и может обрезать/испортить значение на 64-bit Windows.
gdi32.CreateCompatibleDC.restype      = ctypes.c_void_p
gdi32.CreateCompatibleDC.argtypes     = [ctypes.c_void_p]
gdi32.CreateCompatibleBitmap.restype  = ctypes.c_void_p
gdi32.CreateCompatibleBitmap.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype            = ctypes.c_void_p
gdi32.SelectObject.argtypes           = [ctypes.c_void_p, ctypes.c_void_p]
gdi32.DeleteObject.argtypes           = [ctypes.c_void_p]
gdi32.DeleteDC.argtypes               = [ctypes.c_void_p]
gdi32.BitBlt.argtypes = [
    ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_uint32,
]

user32.GetDpiForWindow.restype  = ctypes.c_uint
user32.GetDpiForWindow.argtypes = [wt.HWND]


class Surface:
    """Связывает дерево render-узлов с конкретным HWND окна: layout (с учётом
    DPI), отрисовка с двойной буферизацией, события мыши и клавиатуры
    (hover/press/click/drag/focus), плавные CSS-переходы цвета."""

    def __init__(self, window, root: RenderNode, sheet: StyleSheet) -> None:
        self.window  = window
        self.root    = root
        self.sheet   = sheet
        self.scale   = 1.0
        self.hover_node: RenderNode | None   = None
        self.pressed_node: RenderNode | None = None
        self.focused_node: RenderNode | None = None
        self.dragging: Slider | None         = None
        self._interactive: list[RenderNode]  = []
        self._anim_task: asyncio.Task | None = None

    # ── layout / DPI ────────────────────────────────────────────────
    def _dpi_scale(self) -> float:
        hwnd = self.window._hwnd
        if not hwnd:
            return 1.0
        try:
            dpi = user32.GetDpiForWindow(hwnd)
            return dpi / 96.0 if dpi else 1.0
        except OSError:
            return 1.0

    def _resolve_all(self, node: RenderNode) -> None:
        """Полный пересчёт стилей всего дерева (layout/resize) — без анимации."""
        style = self.sheet.resolve(node)
        if self.scale != 1.0:
            style = scale_style(style, self.scale)
        node.resolved    = style
        node._anim_start = None
        for child in node.children:
            self._resolve_all(child)

    def layout(self, width: int, height: int) -> None:
        self.scale = self._dpi_scale()
        self._resolve_all(self.root)
        self.root.layout(0, 0, width, height)
        self._sync_native(self.root)
        self._interactive = [n for n in self.root.walk() if isinstance(n, (Button, Checkbox, Slider))]
        if any(n.is_animating() for n in self.root.walk()):
            # Анимированные GIF крутятся вечно — цикл сам остановится,
            # когда таких узлов в дереве не останется (см. _animation_loop).
            self._ensure_animation_loop()

    def _sync_native(self, node: RenderNode) -> None:
        if isinstance(node, NativeSlot):
            widget = self.window.get(node.widget_name)
            if widget is not None:
                x, y, w, h = node.content_rect()
                widget._x, widget._y, widget._width, widget._height = int(x), int(y), int(w), int(h)
                if widget._hwnd:
                    user32.MoveWindow(widget._hwnd, int(x), int(y), int(w), int(h), 1)
        for child in node.children:
            self._sync_native(child)

    # ── отрисовка ───────────────────────────────────────────────────
    def paint(self, hwnd, hdc) -> None:
        rect = wt.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(rect))
        w, h = rect.right - rect.left, rect.bottom - rect.top
        if w <= 0 or h <= 0:
            return

        mem_dc  = gdi32.CreateCompatibleDC(hdc)
        bitmap  = gdi32.CreateCompatibleBitmap(hdc, w, h)
        old_obj = gdi32.SelectObject(mem_dc, bitmap)

        g = Graphics(mem_dc)
        self.root.paint(g)
        g.close()

        gdi32.BitBlt(hdc, 0, 0, w, h, mem_dc, 0, 0, SRCCOPY)

        gdi32.SelectObject(mem_dc, old_obj)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)

    def _invalidate(self) -> None:
        if self.window._hwnd:
            user32.InvalidateRect(self.window._hwnd, None, 0)

    def _fire(self, callback, *args) -> None:
        if not callback:
            return
        result = callback(*args)
        if asyncio.iscoroutine(result):
            asyncio.get_event_loop().create_task(result)

    # ── стиль/анимация одного узла (hover/pressed/focused) ────────────
    def _restyle(self, node: RenderNode) -> None:
        style = self.sheet.resolve(node)
        if self.scale != 1.0:
            style = scale_style(style, self.scale)
        if node.apply_style(style):
            self._ensure_animation_loop()

    def _ensure_animation_loop(self) -> None:
        if self._anim_task is not None and not self._anim_task.done():
            return
        self._anim_task = asyncio.get_event_loop().create_task(self._animation_loop())

    async def _animation_loop(self) -> None:
        try:
            while any(n.is_animating() for n in self.root.walk()):
                self._invalidate()
                await asyncio.sleep(1 / ANIM_FPS)
        except asyncio.CancelledError:
            pass

    # ── фокус и активация с клавиатуры ────────────────────────────────
    def set_focus(self, node: RenderNode | None) -> None:
        if self.focused_node is node:
            return
        if self.focused_node is not None:
            self.focused_node.state.discard("focused")
            self._restyle(self.focused_node)
        self.focused_node = node
        if node is not None:
            node.state.add("focused")
            self._restyle(node)
        self._invalidate()

    def clear_focus(self) -> None:
        self.set_focus(None)

    def activate_focused(self) -> None:
        node = self.focused_node
        if node is None:
            return
        if isinstance(node, Button):
            self._fire(node.onclick, self.window)
        elif isinstance(node, Checkbox):
            node.toggle()
            self._restyle(node)
            self._fire(node.onchange, self.window, node.checked)
            self._invalidate()

    def step_focused_slider(self, delta: float) -> bool:
        node = self.focused_node
        if not isinstance(node, Slider):
            return False
        node.step(delta)
        self._fire(node.onchange, self.window, node.value)
        self._invalidate()
        return True

    # ── мышь ────────────────────────────────────────────────────────
    def on_mouse_move(self, x: int, y: int) -> None:
        if self.dragging is not None:
            self.dragging.value = self.dragging.value_from_x(x)
            self._fire(self.dragging.onchange, self.window, self.dragging.value)
            self._invalidate()
            return

        new_hover = next((n for n in self._interactive if n.hit_test(x, y)), None)
        if new_hover is not self.hover_node:
            if self.hover_node is not None:
                self.hover_node.state.discard("hover")
                self._restyle(self.hover_node)
            if new_hover is not None:
                new_hover.state.add("hover")
                self._restyle(new_hover)
            self.hover_node = new_hover
            self._invalidate()

    def on_mouse_leave(self) -> None:
        if self.hover_node is not None:
            self.hover_node.state.discard("hover")
            self._restyle(self.hover_node)
            self.hover_node = None
            self._invalidate()

    def on_lbutton_down(self, x: int, y: int) -> None:
        node = next((n for n in self._interactive if n.hit_test(x, y)), None)
        if node is not None:
            self.set_focus(node)
        if isinstance(node, Slider):
            self.dragging = node
            node.value = node.value_from_x(x)
            self._fire(node.onchange, self.window, node.value)
            self._invalidate()
            return
        if node is not None:
            self.pressed_node = node
            node.state.add("pressed")
            self._restyle(node)
            self._invalidate()

    def on_lbutton_up(self, x: int, y: int) -> None:
        if self.dragging is not None:
            self.dragging = None
            return
        if self.pressed_node is None:
            return
        node = self.pressed_node
        node.state.discard("pressed")
        self.pressed_node = None
        still_inside = node.hit_test(x, y)
        self._restyle(node)
        self._invalidate()
        if not still_inside:
            return
        if isinstance(node, Button):
            self._fire(node.onclick, self.window)
        elif isinstance(node, Checkbox):
            node.toggle()
            self._restyle(node)
            self._fire(node.onchange, self.window, node.checked)
            self._invalidate()
