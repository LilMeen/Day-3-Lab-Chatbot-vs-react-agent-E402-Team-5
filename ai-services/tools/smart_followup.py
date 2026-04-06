from tools.base import register_tool

# Runtime mode: "cli" uses input(), "api" returns interrupt signal
_RUNTIME_MODE = "cli"
_PENDING_USER_REPLY: str | None = None  # Pre-supplied reply for API mode


def set_runtime_mode(mode: str):
    """Call this at startup to set the runtime context ('cli' or 'api')."""
    global _RUNTIME_MODE
    _RUNTIME_MODE = mode


def set_pending_reply(reply: str | None):
    """In API mode, pre-supply the user's answer before running the agent."""
    global _PENDING_USER_REPLY
    _PENDING_USER_REPLY = reply


FOLLOWUP_PROMPTS = {
    "confirm_booking": {
        "intent": "confirm_booking",
        "question": (
            "Bạn muốn xác nhận đặt vé không?\n"
            "Vui lòng cho tôi biết:\n"
            "  - Loại ghế (regular / premium / couple)\n"
            "  - Số lượng vé\n"
            "  - Xác nhận: có / không"
        ),
    },
    "clarify_preference": {
        "intent": "clarify_preference",
        "question": (
            "Để giúp bạn tốt hơn, bạn có thể cho tôi biết thêm:\n"
            "  - Ngày / giờ muốn xem?\n"
            "  - Loại phòng ưu tiên (Standard / IMAX / 4DX / VIP)?\n"
            "  - Ngân sách cho vé (VND)?"
        ),
    },
    "suggest_alternative": {
        "intent": "suggest_alternative",
        "question": (
            "Bạn muốn tôi gợi ý thay thế như thế nào?\n"
            "  - Phim khác cùng thể loại?\n"
            "  - Suất chiếu khác?\n"
            "  - Rạp khác giá tốt hơn?\n"
            "Bạn muốn đổi theo hướng nào?"
        ),
    },
}


def smart_followup(context_summary: str, followup_type: str = "clarify_preference") -> dict:
    """Human-in-the-loop follow-up.

    - CLI mode: prints the question and waits for keyboard input.
    - API mode: returns an INTERRUPT signal so the router can pause the agent
      and ask the frontend to supply the answer in the next request.
    """
    global _PENDING_USER_REPLY

    if followup_type not in FOLLOWUP_PROMPTS:
        return {
            "status": "error",
            "message": (
                f"Invalid followup_type '{followup_type}'. "
                f"Choose: {', '.join(FOLLOWUP_PROMPTS.keys())}"
            ),
        }

    template = FOLLOWUP_PROMPTS[followup_type]
    question = template["question"]

    # --- CLI mode: block and read from stdin ---
    if _RUNTIME_MODE == "cli":
        print(f"\n[Agent cần thêm thông tin]\n{question}")
        print(f"(Context: {context_summary})\n")
        try:
            user_reply = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            user_reply = ""
        if not user_reply:
            user_reply = "(Người dùng không trả lời)"
        return {
            "status": "success",
            "followup_type": followup_type,
            "intent": template["intent"],
            "question_asked": question,
            "user_reply": user_reply,
        }

    # --- API mode ---
    if _PENDING_USER_REPLY is not None:
        # The frontend already sent the answer in this request
        reply = _PENDING_USER_REPLY
        _PENDING_USER_REPLY = None  # consume it
        return {
            "status": "success",
            "followup_type": followup_type,
            "intent": template["intent"],
            "question_asked": question,
            "user_reply": reply,
        }

    # No pre-supplied answer → interrupt: tell the router to stop and ask the client
    return {
        "status": "awaiting_input",
        "followup_type": followup_type,
        "intent": template["intent"],
        "question_asked": question,
        "user_reply": None,
    }


register_tool(
    name="smart_followup",
    description=(
        "Human-in-the-loop clarification tool. In CLI mode it pauses and reads keyboard input. "
        "In API mode it signals the router to pause and ask the client for more information. "
        "Use when the request is ambiguous or needs confirmation before proceeding."
    ),
    parameters={
        "context_summary": {
            "type": "string",
            "description": "Brief summary of what is unclear or needs confirmation",
            "required": True,
        },
        "followup_type": {
            "type": "string",
            "description": "confirm_booking | clarify_preference | suggest_alternative",
            "required": True,
        },
    },
    function=smart_followup,
)
