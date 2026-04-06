import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def load_json(filename: str) -> list | dict:
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)


# Load all data at module level
MOVIES = load_json("movies.json")
THEATERS = load_json("theaters.json")
SHOWTIMES = load_json("showtimes.json")
PRICES = load_json("prices.json")
PROMOTIONS = load_json("promotions.json")


def get_movie_by_id(movie_id: str) -> dict | None:
    return next((m for m in MOVIES if m["id"] == movie_id), None)


def get_theater_by_id(theater_id: str) -> dict | None:
    return next((t for t in THEATERS if t["id"] == theater_id), None)


def get_screen(theater_id: str, screen_id: str) -> dict | None:
    theater = get_theater_by_id(theater_id)
    if not theater:
        return None
    return next((s for s in theater["screens"] if s["screen_id"] == screen_id), None)


def get_showtime_by_id(showtime_id: str) -> dict | None:
    return next((s for s in SHOWTIMES if s["id"] == showtime_id), None)


def calculate_price(screen_type: str, time_str: str, date_str: str, seat_type: str = "regular") -> dict:
    """Calculate ticket price based on rules."""
    from datetime import datetime

    base = PRICES["base_prices"].get(screen_type, PRICES["base_prices"]["Standard"])

    hour = int(time_str.split(":")[0])
    if hour < 12:
        time_mult = PRICES["time_multipliers"]["before_12"]
        time_label = "truoc 12h (x0.8)"
    elif hour < 17:
        time_mult = PRICES["time_multipliers"]["12_to_17"]
        time_label = "12h-17h (x1.0)"
    else:
        time_mult = PRICES["time_multipliers"]["after_17"]
        time_label = "sau 17h (x1.2)"

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_of_week = dt.weekday()
    if day_of_week == 2:  # Wednesday
        day_mult = PRICES["day_multipliers"]["wednesday"]
        day_label = "Thu Tu (x0.7)"
    elif day_of_week >= 5:  # Saturday, Sunday
        day_mult = PRICES["day_multipliers"]["weekend"]
        day_label = "Cuoi tuan (x1.3)"
    else:
        day_mult = PRICES["day_multipliers"]["weekday"]
        day_label = "Ngay thuong (x1.0)"

    seat_mult = PRICES["seat_types"].get(seat_type, 1.0)

    final_price = int(base * time_mult * day_mult * seat_mult)

    return {
        "base_price": base,
        "screen_type": screen_type,
        "time_multiplier": time_label,
        "day_multiplier": day_label,
        "seat_type": seat_type,
        "seat_multiplier": f"x{seat_mult}",
        "final_price": final_price,
        "currency": "VND"
    }


# Tool registry — filled by each tool module
TOOL_REGISTRY: dict[str, dict] = {}


def register_tool(name: str, description: str, parameters: dict, function):
    """Register a tool in the global registry."""
    TOOL_REGISTRY[name] = {
        "function": function,
        "description": description,
        "parameters": parameters
    }


def get_tool_descriptions() -> str:
    """Format all tool descriptions for the LLM prompt."""
    lines = []
    for name, info in TOOL_REGISTRY.items():
        lines.append(f"- **{name}**: {info['description']}")
        lines.append(f"  Parameters: {json.dumps(info['parameters'], ensure_ascii=False)}")
    return "\n".join(lines)


def execute_tool(name: str, parameters: dict) -> str:
    """Execute a tool by name with given parameters."""
    if name not in TOOL_REGISTRY:
        return f"Error: Tool '{name}' not found. Available tools: {', '.join(TOOL_REGISTRY.keys())}"
    try:
        result = TOOL_REGISTRY[name]["function"](**parameters)
        return json.dumps(result, ensure_ascii=False, indent=2) if isinstance(result, (dict, list)) else str(result)
    except Exception as e:
        return f"Error executing {name}: {str(e)}"
