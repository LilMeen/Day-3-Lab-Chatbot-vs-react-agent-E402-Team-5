from datetime import datetime
from tools.base import PROMOTIONS, register_tool

DAY_MAP = {
    0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday",
    4: "friday", 5: "saturday", 6: "sunday"
}


def get_promotions(date: str = "", movie_id: str = "") -> dict:
    """Get available promotions, optionally filtered by date."""
    results = []

    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"status": "error", "message": f"Dinh dang ngay khong hop le: '{date}'. Dung YYYY-MM-DD."}
        day_name = DAY_MAP[dt.weekday()]
    else:
        dt = datetime.now()
        day_name = DAY_MAP[dt.weekday()]
        date = dt.strftime("%Y-%m-%d")

    for promo in PROMOTIONS:
        # Check validity date
        valid_until = datetime.strptime(promo["valid_until"], "%Y-%m-%d")
        if dt > valid_until:
            continue

        # Check applicable day
        if day_name not in promo["applicable_days"]:
            continue

        result = {
            "id": promo["id"],
            "name": promo["name"],
            "description": promo["description"],
            "discount_percent": promo["discount_percent"],
            "conditions": promo["conditions"],
            "valid_until": promo["valid_until"]
        }
        if "bonus" in promo:
            result["bonus"] = promo["bonus"]
        results.append(result)

    return {
        "status": "success",
        "date": date,
        "day": day_name,
        "count": len(results),
        "promotions": results
    }


register_tool(
    name="get_promotions",
    description="Lay danh sach chuong trinh khuyen mai hien co. Co the loc theo ngay va phim.",
    parameters={
        "date": {"type": "string", "description": "Ngay can kiem tra (YYYY-MM-DD). Mac dinh: hom nay", "required": False},
        "movie_id": {"type": "string", "description": "ID phim de loc khuyen mai lien quan", "required": False}
    },
    function=get_promotions
)
