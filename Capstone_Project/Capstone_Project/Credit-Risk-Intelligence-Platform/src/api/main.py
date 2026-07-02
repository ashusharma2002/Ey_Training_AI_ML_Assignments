# src/api/main.py
# ============================================================
# FastAPI Backend — optional API layer over the orchestrator.
#
# Architecture:
#   Client → FastAPI → Validation → AgentOrchestrator → LLM → JSON
#
# Run separately from Streamlit:
#   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
#
# Streamlit UI talks directly to the Orchestrator (not via API).
# This FastAPI layer is for external API consumers / mobile apps.
# ============================================================
from __future__ import annotations
import os
import sys
from pathlib import Path

# Ensure project root is in path
ROOT = Path(__file__).parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from config.settings import settings

# Initialise LangSmith before LangChain imports
from src.services.langsmith_setup import initialise as _init_langsmith
_init_langsmith()

from src.orchestrator.orchestrator import AgentOrchestrator
from src.models.schemas import PlatformState
from src.utils.logger import get_logger

logger  = get_logger(__name__)
app     = FastAPI(
    title="Credit Risk Intelligence Platform API",
    description="AI-powered credit risk analysis API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Streamlit and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session-level state (single-user mode for demo)
_state        = PlatformState()
_orchestrator = AgentOrchestrator()
_security     = HTTPBearer(auto_error=False)


def _verify_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(_security),
) -> bool:
    if not settings.API_KEY:
        return True  # No key configured — open access
    if not credentials or credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# ── Request / Response models ─────────────────────────────

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer:  str
    sources: list[str]

class HealthResponse(BaseModel):
    status:            str
    app_env:           str
    llm_provider:      str
    vector_store:      str
    documents_loaded:  int
    vector_store_ready: bool


# ── Endpoints ─────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return HealthResponse(
        status             = "ok",
        app_env            = settings.APP_ENV,
        llm_provider       = settings.LLM_PROVIDER,
        vector_store       = settings.VECTOR_STORE_PROVIDER,
        documents_loaded   = _state.total_documents(),
        vector_store_ready = _state.vector_store_ready,
    )


@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    req:  ChatRequest,
    auth: bool = Depends(_verify_api_key),
):
    """Ask a question about the uploaded financial documents."""
    if not _state.vector_store_ready:
        raise HTTPException(
            status_code=400,
            detail="No documents loaded. Upload documents first via the Streamlit UI."
        )
    try:
        msg = _orchestrator.chat(req.question, _state)
        return ChatResponse(answer=msg.content, sources=msg.sources)
    except Exception as exc:
        logger.error("Chat API error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/v1/risk-analysis", tags=["Analysis"])
async def run_risk_analysis(auth: bool = Depends(_verify_api_key)):
    """Run AI-powered credit risk analysis."""
    if not _state.summaries:
        raise HTTPException(status_code=400, detail="No documents available for analysis.")
    try:
        risk = _orchestrator.run_risk_analysis(_state)
        return risk.model_dump(mode="json") if risk else {"error": "Analysis failed"}
    except Exception as exc:
        logger.error("Risk analysis API error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/v1/recommendations", tags=["Analysis"])
async def generate_recommendations(auth: bool = Depends(_verify_api_key)):
    """Generate personalised financial recommendations."""
    if not _state.summaries:
        raise HTTPException(status_code=400, detail="No documents available.")
    try:
        recs = _orchestrator.run_recommendations(_state)
        return recs.model_dump(mode="json")
    except Exception as exc:
        logger.error("Recommendations API error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/v1/status", tags=["System"])
async def get_status(auth: bool = Depends(_verify_api_key)):
    """Get current session status."""
    return {
        "documents":      _state.total_documents(),
        "processed":      _state.processed_count(),
        "risk_score":     _state.risk_assessment.risk_score if _state.risk_assessment else None,
        "chat_messages":  len(_state.chat_history),
        "vector_ready":   _state.vector_store_ready,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.APP_ENV == "development",
    )
