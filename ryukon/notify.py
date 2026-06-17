from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

shell32 = ctypes.windll.shell32  # type: ignore

NIF_INFO    = 0x00000010
NIM_MODIFY  = 0x01
NIIF_INFO    = 0x00000001
NIIF_WARNING = 0x00000002
NIIF_ERROR   = 0x00000003
NIIF_NONE    = 0x00000000


class NOTIFYICONDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize",            wt.DWORD),
        ("hWnd",              wt.HWND),
        ("uID",               wt.UINT),
        ("uFlags",            wt.UINT),
        ("uCallbackMessage",  wt.UINT),
        ("hIcon",             wt.HICON),
        ("szTip",             ctypes.c_wchar * 128),
        ("dwState",           wt.DWORD),
        ("dwStateMask",       wt.DWORD),
        ("szInfo",            ctypes.c_wchar * 256),
        ("uTimeout",          wt.UINT),
        ("szInfoTitle",       ctypes.c_wchar * 64),
        ("dwInfoFlags",       wt.DWORD),
    ]


_ICONS = {
    "info":    NIIF_INFO,
    "warning": NIIF_WARNING,
    "error":   NIIF_ERROR,
    "none":    NIIF_NONE,
}


def notify(
    title:   str,
    message: str,
    *,
    icon:    str  = "info",   # "info", "warning", "error", "none"
    tray:    object = None,   # ryukon.Tray — нужен для показа уведомления
) -> None:
    """Показывает toast-уведомление через иконку трея.

    ryukon.notify("Заголовок", "Текст", icon="info", tray=tray)
    """
    if tray is None or tray._nid is None:
        return

    nid = tray._nid
    nid.uFlags     |= NIF_INFO
    nid.szInfo      = message[:255]
    nid.szInfoTitle = title[:63]
    nid.dwInfoFlags = _ICONS.get(icon, NIIF_INFO)
    shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))