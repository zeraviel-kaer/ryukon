import ryukon

app = ryukon.App()

@app.window(title="Ryukon — Layout Test", width=400, height=350, center=True, resizable=True)
class MainWindow(ryukon.Window):

    # Виджеты без x/y — расставляются автоматически
    layout = ryukon.VLayout(padding=15, gap=10)

    @ryukon.label(text="Привет, Ryukon!")
    def greeting(self): ...

    @ryukon.input(placeholder="Введи имя...")
    async def on_type(self, value: str):
        self.get("greeting").text = value or "Привет, Ryukon!"

    @ryukon.checkbox(label="Тёмная тема")
    async def on_theme(self, checked: bool):
        print(f"Тёмная тема: {checked}")

    @ryukon.dropdown(options=["Русский", "English", "日本語"])
    async def on_lang(self, value: str, index: int):
        print(f"Язык: {value}")

    @ryukon.slider(min=0, max=100, value=50)
    async def on_volume(self, value: int):
        print(f"Громкость: {value}")

    # Этот виджет с явными координатами — layout его не трогает
    @ryukon.button(label="ОК", x=300, y=290, width=80, height=30)
    async def on_ok(self):
        print("ОК!")

    async def on_ready(self):
        print("Окно готово!")

app.run()