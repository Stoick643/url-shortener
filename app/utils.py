import hashlib
import io
import base64
import random
import string

import qrcode

from app.config import settings

BASE62_CHARS = string.ascii_letters + string.digits  # A-Za-z0-9


def generate_short_code(length: int = None) -> str:
    """Generate a random Base62 short code."""
    if length is None:
        length = settings.SHORT_CODE_LENGTH
    return "".join(random.choices(BASE62_CHARS, k=length))


def hash_ip(ip: str) -> str:
    """SHA-256 hash of an IP address."""
    return hashlib.sha256(ip.encode()).hexdigest()


def generate_qr_code_bytes(url: str) -> bytes:
    """Generate a QR code PNG as bytes."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def generate_qr_code_base64(url: str) -> str:
    """Generate a QR code as a base64-encoded PNG string."""
    png_bytes = generate_qr_code_bytes(url)
    return base64.b64encode(png_bytes).decode("utf-8")


def build_short_url(short_code: str) -> str:
    """Build the full short URL from a code."""
    base = settings.BASE_URL.rstrip("/")
    return f"{base}/{short_code}"
