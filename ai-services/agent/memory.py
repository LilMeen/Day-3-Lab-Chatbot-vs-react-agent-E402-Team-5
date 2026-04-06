from collections import deque
from datetime import datetime


class ShortTermMemory:
    """Short-term memory storing the 3 most recent conversation turns per session.
    Each entry stores: user message (trigger) → agent response (result).
    Acts as the Observation component in the ReAct loop."""

    def __init__(self, max_entries: int = 3):
        self._store: dict[str, deque] = {}
        self.max_entries = max_entries

    def get_history(self, session_id: str) -> list[dict]:
        return list(self._store.get(session_id, []))

    def add_entry(self, session_id: str, user_message: str, agent_response_text: str):
        """Add a completed turn to memory.

        Args:
            user_message: The user message that triggered this turn (the cause).
            agent_response_text: The full 5-field agent response text (the result).
        """
        if session_id not in self._store:
            self._store[session_id] = deque(maxlen=self.max_entries)
        self._store[session_id].append({
            "user": user_message,
            "response": agent_response_text,
            "timestamp": datetime.now().isoformat()
        })

    def clear(self, session_id: str):
        self._store.pop(session_id, None)

    def format_for_prompt(self, session_id: str) -> str:
        """Format memory as previous turns: user message first, then agent response."""
        history = self.get_history(session_id)
        if not history:
            return "No previous conversation history."

        parts = []
        for i, entry in enumerate(history, 1):
            parts.append(
                f"--- Previous Turn {i} ---\n"
                f"User: {entry['user']}\n\n"
                f"{entry['response']}"
            )
        return "\n\n".join(parts)
