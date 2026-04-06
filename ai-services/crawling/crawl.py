from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Iterable, List

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Cinestar price rules (weekday/weekend × time-of-day × screen type)
# ---------------------------------------------------------------------------

_BASE_PRICES: dict[str, int] = {
    "Standard": 75_000,
    "IMAX":     130_000,
    "4DX":      150_000,
    "VIP":      200_000,
}

_TICKET_TYPES: list[dict] = [
    {"type": "Người lớn",          "multiplier": 1.0},
    {"type": "HSSV / U22",         "multiplier": 1.0},
    {"type": "Người cao tuổi",     "multiplier": 1.0},
    {"type": "Người lớn (đôi)",    "multiplier": 2.0},
]


def _estimate_price(screen_type: str, time_str: str, date_str: str) -> dict:
    """Return estimated prices for all ticket types given screen/time/date."""
    base = _BASE_PRICES.get(screen_type, _BASE_PRICES["Standard"])

    try:
        hour = int(time_str.split(":")[0])
    except (ValueError, IndexError):
        hour = 12

    if hour < 12:
        time_mult = 0.8
    elif hour < 17:
        time_mult = 1.0
    else:
        time_mult = 1.2

    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        dow = dt.weekday()
    except ValueError:
        dow = 0

    if dow == 2:         # Wednesday
        day_mult = 0.7
    elif dow >= 5:       # Weekend
        day_mult = 1.3
    else:                # Weekday
        day_mult = 1.0

    unit = int(base * time_mult * day_mult)

    return {
        tt["type"]: f"{int(unit * tt['multiplier']):,.0f} VND"
        for tt in _TICKET_TYPES
    }


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _normalize_day(raw_day: str) -> str:
    match = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", raw_day)
    return match.group(1) if match else raw_day.strip()


def _normalize_time(raw_time: str) -> str:
    match = re.search(r"(\d{1,2}:\d{2})", raw_time)
    return match.group(1) if match else raw_time.strip()


def _normalize_locality(raw_locality: str) -> str:
    value = raw_locality.strip()
    if not value:
        return "Khác"
    normalized = re.sub(r"\s+", " ", value).strip()
    upper = normalized.upper().replace(".", "")
    if "HCM" in upper or "HO CHI MINH" in upper:
        return "HCM"
    if "HUE" in upper or "HUẾ" in upper:
        return "Huế"
    if "DA NANG" in upper or "ĐÀ NẴNG" in upper:
        return "Đà Nẵng"
    return normalized


def _extract_locality(theatre_name: str) -> str:
    match = re.search(r"\(([^)]+)\)", theatre_name)
    if match:
        return _normalize_locality(match.group(1))
    return _normalize_locality(theatre_name)


# ---------------------------------------------------------------------------
# __NEXT_DATA__ parsing
# ---------------------------------------------------------------------------

def _iter_dict_nodes(data: Any) -> Iterable[dict[str, Any]]:
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from _iter_dict_nodes(value)
    elif isinstance(data, list):
        for item in data:
            yield from _iter_dict_nodes(item)


def _extract_movie_name(next_data: dict[str, Any], soup: BeautifulSoup) -> str:
    page_props = next_data.get("props", {}).get("pageProps", {})
    if isinstance(page_props, dict):
        movie_data = page_props.get("movieData") or page_props.get("movie")
        if isinstance(movie_data, dict):
            for key in ("name_vn", "name", "title", "movie_name_vn", "movie_name_en"):
                value = movie_data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        # Also check res.dataShowTime
        res = page_props.get("res", {})
        if isinstance(res, dict):
            dst = res.get("dataShowTime", {})
            if isinstance(dst, dict):
                for key in ("name_vn", "name_en"):
                    v = dst.get(key)
                    if isinstance(v, str) and v.strip():
                        return v.strip()

    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return "Unknown Movie"


def _parse_rows_from_next_data(
    next_data: dict[str, Any],
) -> List[tuple[str, str, str, str]]:
    """Return list of (theatre, day, time, screen_type) tuples."""
    results: List[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for node in _iter_dict_nodes(next_data):
        day = node.get("date")
        times = node.get("times")

        if not isinstance(day, str) or not isinstance(times, list):
            continue

        normalized_day = _normalize_day(day)

        for item in times:
            if not isinstance(item, dict):
                continue

            raw_time = str(item.get("time") or "").strip()
            normalized_time = _normalize_time(raw_time)
            if not normalized_time:
                continue

            theatre = (
                str(item.get("theater_name_vn") or "").strip()
                or str(item.get("theater_name_en") or "").strip()
            )

            screen_type = (
                str(item.get("room_type_name_vn") or "").strip()
                or str(item.get("room_type_name_en") or "").strip()
                or "Standard"
            )

            key = (theatre, normalized_day, normalized_time)
            if key in seen:
                continue
            seen.add(key)
            results.append((theatre, normalized_day, normalized_time, screen_type))

    return results


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def _group_schedules(
    rows: List[tuple[str, str, str, str]], movie_name: str
) -> List[dict[str, Any]]:
    # grouped[locality][theatre][day][screen_type] = [times]
    grouped: dict[str, dict[str, dict[str, dict[str, list[str]]]]] = {}

    for theatre, day, time, screen_type in rows:
        locality = _extract_locality(theatre)
        grouped.setdefault(locality, {})
        grouped[locality].setdefault(theatre, {})
        grouped[locality][theatre].setdefault(day, {})
        grouped[locality][theatre][day].setdefault(screen_type, [])

        if time not in grouped[locality][theatre][day][screen_type]:
            grouped[locality][theatre][day][screen_type].append(time)

    result: List[dict[str, Any]] = []

    for locality, theatres in grouped.items():
        theatre_items: List[dict[str, Any]] = []

        for theatre_name, day_map in theatres.items():
            schedule: List[dict[str, Any]] = []

            for day, screen_map in day_map.items():
                screens: List[dict[str, Any]] = []

                for screen_type, times in screen_map.items():
                    sorted_times = sorted(times)
                    screens.append({
                        "screen_type": screen_type,
                        "showtimes": sorted_times,
                        "estimated_prices": _estimate_price(screen_type, sorted_times[0], day),
                    })

                schedule.append({
                    "day": day,
                    "screens": screens,
                    # keep flat showtimes for backward compatibility
                    "showtimes": sorted(
                        t for times in screen_map.values() for t in times
                    ),
                })

            theatre_items.append({
                "theatre": theatre_name,
                "movies": [{
                    "movie_name": movie_name,
                    "schedule": schedule,
                }],
            })

        result.append({
            "locality": locality,
            "theatres": theatre_items,
        })

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_movie_schedules(movie_url: str, debug_html: bool = False) -> List[dict[str, Any]]:
    """
    Crawl movie page and return grouped schedules:
    Locality -> Theatre -> Day -> Screen type -> Showtimes + estimated prices
    """
    response = requests.get(movie_url, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding

    if debug_html:
        print(response.text)

    soup = BeautifulSoup(response.text, "html.parser")

    next_data_script = soup.find("script", id="__NEXT_DATA__")
    if not next_data_script or not next_data_script.string:
        return []

    try:
        next_data = json.loads(next_data_script.string)
    except json.JSONDecodeError:
        return []

    movie_name = _extract_movie_name(next_data, soup)
    rows = _parse_rows_from_next_data(next_data)
    return _group_schedules(rows, movie_name)


def get_movie_schedule(movie_url: str) -> List[dict[str, Any]]:
    """Backward-compatible alias."""
    return get_movie_schedules(movie_url)


# ---------------------------------------------------------------------------
# Playwright: get real ticket prices by clicking on a showtime
# ---------------------------------------------------------------------------

def get_ticket_prices_for_showtime(movie_url: str, target_time: str | None = None) -> List[dict[str, Any]]:
    """
    Use Playwright to open the movie page, click on the first (or target) showtime,
    then scrape the 'CHỌN LOẠI VÉ' section for real ticket types and prices.

    DOM structure (from Cinestar):
        .content-top
          p.name            → ticket type name
          .desc p           → "ĐƠN" | "ĐÔI" | "" (empty = food/combo, skip)
          .price.sub-title p → "45,000 VNĐ"

    Args:
        movie_url:   Full URL of the Cinestar movie page.
        target_time: e.g. "16:40". If None, clicks the first available showtime.

    Returns:
        List of dicts: [{"type": "Người lớn", "category": "Đơn", "price": 45000, "formatted": "45,000 VNĐ"}, ...]
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    results: List[dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(20_000)

        try:
            page.goto(movie_url, wait_until="networkidle")

            # Click target or first available showtime
            if target_time:
                btn = page.locator("li.item-time").filter(has_text=target_time).first
            else:
                btn = page.locator("li.item-time").first

            btn.click()
            page.wait_for_timeout(2_000)  # wait for AJAX to load ticket section

            # Parse ticket cards from updated DOM
            soup = BeautifulSoup(page.inner_html("body"), "html.parser")

            for card in soup.select(".content-top"):
                name_el = card.select_one("p.name")
                desc_el  = card.select_one(".desc p")
                price_el = card.select_one(".price.sub-title p")

                if not name_el or not price_el:
                    continue

                category = (desc_el.get_text(strip=True) if desc_el else "").upper()
                # Only keep ticket types with ĐƠN or ĐÔI category; skip food/combo
                if category not in ("ĐƠN", "ĐÔI"):
                    continue

                price_text = price_el.get_text(strip=True)
                price_match = re.search(r"([\d,]+)", price_text)
                if not price_match:
                    continue
                price = int(price_match.group(1).replace(",", ""))
                if not (10_000 <= price <= 1_000_000):
                    continue

                results.append({
                    "type": name_el.get_text(strip=True),
                    "category": category.capitalize(),
                    "price": price,
                    "formatted": f"{price:,.0f} VNĐ",
                })

        except PlaywrightTimeout:
            pass
        except Exception:
            pass
        finally:
            browser.close()

    return results


def get_all_ticket_prices(movie_url: str) -> dict[str, Any]:
    """
    Convenience wrapper: returns real ticket prices scraped via Playwright,
    falling back to estimated prices if Playwright fails or finds nothing.

    Returns:
        {"source": "live"|"estimated", "prices": [{"type":..., "category":..., "price":..., "formatted":...}]}
    """
    live = get_ticket_prices_for_showtime(movie_url)
    if live:
        return {"source": "live", "prices": live}

    # Fallback: return standard estimated prices for Standard screen
    estimated = _estimate_price("Standard", "19:00", "07/04/2026")
    prices = [{"type": k, "category": "Đơn", "price": int(v.replace(",","").replace(" VND","")), "formatted": v}
              for k, v in estimated.items()]
    return {"source": "estimated", "prices": prices}
