from pydantic import BaseModel
from typing import Optional


class ToolAction(BaseModel):
    tool: str
    parameters: dict


class ReActStep(BaseModel):
    reflection: str
    plan: str
    thought: str
    action: Optional[ToolAction] = None
    output: Optional[str] = None
    tool_result: Optional[str] = None


class AgentResponse(BaseModel):
    session_id: str
    steps: list[ReActStep]
    final_answer: str
    tools_used: list[str]
    awaiting_input: bool = False        # True when smart_followup interrupted
    followup_question: str = ""         # The clarifying question to show user
