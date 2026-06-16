from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import asyncio
from typing import Type

from ryukon.window import Window, user32

try:
    import winloop
    _HAS_WINLOOP = True
except ImportError:
    _HAS_WINLOOP = False


class App:
    """Точка входа Ryukon."""

    def __init__(self) -> None:
        self._windows: list = []
        self._running: bool = False

    def window(
        self,
        *,
        title:      str        = "Ryukon Window",
        width:      int        = 800,
        height:     int        = 600,
        icon:       str | None = None,
        resizable:  bool       = True,
        center:     bool       = False,
        min_width:  int | None = None,
        min_height: int | None = None,
        max_width:  int | None = None,
        max_height: int | None = None,
    ):
        """Регистрирует класс как окно приложения."""
        def decorator(cls: Type[Window]) -> Type[Window]:
            cls._title      = title
            cls._width      = width
            cls._height     = height
            cls._icon       = icon
            cls._resizable  = resizable
            cls._center     = center
            cls._min_width  = min_width
            cls._min_height = min_height
            cls._max_width  = max_width
            cls._max_height = max_height

            factories = [
                (name, method._widget_factory)
                for name, method in vars(cls).items()
                if callable(method) and getattr(method, "_is_ryukon_widget", False)
            ]

            original_init = cls.__init__ if "__init__" in cls.__dict__ else None

            def __init__(self, app, _factories=factories):
                Window.__init__(self, app)
                for name, factory in _factories:
                    widget       = factory(self)
                    widget._name = name
                    self._register_widget(widget)

                # Применяем layout если задан
                layout = getattr(self.__class__, "layout", None)
                if layout is not None:
                    layout.apply(self._widgets, self._width, self._height)

                if original_init:
                    original_init(self, app)

            cls.__init__ = __init__
            self._windows.append(cls)
            return cls

        return decorator

    def run(self) -> None:
        if _HAS_WINLOOP:
            winloop.install()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._main())
        finally:
            loop.close()

    async def _main(self) -> None:
        self._running = True
        for cls in self._windows:
            win = cls(self)
            win._create()
            await win.on_ready()

        msg = wt.MSG()
        while self._running:
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                if msg.message == 0x0012:
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                await asyncio.sleep(0.001)

    def _stop(self) -> None:
        self._running = False