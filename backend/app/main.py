"""Mnemos — FastAPI entrypoint.

Exposes the agent investigation API and a /health endpoint.
The agent loop, memory reader/writer, and tool router live in app.agent.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as agent_router

app = FastAPI(
    title="Mnemos",
    description="Autonomous threat hunter with persistent graph memory on FalkorDB.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)


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