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
        self._windows:        list = []
        self._active_windows: list = []
        self._running:        bool = False
        self._tray                 = None
        self._hotkeys              = None

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
                layout = getattr(self.__class__, "layout", None)
                if layout is not None:
                    layout.apply(self._widgets, self._width, self._height)
                if original_init:
                    original_init(self, app)

            cls.__init__ = __init__
            self._windows.append(cls)
            return cls

        return decorator

    def set_tray(self, tray) -> None:
        """Подключает иконку трея к приложению."""
        self._tray = tray

    def set_hotkeys(self, hotkeys) -> None:
        """Подключает менеджер горячих клавиш к приложению."""
        self._hotkeys = hotkeys

    def quit(self) -> None:
        """Завершает приложение."""
        self._stop()

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

        # Создаём окна
        for cls in self._windows:
            win = cls(self)
            win._create()
            self._active_windows.append(win)
            await win.on_ready()

        # Создаём трей если есть
        if self._tray:
            self._tray._create()

        # Создаём менеджер горячих клавиш если есть
        if self._hotkeys:
            self._hotkeys._create()
            # Регистрируем все накопленные горячие клавиши
            for hid, (mods, vk, cb) in list(self._hotkeys._pending.items()):
                user32.RegisterHotKey(self._hotkeys._hwnd, hid, mods, vk)
                self._hotkeys._hotkeys[hid] = cb

        msg = wt.MSG()
        while self._running:
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                if msg.message == 0x0012:  # WM_QUIT
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                await asyncio.sleep(0.001)

        # Убираем трей при выходе
        if self._tray:
            self._tray.remove()

    def _stop(self) -> None:
        self._running = False

    def child_window(
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
        """Регистрирует класс как дочернее окно — не открывается автоматически.
        Открывается вручную через self.open_window(ChildClass).

        @app.child_window(title="Настройки", width=300, height=200)
        class SettingsWindow(ryukon.Window): ...
        """
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
                layout = getattr(self.__class__, "layout", None)
                if layout is not None:
                    layout.apply(self._widgets, self._width, self._height)
                if original_init:
                    original_init(self, app)

            cls.__init__ = __init__
            # Не добавляем в self._windows — только настраиваем класс
            return cls

        return decorator