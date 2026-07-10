"""Génération de QR codes pour l'accès rapide des clients."""
import io
import qrcode


def build_client_link(app_url: str, token: str) -> str:
    app_url = (app_url or "").rstrip("/")
    if not app_url:
        # Lien relatif si l'URL de l'app n'a pas encore été configurée
        return f"?token={token}"
    return f"{app_url}/Espace_Client?token={token}"


def make_qr_image_bytes(data: str) -> bytes:
    img = qrcode.make(data, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
