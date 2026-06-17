import ryukon

app     = ryukon.App()
hotkeys = ryukon.HotkeyManager()
tray    = ryukon.Tray(tooltip="Ryukon App")

app.set_hotkeys(hotkeys)
app.set_tray(tray)


@app.child_window(title="Настройки", width=300, height=250, center=True, resizable=False)
class SettingsWindow(ryukon.Window):
    layout = ryukon.VLayout(padding=15, gap=10)

    @ryukon.label(text="Настройки")
    def title_lbl(self): ...

    @ryukon.checkbox(label="Автозапуск")
    async def on_autostart(self, checked: bool):
        print(f"Автозапуск: {checked}")


@app.window(title="Ryukon", width=500, height=500, center=True)
class MainWindow(ryukon.Window):
    layout = ryukon.VLayout(padding=15, gap=8, auto_resize=True)

    @ryukon.label(text="Прогресс:")
    def progress_lbl(self): ...

    @ryukon.progressbar(min=0, max=100, value=0)
    def progress(self): ...

    @ryukon.textarea(placeholder="Введи текст...")
    async def on_text(self, value: str):
        print(f"Текст: {value[:20]}")

    @ryukon.table(
        columns=["Имя", "Возраст", "Город"],
        rows=[["Иван", "25", "Москва"], ["Анна", "30", "СПб"]],
        height=120,
    )
    async def on_select(self, row_index: int):
        print(f"Выбрана строка: {row_index}")

    @ryukon.button(label="Открыть файл", x=15, y=430, width=120, height=30)
    async def on_open(self):
        path = ryukon.dialog.ask_file("Открыть", filters="Все файлы\0*.*\0")
        if path:
            print(f"Файл: {path}")

    @ryukon.button(label="Цвет", x=145, y=430, width=80, height=30)
    async def on_color(self):
        color = ryukon.dialog.ask_color()
        if color:
            print(f"Цвет: {color}")

    @ryukon.button(label="Настройки", x=235, y=430, width=100, height=30)
    async def on_settings(self):
        self.open_window(SettingsWindow, modal=True)

    async def on_ready(self):
        # Стили через строку
        self.load_style("""
            Window  { background: #1e1e1e; color: #d4d4d4; font-family: Segoe UI; font-size: 11; }
            Button  { color: #ffffff; font-weight: bold; }
            Label   { color: #aaaaaa; }
        """)

        # Или из файла:
        # self.load_style_file("dark.rcss")

        # Анимация появления
        await ryukon.Animation.animate_opacity(self, from_=0.0, to=1.0, duration=0.4)

        # Таймер
        self._timer = ryukon.Timer(interval=1.0, callback=self._tick, autostart=True)

        # Меню
        menu = ryukon.Menu()

        file_menu = menu.add("Файл")
        file_menu.add(ryukon.MenuItem("Открыть", callback=self.on_open, shortcut="Ctrl+O"))
        file_menu.add(ryukon.MenuItem("", separator=True))
        file_menu.add(ryukon.MenuItem("Выход", callback=app.quit, shortcut="Ctrl+Q"))

        edit_menu = menu.add("Правка")
        edit_menu.add(ryukon.MenuItem("Очистить таблицу", callback=lambda: self.get("on_select").clear()))

        self.set_menu(menu)

        # Контекстное меню
        ctx = ryukon.ContextMenu()
        ctx.add(ryukon.MenuItem("Открыть файл", callback=self.on_open))
        ctx.add(ryukon.MenuItem("", separator=True))
        ctx.add(ryukon.MenuItem("Выход", callback=app.quit))
        self.set_context_menu(ctx)

    async def _tick(self):
        bar = self.get("progress")
        if bar.value < 100:
            bar.value += 5
        else:
            bar.value = 0

    async def on_close(self):
        if ryukon.dialog.confirm("Выйти из приложения?"):
            return True
        return False


tray.add_item("Открыть", callback=lambda: print("открыть"))
tray.add_separator()
tray.add_item("Выход", callback=app.quit)

hotkeys.register("CTRL+SHIFT+Q", callback=app.quit)

app.run()