"""FastAPI application — REST API for the AI Social Media Manager."""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.memory import MemorySaver

from app.graph.builder import compile_graph
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

# ── Global state ────────────────────────────────────────────────
checkpointer = MemorySaver()
graph = None
run_results: dict[str, dict[str, Any]] = {}  # thread_id -> result


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compile the graph on startup."""
    global graph
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ───────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "graph_compiled": graph is not None}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
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
                final_posts.append(FinalPost(
                    platform=Platform(post_data.get("platform", platform_key)),
                    content=post_data.get("content", ""),
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

        # Store result for status lookups
        run_results[thread_id] = {
            "status": "completed",
            "response": response.model_dump(),
        }

        logger.info(
            "Generation complete (thread: %s, posts: %d, revisions: %d)",
            thread_id,
            len(final_posts),
            result.get("revision_count", 0),
        )

        return response

    except Exception as e:
        logger.error("Generation failed (thread: %s): %s", thread_id, e, exc_info=True)
        run_results[thread_id] = {"status": "failed", "error": str(e)}
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")


@app.get("/api/generate/{thread_id}/stream")
async def stream_generation(thread_id: str):
    """Stream generation progress via Server-Sent Events.

    Streams node entry/exit events so the frontend can show real-time progress.
    """
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
            yield f"data: {json.dumps({'event': 'error', 'detail': str(e)})}\n\n"

        yield f"data: {json.dumps({'event': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/status/{thread_id}")
async def get_status(thread_id: str):
    """Check the status of a generation run."""
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

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
