from ryukon.config.backends.json.reader import JsonBackend
from pathlib import Path

LOCALES_DIR = Path(__file__).parent / "locales"

class Locale:
    def __init__(self, lang: str = "en"):
        path = LOCALES_DIR / f"{lang}.json"
        if not path.exists():
            path = LOCALES_DIR / "en.json"
        self._data = JsonBackend(str(path)).read()

    def get(self, message_key: str, **kwargs) -> str:
        text = self._data.get(message_key, message_key)
        return text.format(**kwargs)