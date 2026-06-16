from __future__ import annotations

from typing import Callable, Awaitable
from ryukon.widgets.button   import Button
from ryukon.widgets.input    import Input
from ryukon.widgets.label    import Label
from ryukon.widgets.checkbox import Checkbox
from ryukon.widgets.dropdown import Dropdown
from ryukon.widgets.slider   import Slider

_UNSET = object()


def _make_decorator(widget_cls, defaults: dict):
    """Фабрика декораторов — не дублируем логику для каждого виджета."""
    def decorator_factory(**kwargs):
        # Определяем автоматически ли расставлять виджет
        auto = "x" not in kwargs and "y" not in kwargs

        def decorator(func: Callable[..., Awaitable] | None = None):
            def factory(window):
                w = widget_cls(window, **{**defaults, **kwargs},
                               callback=func if callable(func) else None)
                w._auto_layout = auto
                return w
            if func is not None:
                func._is_ryukon_widget = True
                func._widget_factory   = factory
                return func
            # Вызван без метода (для Label без колбека)
            sentinel = lambda self: None
            sentinel._is_ryukon_widget = True
            sentinel._widget_factory   = factory
            return sentinel

        return decorator
    return decorator_factory


def button(*, label: str = "Button", x: int = None, y: int = None,
           width: int = 120, height: int = 30):
    """@ryukon.button(label="Нажми", x=10, y=10)"""
    auto = x is None and y is None
    kw   = {"label": label, "width": width, "height": height}
    if x is not None: kw["x"] = x
    if y is not None: kw["y"] = y

    def decorator(func: Callable[..., Awaitable]):
        def factory(window):
            w = Button(window, **kw, callback=func)
            w._auto_layout = auto
            return w
        func._is_ryukon_widget = True
        func._widget_factory   = factory
        return func
    return decorator


def input(*, placeholder: str | None = None, default: str | None = None,
          x: int = None, y: int = None, width: int = 200, height: int = 25):
    """@ryukon.input(placeholder="Введи текст...", x=10, y=50)"""
    auto = x is None and y is None
    kw   = {"placeholder": placeholder, "default": default, "width": width, "height": height}
    if x is not None: kw["x"] = x
    if y is not None: kw["y"] = y

    def decorator(func: Callable[..., Awaitable]):
        def factory(window):
            w = Input(window, **kw, callback=func)
            w._auto_layout = auto
            return w
        func._is_ryukon_widget = True
        func._widget_factory   = factory
        return func
    return decorator


def label(*, text: str = "", x: int = None, y: int = None,
          width: int = 200, height: int = 20, align: str = "left"):
    """@ryukon.label(text="Привет!", x=10, y=10)"""
    auto = x is None and y is None
    kw   = {"text": text, "width": width, "height": height, "align": align}
    if x is not None: kw["x"] = x
    if y is not None: kw["y"] = y

    def decorator(func):
        def factory(window):
            w = Label(window, **kw)
            w._auto_layout = auto
            return w
        func._is_ryukon_widget = True
        func._widget_factory   = factory
        return func
    return decorator


def checkbox(*, label: str = "", checked: bool = False,
             x: int = None, y: int = None, width: int = 150, height: int = 25):
    """@ryukon.checkbox(label="Согласен", x=10, y=10)"""
    auto = x is None and y is None
    kw   = {"label": label, "checked": checked, "width": width, "height": height}
    if x is not None: kw["x"] = x
    if y is not None: kw["y"] = y

    def decorator(func: Callable[..., Awaitable]):
        def factory(window):
            w = Checkbox(window, **kw, callback=func)
            w._auto_layout = auto
            return w
        func._is_ryukon_widget = True
        func._widget_factory   = factory
        return func
    return decorator


def dropdown(*, options: list[str] = [], default: int = 0,
             x: int = None, y: int = None, width: int = 200, height: int = 25):
    """@ryukon.dropdown(options=["A", "B", "C"], x=10, y=10)"""
    auto = x is None and y is None
    kw   = {"options": options, "default": default, "width": width, "height": height}
    if x is not None: kw["x"] = x
    if y is not None: kw["y"] = y

    def decorator(func: Callable[..., Awaitable]):
        def factory(window):
            w = Dropdown(window, **kw, callback=func)
            w._auto_layout = auto
            return w
        func._is_ryukon_widget = True
        func._widget_factory   = factory
        return func
    return decorator


def slider(*, min: int = 0, max: int = 100, value: int = 0, vertical: bool = False,
           x: int = None, y: int = None, width: int = 200, height: int = 30):
    """@ryukon.slider(min=0, max=100, value=50, x=10, y=10)"""
    auto = x is None and y is None
    kw   = {"min": min, "max": max, "value": value, "vertical": vertical,
            "width": width, "height": height}
    if x is not None: kw["x"] = x
    if y is not None: kw["y"] = y

    def decorator(func: Callable[..., Awaitable]):
        def factory(window):
            w = Slider(window, **kw, callback=func)
            w._auto_layout = auto
            return w
        func._is_ryukon_widget = True
        func._widget_factory   = factory
        return func
    return decorator