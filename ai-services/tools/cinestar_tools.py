"""
7 tools for the ReAct agent — all backed by real Cinestar data.

Tool list:
  1. get_all_movies       — list movies (đang chiếu / sắp chiếu / all)
  2. get_movie_details    — chi tiết một bộ phim
  3. get_discount         — khuyến mãi hiện có
  4. get_movie_schedule   — lịch chiếu theo rạp / địa phương / ngày
  5. get_movie_prices     — giá vé thật (Playwright click)
  6. get_locations        — danh sách rạp chiếu bộ phim đó
  7. smart_followup       — hỏi người dùng câu làm rõ (HITL)
"""

from __future__ import annotations

import difflib
import re
from functools import lru_cache
from typing import Any

from tools.base import register_tool

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _fetch_movies() -> list[dict]:
    """Fetch movie list from Cinestar (cached for process lifetime)."""
    from CrawData import get_all_movies  # type: ignore
    result = get_all_movies()
    return result if isinstance(result, list) else []


def _fuzzy_find(query: str, movies: list[dict]) -> list[dict]:
    """Return movies whose name fuzzy-matches the query."""
    q = query.lower()
    exact, partial, fuzzy = [], [], []

    for m in movies:
        title = (m.get("movie_name") or "").lower()
        if q == title:
            exact.append(m)
        elif q in title or title in q:
            partial.append(m)
        else:
            ratio = difflib.SequenceMatcher(None, q, title).ratio()
            if ratio > 0.45:
                fuzzy.append((ratio, m))

    if exact:
        return exact
    if partial:
        return partial
    if fuzzy:
        fuzzy.sort(key=lambda x: -x[0])
        return [m for _, m in fuzzy[:3]]
    return []


def _movie_url(movie: dict) -> str:
    return movie.get("movie_url") or ""


def _get_schedule(movie: dict) -> list[dict]:
    from crawling.crawl import get_movie_schedules  # type: ignore
    url = _movie_url(movie)
    if not url:
        return []
    return get_movie_schedules(url)


# ---------------------------------------------------------------------------
# Tool 1 — get_all_movies
# ---------------------------------------------------------------------------

def get_all_movies(status: str = "showing") -> dict[str, Any]:
    """List movies from Cinestar homepage."""
    movies = _fetch_movies()

    if status == "showing":
        filtered = [m for m in movies if m.get("status") == "Đang chiếu"]
    elif status == "coming":
        filtered = [m for m in movies if m.get("status") == "Sắp chiếu"]
    else:
        filtered = movies

    return {
        "status": "success",
        "filter": status,
        "count": len(filtered),
        "movies": [
            {
                "movie_name": m.get("movie_name"),
                "category": m.get("category"),
                "status": m.get("status"),
                "release_date": m.get("release_date"),
                "movie_url": m.get("movie_url"),
            }
            for m in filtered
        ],
    }


register_tool(
    name="get_all_movies",
    description="Lấy danh sách phim từ Cinestar. Trả về tên, thể loại, trạng thái chiếu.",
    parameters={
        "status": {
            "type": "string",
            "description": "'showing' = đang chiếu (mặc định), 'coming' = sắp chiếu, 'all' = tất cả",
            "required": False,
        }
    },
    function=get_all_movies,
)


# ---------------------------------------------------------------------------
# Tool 2 — get_movie_details
# ---------------------------------------------------------------------------

def get_movie_details(movie_name: str) -> dict[str, Any]:
    """Get detailed info about a specific movie by name."""
    movies = _fetch_movies()
    matches = _fuzzy_find(movie_name, movies)

    if not matches:
        suggestions = [m.get("movie_name") for m in movies[:5]]
        return {
            "status": "not_found",
            "message": f"Không tìm thấy phim '{movie_name}'.",
            "suggestions": suggestions,
        }

    m = matches[0]
    return {
        "status": "success",
        "movie_name": m.get("movie_name"),
        "category": m.get("category"),
        "director": m.get("director"),
        "cast": m.get("cast"),
        "duration": m.get("time"),
        "release_date": m.get("release_date"),
        "description": m.get("description"),
        "status": m.get("status"),
        "movie_url": m.get("movie_url"),
    }


register_tool(
    name="get_movie_details",
    description="Lấy thông tin chi tiết một bộ phim: đạo diễn, diễn viên, thể loại, thời lượng, mô tả.",
    parameters={
        "movie_name": {
            "type": "string",
            "description": "Tên phim cần tra cứu (hỗ trợ tên gần đúng).",
            "required": True,
        }
    },
    function=get_movie_details,
)


# ---------------------------------------------------------------------------
# Tool 3 — get_discount
# ---------------------------------------------------------------------------

def get_discount() -> dict[str, Any]:
    """Get current promotions and discounts from Cinestar."""
    from CrawData import get_discount as _get_discount  # type: ignore

    result = _get_discount()
    if isinstance(result, dict) and "error" in result:
        return {"status": "error", "message": result["error"]}

    return {
        "status": "success",
        "count": len(result),
        "discounts": [
            {
                "name": d.get("discount_name"),
                "link": d.get("discount_link"),
            }
            for d in result
        ],
    }


register_tool(
    name="get_discount",
    description="Lấy danh sách khuyến mãi, ưu đãi hiện có tại Cinestar.",
    parameters={},
    function=get_discount,
)


# ---------------------------------------------------------------------------
# Tool 4 — get_movie_schedule
# ---------------------------------------------------------------------------

def get_movie_schedule(movie_name: str, locality: str = "") -> dict[str, Any]:
    """Get showtimes for a movie, optionally filtered by locality/city."""
    movies = _fetch_movies()
    matches = _fuzzy_find(movie_name, movies)

    if not matches:
        return {"status": "not_found", "message": f"Không tìm thấy phim '{movie_name}'."}

    movie = matches[0]
    schedules = _get_schedule(movie)

    if not schedules:
        return {
            "status": "no_schedule",
            "message": f"Không tìm thấy lịch chiếu cho '{movie.get('movie_name')}'.",
        }

    # Filter by locality if provided
    if locality:
        loc_q = locality.lower()
        schedules = [
            s for s in schedules
            if loc_q in (s.get("locality") or "").lower()
        ]
        if not schedules:
            return {
                "status": "no_results",
                "message": f"Không có lịch chiếu tại '{locality}'.",
            }

    # Compact output: locality → theatre → day → showtimes
    compact = []
    for loc in schedules:
        for theatre in loc.get("theatres", []):
            for mv in theatre.get("movies", []):
                for day in mv.get("schedule", []):
                    compact.append({
                        "locality": loc.get("locality"),
                        "theatre": theatre.get("theatre"),
                        "day": day.get("day"),
                        "showtimes": day.get("showtimes", []),
                    })

    return {
        "status": "success",
        "movie_name": movie.get("movie_name"),
        "total_showtimes": sum(len(r["showtimes"]) for r in compact),
        "schedule": compact,
    }


register_tool(
    name="get_movie_schedule",
    description="Lấy lịch chiếu của một bộ phim. Có thể lọc theo thành phố/khu vực.",
    parameters={
        "movie_name": {
            "type": "string",
            "description": "Tên phim (hỗ trợ tên gần đúng).",
            "required": True,
        },
        "locality": {
            "type": "string",
            "description": "Lọc theo thành phố, ví dụ: 'HCM', 'Hà Nội', 'Đà Nẵng'. Để trống = tất cả.",
            "required": False,
        },
    },
    function=get_movie_schedule,
)


# ---------------------------------------------------------------------------
# Tool 5 — get_movie_prices
# ---------------------------------------------------------------------------

def get_movie_prices(movie_name: str) -> dict[str, Any]:
    """Get real ticket prices for a movie by clicking on the first showtime (Playwright)."""
    movies = _fetch_movies()
    matches = _fuzzy_find(movie_name, movies)

    if not matches:
        return {"status": "not_found", "message": f"Không tìm thấy phim '{movie_name}'."}

    movie = matches[0]
    url = _movie_url(movie)
    if not url:
        return {"status": "error", "message": "Không có URL phim."}

    from crawling.crawl import get_ticket_prices_for_showtime  # type: ignore

    prices = get_ticket_prices_for_showtime(url)
    if not prices:
        return {
            "status": "no_data",
            "message": "Không lấy được giá vé (chưa có suất chiếu hoặc lỗi trình duyệt).",
        }

    return {
        "status": "success",
        "movie_name": movie.get("movie_name"),
        "note": "Giá lấy từ suất chiếu đầu tiên có sẵn trên trang Cinestar.",
        "prices": prices,
    }


register_tool(
    name="get_movie_prices",
    description="Lấy giá vé thật của một bộ phim (Người lớn, HSSV, Người cao tuổi, Đôi) từ trang Cinestar.",
    parameters={
        "movie_name": {
            "type": "string",
            "description": "Tên phim cần tra giá vé.",
            "required": True,
        }
    },
    function=get_movie_prices,
)


# ---------------------------------------------------------------------------
# Tool 6 — get_locations
# ---------------------------------------------------------------------------

def get_locations(movie_name: str) -> dict[str, Any]:
    """List all theaters and cities showing a specific movie."""
    movies = _fetch_movies()
    matches = _fuzzy_find(movie_name, movies)

    if not matches:
        return {"status": "not_found", "message": f"Không tìm thấy phim '{movie_name}'."}

    movie = matches[0]
    schedules = _get_schedule(movie)

    if not schedules:
        return {"status": "no_schedule", "message": "Không tìm thấy lịch chiếu."}

    locations: dict[str, list[str]] = {}
    for loc in schedules:
        locality = loc.get("locality", "Khác")
        theatres = [t.get("theatre", "") for t in loc.get("theatres", []) if t.get("theatre")]
        locations[locality] = theatres

    return {
        "status": "success",
        "movie_name": movie.get("movie_name"),
        "total_theatres": sum(len(v) for v in locations.values()),
        "locations": [
            {"city": city, "theatres": theatres}
            for city, theatres in locations.items()
        ],
    }


register_tool(
    name="get_locations",
    description="Lấy danh sách rạp chiếu phim và thành phố đang chiếu một bộ phim cụ thể.",
    parameters={
        "movie_name": {
            "type": "string",
            "description": "Tên phim cần tìm rạp chiếu.",
            "required": True,
        }
    },
    function=get_locations,
)


# ---------------------------------------------------------------------------
# HITL runtime mode — "cli" uses input(), "api" returns awaiting_input signal
# ---------------------------------------------------------------------------

_RUNTIME_MODE: str = "cli"


def set_runtime_mode(mode: str) -> None:
    global _RUNTIME_MODE
    _RUNTIME_MODE = mode


# ---------------------------------------------------------------------------
# Tool 7 — smart_followup
# ---------------------------------------------------------------------------

def smart_followup(question: str) -> dict[str, Any]:
    """
    Ask the user a clarifying question when their request is ambiguous.

    CLI:  blocks with input(), returns {"status": "answered", "user_reply": "..."}
    API:  returns {"status": "awaiting_input", "question": "..."}
          → react_agent detects this and surfaces the question to the frontend.
    """
    if _RUNTIME_MODE == "cli":
        print(f"\n🤔 {question}")
        try:
            reply = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            reply = ""
        return {"status": "answered", "question": question, "user_reply": reply}

    # API mode — signal interrupt
    return {"status": "awaiting_input", "question": question}


register_tool(
    name="smart_followup",
    description=(
        "Hỏi người dùng câu hỏi làm rõ khi yêu cầu còn mơ hồ. "
        "Dùng khi user đề cập đến phim nhưng không rõ muốn biết gì. "
        "Ví dụ: hỏi 'Bạn muốn biết về giá vé, lịch chiếu hay thông tin phim?'"
    ),
    parameters={
        "question": {
            "type": "string",
            "description": "Câu hỏi làm rõ với 2-3 lựa chọn cụ thể cho người dùng.",
            "required": True,
        }
    },
    function=smart_followup,
)
