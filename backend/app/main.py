"""Mnemos — FastAPI entrypoint.

Exposes the agent investigation API and a /health endpoint.
The agent loop, memory reader/writer, and tool router live in app.agent.

Run from the project root:  uvicorn backend.app.main:app --port 8000
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.exceptions import ConnectionError as RedisConnectionError

from backend.app.api.routes import init_agent, router as agent_router

logger = logging.getLogger("mnemos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_agent()
    except Exception as e:  # routes retry lazily, so don't crash on startup
        logger.warning("Agent init deferred: %s", e)
    yield


app = FastAPI(
    title="Mnemos",
    description="Autonomous threat hunter with persistent graph memory on FalkorDB.",
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

app.include_router(agent_router)


@app.exception_handler(RedisConnectionError)
async def falkordb_unreachable(request: Request, exc: RedisConnectionError):
    host = os.environ.get("FALKORDB_HOST", "localhost")
    port = os.environ.get("FALKORDB_PORT", "6379")
    return JSONResponse(
        status_code=503,
        content={"detail": f"FalkorDB unreachable at {host}:{port}. Is it running?"},
    )


@app.get("/health")
async def health():
    """Liveness check. docker-compose depends on this."""
    return {
        "status": "ok",
        "service": "mnemos-backend",
        "falkordb_host": os.environ.get("FALKORDB_HOST", "localhost"),
        "falkordb_port": os.environ.get("FALKORDB_PORT", "6379"),
    }


@app.get("/")
async def root():
    return {"name": "Mnemos", "tagline": "Agents forget. The graph remembers."}
