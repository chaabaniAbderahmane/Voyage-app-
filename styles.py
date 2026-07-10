"""Injection CSS pour une interface plus soignée et professionnelle."""
import streamlit as st
from config import PRIMARY_COLOR, PRIMARY_DARK, ACCENT_COLOR


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
        html, body, [class*="css"], .stMarkdown, .stText {{
            font-family: 'Poppins', sans-serif;
        }}

        .hero-banner {{
            background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_DARK} 100%);
            color: white;
            border-radius: 20px;
            padding: 2.2rem 1.5rem;
            text-align: center;
            margin-bottom: 1.3rem;
            box-shadow: 0 10px 30px rgba(37,99,235,0.25);
        }}
        .hero-banner h1 {{ font-size: 2.1rem; margin: 0; }}
        .hero-banner p {{ opacity: 0.92; margin-top: 0.35rem; }}

        .notif-banner {{
            background: #fff7ed;
            border: 1px solid #fdba74;
            border-radius: 14px;
            padding: 0.85rem 1.2rem;
            margin-bottom: 1rem;
            font-size: 0.98rem;
        }}
        .notif-banner b {{ color: {ACCENT_COLOR}; }}

        .success-chip {{
            display:inline-block; background:#dcfce7; color:#166534;
            padding: 0.15rem 0.7rem; border-radius: 999px; font-size: 0.82rem; font-weight:600;
        }}
        .pending-chip {{
            display:inline-block; background:#fef3c7; color:#92400e;
            padding: 0.15rem 0.7rem; border-radius: 999px; font-size: 0.82rem; font-weight:600;
        }}

        div[data-testid="stMetric"] {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 0.75rem 1rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        }}

        .stButton>button {{
            border-radius: 10px;
            font-weight: 600;
        }}
        .stButton>button[kind="primary"] {{
            background: linear-gradient(135deg, {PRIMARY_COLOR}, {PRIMARY_DARK});
            border: none;
        }}

        div[data-testid="stChatMessage"] {{
            border-radius: 14px;
        }}

        hr {{ margin: 0.6rem 0 1.1rem 0; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
