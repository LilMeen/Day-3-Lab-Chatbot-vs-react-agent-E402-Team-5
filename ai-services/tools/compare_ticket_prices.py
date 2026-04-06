from tools.base import (
    SHOWTIMES, get_movie_by_id, get_theater_by_id, get_screen,
    calculate_price, register_tool
)
from tools.search_movie_showtimes import _fuzzy_match_movie


def compare_ticket_prices(movie_title: str, date: str = "", seat_type: str = "regular") -> dict:
    """Compare ticket prices for a movie across different theaters."""
    matched_movies = _fuzzy_match_movie(movie_title)
    if not matched_movies:
        return {
            "status": "no_results",
            "message": f"Khong tim thay phim '{movie_title}'."
        }

    movie_ids = {m["id"] for m in matched_movies}
    comparisons = []

    for st in SHOWTIMES:
        if st["movie_id"] not in movie_ids:
            continue
        if date and st["date"] != date:
            continue

        movie = get_movie_by_id(st["movie_id"])
        theater = get_theater_by_id(st["theater_id"])
        screen = get_screen(st["theater_id"], st["screen_id"])
        if not movie or not theater or not screen:
            continue

        price_info = calculate_price(screen["type"], st["time"], st["date"], seat_type)

        comparisons.append({
            "showtime_id": st["id"],
            "movie": movie["title"],
            "theater": theater["name"],
            "location": theater["location"],
            "screen_type": screen["type"],
            "date": st["date"],
            "time": st["time"],
            "seat_type": seat_type,
            "price": price_info["final_price"],
            "formatted_price": f"{price_info['final_price']:,.0f} VND",
            "available_seats": st["available_seats"]
        })

    # Sort by price ascending
    comparisons.sort(key=lambda x: x["price"])

    if not comparisons:
        return {
            "status": "no_results",
            "message": f"Khong tim thay suat chieu cho '{movie_title}'" + (f" vao ngay {date}" if date else "") + "."
        }

    cheapest = comparisons[0]
    most_expensive = comparisons[-1]

    return {
        "status": "success",
        "movie": matched_movies[0]["title"],
        "seat_type": seat_type,
        "total_options": len(comparisons),
        "cheapest": {
            "theater": cheapest["theater"],
            "price": cheapest["formatted_price"],
            "time": f"{cheapest['date']} {cheapest['time']}",
            "screen": cheapest["screen_type"]
        },
        "most_expensive": {
            "theater": most_expensive["theater"],
            "price": most_expensive["formatted_price"],
            "time": f"{most_expensive['date']} {most_expensive['time']}",
            "screen": most_expensive["screen_type"]
        },
        "price_difference": f"{most_expensive['price'] - cheapest['price']:,.0f} VND",
        "all_options": comparisons[:10]  # Top 10
    }


register_tool(
    name="compare_ticket_prices",
    description="So sanh gia ve cua mot phim giua cac rap khac nhau. Sap xep theo gia tu thap den cao.",
    parameters={
        "movie_title": {"type": "string", "description": "Ten phim can so sanh gia", "required": True},
        "date": {"type": "string", "description": "Ngay cu the (YYYY-MM-DD). De trong neu muon xem tat ca ngay", "required": False},
        "seat_type": {"type": "string", "description": "Loai ghe: regular, premium, couple. Mac dinh: regular", "required": False}
    },
    function=compare_ticket_prices
)
