import os
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from crawling.crawl import get_movie_schedules


# Khởi tạo Router
router = APIRouter(prefix="/api/v1", tags=["AI Chat Services"])


# --- DATA MODELS ---
class ChatRequest(BaseModel):
    user_message: str


class ChatResponse(BaseModel):
    status: str
    bot_type: str
    reply: str


class MovieMeta(BaseModel):
    title: str
    description: str
    poster_url: str


class MovieScheduleResponse(BaseModel):
    status: str
    movie_url: str
    total: int
    movie: MovieMeta
    schedules: list[dict[str, Any]]


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



# --- ENDPOINTS ---
@router.post("/baseline", response_model=ChatResponse)
async def chat_baseline(request: ChatRequest):
    """Bot cơ bản, chỉ dùng não LLM, KHÔNG dùng tool"""
    try:
        #reply = llm.invoke(request.user_message).content
        reply = ""
        return ChatResponse(status="success", bot_type="baseline", reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent", response_model=ChatResponse)
async def chat_react_agent(request: ChatRequest):
    """Bot thông minh, dùng ReAct Agent và Tool để cào data thực tế"""
    try:
        # Cách gọi AI MỚI: dùng .invoke thay vì .run
        # response = agent_executor.invoke({"input": request.user_message})

        # Lấy câu trả lời cuối cùng từ Output
        reply = ""
        return ChatResponse(status="success", bot_type="react_agent", reply=reply)
    except Exception as e:
        # Nhánh Bonus (Fallback Path) khi có lỗi
        return ChatResponse(
            status="error",
            bot_type="fallback",
            reply="Hệ thống AI đang quá tải hoặc lỗi mạng. Vui lòng liên hệ nhân viên hỗ trợ."
        )


@router.get("/movie-schedules", response_model=MovieScheduleResponse)
async def movie_schedules(movie_url: str, debug_html: bool = False):
    """Lấy lịch chiếu phim từ URL trang movie của Cinestar."""
    try:
        data = get_movie_schedules(movie_url=movie_url, debug_html=debug_html)
        schedules = data.get("schedules", []) if isinstance(data, dict) else []
        movie = data.get("movie", {}) if isinstance(data, dict) else {}

        return MovieScheduleResponse(
            status="success",
            movie_url=movie_url,
            total=_count_showtimes(schedules),
            movie=MovieMeta(
                title=str(movie.get("title", "Unknown Movie")),
                description=str(movie.get("description", "")),
                poster_url=str(movie.get("poster_url", "")),
            ),
            schedules=schedules,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))