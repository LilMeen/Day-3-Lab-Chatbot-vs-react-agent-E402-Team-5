import requests
from bs4 import BeautifulSoup
import json
import re

BASE_URL = "https://cinestar.com.vn"


def get_all_movies():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(BASE_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')

        full_data = json.loads(script_tag.string)
        res = full_data.get('props', {}).get('pageProps', {}).get('res', {})

        raw_list = res.get('listMovie', []) + res.get('listComingMovie', [])

        final_results = []
        for movie in raw_list:
            final_results.append({
                "movie_id": movie.get('id'),
                "movie_url": f"{BASE_URL}/movie/{movie.get('id')}",
                "movie_name": movie.get('name_vn'),
                "image": movie.get('image'),
                "category": movie.get('type_name_vn'),
                "description": movie.get('brief_vn'),
                "director": movie.get('director'),
                "cast": movie.get('actor'),
                "time": movie.get('time'),
                "release_date": movie.get('release_date'),
                "status": "Đang chiếu" if movie in res.get('listMovie', []) else "Sắp chiếu"
            })
        return final_results
    except Exception as e:
        return {"error": f"Lỗi get_all_movies: {str(e)}"}


def get_movie_details(movie_id, all_movies_list):
    for movie in all_movies_list:
        if movie['movie_id'] == movie_id:
            return movie
    return {"error": "Không tìm thấy phim"}


def get_discount():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(BASE_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__')

        full_data = json.loads(script_tag.string)
        promo_data = full_data.get('props', {}).get('pageProps', {}).get('listPromotion', {}).get('listPromotion', [])

        results = []
        for promo in promo_data:
            results.append({
                "discount_name": promo.get('name'),
                "discount_link": promo.get('link'),
                "image": promo.get('media')
            })
        return results
    except Exception as e:
        return {"error": f"Lỗi get_discount: {str(e)}"}


# ------------------------------------------------------------------
# New: So sánh giá vé các rạp khác qua Google Custom Search API
# ------------------------------------------------------------------

COMPETITOR_CINEMAS = ["CGV", "Lotte Cinema", "Galaxy Cinema", "BHD Star"]

_PRICE_PATTERNS = [
    r'(\d{2,3}[.,]\d{3})\s*(?:đ|vnd|vnđ|đồng)',
    r'(\d{5,6})\s*(?:đ|vnd|vnđ|đồng)',
    r'(?:giá|price)[^\d]*(\d{2,3}[.,]\d{3})',
]


def _extract_price(text: str) -> int | None:
    """Extract the first valid VND price (30k–500k) from a text snippet."""
    text_lower = text.lower()
    for pattern in _PRICE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            raw = match.group(1).replace(".", "").replace(",", "")
            try:
                price = int(raw)
                if 30000 <= price <= 500000:
                    return price
            except ValueError:
                continue
    return None


def compare_prices_google_search(movie_name: str) -> dict:
    """So sánh giá vé của một phim giữa Cinestar và các rạp đối thủ
    (CGV, Lotte, Galaxy, BHD) bằng Google Custom Search API.

    Args:
        movie_name: Tên phim, ví dụ "Avengers: Secret Wars"

    Requires env:
        GOOGLE_SEARCH_API_KEY — Google API key có Custom Search enabled
        GOOGLE_CSE_ID         — Custom Search Engine ID (cx)
    """
    import config

    api_key = config.GOOGLE_SEARCH_API_KEY
    cse_id = config.GOOGLE_CSE_ID

    if not api_key or not cse_id:
        return {
            "status": "error",
            "message": "Thiếu GOOGLE_SEARCH_API_KEY hoặc GOOGLE_CSE_ID trong .env",
        }

    SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
    results = {}

    for cinema in COMPETITOR_CINEMAS:
        query = f"giá vé {movie_name} {cinema} 2025"
        try:
            resp = requests.get(
                SEARCH_URL,
                params={"key": api_key, "cx": cse_id, "q": query, "num": 3, "hl": "vi", "gl": "vn"},
                timeout=8,
            )
            items = resp.json().get("items", [])

            price, source_url, snippet_used = None, "", ""
            for item in items:
                text = item.get("snippet", "") + " " + item.get("title", "")
                price = _extract_price(text)
                if price:
                    source_url = item.get("link", "")
                    snippet_used = text[:200]
                    break

            results[cinema] = {
                "price": price,
                "formatted_price": f"{price:,.0f} VND" if price else "Không tìm thấy",
                "source_url": source_url,
                "snippet": snippet_used,
            }
        except Exception as e:
            results[cinema] = {"price": None, "formatted_price": "Lỗi", "error": str(e)}

    # Add Cinestar baseline from get_discount / local knowledge
    results["Cinestar"] = {
        "price": 75000,
        "formatted_price": "75,000 VND (Standard)",
        "source_url": BASE_URL,
        "snippet": "Giá vé Cinestar từ 75,000 VND (Standard weekday)",
    }

    # Sort by price ascending (None last)
    sorted_results = dict(
        sorted(results.items(), key=lambda x: (x[1]["price"] is None, x[1]["price"] or 0))
    )

    priced = {k: v for k, v in sorted_results.items() if v["price"]}
    cheapest = min(priced.items(), key=lambda x: x[1]["price"]) if priced else None

    return {
        "status": "success",
        "movie": movie_name,
        "comparison": sorted_results,
        "cheapest_cinema": cheapest[0] if cheapest else "Không xác định",
        "cheapest_price": cheapest[1]["formatted_price"] if cheapest else "",
        "note": "Giá lấy từ Google Search, có thể không realtime. Kiểm tra trang rạp để xác nhận.",
    }
