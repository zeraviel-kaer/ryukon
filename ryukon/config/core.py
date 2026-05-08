import difflib
import warnings
from ryukon.config.node import ConfigNode
from ryukon.config.backends.json import JsonBackend
from ryukon.config.exceptions import RyukonWarning, RyukonKeyError
from ryukon.config.locale import Locale


class Config:
    def __init__(self, path: str, lang: str = "en", auto_load: bool = True):
        self.path = path
        self._data = {}
        self._locale = Locale(lang)
        self._backend = JsonBackend(path)

        if auto_load:
            self.load()

    def load(self):
        self._data = self._backend.read()

    def save(self):
        self._backend.write(self._data)

    def _fuzzy_key(self, data: dict, key: str) -> str:
        if key not in data:
            matches = difflib.get_close_matches(key, data.keys(), n=1, cutoff=0.6)
            if matches:
                msg = self._locale.get("key_not_found", key=key, match=matches[0])
                warnings.warn(msg, RyukonWarning)
                return matches[0]
            raise RyukonKeyError(self._locale.get("key_missing", key=key))
        return key

    def get(self, path: str, default=None):
        keys = path.split(".")
        data = self._data
        for key in keys:
            if isinstance(data, dict):
                try:
                    key = self._fuzzy_key(data, key)
                except RyukonKeyError:
                    return default
                data = data[key]
            else:
                return default
        return data

    def set(self, path: str, value):
        keys = path.split(".")
        data = self._data
        for key in keys[:-1]:
            if key not in data:
                data[key] = {}
            data = data[key]
        last_key = self._fuzzy_key(data, keys[-1]) if keys[-1] in data else keys[-1]
        data[last_key] = value

    def delete(self, path: str):
        keys = path.split(".")
        data = self._data
        for key in keys[:-1]:
            data = data[key]
        last_key = self._fuzzy_key(data, keys[-1])
        del data[last_key]

    def __getattr__(self, key: str):
        return ConfigNode(self._data, self._locale).__getattr__(key)