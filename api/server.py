"""
Qreen Contextual Engine | FastAPI Server
=========================================
محرك استرجاع معلومات محلي بالكامل — يدعم العربية بدون أي API خارجي 🔒🇸🇦

Author: Qreen Team
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import logging

# Import our internal modules
from src.context_engine.engine import AdaptiveMemoryEngine
from src.rag_engine.engine import GroundedRAGEngine
from src.telemetry.tracker import TelemetryTracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qreen")

# ============================================================
# App Configuration
# ============================================================

app = FastAPI(
    title="Qreen Contextual Engine",
    description="نظام ذاكرة سياقية تكيفية ومحرك استرجاع محلي بالكامل",
    version="0.1.0-alpha",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Initialize engines
memory_engine = AdaptiveMemoryEngine(collection_name="qreen_memories")
rag_engine = GroundedRAGEngine(auto_index=True)
telemetry = TelemetryTracker()


# ============================================================
# Request/Response Models
# ============================================================

class QueryRequest(BaseModel):
    """طلب استعلام من المستخدم"""
    query: str
    top_k: int = 3
    include_context: bool = True


class MemoryResponse(BaseModel):
    """استجابة محرك الذاكرة"""
    memories: List[dict]
    count: int
    confidence_scores: List[float]


class RAGResponse(BaseModel):
    """استجابة محرك RAG"""
    answer: str
    sources: List[str]
    confidence: float
    context_used: List[str]


class HealthResponse(BaseModel):
    """استجابة فحص الصحة"""
    status: str
    version: str
    memory_size: int
    vector_count: int


# ============================================================
# Routes
# ============================================================

@app.get("/", tags=["General"])
async def root():
    """نقطة البداية — هوية Qreen"""
    return {
        "name": "Qreen Contextual Engine",
        "version": "0.1.0-alpha",
        "flag": "🇸🇦",
        "philosophy": "السياق → النمط → التنبؤ",
        "endpoints": ["/query", "/memory/search", "/health"]
    }


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """فحص صحة النظام"""
    try:
        mem_stats = memory_engine.get_stats()
        return HealthResponse(
            status="healthy",
            version="0.1.0-alpha",
            memory_size=mem_stats.get("total_memories", 0),
            vector_count=mem_stats.get("total_memories", 0)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service degraded: {str(e)}")


@app.post("/query", response_model=RAGResponse, tags=["Query"])
async def query(request: QueryRequest):
    """
    نقطة الاستعلام الرئيسية
    -------------------------
    يستقبل سؤال بالعربية ويعيد إجابة مدعومة بالسياق
    """
    try:
        # Step 1: Search in knowledge base via RAG
        result = rag_engine.answer_query(query=request.query)

        # Step 2: Enrich with adaptive memory context
        context_used = []
        if request.include_context:
            context_memories = memory_engine.retrieve_by_text(
                query=request.query,
                top_k=request.top_k
            )
            context_used = [m["content"] for m in context_memories]

        # Step 3: Track anonymously
        telemetry.track_query(
            query_length=len(request.query),
            results_found=len(result.get("sources", []))
        )

        return RAGResponse(
            answer=result.get("answer", ""),
            sources=[s.get("title", "") for s in result.get("sources", [])],
            confidence=1.0 if result.get("grounded") else 0.0,
            context_used=context_used
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.post("/memory/search", response_model=MemoryResponse, tags=["Memory"])
async def search_memory(request: QueryRequest):
    """
    البحث في الذاكرة التكيفية
    --------------------------
    يبحث عن ذكريات مشابهة مع تضاؤل زمني
    """
    try:
        memories = memory_engine.retrieve_by_text(
            query=request.query,
            top_k=request.top_k
        )

        return MemoryResponse(
            memories=memories,
            count=len(memories),
            confidence_scores=[m.get("final_score", 0) for m in memories]
        )

    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/save", tags=["Memory"])
async def save_memory(text: str, metadata: Optional[dict] = None):
    """حفظ ذكرى جديدة في الذاكرة التكيفية"""
    try:
        import uuid
        memory_id = str(uuid.uuid4())
        success = memory_engine.add_memory(
            memory_id=memory_id,
            content=text
        )
        return {"status": "saved" if success else "duplicate", "memory_id": memory_id}
    except Exception as e:
        logger.error(f"Save memory failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/cleanup", tags=["Memory"])
async def cleanup_memory(threshold: float = 0.1):
    """تنظيف الذكريات منخفضة الدرجة"""
    try:
        removed_ids = memory_engine.cleanup_low_score(min_final_score=threshold)
        return {"status": "cleaned", "removed": len(removed_ids)}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/telemetry/stats", tags=["Telemetry"])
async def get_telemetry_stats():
    """إحصائيات التتبع المجهول"""
    try:
        stats = telemetry.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Telemetry stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Startup & Shutdown Events
# ============================================================

@app.on_event("startup")
async def startup_event():
    """أحداث بدء التشغيل"""
    logger.info("🏜️ Qreen Contextual Engine starting...")
    logger.info("Loading embedding model...")
    logger.info("Initializing ChromaDB...")
    logger.info("✅ Qreen is ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """أحداث إيقاف التشغيل"""
    logger.info("🏜️ Qreen shutting down gracefully...")
    memory_engine.close()


# ============================================================
# Run with: uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
# ============================================================
