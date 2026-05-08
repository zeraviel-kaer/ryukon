import warnings

class RyukonWarning(UserWarning):
    pass

class RyukonKeyError(KeyError):
    pass

def _custom_warning(message, category, filename, lineno, file=None, line=None):
    if category == RyukonWarning:
        print(f"[ryukon.config] ⚠️  {message}")
    else:
        warnings._showwarning_orig(message, category, filename, lineno, file, line)

warnings.showwarning = _custom_warning