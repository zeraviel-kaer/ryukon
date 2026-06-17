"""Полная демонстрация Ryukon: render-движок + вся остальная библиотека —
в одном окне, тёмно-фиолетовая тема, все функции рабочие (не заглушки).

Render-движок (GDI+ + CSS): Panel (vertical/horizontal, flex-wrap,
justify-content, align-items, flex-grow, gap, padding, border-radius,
box-shadow), Label, Button (hover/pressed/focused, transition), Checkbox,
ProgressBar, Slider — с клавиатурной навигацией (Tab/Shift+Tab, Enter/Space,
стрелки) и DPI-масштабом.

Остальная библиотека: Input/TextArea/Dropdown/Table (нативные, встроены в
карточки через NativeSlot), Menu, ContextMenu, Tray, HotkeyManager,
Animation, Timer, dialog.* — и живая смена акцентной темы через Dropdown
(пересборка render-дерева на месте).
"""

import asyncio
import ctypes
import time

import ryukon
from ryukon import render

app     = ryukon.App()
hotkeys = ryukon.HotkeyManager()
tray    = ryukon.Tray(tooltip="Ryukon — Full Demo")

app.set_hotkeys(hotkeys)
app.set_tray(tray)

_main_window = None  # ссылка на единственное окно — нужна треям/хоткеям

TAGS = ["Python", "WinAPI", "GDI+", "CSS", "render-движок", "без браузера"]
DEFAULT_BG = "https://i.pinimg.com/originals/09/66/15/09661552ffe8d3a5255b7d57de5ffc6a.gif"

ACCENTS = {
    "Фиолетовый": ("#8b5cf6", "#a78bfa", "#7c3aed"),
    "Розовый":    ("#ec4899", "#f472b6", "#db2777"),
    "Синий":      ("#3b82f6", "#60a5fa", "#2563eb"),
}

NATIVE_CSS = """
Input    { background: #150f22; color: #f1edfb; }
TextArea { background: #150f22; color: #f1edfb; }
Dropdown { background: #150f22; color: #f1edfb; }
Table    { background: #150f22; color: #f1edfb; }
"""


def make_render_css(accent: str, accent_hover: str, accent_pressed: str) -> str:
    return f"""
Panel.root   {{ background: #140f1f; padding: 18; gap: 12; }}
Panel.card   {{ background: #1f1830; border-radius: 14; padding: 16; gap: 10;
                border-color: #2c2342; border-width: 1; box-shadow: 0 6 18 #00000080; }}
Panel.row    {{ background: transparent; padding: 0; gap: 12; }}
Panel.tags   {{ background: transparent; padding: 0; gap: 8; flex-wrap: wrap; justify-content: start; }}

Label.title    {{ color: #f1edfb; font-size: 20; font-weight: bold; text-align: left; }}
Label.subtitle {{ color: #a89cc8; font-size: 11; text-align: left; }}
Label.section  {{ color: #cabfe6; font-size: 11; font-weight: bold; text-align: left; }}
Label.field    {{ color: #a89cc8; font-size: 10; text-align: left; }}

ProgressBar {{ background: #2a2142; border-radius: 7; accent-color: {accent}; height: 14; }}
Slider      {{ accent-color: {accent}; height: 24; }}

Checkbox {{ background: #2a2142; border-color: #3a2f54; border-width: 1;
            border-radius: 5; color: #d8d0ea; accent-color: {accent}; width: 190;
            transition: 120ms; }}

NativeSlot {{ background: #150f22; border-radius: 8; padding: 4; }}

Button          {{ background: #2a2142; color: #d8d0ea; border-radius: 10;
                    font-weight: bold; transition: 120ms; }}
Button:hover    {{ background: #362a52; }}
Button:pressed  {{ background: #1c1530; }}
Button.primary         {{ background: {accent}; color: #ffffff; }}
Button.primary:hover    {{ background: {accent_hover}; }}
Button.primary:pressed  {{ background: {accent_pressed}; }}
Button.danger           {{ background: #e1457a; color: #ffffff; }}
Button.danger:hover     {{ background: #ec5f8d; }}
Button.ghost             {{ background: transparent; border-color: #3a2f54; border-width: 1; color: #cabfe6; }}
Button.ghost:hover       {{ background: #211a35; }}
.grow {{ flex-grow: 1; }}
Button.chip {{ background: #241c3d; color: #b6acce; font-weight: normal;
               border-radius: 999; height: 28; transition: 120ms; }}
Button.chip:hover {{ background: #2f2650; }}
"""


# ── helpers ──────────────────────────────────────────────────────────────

_user32 = ctypes.windll.user32  # type: ignore
_WS_EX_LAYERED = 0x00080000
_GWL_EXSTYLE   = -20
_LWA_ALPHA     = 0x2


def _enable_layered(hwnd) -> None:
    style = _user32.GetWindowLongW(hwnd, _GWL_EXSTYLE)
    _user32.SetWindowLongW(hwnd, _GWL_EXSTYLE, style | _WS_EX_LAYERED)


def _set_opacity(hwnd, percent: float) -> None:
    # Не даём окну стать слишком прозрачным (нижний порог ~80%) — это просто
    # демонстрация эффекта, а не способ сделать программу нечитаемой.
    alpha = max(204, min(255, int(percent / 100 * 255)))
    _user32.SetLayeredWindowAttributes(hwnd, 0, alpha, _LWA_ALPHA)


def log_action(window, text: str) -> None:
    table = window.get("log")
    if table is not None and getattr(window, "_log_enabled", True):
        table.add_row([time.strftime("%H:%M:%S"), text])


def make_tag_handler(tag: str):
    def handler(window):
        log_action(window, f"Тег: {tag}")
    return handler


# ── render-callbacks (сигнатура (window, ...) — вызывает Surface) ─────────

def on_opacity(window, value):
    window._opacity = value
    lbl = window.render_get("opacity_lbl")
    if lbl:
        lbl.text = f"Прозрачность окна: {int(value)}%"
    _set_opacity(window.hwnd, value)
    window.invalidate()


async def on_notify_toggle(window, checked):
    window._notify_enabled = checked
    log_action(window, f"Уведомления: {'включены' if checked else 'выключены'}")


async def on_log_toggle(window, checked):
    window._log_enabled = checked
    if checked:
        log_action(window, "Логирование включено")


async def on_save(window):
    name = window.get("username").value
    note = window.get("note").value
    log_action(window, f"Сохранено: {name or '—'}")
    if window._notify_enabled and window._app._tray is not None:
        ryukon.notify("Ryukon", f"Сохранено: {name or '(без имени)'}", tray=window._app._tray)
    ryukon.dialog.alert(f"Имя: {name or '(пусто)'}\nЗаметка: {note or '(пусто)'}", title="Сохранено")


async def on_reset(window):
    window.get("username").value = ""
    window.get("note").value = ""
    log_action(window, "Форма сброшена")


async def on_delete(window):
    if ryukon.dialog.confirm("Удалить данные формы?", icon="warning"):
        window.get("username").value = ""
        window.get("note").value = ""
        log_action(window, "Данные удалены")


async def on_animate(window):
    await ryukon.Animation.animate_opacity(window, from_=1.0, to=0.35, duration=0.25)
    await ryukon.Animation.animate_opacity(window, from_=0.35, to=1.0, duration=0.25)
    log_action(window, "Проигран Animation.animate_opacity")


async def on_apply_background(window):
    widget = window.get("bg_url")
    value  = widget.value.strip() if widget else ""
    if not value:
        log_action(window, "Введите ссылку или путь к файлу")
        return
    await window._apply_background(value)


async def on_reset_background(window):
    await window._apply_background(DEFAULT_BG)
    widget = window.get("bg_url")
    if widget:
        widget.value = DEFAULT_BG


async def on_about(window):
    ryukon.dialog.alert(
        "Ryukon — нативный Win32 GUI на Python без браузера.\n\n"
        "В этом окне: собственный render-движок (GDI+, flex-layout,\n"
        "CSS-transition, focus ring, DPI-масштаб), нативные Input/\n"
        "TextArea/Dropdown/Table, Menu, ContextMenu, Tray, HotkeyManager,\n"
        "Animation, Timer и системные диалоги Win32.",
        title="О библиотеке",
    )


# ── дерево интерфейса ───────────────────────────────────────────────────

def build_ui(window) -> render.Panel:
    # Фон всей программы — картинка-виджет (render.Image), растянутая на весь
    # root-блок и сама подстраивающаяся под его размер при ресайзе окна.
    # Источник (путь к файлу или URL, в т.ч. GIF) задаётся полем ниже и хранится
    # в window._bg_source, чтобы переживать пересборку дерева при смене темы.
    root = render.Panel(classes=["root"], background_image=window._bg_source, image_fit="stretch")

    header = render.Panel(classes=["card"]).add(
        render.Label("Ryukon UI", classes=["title"]),
        render.Label("GDI+ · flex-layout · CSS-transition · Tab/Enter · DPI", classes=["subtitle"]),
    )

    bg_row = render.Panel(direction="horizontal").add(
        render.NativeSlot("bg_url", height=32, classes=["grow"]),
        render.Button("Применить", classes=["primary"], onclick=on_apply_background),
        render.Button("Сбросить", classes=["ghost"], onclick=on_reset_background),
    )
    bg_card = render.Panel(classes=["card"]).add(
        render.Label("Фон программы — путь к файлу или URL (PNG/JPG/GIF)", classes=["section"]),
        bg_row,
    )

    tags_row = render.Panel(classes=["tags"], direction="horizontal").add(
        *[render.Button(tag, classes=["chip"], onclick=make_tag_handler(tag)) for tag in TAGS]
    )
    tags_card = render.Panel(classes=["card"]).add(
        render.Label("Технологии", classes=["section"]), tags_row,
    )

    progress    = render.ProgressBar(id="progress", min=0, max=100, value=window._progress)
    opacity_lbl = render.Label(f"Прозрачность окна: {int(window._opacity)}%", id="opacity_lbl", classes=["field"])
    settings_card = render.Panel(classes=["card"]).add(
        render.Label("Тема и статус", classes=["section"]),
        render.NativeSlot("accent", height=30),
        progress,
        opacity_lbl,
        render.Slider(id="opacity", min=85, max=100, value=window._opacity, onchange=on_opacity),
    )

    toggles = render.Panel(classes=["row"], direction="horizontal").add(
        render.Checkbox("Уведомления", checked=window._notify_enabled, onchange=on_notify_toggle),
        render.Checkbox("Логировать действия", checked=window._log_enabled, onchange=on_log_toggle),
    )

    form = render.Panel(classes=["card"]).add(
        render.Label("Имя пользователя", classes=["field"]),
        render.NativeSlot("username", height=32),
        render.Label("Заметка", classes=["field"]),
        render.NativeSlot("note", height=64),
    )

    log_card = render.Panel(classes=["card"]).add(
        render.Label("Журнал действий", classes=["section"]),
        render.NativeSlot("log", height=90),
    )

    # Анимация/О библиотеке вынесены в меню «Вид» — экономит целый ряд по высоте,
    # к тому же это более привычное место для такого рода действий.
    actions = render.Panel(classes=["row"], direction="horizontal").add(
        render.Button("Сохранить", classes=["primary", "grow"], onclick=on_save),
        render.Button("Сброс", classes=["ghost", "grow"], onclick=on_reset),
        render.Button("Удалить", classes=["danger", "grow"], onclick=on_delete),
    )

    root.add(header, bg_card, tags_card, settings_card, toggles, form, log_card, actions)
    return root


# ── окно ────────────────────────────────────────────────────────────────

@app.window(title="Ryukon — Full Demo", width=480, height=1100, center=True,
            min_width=440, min_height=480, resizable=True)
class MainWindow(ryukon.Window):

    @ryukon.input(placeholder="Введите имя...")
    async def username(self, value: str): ...

    @ryukon.input(placeholder="https://... или путь к файлу (PNG/JPG/GIF)", default=DEFAULT_BG)
    async def bg_url(self, value: str): ...

    @ryukon.textarea(placeholder="Свободный текст...")
    async def note(self, value: str): ...

    @ryukon.dropdown(options=list(ACCENTS.keys()), default=0)
    async def accent(self, value: str, index: int):
        await self._apply_accent(index)

    @ryukon.table(columns=["Время", "Действие"], height=90)
    async def log(self, row_index: int): ...

    def _rebuild(self) -> None:
        """Пересобирает render-дерево с текущей темой/фоном — состояние
        (прогресс, прозрачность, чекбоксы, источник фона) хранится на self
        и переживает пересборку, в отличие от самих render-узлов."""
        name = list(ACCENTS.keys())[self._accent_index]
        accent, hover, pressed = ACCENTS[name]
        self.use_render(build_ui(self), make_render_css(accent, hover, pressed))

    async def _apply_accent(self, index: int) -> None:
        self._accent_index = index
        self._rebuild()
        log_action(self, f"Акцент темы: {list(ACCENTS.keys())[index]}")

    async def _apply_background(self, source: str) -> None:
        self._bg_source = source
        self._rebuild()
        log_action(self, f"Фон обновлён: {source}")

    async def on_open_file(self) -> None:
        path = ryukon.dialog.ask_file("Открыть файл", filters="Все файлы\0*.*\0")
        if path:
            log_action(self, f"Открыт файл: {path}")

    async def on_pick_color(self) -> None:
        color = ryukon.dialog.ask_color()
        if color:
            log_action(self, f"Выбран цвет: {color}")

    async def on_clear_log(self) -> None:
        table = self.get("log")
        if table:
            table.clear()

    async def on_animate_demo(self) -> None:
        await on_animate(self)

    async def on_about_demo(self) -> None:
        await on_about(self)

    async def on_ready(self) -> None:
        global _main_window
        _main_window = self

        self._progress      = 0
        self._opacity        = 100
        self._notify_enabled = True
        self._log_enabled    = True
        self._accent_index   = 0
        self._bg_source       = DEFAULT_BG

        _enable_layered(self.hwnd)
        _set_opacity(self.hwnd, self._opacity)

        self.load_style(NATIVE_CSS)
        self._rebuild()

        menu = ryukon.Menu()
        file_menu = menu.add("Файл")
        file_menu.add(ryukon.MenuItem("Открыть файл...", callback=self.on_open_file, shortcut="Ctrl+O"))
        file_menu.add(ryukon.MenuItem("", separator=True))
        file_menu.add(ryukon.MenuItem("Выход", callback=app.quit, shortcut="Ctrl+Q"))

        view_menu = menu.add("Вид")
        view_menu.add(ryukon.MenuItem("Выбрать цвет...", callback=self.on_pick_color))
        view_menu.add(ryukon.MenuItem("Анимация (демо)", callback=self.on_animate_demo))
        view_menu.add(ryukon.MenuItem("", separator=True))
        view_menu.add(ryukon.MenuItem("О библиотеке", callback=self.on_about_demo))

        edit_menu = menu.add("Правка")
        edit_menu.add(ryukon.MenuItem("Очистить журнал", callback=self.on_clear_log, shortcut="Ctrl+L"))
        self.set_menu(menu)

        ctx = ryukon.ContextMenu()
        ctx.add(ryukon.MenuItem("Открыть файл...", callback=self.on_open_file))
        ctx.add(ryukon.MenuItem("", separator=True))
        ctx.add(ryukon.MenuItem("Очистить журнал", callback=self.on_clear_log))
        ctx.add(ryukon.MenuItem("", separator=True))
        ctx.add(ryukon.MenuItem("Выход", callback=app.quit))
        self.set_context_menu(ctx)

        self._timer = ryukon.Timer(interval=0.08, callback=self._tick, autostart=True)
        log_action(self, "Приложение запущено")

    async def on_close(self) -> bool:
        return ryukon.dialog.confirm("Закрыть приложение?")

    async def _tick(self) -> None:
        self._progress = 0 if self._progress >= 100 else self._progress + 2
        bar = self.render_get("progress")
        if bar:
            bar.value = self._progress
        self.invalidate()


def _on_tray_clear() -> None:
    if _main_window:
        asyncio.get_event_loop().create_task(_main_window.on_clear_log())


async def _on_tray_click() -> None:
    if _main_window:
        log_action(_main_window, "Клик по иконке трея")


def _hotkey_clear_log() -> None:
    if _main_window:
        asyncio.get_event_loop().create_task(_main_window.on_clear_log())


tray._on_click = _on_tray_click
tray.add_item("Очистить журнал", callback=_on_tray_clear)
tray.add_separator()
tray.add_item("Выход", callback=app.quit)

hotkeys.register("CTRL+SHIFT+L", callback=_hotkey_clear_log)
hotkeys.register("CTRL+SHIFT+Q", callback=app.quit)

app.run()
