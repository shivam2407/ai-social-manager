"""FastAPI application — REST API for the AI Social Media Manager."""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db, init_db
from app.graph.builder import compile_graph
from app.models import Generation, Post, User
from app.routers import auth as auth_router
from app.routers import brands as brands_router
from app.routers import history as history_router
from app.schemas import (
    BrandProfile,
    FinalPost,
    GenerateRequest,
    GenerateResponse,
    Platform,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)

# Maximum stored results to prevent unbounded memory growth
MAX_STORED_RESULTS = 500

# ── Global state ────────────────────────────────────────────────
checkpointer = MemorySaver()
graph = None
run_results: OrderedDict[str, dict[str, Any]] = OrderedDict()  # thread_id -> result


def _store_result(thread_id: str, data: dict[str, Any]) -> None:
    """Store a result, evicting oldest entries if at capacity."""
    run_results[thread_id] = data
    while len(run_results) > MAX_STORED_RESULTS:
        run_results.popitem(last=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compile the graph on startup; validate env vars; init DB."""
    global graph

    # Validate required environment variables at startup
    if not os.environ.get("GROQ_API_KEY"):
        logger.error("GROQ_API_KEY environment variable is not set!")
        raise RuntimeError("GROQ_API_KEY environment variable is required")

    logger.info("Initializing database...")
    await init_db()

    logger.info("Compiling LangGraph multi-agent graph...")
    graph = compile_graph(checkpointer=checkpointer)
    logger.info("Graph ready. API is live.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AI Social Media Manager",
    description=(
        "Multi-agent content generation pipeline powered by LangGraph + Claude. "
        "Generates platform-specific social media content with trend research, "
        "strategic planning, writing, and quality review."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: restrict to known frontend origins (configurable via env var)
_allowed_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# ── Routers ────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(brands_router.router)
app.include_router(history_router.router)

# ── Endpoints ───────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "graph_compiled": graph is not None}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_content(
    request: GenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger the full content generation pipeline.

    Runs all 4 agents: trend researcher → strategist → writer → critic
    with automatic revision cycles if quality score < 7.
    """
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not compiled yet")

    thread_id = str(uuid.uuid4())

    brand_profile = BrandProfile(
        name=request.brand_name,
        niche=request.niche,
        target_audience=request.target_audience,
        voice_description=request.voice_description,
        tone_keywords=request.tone_keywords,
        example_posts=request.example_posts,
    )

    initial_state = {
        "brand_profile": brand_profile.model_dump(),
        "content_request": request.content_request,
        "target_platforms": [p.value for p in request.target_platforms],
        "messages": [],
        "trending_topics": [],
        "competitor_insights": [],
        "content_plan": {},
        "selected_angles": [],
        "drafts": {},
        "critic_scores": {},
        "critic_summary": "",
        "revision_count": 0,
        "approved": False,
        "final_posts": {},
    }

    config = {"configurable": {"thread_id": thread_id}}

    logger.info("Starting generation pipeline (thread: %s)", thread_id)

    try:
        result = await graph.ainvoke(initial_state, config=config)

        final_posts = []
        for platform_key, post_data in result.get("final_posts", {}).items():
            try:
                # Handle content that may be a list (e.g. Twitter threads)
                content = post_data.get("content", "")
                if isinstance(content, list):
                    content = "\n\n".join(str(item) for item in content)

                final_posts.append(FinalPost(
                    platform=Platform(post_data.get("platform", platform_key)),
                    content=content,
                    hashtags=post_data.get("hashtags", []),
                    call_to_action=post_data.get("call_to_action", ""),
                    content_type=post_data.get("content_type", "single_post"),
                    image_prompt=post_data.get("image_prompt", ""),
                    critic_score=post_data.get("critic_score", 0),
                ))
            except Exception as e:
                logger.warning("Failed to parse post for %s: %s", platform_key, e)

        response = GenerateResponse(
            thread_id=thread_id,
            status="completed",
            posts=final_posts,
            revision_count=result.get("revision_count", 0),
            critic_summary=result.get("critic_summary", ""),
        )

        # Save generation + posts to database
        try:
            gen = Generation(
                user_id=user.id,
                thread_id=thread_id,
                content_request=request.content_request,
                brand_name=request.brand_name,
                status="completed",
                revision_count=result.get("revision_count", 0),
                critic_summary=result.get("critic_summary", ""),
            )
            db.add(gen)
            await db.flush()

            for fp in final_posts:
                db.add(Post(
                    generation_id=gen.id,
                    platform=fp.platform.value,
                    content=fp.content,
                    hashtags=fp.hashtags,
                    call_to_action=fp.call_to_action,
                    content_type=fp.content_type,
                    image_prompt=fp.image_prompt,
                    critic_score=fp.critic_score,
                ))
            await db.commit()
        except Exception as e:
            logger.error("Failed to save generation to DB: %s", e)

        # Store result for status lookups (bounded)
        _store_result(thread_id, {
            "status": "completed",
            "response": response.model_dump(),
        })

        logger.info(
            "Generation complete (thread: %s, posts: %d, revisions: %d)",
            thread_id,
            len(final_posts),
            result.get("revision_count", 0),
        )

        return response

    except Exception as e:
        logger.error("Generation failed (thread: %s): %s", thread_id, e, exc_info=True)
        _store_result(thread_id, {"status": "failed", "error": str(e)})
        # Don't leak internal error details to client
        raise HTTPException(status_code=500, detail="Content generation failed. Please try again.")


def _validate_thread_id(thread_id: str) -> None:
    """Validate that a thread_id looks like a UUID."""
    try:
        uuid.UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread ID format")


@app.get("/api/generate/{thread_id}/stream")
async def stream_generation(thread_id: str):
    """Stream generation progress via Server-Sent Events.

    Streams node entry/exit events so the frontend can show real-time progress.
    """
    _validate_thread_id(thread_id)
    if graph is None:
        raise HTTPException(status_code=503, detail="Graph not compiled yet")

    async def event_stream():
        config = {"configurable": {"thread_id": thread_id}}

        try:
            async for event in graph.astream_events(
                None, config=config, version="v2"
            ):
                kind = event.get("event", "")
                if kind in ("on_chain_start", "on_chain_end"):
                    name = event.get("name", "unknown")
                    data = json.dumps({"event": kind, "node": name})
                    yield f"data: {data}\n\n"
        except Exception as e:
            logger.error("SSE stream error (thread: %s): %s", thread_id, e, exc_info=True)
            yield f"data: {json.dumps({'event': 'error', 'detail': 'Stream error occurred'})}\n\n"

        yield f"data: {json.dumps({'event': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/status/{thread_id}")
async def get_status(thread_id: str):
    """Check the status of a generation run."""
    _validate_thread_id(thread_id)
    if thread_id in run_results:
        return run_results[thread_id]

    # Check the checkpointer for in-progress runs
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await graph.aget_state(config)
        if state and state.values:
            return {
                "status": "in_progress",
                "revision_count": state.values.get("revision_count", 0),
                "approved": state.values.get("approved", False),
            }
    except Exception:
        pass

    raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")


# ── Entry point for development ─────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
