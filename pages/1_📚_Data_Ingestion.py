"""Saarthi source library — safe browsing and incremental PDF indexing."""
from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from settings import PDF_DIR
from src.ingest.build_store import get_chroma_collection, get_collection_count, index_documents
from src.ingest.pdf_parser import pdf_to_documents
from src.references.catalog import build_catalog, load_catalog

st.set_page_config(page_title="Source Library — Saarthi", page_icon="📚", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Newsreader:wght@600&display=swap');
.stApp{background:#f7f6f2;color:#1c2824;font-family:'DM Sans',sans-serif}.block-container{max-width:1080px;padding:2rem 2rem 5rem}header,#MainMenu,footer,[data-testid="stSidebarNav"]{display:none!important}h1,h2{font-family:'Newsreader',serif}.hero{padding:1rem 0 1.3rem;border-bottom:1px solid #dedfd9;margin-bottom:1.3rem}.hero small{color:#d97735;font-weight:700;letter-spacing:.12em}.hero h1{font-size:40px;margin:.35rem 0}.hero p{color:#68736f}.source{background:#fff;border:1px solid #dedfd9;border-radius:14px;padding:16px;margin:.55rem 0}.source b{color:#1c2824}.source small{color:#1f6b54}.source p{color:#68736f;font-size:13px;line-height:1.55}.stat{background:#edf3ef;border:1px solid #cbdad2;border-radius:12px;padding:12px}.stButton button{border-radius:10px}
</style>""", unsafe_allow_html=True)

if st.sidebar.button("← Back to Ask Saarthi", use_container_width=True):
    st.switch_page("app.py")
if st.sidebar.button("Mock tests", use_container_width=True):
    st.switch_page("pages/3_Mock_Tests.py")

catalog = load_catalog()
entries = catalog.get("entries", [])
try:
    chunks = get_collection_count()
except Exception:
    chunks = 0

st.markdown('<div class="hero"><small>GROUNDED KNOWLEDGE</small><h1>My Source Library</h1><p>Browse exactly what Saarthi can search. Add a PDF without rebuilding the entire library.</p></div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
c1.metric("Sources", len(entries)); c2.metric("Indexed passages", f"{chunks:,}"); c3.metric("Subjects", len({e.get('subject','General') for e in entries}))

browse, add = st.tabs(["Browse sources", "Add a PDF"])
with browse:
    subjects = sorted({e.get("subject", "General Studies") for e in entries})
    f1, f2 = st.columns([2.3, 1])
    query = f1.text_input("Search library", placeholder="Search title, subject or preview…")
    subject = f2.selectbox("Subject", ["All subjects"] + subjects)
    needle = query.strip().lower()
    filtered = [e for e in entries if (subject == "All subjects" or e.get("subject") == subject) and (not needle or needle in " ".join([e.get("filename",""), e.get("subject",""), e.get("preview","")]).lower())]
    st.caption(f"Showing {len(filtered)} of {len(entries)} sources")
    for item in filtered:
        preview = " ".join(item.get("preview", "").split())[:360]
        st.markdown(f'<div class="source"><small>{item.get("subject","GENERAL STUDIES").upper()}</small><br><b>{item.get("filename","Untitled source")}</b><p>{preview or "Indexed source — ask Saarthi to retrieve a matching passage."}</p></div>', unsafe_allow_html=True)
    if not filtered:
        st.info("No source matches that search. Try a broader keyword.")

with add:
    st.subheader("Add study material")
    st.caption("PDF only. The file is indexed page-by-page so answers can cite exact locations.")
    uploaded = st.file_uploader("Choose a UPSC PDF", type=["pdf"], accept_multiple_files=False)
    if uploaded and st.button("Save and index PDF", type="primary"):
        safe_name = re.sub(r"[^A-Za-z0-9._ -]", "_", Path(uploaded.name).name)
        target = PDF_DIR / safe_name
        try:
            target.write_bytes(uploaded.getbuffer())
            with st.spinner("Extracting pages and updating the search index…"):
                docs = pdf_to_documents(target)
                if not docs:
                    raise ValueError("No readable text was found in this PDF.")
                added = index_documents(get_chroma_collection(reset=False), docs, safe_name)
                build_catalog()
            st.success(f"Indexed {added:,} passages from {safe_name}.")
            st.cache_data.clear(); st.cache_resource.clear()
        except Exception as exc:
            st.error(f"This PDF could not be indexed: {exc}")
