from __future__ import annotations

import json
from pathlib import Path

import requests
import streamlit as st


API_URL = st.sidebar.text_input("Local API", "http://127.0.0.1:8000")

st.set_page_config(page_title="AirGap — private meeting intelligence", page_icon="◈", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#f5f7fb; --muted:#8d96a8; --line:#263044; --panel:#111827; --accent:#9cffc7; --violet:#a991ff; }
    .stApp { background: radial-gradient(circle at 84% 2%, #202f4d 0, #0a0f19 34%, #070b12 72%); color:var(--ink); font-family:'DM Sans',sans-serif; }
    [data-testid="stSidebar"] { background:#0b101a; border-right:1px solid var(--line); }
    h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.04em; }
    .hero { padding:3.5rem 0 2rem; max-width:950px; }
    .eyebrow { color:var(--accent); font-size:.78rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }
    .hero h1 { font-size:clamp(3rem,7vw,6.2rem); line-height:.95; margin:.7rem 0 1.1rem; }
    .hero h1 span { color:var(--accent); }
    .hero p { color:var(--muted); font-size:1.15rem; max-width:650px; line-height:1.6; }
    .pill { display:inline-block; border:1px solid #385546; background:#11231d; color:var(--accent); border-radius:999px; padding:.38rem .75rem; font-size:.8rem; margin:.25rem .25rem 0 0; }
    .card { background:rgba(17,24,39,.78); border:1px solid var(--line); border-radius:20px; padding:1.35rem; height:100%; }
    .metric { font-size:2rem; font-family:'Space Grotesk'; color:var(--ink); }
    .muted { color:var(--muted); font-size:.88rem; }
    .feature { min-height:145px; }
    div[data-testid="stFileUploader"] { border:1px dashed #49617e; border-radius:16px; padding:.4rem; background:#0d1523; }
    .stButton button { border-radius:10px; border:1px solid #3b506b; background:#162235; color:var(--ink); }
    .stButton button:hover { border-color:var(--accent); color:var(--accent); }
    footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_get(path: str) -> object | None:
    try:
        response = requests.get(f"{API_URL}{path}", timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def upload_file(uploaded_file: object) -> dict[str, object] | None:
    try:
        response = requests.post(
            f"{API_URL}/api/meetings",
            files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        st.error(f"Не удалось загрузить файл: {error}")
        return None


with st.sidebar:
    st.markdown("## ◈ AirGap")
    st.caption("Private meeting intelligence")
    st.divider()
    page = st.radio("Навигация", ["Обзор", "Новая встреча", "История", "О продукте"], label_visibility="collapsed")
    st.divider()
    st.markdown("<span class='pill'>● LOCAL ONLY</span>", unsafe_allow_html=True)
    st.caption("Аудио и текст не покидают устройство")


if page == "Обзор":
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">AirGap / meeting intelligence</div>
          <h1>Встречи.<br><span>Поняты.</span></h1>
          <p>Локальная AI-платформа, которая превращает разговоры команды в решения, задачи и ясный следующий шаг — без отправки данных в облако.</p>
          <span class="pill">RU</span><span class="pill">KZ</span><span class="pill">EN</span><span class="pill">OFFLINE-FIRST</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    meetings = api_get("/api/meetings")
    count = len(meetings) if isinstance(meetings, list) else 0
    cols = st.columns(3)
    for column, value, label in zip(cols, [count, "100%", "0"], ["Встреч сохранено", "Данные локально", "Облачных запросов"]):
        with column:
            st.markdown(f"<div class='card'><div class='metric'>{value}</div><div class='muted'>{label}</div></div>", unsafe_allow_html=True)
    st.markdown("### Что умеет AirGap")
    feature_cols = st.columns(3)
    features = [("01 / TRANSCRIBE", "Точная расшифровка", "Локальный Whisper распознаёт русскую, казахскую и английскую речь."), ("02 / UNDERSTAND", "Смысл вместо шума", "Summary, решения, риски и открытые вопросы из каждой встречи."), ("03 / ACT", "Команда действует", "Action items с ответственными, сроками и экспортом в привычные инструменты.")]
    for column, (tag, title, text) in zip(feature_cols, features):
        with column:
            st.markdown(f"<div class='card feature'><div class='eyebrow'>{tag}</div><h3>{title}</h3><div class='muted'>{text}</div></div>", unsafe_allow_html=True)
    st.markdown("### Быстрый старт")
    if st.button("＋ Загрузить первую встречу", use_container_width=True):
        st.session_state["page"] = "Новая встреча"
        st.rerun()

elif page == "Новая встреча":
    st.markdown("## Новая встреча")
    st.caption("Поддерживаются MP3, WAV, M4A, MP4 и WebM. Файл сохраняется только локально.")
    uploaded = st.file_uploader("Перетащите запись встречи", type=["mp3", "wav", "m4a", "mp4", "webm"])
    if uploaded:
        st.audio(uploaded)
        if st.button("Обработать встречу", type="primary", use_container_width=True):
            result = upload_file(uploaded)
            if result:
                st.success(f"Встреча сохранена: #{result['id']}")
                st.info("Следующий шаг — запуск локальной транскрибации.")

elif page == "История":
    st.markdown("## История встреч")
    meetings = api_get("/api/meetings")
    if not meetings:
        st.info("Встреч пока нет. Загрузите первую запись.")
    else:
        for meeting in meetings:
            st.markdown(
                f"<div class='card' style='margin-bottom:12px'><h3>{meeting.get('filename', 'Без названия')}</h3>"
                f"<span class='pill'>{meeting.get('status', 'uploaded').upper()}</span>"
                f"<span class='muted' style='margin-left:12px'>{meeting.get('created_at', '')}</span></div>",
                unsafe_allow_html=True,
            )

elif page == "О продукте":
    st.markdown("## AirGap")
    st.markdown("### Private by architecture")
    st.write("AirGap создан для команд, которым нельзя отправлять обсуждения клиентов, бюджеты и внутренние решения в облачные AI-сервисы.")
    st.markdown("#### Локальный стек")
    st.code(json.dumps({"speech_to_text": "faster-whisper", "llm": "Ollama / Qwen", "storage": "SQLite + ChromaDB", "transport": "localhost only"}, indent=2), language="json")
    st.markdown("[Открыть API-документацию](http://127.0.0.1:8000/docs)")
