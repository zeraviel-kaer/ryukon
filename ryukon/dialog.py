from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

user32 = ctypes.windll.user32
comdlg32 = ctypes.windll.comdlg32


MB_OK = 0x0000
MB_YESNO = 0x0004

MB_ICONINFO = 0x0040
MB_ICONWARNING = 0x0030
MB_ICONERROR = 0x0010
MB_ICONQUESTION = 0x0020

IDYES = 6


OFN_FILEMUSTEXIST = 0x00001000
OFN_EXPLORER = 0x00080000


class OPENFILENAME(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wt.DWORD),
        ("hwndOwner", wt.HWND),
        ("hInstance", wt.HINSTANCE),
        ("lpstrFilter", wt.LPCWSTR),
        ("lpstrCustomFilter", wt.LPWSTR),
        ("nMaxCustFilter", wt.DWORD),
        ("nFilterIndex", wt.DWORD),

        ("lpstrFile", ctypes.POINTER(wt.WCHAR)),
        ("nMaxFile", wt.DWORD),

        ("lpstrFileTitle", ctypes.POINTER(wt.WCHAR)),
        ("nMaxFileTitle", wt.DWORD),

        ("lpstrInitialDir", wt.LPCWSTR),
        ("lpstrTitle", wt.LPCWSTR),
        ("Flags", wt.DWORD),

        ("nFileOffset", wt.WORD),
        ("nFileExtension", wt.WORD),

        ("lpstrDefExt", wt.LPCWSTR),
        ("lCustData", wt.LPARAM),
        ("lpfnHook", ctypes.c_void_p),
        ("lpTemplateName", wt.LPCWSTR),

        ("pvReserved", ctypes.c_void_p),
        ("dwReserved", wt.DWORD),
        ("FlagsEx", wt.DWORD),
    ]


class CHOOSECOLOR(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wt.DWORD),
        ("hwndOwner", wt.HWND),
        ("hInstance", wt.HWND),
        ("rgbResult", wt.COLORREF),
        ("lpCustColors", ctypes.POINTER(wt.COLORREF)),
        ("Flags", wt.DWORD),
        ("lCustData", wt.LPARAM),
        ("lpfnHook", ctypes.c_void_p),
        ("lpTemplateName", wt.LPCWSTR),
    ]


def confirm(
    message: str,
    title: str = "Подтверждение",
    *,
    icon: str = "question",
) -> bool:
    icons = {
        "question": MB_ICONQUESTION,
        "info": MB_ICONINFO,
        "warning": MB_ICONWARNING,
        "error": MB_ICONERROR,
    }

    result = user32.MessageBoxW(
        None,
        message,
        title,
        MB_YESNO | icons.get(icon, MB_ICONQUESTION),
    )

    return result == IDYES


def alert(
    message: str,
    title: str = "Сообщение",
    *,
    icon: str = "info",
) -> None:
    icons = {
        "question": MB_ICONQUESTION,
        "info": MB_ICONINFO,
        "warning": MB_ICONWARNING,
        "error": MB_ICONERROR,
    }

    user32.MessageBoxW(
        None,
        message,
        title,
        MB_OK | icons.get(icon, MB_ICONINFO),
    )


def ask_file(
    title: str = "Открыть файл",
    *,
    filters: str = "Все файлы\0*.*\0\0",
    initial_dir: str | None = None,
) -> str | None:

    buffer = ctypes.create_unicode_buffer(4096)

    ofn = OPENFILENAME()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAME)

    ofn.lpstrFilter = filters

    ofn.lpstrFile = buffer
    ofn.nMaxFile = len(buffer)

    ofn.lpstrTitle = title
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_EXPLORER

    if initial_dir:
        ofn.lpstrInitialDir = initial_dir

    if comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return buffer.value

    return None


def save_file(
    title: str = "Сохранить файл",
    *,
    filters: str = "Все файлы\0*.*\0\0",
    default_ext: str | None = None,
) -> str | None:

    buffer = ctypes.create_unicode_buffer(4096)

    ofn = OPENFILENAME()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAME)

    ofn.lpstrFilter = filters

    ofn.lpstrFile = buffer
    ofn.nMaxFile = len(buffer)

    ofn.lpstrTitle = title
    ofn.Flags = OFN_EXPLORER

    if default_ext:
        ofn.lpstrDefExt = default_ext

    if comdlg32.GetSaveFileNameW(ctypes.byref(ofn)):
        return buffer.value

    return None


def ask_color(
    initial: tuple[int, int, int] | None = None,
) -> tuple[int, int, int] | None:

    custom_colors = (wt.COLORREF * 16)()

    cc = CHOOSECOLOR()
    cc.lStructSize = ctypes.sizeof(CHOOSECOLOR)
    cc.lpCustColors = custom_colors
    cc.Flags = 0x0003

    if initial:
        r, g, b = initial
        cc.rgbResult = r | (g << 8) | (b << 16)

    if comdlg32.ChooseColorW(ctypes.byref(cc)):
        rgb = cc.rgbResult

        return (
            rgb & 0xFF,
            (rgb >> 8) & 0xFF,
            (rgb >> 16) & 0xFF,
        )

    return None