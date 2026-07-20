from __future__ import annotations

import time
import streamlit as st

from src.mock_tests.catalog import fetch_external_tests
from src.mock_tests.question_bank import TESTS, questions_for

st.set_page_config(page_title="Mock Tests — Saarthi", page_icon="◉", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Newsreader:wght@600&display=swap');
.stApp{background:#f7f6f2;color:#1c2824;font-family:'DM Sans',sans-serif}.block-container{max-width:1120px;padding:2rem 2rem 6rem}header,#MainMenu,footer{visibility:hidden}
h1,h2{font-family:'Newsreader',serif;letter-spacing:-.025em}.mock-hero{padding:1.5rem 0 1.8rem;border-bottom:1px solid #dedfd9;margin-bottom:1.5rem}.mock-hero small{color:#d97735;font-weight:700;letter-spacing:.12em}.mock-hero h1{font-size:42px;margin:.35rem 0}.mock-hero p{color:#68736f;max-width:650px}
.test-card{background:#fff;border:1px solid #dedfd9;border-radius:15px;padding:18px;min-height:172px}.test-card .kind{font-size:10px;text-transform:uppercase;color:#1f6b54;font-weight:700;letter-spacing:.1em}.test-card h3{font-size:17px;margin:.7rem 0}.test-card p{font-size:12px;color:#68736f}.metric{display:inline-block;background:#edf3ef;border-radius:20px;padding:4px 8px;margin-right:5px;font-size:11px}
.question-box{background:#fff;border:1px solid #dedfd9;border-radius:16px;padding:22px;margin:1rem 0}.question-num{font-size:11px;color:#d97735;font-weight:700;letter-spacing:.1em}.timer{background:#1f6b54;color:white;padding:7px 12px;border-radius:20px;font-size:13px}.score{background:#e5f0e9;border:1px solid #bcd2c6;padding:20px;border-radius:14px;margin:1rem 0}.ext{border-left:3px solid #d97735;padding:.4rem .8rem;margin:.6rem 0;background:#fff;border-radius:0 10px 10px 0}
.exam-head{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;border-bottom:1px solid #dedfd9;padding-bottom:1rem;margin-bottom:1.5rem}.exam-head h1{font-size:30px;margin:0 0 .3rem}.exam-head p{color:#68736f;margin:0;font-size:13px}.progress-track{height:6px;background:#e2e4df;border-radius:10px;margin:1rem 0 1.7rem;overflow:hidden}.progress-fill{height:100%;background:#1f6b54;border-radius:10px}
div[data-testid="stRadio"]{background:#fff;border:1px solid #dedfd9;border-radius:14px;padding:8px 14px;margin-bottom:1.2rem}div[data-testid="stRadio"] label{padding:10px 8px;border-bottom:1px solid #ecece8}div[data-testid="stRadio"] label:last-child{border-bottom:0}div[data-testid="stRadio"] label p{color:#1c2824!important;font-size:15px!important;line-height:1.45!important}div[data-testid="stRadio"] [data-testid="stMarkdownContainer"]{color:#1c2824!important}
.palette{background:#eeeee9;border:1px solid #dedfd9;border-radius:14px;padding:12px;margin-top:1rem}.palette-title{font-size:11px;color:#68736f;text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin-bottom:8px}.legend{font-size:11px;color:#68736f;margin-top:.7rem}.legend b{display:inline-block;width:9px;height:9px;border-radius:3px;background:#1f6b54;margin-right:4px}.legend i{display:inline-block;width:9px;height:9px;border-radius:3px;background:#fff;border:1px solid #bbb;margin:0 4px 0 12px}
@media(max-width:700px){.block-container{padding:1rem 1rem 5rem}.exam-head{display:block}.exam-head h1{font-size:25px}.timer{display:inline-block;margin-top:.8rem}.question-box{padding:16px}.mock-hero h1{font-size:34px}}
</style>""", unsafe_allow_html=True)

if st.sidebar.button("← Back to Ask Saarthi", use_container_width=True):
    st.switch_page("app.py")

if "mock_active" not in st.session_state:
    st.session_state.mock_active = None

active = st.session_state.mock_active
if active:
    test = next(t for t in TESTS if t["id"] == active)
    questions = questions_for(test)
    if "mock_started" not in st.session_state:
        st.session_state.mock_started = time.time()
    current_key = f"current_{active}"
    current = st.session_state.setdefault(current_key, 0)
    current = max(0, min(current, len(questions) - 1))
    q = questions[current]
    elapsed = int((time.time() - st.session_state.mock_started) // 60)
    st.markdown(f'<div class="exam-head"><div><h1>{test["title"]}</h1><p>{len(questions)} questions · +2 correct · −0.66 incorrect</p></div><span class="timer">{max(0, test["minutes"]-elapsed)} min remaining</span></div>', unsafe_allow_html=True)
    answers = st.session_state.setdefault(f"answers_{active}", {})
    st.markdown(f'<div class="progress-track"><div class="progress-fill" style="width:{(current+1)/len(questions)*100:.1f}%"></div></div>', unsafe_allow_html=True)
    main, side = st.columns([3.2, 1])
    with main:
        st.markdown(f'<div class="question-num">QUESTION {current+1} OF {len(questions)} · {q["subject"].upper()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="question-box">{q["q"]}</div>', unsafe_allow_html=True)
        prior = answers.get(q["id"])
        choice = st.radio("Choose one", q["options"], index=prior, key=f"choice_{active}_{q['id']}", label_visibility="collapsed")
        if choice is not None:
            answers[q["id"]] = q["options"].index(choice)
        nav1, nav2, nav3 = st.columns([1,1,1.25])
        if nav1.button("← Previous", use_container_width=True, disabled=current == 0):
            st.session_state[current_key] = current - 1; st.rerun()
        if nav2.button("Clear", use_container_width=True, disabled=q["id"] not in answers):
            answers.pop(q["id"], None); st.session_state.pop(f"choice_{active}_{q['id']}", None); st.rerun()
        if nav3.button("Next question →", type="primary", use_container_width=True, disabled=current == len(questions)-1):
            st.session_state[current_key] = current + 1; st.rerun()
    with side:
        st.markdown('<div class="palette"><div class="palette-title">Question navigator</div>', unsafe_allow_html=True)
        palette_cols = st.columns(4)
        for idx, question in enumerate(questions):
            label = f"{'✓' if question['id'] in answers else ''}{idx+1}"
            if palette_cols[idx % 4].button(label, key=f"jump_{active}_{idx}", use_container_width=True, type="primary" if question["id"] in answers else "secondary"):
                st.session_state[current_key] = idx; st.rerun()
        st.markdown(f'<div class="legend"><b></b> Answered <i></i> Unanswered<br><br>{len(answers)} of {len(questions)} answered</div></div>', unsafe_allow_html=True)
    st.divider()
    action1, action2, _ = st.columns([1.2,1,2])
    if action1.button("Submit test", type="primary", use_container_width=True):
        st.session_state.mock_submitted = active; st.rerun()
    if action2.button("Save & exit", use_container_width=True):
        st.session_state.mock_active = None; st.session_state.pop("mock_started",None); st.rerun()
    if st.session_state.get("mock_submitted") == active:
        correct = sum(answers.get(q["id"]) == q["answer"] for q in questions)
        wrong = sum(q["id"] in answers and answers[q["id"]] != q["answer"] for q in questions)
        score = correct * 2 - wrong * (2/3)
        st.markdown(f'<div class="score"><h2>{score:.2f} marks</h2><b>{correct} correct · {wrong} incorrect · {len(questions)-correct-wrong} unattempted</b></div>', unsafe_allow_html=True)
        st.subheader("Review with explanations")
        for i, q in enumerate(questions, 1):
            with st.expander(f"Q{i} · {'Correct' if answers.get(q['id']) == q['answer'] else 'Review'}"):
                st.write(q["q"]); st.success(f"Correct answer: {q['options'][q['answer']]}"); st.write(q["explanation"]); st.caption(f"Reference: {q['source']}")
else:
    st.markdown('<div class="mock-hero"><small>EXAM SIMULATION</small><h1>Mock Tests</h1><p>Build speed, accuracy and judgement under UPSC conditions. Every native test includes negative marking, detailed review and reference-led explanations.</p></div>', unsafe_allow_html=True)
    selected_kind = st.segmented_control("Test type", ["Sectional Mock Test","Full Length Mock Test"], default="Sectional Mock Test")
    available = [t for t in TESTS if t["kind"] == selected_kind]
    cols = st.columns(2)
    for col, test in zip(cols, available):
        with col:
            st.markdown(f'<div class="test-card"><div class="kind">{test["kind"]}</div><h3>{test["title"]}</h3><p>{test["subject"]} · {test["difficulty"]}</p><span class="metric">{len(test["question_ids"])} questions</span><span class="metric">{test["minutes"]} min</span></div>', unsafe_allow_html=True)
            if st.button("Begin test →", key=f"begin_{test['id']}", use_container_width=True):
                st.session_state.mock_active=test["id"]; st.session_state.pop("mock_started",None); st.session_state.pop("mock_submitted",None); st.rerun()
    st.divider()
    st.subheader("External open mocks")
    st.caption("Public listings refreshed from providers. Tests open on the provider's official site; Saarthi does not copy or claim their question banks.")
    @st.cache_data(ttl=21600, show_spinner=False)
    def external(): return fetch_external_tests()
    for item in external()[:8]:
        st.markdown(f'<div class="ext"><b>{item["title"]}</b><br><small>{item["provider"]} · {item["test_type"]} · <a href="{item["url"]}" target="_blank">Open official test ↗</a></small></div>', unsafe_allow_html=True)
