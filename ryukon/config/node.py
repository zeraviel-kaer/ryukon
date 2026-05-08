import difflib
import warnings
from ryukon.config.exceptions import RyukonWarning, RyukonKeyError

class ConfigNode:
    def __init__(self, data: dict, locale=None):
        self._data = data
        self._locale = locale

    def __getattr__(self, key: str):
        if key not in self._data:
            matches = difflib.get_close_matches(key, self._data.keys(), n=1, cutoff=0.6)
            if matches:
                msg = self._locale.get("key_not_found", key=key, match=matches[0]) if self._locale else f"Key '{key}' not found, using '{matches[0]}'"
                warnings.warn(msg, RyukonWarning)
                key = matches[0]
            else:
                msg = self._locale.get("key_missing", key=key) if self._locale else f"Key '{key}' not found"
                raise RyukonKeyError(msg)

        value = self._data[key]
        if isinstance(value, dict):
            return ConfigNode(value, self._locale)
        return value