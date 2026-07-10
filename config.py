"""
Configuration globale de l'application.
L'URL publique est codée ici en dur (pas affichée/éditable dans l'interface),
conformément à la demande : elle sert uniquement à construire les liens des QR codes.
"""

APP_URL = "https://checkbus.streamlit.app"

# Palette de couleurs utilisée par styles.py
PRIMARY_COLOR = "#2563eb"
PRIMARY_DARK = "#1e3a8a"
ACCENT_COLOR = "#f59e0b"
SUCCESS_COLOR = "#16a34a"
DANGER_COLOR = "#dc2626"

GROUP_TYPES = ["famille", "couple", "amis"]
GROUP_TYPE_LABELS = {"famille": "👨‍👩‍👧‍👦 Famille", "couple": "💑 Couple", "amis": "🧑‍🤝‍🧑 Amis"}
