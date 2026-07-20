"""Stable daily practice with local questions and answer-writing rubrics."""
from __future__ import annotations

import streamlit as st

from src.mock_tests.question_bank import QUESTIONS

st.set_page_config(page_title="Daily Practice — Saarthi", page_icon="✍️", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Newsreader:wght@600&display=swap');
.stApp{background:#f7f6f2;color:#1c2824;font-family:'DM Sans',sans-serif}.block-container{max-width:980px;padding:2rem 2rem 5rem}header,#MainMenu,footer,[data-testid="stSidebarNav"]{display:none!important}h1,h2{font-family:'Newsreader',serif}.hero{padding:1rem 0 1.4rem;border-bottom:1px solid #dedfd9;margin-bottom:1.4rem}.hero small{color:#d97735;font-weight:700;letter-spacing:.12em}.hero h1{font-size:40px;margin:.35rem 0}.hero p{color:#68736f}.question{background:#fff;border:1px solid #dedfd9;border-radius:16px;padding:22px;margin:1rem 0}.question small{color:#1f6b54;font-weight:700}.question p{font-size:18px;line-height:1.6}.rubric{background:#edf3ef;border:1px solid #cbdad2;border-radius:14px;padding:16px}.stButton button{border-radius:10px}div[data-testid="stRadio"] label p{color:#1c2824!important}
</style>""", unsafe_allow_html=True)

MAINS = [
    {"subject":"Polity","q":"Constitutional morality is essential for sustaining substantive democracy in India. Discuss. (150 words)","points":["Define constitutional morality","Institutions and restraint on majoritarian power","Key judicial or constitutional examples","Challenges and constructive way forward"]},
    {"subject":"Economy","q":"Inclusive growth requires more than a rise in GDP. Examine. (150 words)","points":["Growth versus distribution","Jobs, health, education and financial access","Regional and gender gaps","Targeted policy plus productive capacity"]},
    {"subject":"Environment","q":"Wetland conservation is simultaneously an ecological and developmental necessity. Explain. (150 words)","points":["Flood moderation and water security","Biodiversity and livelihoods","Urbanisation and pollution threats","Ramsar principle of wise use"]},
]

if st.sidebar.button("← Back to Ask Saarthi", use_container_width=True): st.switch_page("app.py")
if st.sidebar.button("Mock tests", use_container_width=True): st.switch_page("pages/3_Mock_Tests.py")

st.markdown('<div class="hero"><small>DAILY DELIBERATE PRACTICE</small><h1>Practice & Revision</h1><p>Short, dependable practice that works even when the answer model is busy.</p></div>', unsafe_allow_html=True)
mode = st.segmented_control("Practice mode", ["Prelims MCQ", "Mains writing"], default="Prelims MCQ")

if mode == "Prelims MCQ":
    subjects = sorted({q["subject"] for q in QUESTIONS})
    subject = st.selectbox("Subject", ["Mixed"] + subjects)
    pool = QUESTIONS if subject == "Mixed" else [q for q in QUESTIONS if q["subject"] == subject]
    idx_key = f"practice_idx_{subject}"
    idx = st.session_state.setdefault(idx_key, 0) % len(pool)
    q = pool[idx]
    st.markdown(f'<div class="question"><small>{q["subject"].upper()}</small><p>{q["q"]}</p></div>', unsafe_allow_html=True)
    choice = st.radio("Select one answer", q["options"], index=None, key=f"practice_{subject}_{q['id']}")
    a, b = st.columns(2)
    if a.button("Check answer", type="primary", use_container_width=True, disabled=choice is None):
        if q["options"].index(choice) == q["answer"]: st.success("Correct — well done.")
        else: st.error(f"Not quite. Correct answer: {q['options'][q['answer']]}")
        st.info(q["explanation"]); st.caption(f"Reference: {q['source']}")
    if b.button("Next question →", use_container_width=True):
        st.session_state[idx_key] = (idx + 1) % len(pool); st.rerun()
else:
    subject = st.selectbox("Paper area", [item["subject"] for item in MAINS])
    prompt = next(item for item in MAINS if item["subject"] == subject)
    st.markdown(f'<div class="question"><small>{subject.upper()}</small><p>{prompt["q"]}</p></div>', unsafe_allow_html=True)
    answer = st.text_area("Write your answer", height=260, placeholder="Introduction…\n\nBody…\n\nConclusion…")
    words = len(answer.split())
    st.caption(f"{words} words · target 150")
    if st.button("Show evaluation rubric", type="primary"):
        st.markdown('<div class="rubric"><b>A strong answer should cover:</b><ul>' + ''.join(f'<li>{p}</li>' for p in prompt["points"]) + '</ul></div>', unsafe_allow_html=True)
