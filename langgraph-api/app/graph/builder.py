"""LangGraph StateGraph builder — the core multi-agent orchestration.

Patterns demonstrated:
- StateGraph with typed state
- Conditional edges (score-based routing)
- Cycles (writer ↔ critic revision loop, capped at 3)
- **Durable checkpointing** via SqliteSaver — survives process crashes
  (MemorySaver loses all in-flight generations on restart)
- Clean node registration and edge definitions
"""

from __future__ import annotations

import logging
import os
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.critic import critic_node
from app.agents.strategist import strategist_node
from app.agents.trend_researcher import trend_researcher_node
from app.agents.writer import writer_node
from app.graph.state import SocialMediaState

logger = logging.getLogger(__name__)

# Path for durable checkpoint storage (SQLite)
CHECKPOINT_DB_PATH = os.environ.get(
    "CHECKPOINT_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "checkpoints.db"),
)

# Maximum revision cycles before force-approving
MAX_REVISIONS = 3


def should_revise(state: SocialMediaState) -> str:
    """Conditional edge: decide whether to revise drafts or finalize.

    This is the routing function that creates the writer ↔ critic cycle.

    Returns:
        "revise" — loop back to writer with critic feedback
        "finalize" — proceed to output (drafts approved or max revisions hit)
    """
    approved = state.get("approved", False)
    revision_count = state.get("revision_count", 0)

    if approved:
        logger.info("Drafts APPROVED — proceeding to finalize")
        return "finalize"

    if revision_count >= MAX_REVISIONS:
        logger.info(
            "Max revisions reached (%d/%d) — force finalizing",
            revision_count,
            MAX_REVISIONS,
        )
        return "finalize"

    logger.info(
        "Drafts need revision (%d/%d revisions used) — looping back to writer",
        revision_count,
        MAX_REVISIONS,
    )
    return "revise"


def finalize_posts(state: SocialMediaState) -> dict[str, Any]:
    """Terminal node: package approved drafts as final posts.

    Copies drafts to final_posts with status set to 'draft' (ready for
    human review or scheduling via n8n).
    """
    drafts = state.get("drafts", {})
    critic_scores = state.get("critic_scores", {})

    final_posts: dict[str, dict[str, Any]] = {}
    for platform, draft in drafts.items():
        score = critic_scores.get(platform, {})
        final_posts[platform] = {
            **draft,
            "critic_score": score.get("overall_score", 0),
            "status": "draft",
            "scheduled_at": None,
        }

    logger.info("Finalized %d posts", len(final_posts))
    return {"final_posts": final_posts}


def build_graph() -> StateGraph:
    """Construct the full content generation graph.

    Graph flow:
        START
          → trend_researcher  (research trends and competitors)
          → strategist        (plan content strategy per platform)
          → writer            (generate platform-specific drafts)
          → critic            (score and review drafts)
          → [conditional]
              ├─ "revise"   → writer  (revision cycle)
              └─ "finalize" → finalize_posts → END
    """
    graph = StateGraph(SocialMediaState)

    # ── Register nodes ──────────────────────────────────────────
    graph.add_node("trend_researcher", trend_researcher_node)
    graph.add_node("strategist", strategist_node)
    graph.add_node("writer", writer_node)
    graph.add_node("critic", critic_node)
    graph.add_node("finalize", finalize_posts)

    # ── Linear edges (research → strategy → first draft) ───────
    graph.add_edge(START, "trend_researcher")
    graph.add_edge("trend_researcher", "strategist")
    graph.add_edge("strategist", "writer")
    graph.add_edge("writer", "critic")

    # ── Conditional edge: the revision cycle ────────────────────
    graph.add_conditional_edges(
        "critic",
        should_revise,
        {
            "revise": "writer",     # Loop back for revision
            "finalize": "finalize",  # Proceed to output
        },
    )

    # ── Terminal edge ───────────────────────────────────────────
    graph.add_edge("finalize", END)

    return graph


def compile_graph(checkpointer=None):
    """Build and compile the graph with a checkpointer.

    The checkpointer enables:
    - **Durable persistence** — state survives process crashes
    - Resumable runs — if the process dies after step N, it resumes from step N
    - Human-in-the-loop (pause at checkpoints for approval)
    - Debugging (inspect state at any node)

    Pass a pre-built AsyncSqliteSaver from the lifespan for durable persistence,
    or None to use MemorySaver as fallback.
    """
    graph = build_graph()

    if checkpointer is None:
        checkpointer = MemorySaver()
        logger.info("Using in-memory checkpointer (state lost on restart)")

    compiled = graph.compile(checkpointer=checkpointer)
    logger.info("Graph compiled successfully with %s", type(checkpointer).__name__)
    return compiled
