"""
QR Code generation helpers behind the QR Code tool. Styling (color /
module shape) uses qrcode's StyledPilImage — a real, functional
customization, not decorative — while framing (border/label around the
preview) is applied client-side in CSS, so it is preview-only and not
baked into the downloaded image.
"""
import io

import qrcode
import qrcode.constants
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer, RoundedModuleDrawer, SquareModuleDrawer
from PIL import Image

from .pdf_tools import ToolError

MODULE_DRAWERS = {
    "square": SquareModuleDrawer,
    "rounded": RoundedModuleDrawer,
    "circle": CircleModuleDrawer,
}


def _valid_hex_color(value):
    if not isinstance(value, str) or not value.startswith("#") or len(value) not in (4, 7):
        return False
    try:
        int(value[1:], 16)
        return True
    except ValueError:
        return False


def build_image(data, fg_color="#000000", bg_color="#ffffff", shape="square"):
    if not data:
        raise ToolError("กรุณากรอกข้อมูลสำหรับสร้าง QR Code")
    if len(data) > 2000:
        raise ToolError("ข้อมูลยาวเกินไป (สูงสุด 2000 ตัวอักษร)")

    fg = fg_color if _valid_hex_color(fg_color) else "#000000"
    bg = bg_color if _valid_hex_color(bg_color) else "#ffffff"
    drawer_cls = MODULE_DRAWERS.get(shape, SquareModuleDrawer)

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
    qr.add_data(data)
    qr.make(fit=True)

    try:
        styled = qr.make_image(image_factory=StyledPilImage, module_drawer=drawer_cls(), fill_color=fg, back_color=bg)
        return styled.get_image().convert("RGB")
    except Exception as exc:
        raise ToolError("ไม่สามารถสร้าง QR Code ได้ — กรุณาตรวจสอบข้อมูลที่กรอก") from exc


def image_to_bytes(image, fmt="png"):
    buffer = io.BytesIO()
    fmt = fmt.lower()
    if fmt == "jpg":
        fmt = "jpeg"
    if fmt not in ("png", "jpeg"):
        fmt = "png"
    image.save(buffer, format=fmt.upper())
    buffer.seek(0)
    return buffer, ("image/jpeg" if fmt == "jpeg" else "image/png")
