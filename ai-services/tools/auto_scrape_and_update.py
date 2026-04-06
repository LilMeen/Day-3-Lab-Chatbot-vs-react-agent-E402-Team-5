from datetime import datetime
from tools.base import MOVIES, SHOWTIMES, THEATERS, PROMOTIONS, register_tool


def auto_scrape_and_update(source: str = "all") -> dict:
    """Simulate auto-scraping and updating movie data from external sources."""
    timestamp = datetime.now().isoformat()

    # Simulate a data refresh by reporting current data stats
    stats = {
        "movies": len(MOVIES),
        "theaters": len(THEATERS),
        "showtimes": len(SHOWTIMES),
        "promotions": len(PROMOTIONS)
    }

    if source == "all":
        return {
            "status": "success",
            "message": f"Da cap nhat du lieu tu tat ca nguon luc {timestamp}",
            "source": "all",
            "updated_at": timestamp,
            "stats": stats,
            "changes": {
                "new_showtimes": 3,
                "updated_prices": 5,
                "new_promotions": 1,
                "removed_expired": 2
            }
        }
    else:
        # Filter by specific theater/source name
        matched_theater = None
        for t in THEATERS:
            if source.lower() in t["name"].lower():
                matched_theater = t
                break

        if matched_theater:
            theater_showtimes = len([s for s in SHOWTIMES if s["theater_id"] == matched_theater["id"]])
            return {
                "status": "success",
                "message": f"Da cap nhat du lieu tu {matched_theater['name']} luc {timestamp}",
                "source": matched_theater["name"],
                "updated_at": timestamp,
                "stats": {
                    "showtimes": theater_showtimes,
                    "screens": len(matched_theater["screens"])
                },
                "changes": {
                    "new_showtimes": 1,
                    "updated_prices": 2
                }
            }

        return {
            "status": "warning",
            "message": f"Khong tim thay nguon '{source}'. Da cap nhat tu tat ca nguon.",
            "updated_at": timestamp,
            "stats": stats
        }


register_tool(
    name="auto_scrape_and_update",
    description="Mo phong cap nhat du lieu tu dong tu cac nguon ben ngoai. Tai lai du lieu phim, suat chieu, gia ve.",
    parameters={
        "source": {"type": "string", "description": "Nguon cap nhat: 'all' hoac ten rap cu the. Mac dinh: 'all'", "required": False}
    },
    function=auto_scrape_and_update
)
