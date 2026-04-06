import os
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

import config
from agent.react_agent import ReActAgent
from crawling.crawl import get_movie_schedules
from tools.cinestar_tools import (
    get_all_movies,
    get_movie_details,
    get_discount,
    get_movie_schedule,
    get_movie_prices,
    get_locations,
    set_runtime_mode,
)

# Set API mode so smart_followup returns awaiting_input instead of blocking input()
set_runtime_mode("api")

# Khởi tạo Router
router = APIRouter(prefix="/api/v1", tags=["AI Chat Services"])

# ReAct agent instance (shared, holds session memory)
_react_agent = ReActAgent()
LLM_TIMEOUT_SEC = int(os.getenv("LLM_TIMEOUT_SEC", "45"))

# ------------------------------------------------------------------
# LLM caller for baseline (no tools, no ReAct)
# ------------------------------------------------------------------

OUT_OF_DOMAIN_REPLY = (
    "Xin lỗi, tôi chỉ có thể hỗ trợ các câu hỏi liên quan đến rạp chiếu phim "
    "như lịch chiếu, giá vé, khuyến mãi và gợi ý phim. "
    "Bạn có câu hỏi nào về phim không? 🎬"
)

_DOMAIN_CLASSIFIER_PROMPT = """You are a domain classifier for a movie theater chatbot.
Determine if the user's message is related to the movie theater domain.

IN-DOMAIN topics: movies, showtimes, ticket prices, promotions, theater locations, seat types, film genres, booking, concessions.
OUT-OF-DOMAIN topics: everything else (politics, cooking, math, coding, weather, health, sports unrelated to movies, etc.).

Reply with ONLY one word: IN or OUT.

User message: {message}"""


def _is_out_of_domain(user_message: str) -> bool:
    """Use LLM as a fast classifier to detect out-of-domain messages."""
    prompt = _DOMAIN_CLASSIFIER_PROMPT.format(message=user_message)
    provider = config.LLM_PROVIDER.lower()

    try:
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=5,
            )
            verdict = (response.choices[0].message.content or "").strip().upper()

        elif provider == "gemini":
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config={"temperature": 0},
            )
            verdict = (response.text or "").strip().upper()

        else:
            return False  # Unknown provider — let it pass

        return verdict.startswith("OUT")

    except Exception:
        return False  # On classifier error — let it pass, don't block user


def _run_with_timeout(func, *args):
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args)
        try:
            return future.result(timeout=LLM_TIMEOUT_SEC)
        except FuturesTimeoutError:
            return None


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
    awaiting_input: bool = False
    followup_question: str = ""
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


# ------------------------------------------------------------------
# Cinestar Data Endpoints
# ------------------------------------------------------------------

@router.get("/movies")
async def api_get_all_movies(status: str = Query("showing", description="showing | coming | all")):
    """Danh sách phim đang chiếu hoặc sắp chiếu."""
    try:
        return get_all_movies(status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movies/details")
async def api_get_movie_details(movie_name: str = Query(..., description="Tên phim")):
    """Chi tiết một bộ phim: đạo diễn, diễn viên, mô tả..."""
    try:
        return get_movie_details(movie_name=movie_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movies/schedule")
async def api_get_movie_schedule(
    movie_name: str = Query(..., description="Tên phim"),
    locality: str = Query("", description="Lọc theo thành phố, ví dụ: HCM"),
):
    """Lịch chiếu của một bộ phim theo rạp và ngày."""
    try:
        return get_movie_schedule(movie_name=movie_name, locality=locality)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movies/prices")
async def api_get_movie_prices(movie_name: str = Query(..., description="Tên phim")):
    """Giá vé thật của một bộ phim (scrape qua Playwright)."""
    try:
        return get_movie_prices(movie_name=movie_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/movies/locations")
async def api_get_locations(movie_name: str = Query(..., description="Tên phim")):
    """Danh sách rạp và thành phố đang chiếu một bộ phim."""
    try:
        return get_locations(movie_name=movie_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discounts")
async def api_get_discount():
    """Khuyến mãi hiện có tại Cinestar."""
    try:
        return get_discount()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/baseline", response_model=ChatResponse)
async def chat_baseline(request: ChatRequest):
    """Bot cơ bản: chỉ dùng LLM, KHÔNG dùng tool hay ReAct loop."""
    ood_result = _run_with_timeout(_is_out_of_domain, request.user_message)
    if ood_result is True:
        return ChatResponse(status="out_of_domain", bot_type="baseline", reply=OUT_OF_DOMAIN_REPLY)

    try:
        reply = _run_with_timeout(_call_llm_baseline, request.user_message)
        if reply is None:
            return ChatResponse(
                status="error",
                bot_type="baseline",
                reply="Baseline model timeout. Vui lòng thử lại hoặc chuyển sang Agent.",
                session_id=request.session_id,
            )
        return ChatResponse(status="success", bot_type="baseline", reply=reply)
    except Exception as e:
        return ChatResponse(
            status="error",
            bot_type="baseline",
            reply="Baseline model gặp lỗi nội bộ. Vui lòng thử lại sau.",
            session_id=request.session_id,
        )


@router.post("/agent", response_model=ChatResponse)
async def chat_react_agent(request: ChatRequest):
    """Bot thông minh: dùng ReAct Agent với 7 tools để tra cứu dữ liệu thực tế."""
    ood_result = _run_with_timeout(_is_out_of_domain, request.user_message)
    if ood_result is True:
        return ChatResponse(status="out_of_domain", bot_type="react_agent", reply=OUT_OF_DOMAIN_REPLY)
    try:
        session_id = request.session_id or str(uuid.uuid4())
        response = _react_agent.run(session_id, request.user_message)
        if response.awaiting_input:
            return ChatResponse(
                status="awaiting_input",
                bot_type="react_agent",
                reply=response.followup_question,
                session_id=session_id,
                awaiting_input=True,
                followup_question=response.followup_question,
            )
        return ChatResponse(status="success", bot_type="react_agent", reply=response.final_answer, session_id=session_id)
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
