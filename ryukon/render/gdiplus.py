from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

gdiplus = ctypes.windll.gdiplus  # type: ignore

SmoothingModeAntiAlias       = 4
TextRenderingHintAntiAlias   = 4
TextRenderingHintClearType   = 5
UnitPixel                    = 2
FontStyleRegular             = 0
FontStyleBold                = 1
FontStyleItalic              = 2
FontStyleBoldItalic          = 3
StringAlignmentNear          = 0
StringAlignmentCenter        = 1
StringAlignmentFar           = 2
FillModeAlternate            = 0


class GdiplusStartupInput(ctypes.Structure):
    _fields_ = [
        ("GdiplusVersion",           ctypes.c_uint32),
        ("DebugEventCallback",       ctypes.c_void_p),
        ("SuppressBackgroundThread", ctypes.c_int),
        ("SuppressExternalCodecs",   ctypes.c_int),
    ]


class RectF(ctypes.Structure):
    _fields_ = [
        ("X", ctypes.c_float), ("Y", ctypes.c_float),
        ("Width", ctypes.c_float), ("Height", ctypes.c_float),
    ]


def _fn(name, argtypes, restype=ctypes.c_int):
    f = getattr(gdiplus, name)
    f.argtypes = argtypes
    f.restype  = restype
    return f


_GdiplusStartup  = _fn("GdiplusStartup", [ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(GdiplusStartupInput), ctypes.c_void_p])
_GdiplusShutdown = _fn("GdiplusShutdown", [ctypes.c_size_t])

_GdipCreateFromHDC          = _fn("GdipCreateFromHDC", [wt.HDC, ctypes.POINTER(ctypes.c_void_p)])
_GdipDeleteGraphics         = _fn("GdipDeleteGraphics", [ctypes.c_void_p])
_GdipSetSmoothingMode       = _fn("GdipSetSmoothingMode", [ctypes.c_void_p, ctypes.c_int])
_GdipSetTextRenderingHint   = _fn("GdipSetTextRenderingHint", [ctypes.c_void_p, ctypes.c_int])

_GdipCreateSolidFill = _fn("GdipCreateSolidFill", [ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)])
_GdipDeleteBrush     = _fn("GdipDeleteBrush", [ctypes.c_void_p])
_GdipSetSolidFillColor = _fn("GdipSetSolidFillColor", [ctypes.c_void_p, ctypes.c_uint32])

_GdipCreatePen1 = _fn("GdipCreatePen1", [ctypes.c_uint32, ctypes.c_float, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)])
_GdipDeletePen  = _fn("GdipDeletePen", [ctypes.c_void_p])

_GdipCreatePath        = _fn("GdipCreatePath", [ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)])
_GdipDeletePath        = _fn("GdipDeletePath", [ctypes.c_void_p])
_GdipAddPathArc        = _fn("GdipAddPathArc", [ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float])
_GdipClosePathFigure   = _fn("GdipClosePathFigure", [ctypes.c_void_p])
_GdipFillPath          = _fn("GdipFillPath", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p])
_GdipDrawPath          = _fn("GdipDrawPath", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p])

_GdipFillRectangle = _fn("GdipFillRectangle", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float])
_GdipFillEllipse   = _fn("GdipFillEllipse", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float])
_GdipDrawLine      = _fn("GdipDrawLine", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float])

_GdipCreateFontFamilyFromName = _fn("GdipCreateFontFamilyFromName", [ctypes.c_wchar_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)])
_GdipDeleteFontFamily         = _fn("GdipDeleteFontFamily", [ctypes.c_void_p])
_GdipCreateFont               = _fn("GdipCreateFont", [ctypes.c_void_p, ctypes.c_float, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)])
_GdipDeleteFont               = _fn("GdipDeleteFont", [ctypes.c_void_p])

_GdipCreateStringFormat      = _fn("GdipCreateStringFormat", [ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)])
_GdipDeleteStringFormat      = _fn("GdipDeleteStringFormat", [ctypes.c_void_p])
_GdipSetStringFormatAlign    = _fn("GdipSetStringFormatAlign", [ctypes.c_void_p, ctypes.c_int])
_GdipSetStringFormatLineAlign = _fn("GdipSetStringFormatLineAlign", [ctypes.c_void_p, ctypes.c_int])

_GdipDrawString = _fn("GdipDrawString", [
    ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int, ctypes.c_void_p,
    ctypes.POINTER(RectF), ctypes.c_void_p, ctypes.c_void_p,
])

_GdipLoadImageFromFile      = _fn("GdipLoadImageFromFile", [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p)])
_GdipCreateBitmapFromStream = _fn("GdipCreateBitmapFromStream", [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)])
_GdipDisposeImage           = _fn("GdipDisposeImage", [ctypes.c_void_p])
_GdipGetImageDimension      = _fn("GdipGetImageDimension", [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)])
_GdipImageGetFrameCount     = _fn("GdipImageGetFrameCount", [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)])
_GdipImageSelectActiveFrame = _fn("GdipImageSelectActiveFrame", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint])
_GdipGetPropertyItemSize    = _fn("GdipGetPropertyItemSize", [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)])
_GdipGetPropertyItem        = _fn("GdipGetPropertyItem", [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p])

_GdipDrawImageRectRectI = _fn("GdipDrawImageRectRectI", [
    ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
])

_GdipCreateImageAttributes         = _fn("GdipCreateImageAttributes", [ctypes.POINTER(ctypes.c_void_p)])
_GdipDisposeImageAttributes        = _fn("GdipDisposeImageAttributes", [ctypes.c_void_p])
_GdipSetImageAttributesColorMatrix = _fn("GdipSetImageAttributesColorMatrix", [
    ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
])

_GdipSetClipPath = _fn("GdipSetClipPath", [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int])
_GdipResetClip   = _fn("GdipResetClip", [ctypes.c_void_p])

_shlwapi = ctypes.windll.shlwapi  # type: ignore
_shlwapi.SHCreateMemStream.restype  = ctypes.c_void_p
_shlwapi.SHCreateMemStream.argtypes = [ctypes.c_void_p, ctypes.c_uint]


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32), ("Data2", ctypes.c_uint16), ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_uint8 * 8),
    ]


class PropertyItem(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32), ("length", ctypes.c_uint32),
        ("type", ctypes.c_uint16), ("value", ctypes.c_void_p),
    ]


# FrameDimensionTime — стандартный GUID GDI+ для кадров анимации (используется для GIF).
FRAME_DIMENSION_TIME = GUID(0x6aedbd6d, 0x3fb5, 0x418a,
                             (ctypes.c_uint8 * 8)(0x83, 0xa6, 0x7f, 0x45, 0x22, 0x9d, 0xc8, 0x72))
_PROPERTY_TAG_FRAME_DELAY = 0x5100

_token = None


def ensure_started() -> None:
    global _token
    if _token is not None:
        return
    token = ctypes.c_size_t(0)
    inp   = GdiplusStartupInput(1, None, 0, 0)
    _GdiplusStartup(ctypes.byref(token), ctypes.byref(inp), None)
    _token = token.value


def argb(r: int, g: int, b: int, a: int = 255) -> int:
    return ((a & 0xFF) << 24) | ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF)


def load_image_from_file(path: str):
    """Загружает PNG/JPG/BMP/GIF из файла. Возвращает хендл GpImage или None."""
    ensure_started()
    handle = ctypes.c_void_p()
    status = _GdipLoadImageFromFile(path, ctypes.byref(handle))
    return handle if status == 0 and handle else None


def load_image_from_bytes(data: bytes):
    """Загружает изображение из байтов в памяти (например, скачанное по URL).

    Поток, отдаваемый SHCreateMemStream, намеренно не освобождается — GDI+
    может подгружать кадры лениво, и закрытие потока раньше времени испортит
    изображение. Цена — небольшая утечка COM-объекта на каждое загруженное
    изображение, что приемлемо для редко создаваемых картинок фона/виджетов.
    """
    ensure_started()
    buf    = ctypes.create_string_buffer(data, len(data))
    stream = _shlwapi.SHCreateMemStream(buf, len(data))
    if not stream:
        return None
    handle = ctypes.c_void_p()
    status = _GdipCreateBitmapFromStream(stream, ctypes.byref(handle))
    return handle if status == 0 and handle else None


def dispose_image(handle) -> None:
    if handle:
        _GdipDisposeImage(handle)


def get_image_size(handle) -> tuple[float, float]:
    w, h = ctypes.c_float(0), ctypes.c_float(0)
    _GdipGetImageDimension(handle, ctypes.byref(w), ctypes.byref(h))
    return w.value, h.value


def get_frame_count(handle) -> int:
    count = ctypes.c_uint(0)
    _GdipImageGetFrameCount(handle, ctypes.byref(FRAME_DIMENSION_TIME), ctypes.byref(count))
    return max(1, count.value)


def select_frame(handle, index: int) -> None:
    _GdipImageSelectActiveFrame(handle, ctypes.byref(FRAME_DIMENSION_TIME), index)


def get_frame_delays(handle, frame_count: int) -> list[float]:
    """Возвращает задержки кадров GIF в секундах (по тегу PropertyTagFrameDelay)."""
    size = ctypes.c_uint(0)
    if _GdipGetPropertyItemSize(handle, _PROPERTY_TAG_FRAME_DELAY, ctypes.byref(size)) != 0 or size.value == 0:
        return [0.1] * frame_count
    buf = (ctypes.c_byte * size.value)()
    if _GdipGetPropertyItem(handle, _PROPERTY_TAG_FRAME_DELAY, size.value, buf) != 0:
        return [0.1] * frame_count
    item  = ctypes.cast(buf, ctypes.POINTER(PropertyItem)).contents
    count = item.length // 4
    if count <= 0 or not item.value:
        return [0.1] * frame_count
    raw    = ctypes.cast(item.value, ctypes.POINTER(ctypes.c_uint32 * count)).contents
    delays = [max(0.02, v / 100.0) for v in raw]  # значения в 1/100 секунды
    if len(delays) < frame_count:
        delays += [delays[-1] if delays else 0.1] * (frame_count - len(delays))
    return delays[:frame_count]


class Graphics:
    """Тонкая обёртка над GpGraphics для рисования в HDC."""

    def __init__(self, hdc) -> None:
        ensure_started()
        handle = ctypes.c_void_p()
        _GdipCreateFromHDC(hdc, ctypes.byref(handle))
        self._h = handle
        _GdipSetSmoothingMode(self._h, SmoothingModeAntiAlias)
        _GdipSetTextRenderingHint(self._h, TextRenderingHintClearType)

    def close(self) -> None:
        if self._h:
            _GdipDeleteGraphics(self._h)
            self._h = None

    def fill_rect(self, x, y, w, h, color: int) -> None:
        brush = ctypes.c_void_p()
        _GdipCreateSolidFill(color, ctypes.byref(brush))
        _GdipFillRectangle(self._h, brush, float(x), float(y), float(w), float(h))
        _GdipDeleteBrush(brush)

    def fill_ellipse(self, x, y, w, h, color: int) -> None:
        brush = ctypes.c_void_p()
        _GdipCreateSolidFill(color, ctypes.byref(brush))
        _GdipFillEllipse(self._h, brush, float(x), float(y), float(w), float(h))
        _GdipDeleteBrush(brush)

    def draw_line(self, x1, y1, x2, y2, color: int, width: float = 2.0) -> None:
        pen = ctypes.c_void_p()
        _GdipCreatePen1(color, width, UnitPixel, ctypes.byref(pen))
        _GdipDrawLine(self._h, pen, float(x1), float(y1), float(x2), float(y2))
        _GdipDeletePen(pen)

    def _round_rect_path(self, x, y, w, h, r):
        path = ctypes.c_void_p()
        _GdipCreatePath(FillModeAlternate, ctypes.byref(path))
        r = max(0.0, min(float(r), w / 2.0, h / 2.0))
        d = r * 2
        if d <= 0.01:
            _GdipAddPathArc(path, x, y, 0.01, 0.01, 180, 90)
            _GdipAddPathArc(path, x + w, y, 0.01, 0.01, 270, 90)
            _GdipAddPathArc(path, x + w, y + h, 0.01, 0.01, 0, 90)
            _GdipAddPathArc(path, x, y + h, 0.01, 0.01, 90, 90)
        else:
            _GdipAddPathArc(path, x, y, d, d, 180, 90)
            _GdipAddPathArc(path, x + w - d, y, d, d, 270, 90)
            _GdipAddPathArc(path, x + w - d, y + h - d, d, d, 0, 90)
            _GdipAddPathArc(path, x, y + h - d, d, d, 90, 90)
        _GdipClosePathFigure(path)
        return path

    def fill_round_rect(self, x, y, w, h, r, color: int) -> None:
        path  = self._round_rect_path(float(x), float(y), float(w), float(h), r)
        brush = ctypes.c_void_p()
        _GdipCreateSolidFill(color, ctypes.byref(brush))
        _GdipFillPath(self._h, brush, path)
        _GdipDeleteBrush(brush)
        _GdipDeletePath(path)

    def stroke_round_rect(self, x, y, w, h, r, color: int, width: float = 1.0) -> None:
        path = self._round_rect_path(float(x) + width / 2, float(y) + width / 2,
                                      float(w) - width, float(h) - width, r)
        pen = ctypes.c_void_p()
        _GdipCreatePen1(color, width, UnitPixel, ctypes.byref(pen))
        _GdipDrawPath(self._h, pen, path)
        _GdipDeletePen(pen)
        _GdipDeletePath(path)

    def draw_image(self, bitmap, x, y, w, h, native_w, native_h, *,
                    fit: str = "cover", radius: float = 0, opacity: float = 1.0) -> None:
        if not bitmap or w <= 0 or h <= 0:
            return
        x, y, w, h = float(x), float(y), float(w), float(h)

        clip_path = None
        if radius > 0:
            clip_path = self._round_rect_path(x, y, w, h, radius)
            _GdipSetClipPath(self._h, clip_path, 0)  # CombineModeReplace

        dst_x, dst_y, dst_w, dst_h = x, y, w, h
        src_x, src_y, src_w, src_h = 0.0, 0.0, native_w, native_h
        if native_w > 0 and native_h > 0 and w > 0 and h > 0:
            src_ratio, dst_ratio = native_w / native_h, w / h
            if fit == "cover":
                if src_ratio > dst_ratio:
                    src_w = native_h * dst_ratio
                    src_x = (native_w - src_w) / 2
                else:
                    src_h = native_w / dst_ratio
                    src_y = (native_h - src_h) / 2
            elif fit == "contain":
                if src_ratio > dst_ratio:
                    dst_h = w / src_ratio
                    dst_y = y + (h - dst_h) / 2
                else:
                    dst_w = h * src_ratio
                    dst_x = x + (w - dst_w) / 2
            # fit == "stretch" — оставляем как есть (искажает пропорции).

        attrs = None
        if opacity < 0.999:
            attrs = ctypes.c_void_p()
            _GdipCreateImageAttributes(ctypes.byref(attrs))
            opacity = max(0.0, min(1.0, opacity))
            matrix = (ctypes.c_float * 25)(
                1, 0, 0, 0, 0,
                0, 1, 0, 0, 0,
                0, 0, 1, 0, 0,
                0, 0, 0, opacity, 0,
                0, 0, 0, 0, 1,
            )
            _GdipSetImageAttributesColorMatrix(attrs, 0, 1, matrix, None, 0)

        _GdipDrawImageRectRectI(
            self._h, bitmap,
            int(dst_x), int(dst_y), int(dst_w), int(dst_h),
            int(src_x), int(src_y), int(src_w), int(src_h),
            UnitPixel, attrs, None, None,
        )

        if attrs:
            _GdipDisposeImageAttributes(attrs)
        if clip_path:
            _GdipResetClip(self._h)
            _GdipDeletePath(clip_path)

    def draw_text(self, text: str, x, y, w, h, *, family: str, size: float,
                   bold: bool, italic: bool, color: int, align: str = "center") -> None:
        ff = ctypes.c_void_p()
        if _GdipCreateFontFamilyFromName(family, None, ctypes.byref(ff)) != 0:
            _GdipCreateFontFamilyFromName("Segoe UI", None, ctypes.byref(ff))
        style = FontStyleRegular
        if bold and italic: style = FontStyleBoldItalic
        elif bold:           style = FontStyleBold
        elif italic:          style = FontStyleItalic
        font = ctypes.c_void_p()
        _GdipCreateFont(ff, float(size), style, UnitPixel, ctypes.byref(font))

        fmt = ctypes.c_void_p()
        _GdipCreateStringFormat(0, 0, ctypes.byref(fmt))
        h_align = {"left": StringAlignmentNear, "center": StringAlignmentCenter, "right": StringAlignmentFar}.get(align, StringAlignmentCenter)
        _GdipSetStringFormatAlign(fmt, h_align)
        _GdipSetStringFormatLineAlign(fmt, StringAlignmentCenter)

        brush = ctypes.c_void_p()
        _GdipCreateSolidFill(color, ctypes.byref(brush))

        rect = RectF(float(x), float(y), float(w), float(h))
        _GdipDrawString(self._h, text, -1, font, ctypes.byref(rect), fmt, brush)

        _GdipDeleteBrush(brush)
        _GdipDeleteStringFormat(fmt)
        _GdipDeleteFont(font)
        _GdipDeleteFontFamily(ff)
