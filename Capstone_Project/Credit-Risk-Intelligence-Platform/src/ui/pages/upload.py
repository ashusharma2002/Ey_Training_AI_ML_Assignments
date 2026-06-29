# src/ui/pages/upload.py
# Fix: Clear All Documents now deletes persisted FAISS files
from __future__ import annotations
import tempfile
from pathlib import Path
import streamlit as st
from config.settings import settings
from src.agents.orchestrator import AgentOrchestrator
from src.models.schemas import DocumentMetadata, PlatformState, ProcessingStatus
from src.ui.theme import C, badge, empty_state, info_box, page_header, section_header, step_tracker

_ACCEPTED_TYPES = ["pdf"]
_MAX_FILE_MB    = 50
_MAX_FILE_BYTES = _MAX_FILE_MB * 1024 * 1024


def render(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    page_header("Upload Documents",
                "Upload official financial PDFs for AI-powered extraction and analysis.")
    _doc_types()
    st.markdown("---")
    col_up, col_lib = st.columns([3, 2], gap="large")
    with col_up:
        _uploader(state, orchestrator)
    with col_lib:
        _library(state, orchestrator)


def _doc_types() -> None:
    types = [
        ("🏦", "Bank Statement",    "Account transactions & balances"),
        ("📑", "Income Tax Return", "ITR / annual tax filings"),
        ("⚖️", "Balance Sheet",     "Assets & liabilities snapshot"),
        ("📈", "Annual Report",     "Full year financial statements"),
    ]
    cols = st.columns(4, gap="small")
    for col, (icon, name, desc) in zip(cols, types):
        with col:
            st.markdown(
                f"<div class='doc-type-card'>"
                f"<div style='font-size:1.75rem;margin-bottom:8px'>{icon}</div>"
                f"<div style='font-size:0.82rem;font-weight:700;color:{C['text']};"
                f"margin-bottom:3px'>{name}</div>"
                f"<div style='font-size:0.72rem;color:{C['text3']}'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


def _uploader(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    section_header("⬆️", "Upload Files")
    uploaded_files = st.file_uploader(
        "Drag & drop financial PDFs here or click to browse",
        type=_ACCEPTED_TYPES,
        accept_multiple_files=True,
        help=f"PDF only · Max {_MAX_FILE_MB} MB per file",
        key="file_uploader",
    )

    if not uploaded_files:
        st.markdown(
            f"<div style='margin-top:12px;padding:14px 16px;"
            f"background:{C['surface2']};border-radius:8px;"
            f"border:1px solid {C['border']};"
            f"font-size:0.82rem;color:{C['text2']};line-height:1.6'>"
            f"<strong>Accepted:</strong> PDF only &nbsp;·&nbsp; "
            f"<strong>Max size:</strong> {_MAX_FILE_MB} MB &nbsp;·&nbsp; "
            f"<strong>Multiple files:</strong> supported<br>"
            f"<span style='color:{C['text3']}'>Files processed locally — not stored permanently.</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        return

    existing_names = {d.file_name for d in state.documents}
    new_files = [f for f in uploaded_files if f.name not in existing_names]

    if not new_files:
        info_box("All selected files have already been processed.", "success")
        return

    step_tracker(["Upload", "Process", "Analyse", "Chat"],
                 0 if state.processed_count() == 0 else 1)

    st.markdown(
        f"<div style='padding:10px 14px;background:{C['blue_dim']};"
        f"border-radius:8px;border:1px solid rgba(0,82,204,0.2);"
        f"font-size:0.84rem;color:{C['blue']};font-weight:600;margin:8px 0'>"
        f"🔵 {len(new_files)} new file(s) ready to process</div>",
        unsafe_allow_html=True,
    )

    if st.button("🚀  Process Documents", type="primary", use_container_width=True):
        _process(new_files, state, orchestrator)


def _process(files, state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    prog = st.progress(0, text="Initialising…")
    msg  = st.empty()
    processed_ok = 0

    for idx, f in enumerate(files):
        if f.size > _MAX_FILE_BYTES:
            st.error(f"❌ {f.name} exceeds {_MAX_FILE_MB} MB — skipped.")
            continue

        pct = int(idx / len(files) * 80)
        prog.progress(pct, text=f"Processing {f.name}…")
        msg.info(f"⚙️  Extracting & embedding: **{f.name}**")

        upload_dir = Path(settings.DATA_UPLOAD_DIR).resolve()
        upload_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False, dir=str(upload_dir)) as tmp:
            tmp.write(f.read())
            tmp_path = Path(tmp.name)

        # DocumentMetadata uses the REAL filename — stored in chunk metadata
        meta = DocumentMetadata(file_name=f.name, file_size_kb=round(f.size / 1024, 1))
        state.documents.append(meta)

        try:
            orchestrator.ingest_document(tmp_path, meta, state)
            processed_ok += 1
        except Exception as exc:  # noqa: BLE001
            meta.processing_status = ProcessingStatus.FAILED
            meta.error_message     = str(exc)
            st.error(f"❌ {f.name}: {exc}")

    if processed_ok > 0 and state.summaries:
        prog.progress(85, text="Generating combined analysis & questions…")
        msg.info("🤖 Building combined summary and intelligent questions…")
        try:
            orchestrator.refresh_intelligence(state)
        except Exception as exc:  # noqa: BLE001
            st.warning(f"⚠️ Combined analysis had an issue: {exc}")

    prog.progress(100, text="Done!")
    msg.success(f"✅  {processed_ok} document(s) processed successfully.")
    st.balloons()
    st.rerun()


def _library(state: PlatformState, orchestrator: AgentOrchestrator) -> None:
    section_header("📁", "Document Library")

    if not state.documents:
        empty_state("📂", "Library Empty",
                    "Uploaded documents will appear here with their processing status.")
        return

    for doc in reversed(state.documents):
        s = doc.processing_status
        if s == ProcessingStatus.COMPLETE:
            b, icon = badge("✓ Ready", "success"),     "📄"
        elif s == ProcessingStatus.PROCESSING:
            b, icon = badge("⟳ Processing", "warning"), "⏳"
        elif s == ProcessingStatus.FAILED:
            b, icon = badge("✗ Error", "danger"),      "❌"
        else:
            b, icon = badge("○ Pending", "neutral"),   "🕐"

        with st.expander(f"{icon}  {doc.file_name[:34]}", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Type:** {doc.document_type.value}")
                st.markdown(f"**Pages:** {doc.page_count or '—'}")
            with c2:
                st.markdown(f"**Size:** {doc.file_size_kb} KB")
                st.markdown("**Status:**")
                st.markdown(b, unsafe_allow_html=True)
            if doc.error_message:
                st.error(f"Error: {doc.error_message}")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("🗑️  Clear All Documents", use_container_width=True):
        state.documents.clear()
        state.summaries.clear()
        state.combined_summary    = None
        state.suggested_questions = type(state.suggested_questions)()
        state.risk_assessment     = None
        state.recommendations     = None
        state.chat_history.clear()
        state.vector_store_ready  = False
        # delete_persisted=True prevents ghost embeddings in the next session
        orchestrator.reset()
        st.rerun()
