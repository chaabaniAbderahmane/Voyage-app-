"""Génération de QR codes pour l'accès rapide des clients."""
import io
import qrcode
from config import APP_URL


def build_client_link(token: str) -> str:
    """L'URL publique est fixée dans config.py (non modifiable depuis l'interface)."""
    return f"{APP_URL.rstrip('/')}/?token={token}"


def make_qr_image_bytes(data: str) -> bytes:
    img = qrcode.make(data, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
