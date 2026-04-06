import os
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from agent.react_agent import ReActAgent

# Khởi tạo Router
router = APIRouter(prefix="/api/v1", tags=["AI Chat Services"])

# ReAct agent instance (shared, holds session memory)
_react_agent = ReActAgent()

# ------------------------------------------------------------------
# LLM caller for baseline (no tools, no ReAct)
# ------------------------------------------------------------------

def _call_llm_baseline(user_message: str) -> str:
    """Call the LLM directly with a simple system prompt — no tools, no ReAct loop."""
    system_prompt = (
        "Bạn là trợ lý rạp chiếu phim thân thiện. "
        "Hãy trả lời câu hỏi của khách hàng về phim ảnh, suất chiếu và giá vé một cách ngắn gọn và hữu ích."
    )

    provider = config.LLM_PROVIDER.lower()

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
        return response.choices[0].message.content or ""

    elif provider == "gemini":
        from google import genai
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        full_prompt = f"{system_prompt}\n\nUser: {user_message}"
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=full_prompt,
            config={"temperature": 0},
        )
        return response.text or ""

    else:
        raise ValueError(f"Unsupported provider: {provider}")


# --- DATA MODELS ---

class ChatRequest(BaseModel):
    user_message: str
    session_id: str = ""          # Optional; auto-generated if empty


class ChatResponse(BaseModel):
    status: str
    bot_type: str
    reply: str
    session_id: str = ""
class MovieScheduleResponse(BaseModel):
    status: str
    movie_url: str
    total: int
    schedules: list[dict[str, Any]]

# --- ENDPOINTS ---

@router.get("/movie-schedules", response_model=MovieScheduleResponse)
async def movie_schedules(movie_url: str, debug_html: bool = False):
    """Lấy lịch chiếu phim từ URL trang movie của Cinestar."""
    try:
        schedules = get_movie_schedules(movie_url=movie_url, debug_html=debug_html)
        return MovieScheduleResponse(
            status="success",
            movie_url=movie_url,
            total=_count_showtimes(schedules),
            schedules=schedules,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/baseline", response_model=ChatResponse)
async def chat_baseline(request: ChatRequest):
    """Bot cơ bản: chỉ dùng LLM, KHÔNG dùng tool hay ReAct loop."""
    try:
        reply = _call_llm_baseline(request.user_message)
        return ChatResponse(
            status="success",
            bot_type="baseline",
            reply=reply,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent", response_model=ChatResponse)
async def chat_react_agent(request: ChatRequest):
    """Bot thông minh: dùng ReAct Agent với 7 tools để tra cứu dữ liệu thực tế."""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        response = _react_agent.run(session_id, request.user_message)
        return ChatResponse(
            status="success",
            bot_type="react_agent",
            reply=response.final_answer,
            session_id=session_id,
        )
    except Exception as e:
        return ChatResponse(
            status="error",
            bot_type="fallback",
            reply="Hệ thống AI đang quá tải hoặc lỗi mạng. Vui lòng liên hệ nhân viên hỗ trợ.",
            session_id=request.session_id,
        )
    
    
def _count_showtimes(grouped_schedules: list[dict[str, Any]]) -> int:
    total = 0
    for locality in grouped_schedules:
        theatres = locality.get("theatres", [])
        if not isinstance(theatres, list):
            continue

        for theatre in theatres:
            movies = theatre.get("movies", [])
            if not isinstance(movies, list):
                continue

            for movie in movies:
                schedule = movie.get("schedule", [])
                if not isinstance(schedule, list):
                    continue

                for day_item in schedule:
                    showtimes = day_item.get("showtimes", [])
                    if isinstance(showtimes, list):
                        total += len(showtimes)
    return total