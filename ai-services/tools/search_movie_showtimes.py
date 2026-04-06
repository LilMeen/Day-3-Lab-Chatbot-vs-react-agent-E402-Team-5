import difflib
from datetime import datetime, timedelta

from tools.base import (
    MOVIES, SHOWTIMES, THEATERS,
    get_movie_by_id, get_theater_by_id, get_screen,
    register_tool
)

# Vietnamese + English keyword mappings for date/time
DATE_KEYWORDS = {
    "hom nay": 0, "today": 0,
    "ngay mai": 1, "tomorrow": 1,
    "ngay kia": 2, "mot": 2,
    "cuoi tuan": "weekend",
}

TIME_KEYWORDS = {
    "sang": (0, 12), "morning": (0, 12), "buoi sang": (0, 12),
    "trua": (11, 14), "noon": (11, 14),
    "chieu": (12, 18), "afternoon": (12, 18), "buoi chieu": (12, 18),
    "toi": (18, 24), "evening": (18, 24), "buoi toi": (18, 24),
    "dem": (20, 24), "night": (20, 24),
}


def _fuzzy_match_movie(query: str) -> list[dict]:
    """Find movies matching a query string using fuzzy matching."""
    query_lower = query.lower()
    matches = []
    for movie in MOVIES:
        title_lower = movie["title"].lower()
        # Direct substring match
        if query_lower in title_lower or title_lower in query_lower:
            matches.append(movie)
            continue
        # Check each word in query against title
        query_words = query_lower.split()
        for word in query_words:
            if len(word) >= 3 and word in title_lower:
                matches.append(movie)
                break
        else:
            # Fuzzy ratio
            ratio = difflib.SequenceMatcher(None, query_lower, title_lower).ratio()
            if ratio > 0.4:
                matches.append(movie)
    return matches


def _parse_date(query: str) -> list[str] | None:
    """Parse date from natural language query."""
    query_lower = query.lower()
    today = datetime.now()

    for keyword, offset in DATE_KEYWORDS.items():
        if keyword in query_lower:
            if offset == "weekend":
                # Find next Saturday and Sunday
                days_until_sat = (5 - today.weekday()) % 7
                if days_until_sat == 0 and today.weekday() == 5:
                    days_until_sat = 0
                sat = today + timedelta(days=days_until_sat)
                sun = sat + timedelta(days=1)
                return [sat.strftime("%Y-%m-%d"), sun.strftime("%Y-%m-%d")]
            return [(today + timedelta(days=offset)).strftime("%Y-%m-%d")]

    # Try to find a date pattern like "7/4", "07-04", "2026-04-07"
    import re
    date_match = re.search(r'(\d{1,2})[/-](\d{1,2})', query)
    if date_match:
        day, month = int(date_match.group(1)), int(date_match.group(2))
        try:
            dt = datetime(today.year, month, day)
            return [dt.strftime("%Y-%m-%d")]
        except ValueError:
            pass

    return None


def _parse_time_range(query: str) -> tuple[int, int] | None:
    """Parse time range from natural language."""
    query_lower = query.lower()
    for keyword, time_range in TIME_KEYWORDS.items():
        if keyword in query_lower:
            return time_range
    return None


def search_movie_showtimes(query: str) -> dict:
    """Search for movie showtimes using natural language query."""
    matched_movies = _fuzzy_match_movie(query)
    target_dates = _parse_date(query)
    time_range = _parse_time_range(query)

    # Filter showtimes
    results = []
    for st in SHOWTIMES:
        movie = get_movie_by_id(st["movie_id"])
        if not movie:
            continue

        # Filter by movie if any matched
        if matched_movies and movie not in matched_movies:
            continue

        # Filter by date
        if target_dates and st["date"] not in target_dates:
            continue

        # Filter by time range
        if time_range:
            hour = int(st["time"].split(":")[0])
            if not (time_range[0] <= hour < time_range[1]):
                continue

        theater = get_theater_by_id(st["theater_id"])
        screen = get_screen(st["theater_id"], st["screen_id"])

        results.append({
            "showtime_id": st["id"],
            "movie": movie["title"],
            "theater": theater["name"] if theater else "Unknown",
            "location": theater["location"] if theater else "",
            "screen_type": screen["type"] if screen else "Unknown",
            "date": st["date"],
            "time": st["time"],
            "available_seats": st["available_seats"],
            "language": st["language"],
            "subtitle": st["subtitle"]
        })

    if not results:
        return {
            "status": "no_results",
            "message": f"Khong tim thay suat chieu phu hop voi '{query}'. Vui long thu lai voi tu khoa khac.",
            "suggestions": [m["title"] for m in MOVIES[:5]]
        }

    return {
        "status": "success",
        "count": len(results),
        "showtimes": results[:15]  # Limit to 15 results
    }


register_tool(
    name="search_movie_showtimes",
    description="Tim kiem suat chieu phim bang ngon ngu tu nhien. Ho tro tim theo ten phim, ngay (hom nay, ngay mai, cuoi tuan), va khung gio (sang, chieu, toi).",
    parameters={
        "query": {"type": "string", "description": "Cau truy van ngon ngu tu nhien, vi du: 'Dune chieu ngay mai toi'", "required": True}
    },
    function=search_movie_showtimes
)
