import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .state import AgentState
from .graph import graph
from .config import settings


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    text: str
    instructions: list[dict]
    suggestions: list[str]


sessions: dict[str, AgentState] = {}


def get_or_create_session(session_id: str | None) -> tuple[str, AgentState]:
    sid = session_id or str(uuid.uuid4())
    if sid not in sessions:
        sessions[sid] = AgentState(
            session_id=sid,
            messages=[],
            user_input="",
            intent=None,
            constraints=None,
            missing=[],
            tool_results=[],
            reply_text="",
            instructions=[],
            suggestions=[],
            relax_history=[],
        )
    return sid, sessions[sid]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    sessions.clear()


app = FastAPI(title="RailwayMap Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "message is required")

    sid, state = get_or_create_session(req.session_id)

    state["user_input"] = req.message.strip()
    state["messages"].append({"role": "user", "content": req.message.strip()})
    state["tool_results"] = []
    state["instructions"] = []
    state["suggestions"] = []
    state["reply_text"] = ""

    result = await graph.ainvoke(state)

    sessions[sid] = {**state, **result}

    reply = sessions[sid].get("reply_text", "")
    instructions = sessions[sid].get("instructions", [])
    suggestions = sessions[sid].get("suggestions", [])

    sessions[sid]["messages"].append({"role": "agent", "content": reply})

    return ChatResponse(
        session_id=sid,
        text=reply,
        instructions=instructions,
        suggestions=suggestions,
    )


@app.get("/api/agent/health")
async def health():
    return {"status": "ok", "model": settings.llm_model}
