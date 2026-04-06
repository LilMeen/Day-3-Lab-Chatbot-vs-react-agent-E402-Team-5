from tools.base import (
    get_showtime_by_id, get_screen, get_movie_by_id, get_theater_by_id,
    calculate_price, register_tool
)


def get_ticket_price(showtime_id: str, seat_type: str = "regular", quantity: int = 1) -> dict:
    """Get ticket price for a specific showtime."""
    showtime = get_showtime_by_id(showtime_id)
    if not showtime:
        return {"status": "error", "message": f"Khong tim thay suat chieu voi ID '{showtime_id}'"}

    screen = get_screen(showtime["theater_id"], showtime["screen_id"])
    if not screen:
        return {"status": "error", "message": "Khong tim thay thong tin phong chieu"}

    movie = get_movie_by_id(showtime["movie_id"])
    theater = get_theater_by_id(showtime["theater_id"])

    price_info = calculate_price(
        screen_type=screen["type"],
        time_str=showtime["time"],
        date_str=showtime["date"],
        seat_type=seat_type
    )

    total = price_info["final_price"] * quantity

    return {
        "status": "success",
        "movie": movie["title"] if movie else "Unknown",
        "theater": theater["name"] if theater else "Unknown",
        "date": showtime["date"],
        "time": showtime["time"],
        "screen_type": screen["type"],
        "price_breakdown": price_info,
        "quantity": quantity,
        "total_price": total,
        "currency": "VND",
        "formatted_total": f"{total:,.0f} VND"
    }


register_tool(
    name="get_ticket_price",
    description="Tinh gia ve cho mot suat chieu cu the, dua tren loai ghe, thoi gian, va ngay trong tuan.",
    parameters={
        "showtime_id": {"type": "string", "description": "ID cua suat chieu (vi du: st_001)", "required": True},
        "seat_type": {"type": "string", "description": "Loai ghe: regular, premium, couple. Mac dinh: regular", "required": False},
        "quantity": {"type": "integer", "description": "So luong ve. Mac dinh: 1", "required": False}
    },
    function=get_ticket_price
)
