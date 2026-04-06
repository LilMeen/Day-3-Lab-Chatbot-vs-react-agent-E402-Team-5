from collections import deque
from datetime import datetime


class ShortTermMemory:
    """Short-term memory storing the 3 most recent conversation turns per session.
    Uses CyBench-style response-observation pairs as the Observation component."""

    def __init__(self, max_entries: int = 3):
        # Each entry: {response: full agent text, observation: next user message}
        self._store: dict[str, deque] = {}
        self.max_entries = max_entries

    def get_history(self, session_id: str) -> list[dict]:
        return list(self._store.get(session_id, []))

    def add_entry(self, session_id: str, agent_response_text: str, user_observation: str):
        """Add a completed turn to memory.

        Args:
            agent_response_text: The full formatted agent response (all 5 fields as plain text).
            user_observation: The user message that followed (acts as the Observation).
        """
        if session_id not in self._store:
            self._store[session_id] = deque(maxlen=self.max_entries)
        self._store[session_id].append({
            "response": agent_response_text,
            "observation": user_observation,
            "timestamp": datetime.now().isoformat()
        })

    def clear(self, session_id: str):
        self._store.pop(session_id, None)

    def format_for_prompt(self, session_id: str) -> str:
        """Format memory as CyBench-style response-observation pairs for the prompt."""
        history = self.get_history(session_id)
        if not history:
            return "No previous conversation history."

        lines = []
        for i, entry in enumerate(history, 1):
            lines.append(f"--- Previous Turn {i} ---")
            lines.append(entry["response"])
            lines.append(f"Observation:\n{entry['observation']}")
        return "\n\n".join(lines)
