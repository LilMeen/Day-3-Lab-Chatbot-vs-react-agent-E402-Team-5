from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agent.react_agent import ReActAgent
from agent.models import ReActStep

router = APIRouter(prefix="/agent", tags=["agent"])

# Single agent instance shared across requests (holds in-memory session store)
_agent = ReActAgent()


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ToolActionOut(BaseModel):
    tool: str
    parameters: dict


class ReActStepOut(BaseModel):
    reflection: str
    plan: str
    thought: str
    action: Optional[ToolActionOut] = None
    tool_result: Optional[str] = None
    output: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    steps: list[ReActStepOut]
    final_answer: str
    tools_used: list[str]


class ResetRequest(BaseModel):
    session_id: str


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _step_to_out(step: ReActStep) -> ReActStepOut:
    return ReActStepOut(
        reflection=step.reflection,
        plan=step.plan,
        thought=step.thought,
        action=ToolActionOut(tool=step.action.tool, parameters=step.action.parameters) if step.action else None,
        tool_result=step.tool_result,
        output=step.output,
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a user message and get the full ReAct response."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    response = _agent.run(req.session_id, req.message)

    return ChatResponse(
        session_id=response.session_id,
        steps=[_step_to_out(s) for s in response.steps],
        final_answer=response.final_answer,
        tools_used=response.tools_used,
    )


@router.post("/reset")
def reset(req: ResetRequest):
    """Clear the short-term memory for a session."""
    _agent.reset_memory(req.session_id)
    return {"status": "ok", "session_id": req.session_id, "message": "Memory cleared."}


@router.get("/health")
def health():
    """Health check."""
    return {
        "status": "ok",
        "provider": _agent.provider,
        "model": _agent.model,
    }
