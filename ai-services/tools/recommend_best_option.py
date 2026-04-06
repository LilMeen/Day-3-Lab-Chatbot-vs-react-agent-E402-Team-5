from tools.base import (
    MOVIES, SHOWTIMES,
    get_movie_by_id, get_theater_by_id, get_screen,
    calculate_price, register_tool
)
from tools.search_movie_showtimes import _fuzzy_match_movie


def recommend_best_option(
    movie_title: str = "",
    budget: float = 0,
    preferred_time: str = "",
    screen_type: str = ""
) -> dict:
    """Recommend the best movie options based on user preferences and budget."""

    # Filter movies if title given
    if movie_title:
        matched_movies = _fuzzy_match_movie(movie_title)
        movie_ids = {m["id"] for m in matched_movies}
    else:
        movie_ids = {m["id"] for m in MOVIES}

    # Score each showtime
    scored = []
    for st in SHOWTIMES:
        if st["movie_id"] not in movie_ids:
            continue
        if st["available_seats"] <= 0:
            continue

        movie = get_movie_by_id(st["movie_id"])
        theater = get_theater_by_id(st["theater_id"])
        screen = get_screen(st["theater_id"], st["screen_id"])
        if not movie or not theater or not screen:
            continue

        # Filter by screen type
        if screen_type and screen["type"].lower() != screen_type.lower():
            continue

        price_info = calculate_price(screen["type"], st["time"], st["date"])
        price = price_info["final_price"]

        # Filter by budget
        if budget > 0 and price > budget:
            continue

        # Score calculation
        score = 100.0

        # Price score: cheaper is better (relative to budget if given)
        if budget > 0:
            score += (budget - price) / budget * 30
        else:
            score -= price / 100000 * 10

        # Time preference match
        hour = int(st["time"].split(":")[0])
        if preferred_time:
            pt = preferred_time.lower()
            if ("sang" in pt or "morning" in pt) and hour < 12:
                score += 20
            elif ("chieu" in pt or "afternoon" in pt) and 12 <= hour < 18:
                score += 20
            elif ("toi" in pt or "evening" in pt) and hour >= 18:
                score += 20

        # Availability bonus
        if st["available_seats"] > 100:
            score += 10
        elif st["available_seats"] > 50:
            score += 5

        # Screen type quality bonus
        screen_bonus = {"VIP": 15, "IMAX": 12, "4DX": 10, "Standard": 0}
        score += screen_bonus.get(screen["type"], 0)

        scored.append({
            "showtime_id": st["id"],
            "movie": movie["title"],
            "genre": ", ".join(movie["genre"]),
            "theater": theater["name"],
            "screen_type": screen["type"],
            "date": st["date"],
            "time": st["time"],
            "price": price,
            "formatted_price": f"{price:,.0f} VND",
            "available_seats": st["available_seats"],
            "score": round(score, 1)
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_3 = scored[:3]

    if not top_3:
        return {
            "status": "no_results",
            "message": "Khong tim thay lua chon phu hop voi yeu cau cua ban.",
            "suggestions": "Thu noi rong ngan sach hoac thay doi khung gio mong muon."
        }

    return {
        "status": "success",
        "criteria": {
            "movie": movie_title or "Tat ca phim",
            "budget": f"{budget:,.0f} VND" if budget else "Khong gioi han",
            "preferred_time": preferred_time or "Bat ky",
            "screen_type": screen_type or "Bat ky"
        },
        "recommendations": top_3
    }


register_tool(
    name="recommend_best_option",
    description="Goi y lua chon xem phim toi uu dua tren ngan sach, so thich gio chieu, va loai phong chieu.",
    parameters={
        "movie_title": {"type": "string", "description": "Ten phim (de trong neu muon goi y tat ca)", "required": False},
        "budget": {"type": "number", "description": "Ngan sach toi da cho 1 ve (VND). Vi du: 150000", "required": False},
        "preferred_time": {"type": "string", "description": "Thoi gian uu tien: sang, chieu, toi", "required": False},
        "screen_type": {"type": "string", "description": "Loai phong: Standard, IMAX, 4DX, VIP", "required": False}
    },
    function=recommend_best_option
)
