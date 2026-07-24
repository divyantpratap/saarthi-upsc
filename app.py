"""Saarthi — a focused, source-grounded UPSC study workspace."""
from __future__ import annotations

import html
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
load_dotenv()

from src.core.secrets import apply_streamlit_secrets

apply_streamlit_secrets()

from settings import GEMINI_MODEL
from src.core.health import check_health
from src.core.logging_config import setup_logging
from src.ingest.build_store import get_collection_count
from src.rag.pipeline import UPSCChatbot
from src.references.catalog import build_catalog, load_catalog
from src.ui.sessions import active_session, delete_session, init_sessions, new_session, session_list, switch_session, touch_session, update_session_title

setup_logging()
st.set_page_config(page_title="Saarthi — UPSC AI", page_icon="◉", layout="wide", initial_sidebar_state="expanded")


def ensure_demo_index() -> None:
    """On Streamlit Cloud, auto-build a tiny public notes index if chroma is empty."""
    if get_collection_count() > 0:
        return
    if not os.getenv("GEMINI_API_KEY"):
        return
    os.environ.setdefault("EMBEDDING_BACKEND", "gemini")
    try:
        from scripts.build_demo_index import build_demo_index

        with st.spinner("Building the public demo knowledge base (one-time)…"):
            build_demo_index(reset=True)
    except Exception as exc:
        st.warning(f"Demo index not ready yet: {exc}")

STARTERS = {
    "Prelims drill": "Create 5 UPSC Prelims MCQs on Fundamental Rights. Ask one at a time and explain every option.",
    "Mains answer": "Write a 150-word GS-II answer: Constitutional morality is the soul of the Constitution. Discuss.",
    "Concept clarity": "Explain the basic structure doctrine with key cases and a simple memory framework.",
    "Revise a topic": "Help me revise the emergency provisions of the Constitution in 10 minutes.",
}
MODE_HINTS = {
    "Learn": "Explain clearly for a UPSC aspirant. Connect the concept to the syllabus and cite every factual claim.",
    "Prelims": "Answer for UPSC Prelims. Prioritise precise facts, traps, elimination logic, and a short recall cue.",
    "Mains": "Answer for UPSC Mains. Use a crisp introduction, dimensional body, examples, and a constructive conclusion.",
    "Evaluate": "Act as a strict UPSC evaluator. Give marks, identify missing dimensions, and provide an improved answer.",
}


def styles() -> None:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,500;6..72,600&display=swap');
    :root{--bg:#f7f6f2;--paper:#fff;--ink:#1c2824;--muted:#68736f;--line:#dedfd9;--green:#1f6b54;--green2:#e5f0e9;--saffron:#d97735}
    .stApp{background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif}
    header,[data-testid="stToolbar"],#MainMenu,footer,[data-testid="stSidebarNav"]{display:none!important}
    .block-container{max-width:940px;padding:1rem 2rem 8rem}
    [data-testid="stSidebar"]{background:#eeeee9;border-right:1px solid var(--line);min-width:286px;max-width:286px}
    [data-testid="stSidebar"]>div:first-child{padding:1.35rem 1rem}
    .brand{display:flex;align-items:center;gap:.7rem;margin:0 .2rem 1.4rem}.mark{height:34px;width:34px;border-radius:10px;background:var(--green);color:white;display:grid;place-items:center;font-family:'Newsreader';font-size:21px}.brand b{font-size:18px;letter-spacing:-.02em}.brand small{display:block;color:var(--muted);font-size:10px;letter-spacing:.09em;text-transform:uppercase}
    [data-testid="stSidebar"] button{border-radius:10px;border:0;text-align:left;justify-content:flex-start;font-weight:500;color:#33413c!important}
    [data-testid="stSidebar"] button p{color:inherit!important}
    [data-testid="stSidebar"] button[kind="primary"]{background:var(--green)!important;color:#fff!important;padding:.62rem .8rem}
    [data-testid="stSidebar"] button[kind="secondary"]{background:transparent!important;color:#33413c!important;padding:.5rem .65rem}
    [data-testid="stSidebar"] button[kind="secondary"]:hover{background:#e2e4df;color:var(--ink)}
    .section-label{font-size:10px;letter-spacing:.11em;text-transform:uppercase;color:#8a928e;margin:1.35rem .65rem .45rem;font-weight:700}
    .index-card{margin-top:1.2rem;padding:.8rem;border:1px solid #d6d9d3;background:#f7f7f3;border-radius:12px;font-size:12px;color:var(--muted)}.index-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#41a476;margin-right:6px}.index-card b{color:var(--ink)}
    .topbar{display:flex;justify-content:space-between;align-items:center;padding:.25rem 0 1rem;border-bottom:1px solid var(--line);margin-bottom:1rem}.crumb{color:var(--muted);font-size:13px}.crumb b{color:var(--ink)}.status{font-size:11px;color:var(--green);border:1px solid #bcd2c6;background:#edf5f0;padding:5px 9px;border-radius:20px}
    .hero{text-align:center;padding:3.4rem 0 1.4rem}.eyebrow{font-size:11px;color:var(--saffron);font-weight:700;letter-spacing:.13em;text-transform:uppercase}.hero h1{font-family:'Newsreader',serif;font-size:43px;line-height:1.05;letter-spacing:-.035em;margin:.6rem 0 .55rem;color:var(--ink)}.hero p{color:var(--muted);font-size:15px;max-width:560px;margin:auto;line-height:1.6}
    .starter{border:1px solid var(--line);border-radius:14px;padding:16px;background:#fff;min-height:92px}.starter b{font-size:14px}.starter p{font-size:13px;color:var(--muted);line-height:1.45;margin:.35rem 0 0}.workflow-label{font-size:11px;color:#7a8580;font-weight:700;letter-spacing:.09em;text-transform:uppercase;margin:1.4rem 0 .65rem}
    div[data-testid="stChatMessage"]{background:transparent;padding:.45rem 0}.stChatMessage [data-testid="stChatMessageContent"]{font-size:15px;line-height:1.7}.stChatMessage:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageContent"]{background:#e9ebe6;border:1px solid var(--line);border-radius:18px 18px 4px 18px;padding:.7rem 1rem;max-width:82%;margin-left:auto}
    .answer-meta{font-size:11px;color:var(--muted);margin:.5rem 0}.answer-meta span{color:var(--green);background:var(--green2);padding:3px 7px;border-radius:12px;font-weight:600}
    .source-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:8px 0}.source-head{display:flex;justify-content:space-between;gap:12px;font-size:12px;font-weight:700;color:var(--ink)}.source-loc{color:var(--saffron);white-space:nowrap}.source-card p{font-family:'Newsreader',serif;font-size:14px;line-height:1.55;color:#47514d;margin:8px 0 0}.source-sub{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-top:3px}
    [data-testid="stForm"]{background:#fff!important;border:1px solid #bfc9c3!important;border-radius:18px!important;padding:12px 14px 10px!important;box-shadow:0 12px 35px rgba(32,45,39,.10);margin:0 auto 1.5rem;max-width:760px}
    [data-testid="stForm"] textarea{background:#fff!important;color:var(--ink)!important;border:0!important;box-shadow:none!important;font-size:16px!important;min-height:74px!important;padding:8px!important}
    [data-testid="stForm"] textarea::placeholder{color:#7a8580!important;opacity:1!important}
    [data-testid="stForm"] button[kind="primary"]{background:var(--green)!important;color:#fff!important;border:0!important;border-radius:11px!important;font-weight:700!important}
    [data-testid="stForm"] button[kind="primary"] p{color:#fff!important}
    .composer-label{max-width:760px;margin:0 auto .45rem;font-size:12px;color:var(--green);font-weight:700;letter-spacing:.03em}
    button[kind="secondary"]{background:#fff!important;color:var(--ink)!important;border:1px solid var(--line)!important}button[kind="secondary"] p{color:inherit!important}
    div[data-baseweb="select"]>div,[data-testid="stSegmentedControl"]{background:#efefeb;border-color:var(--line)}
    @media(max-width:800px){.block-container{padding:1rem 1rem 7rem}.hero{padding:2.7rem 0 1.5rem}.hero h1{font-size:34px}[data-testid="stSidebar"]{min-width:270px}.topbar .crumb{max-width:190px;overflow:hidden;white-space:nowrap}.starter{min-height:auto}}
    </style>
    """, unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def index_count() -> int:
    return get_collection_count()


def bot_for(session: dict) -> UPSCChatbot:
    if st.session_state.get("bot_session_id") != session["id"]:
        bot = UPSCChatbot()
        bot.load_history(session["messages"])
        st.session_state.bot, st.session_state.bot_session_id = bot, session["id"]
    return st.session_state.bot


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"View {len(sources)} source passage{'s' if len(sources) != 1 else ''}", expanded=False):
        for i, source in enumerate(sources, 1):
            name = source.get("filename") or source.get("source", "Study material").removeprefix("pdf:")
            location = []
            if source.get("page_number"):
                location.append(f"Page {source['page_number']}")
            if source.get("paragraph_index"):
                location.append(f"¶ {source['paragraph_index']}")
            if source.get("relevance"):
                location.append(f"{source['relevance']}% match")
            preview = html.escape(source.get("preview", "No passage preview available."))
            st.markdown(
                f'<div class="source-card"><div class="source-head"><span>[{i}] {html.escape(name)}</span>'
                f'<span class="source-loc">{" · ".join(location) or "Reference"}</span></div>'
                f'<div class="source-sub">{html.escape(source.get("subject", "UPSC source"))}</div>'
                f'<p>{preview}</p></div>', unsafe_allow_html=True)


def render_composer(mode: str) -> str | None:
    st.markdown('<div class="composer-label">ASK SAARTHI</div>', unsafe_allow_html=True)
    with st.form("ask_saarthi", clear_on_submit=True):
        question = st.text_area(
            "Your UPSC question",
            placeholder=f"Ask a UPSC question in {mode} mode…",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Ask Saarthi  →", type="primary", use_container_width=True)
    return question.strip() if submitted and question.strip() else None


styles()
ensure_demo_index()
init_sessions()
session = active_session()

with st.sidebar:
    st.markdown('<div class="brand"><div class="mark">S</div><div><b>Saarthi</b><small>UPSC study intelligence</small></div></div>', unsafe_allow_html=True)
    if st.button("＋  New study chat", type="primary", use_container_width=True):
        new_session(); st.session_state.pop("bot_session_id", None); st.rerun()
    st.markdown('<div class="section-label">Workspace</div>', unsafe_allow_html=True)
    st.button("◉  Ask Saarthi", use_container_width=True, disabled=True)
    if st.button("▤  My source library", use_container_width=True):
        st.switch_page("pages/1_📚_Data_Ingestion.py")
    if st.button("✎  Practice & revision", use_container_width=True):
        st.switch_page("pages/2_📝_Practice_Questions.py")
    if st.button("✓  Mock tests", use_container_width=True):
        st.switch_page("pages/3_Mock_Tests.py")
    st.markdown('<div class="section-label">Recent study</div>', unsafe_allow_html=True)
    for item in session_list():
        if st.button(("●  " if item["id"] == session["id"] else "○  ") + item["title"], key=item["id"], use_container_width=True):
            switch_session(item["id"]); st.session_state.pop("bot_session_id", None); st.rerun()
    try:
        count = index_count()
    except Exception:
        count = 0
    catalog = load_catalog()
    st.markdown(f'<div class="index-card"><span class="index-dot"></span><b>Knowledge base ready</b><br>{catalog.get("count",0)} sources · {count:,} passages indexed</div>', unsafe_allow_html=True)
    with st.expander("Library management"):
        st.caption(f"Answer model: {GEMINI_MODEL}")
        if st.button("Rebuild source catalog", use_container_width=True):
            build_catalog(); st.rerun()
        if st.button("Re-index exact passages", use_container_width=True):
            from src.ingest.build_store import build_vector_store
            with st.spinner("Reading and indexing your library…"):
                build_vector_store(reset=True)
            index_count.clear(); st.rerun()
        if st.button("Delete this chat", use_container_width=True):
            delete_session(session["id"]); st.session_state.pop("bot_session_id", None); st.rerun()

st.markdown(f'<div class="topbar"><div class="crumb">Saarthi / <b>{html.escape(session["title"])}</b></div><div class="status">● Sources grounded</div></div>', unsafe_allow_html=True)

mode = st.segmented_control("Answer mode", list(MODE_HINTS), default="Learn", label_visibility="collapsed")

if not session["messages"]:
    st.markdown('<div class="hero"><div class="eyebrow">Built only for UPSC CSE</div><h1>What will you master today?</h1><p>Ask from your study library, practise Prelims, structure Mains answers, or get evaluated — with the exact source passage behind every response.</p></div>', unsafe_allow_html=True)
    prompt = render_composer(mode)
    st.markdown('<div class="workflow-label">Or start a guided workflow</div>', unsafe_allow_html=True)
    starter_items = list(STARTERS.items())
    for row in range(0, len(starter_items), 2):
        cols = st.columns(2)
        for col, (label, prompt_text) in zip(cols, starter_items[row:row + 2]):
            with col:
                st.markdown(f'<div class="starter"><b>{label}</b><p>{prompt_text}</p></div>', unsafe_allow_html=True)
                if st.button("Start →", key=f"start-{label}", use_container_width=True):
                    st.session_state.pending_prompt = prompt_text; st.rerun()

for message in session["messages"]:
    avatar = "🎓" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            st.markdown(f'<div class="answer-meta"><span>{message.get("study_mode","Learn")}</span> · {message.get("latency_ms",0)/1000:.1f}s · grounded response</div>', unsafe_allow_html=True)
            render_sources(message.get("sources", []))

if session["messages"]:
    prompt = render_composer(mode)
prompt = st.session_state.pop("pending_prompt", None) or prompt
if prompt:
    if not check_health().api_key_set:
        st.error("Add GEMINI_API_KEY in Streamlit secrets (or local .env) to start asking questions.")
        st.stop()
    update_session_title(session, prompt)
    session["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🎓"):
        with st.spinner("Finding the strongest passages…"):
            result = bot_for(session).ask(prompt, guidance=MODE_HINTS[mode])
        answer = result.get("answer", "I couldn't prepare an answer.")
        st.markdown(answer)
        st.markdown(f'<div class="answer-meta"><span>{mode}</span> · {result.get("latency_ms",0)/1000:.1f}s · grounded response</div>', unsafe_allow_html=True)
        render_sources(result.get("sources", []))
    session["messages"].append({"role":"assistant","content":answer,"sources":result.get("sources",[]),"mode":result.get("mode"),"study_mode":mode,"latency_ms":result.get("latency_ms",0)})
    touch_session(session)
    st.rerun()
