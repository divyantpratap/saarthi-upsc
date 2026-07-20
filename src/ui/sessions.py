"""Chat session state for multi-conversation UI."""
from __future__ import annotations

import uuid
from datetime import datetime

import streamlit as st


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def init_sessions() -> None:
    if "sessions" not in st.session_state:
        sid = str(uuid.uuid4())[:8]
        st.session_state.sessions = {
            sid: {
                "id": sid,
                "title": "New chat",
                "messages": [],
                "updated": _now(),
            }
        }
        st.session_state.active_session_id = sid
    if "active_session_id" not in st.session_state:
        st.session_state.active_session_id = next(iter(st.session_state.sessions))


def active_session() -> dict:
    init_sessions()
    sid = st.session_state.active_session_id
    if sid not in st.session_state.sessions:
        st.session_state.active_session_id = next(iter(st.session_state.sessions))
        sid = st.session_state.active_session_id
    return st.session_state.sessions[sid]


def session_list() -> list[dict]:
    init_sessions()
    items = list(st.session_state.sessions.values())
    items.sort(key=lambda x: x.get("updated", ""), reverse=True)
    return items


def new_session() -> str:
    init_sessions()
    sid = str(uuid.uuid4())[:8]
    st.session_state.sessions[sid] = {
        "id": sid,
        "title": "New chat",
        "messages": [],
        "updated": _now(),
    }
    st.session_state.active_session_id = sid
    return sid


def switch_session(session_id: str) -> None:
    init_sessions()
    if session_id in st.session_state.sessions:
        st.session_state.active_session_id = session_id


def update_session_title(session: dict, first_user_message: str) -> None:
    if session["title"] == "New chat" and first_user_message:
        title = first_user_message.strip().replace("\n", " ")
        session["title"] = (title[:42] + "…") if len(title) > 43 else title


def touch_session(session: dict) -> None:
    session["updated"] = _now()


def delete_session(session_id: str) -> None:
    init_sessions()
    if len(st.session_state.sessions) <= 1:
        st.session_state.sessions[session_id]["messages"] = []
        st.session_state.sessions[session_id]["title"] = "New chat"
        return
    st.session_state.sessions.pop(session_id, None)
    st.session_state.active_session_id = next(iter(st.session_state.sessions))
