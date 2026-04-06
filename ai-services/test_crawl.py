"""
Test crawling thông tin lịch chiếu + giá vé + khuyến mãi từ Cinestar.
Tự động lấy danh sách phim từ homepage rồi crawl lịch chiếu.

Cách chạy:
    cd ai-services
    python test_crawl.py              # list phim rồi hỏi chọn
    python test_crawl.py --all        # crawl tất cả phim (chậm)
    python test_crawl.py --json       # dump raw JSON
    python test_crawl.py --discount   # hiện khuyến mãi từ Cinestar
    python test_crawl.py --compare    # so sánh giá với rạp khác (cần Google API key)
"""

import sys
import json
from CrawData import get_all_movies, get_movie_details, get_discount, compare_prices_google_search
from crawling.crawl import get_movie_schedules, get_ticket_prices_for_showtime


def sep(char="=", width=60):
    print(char * width)


def print_movie_list(movies: list[dict]):
    sep()
    print(f"  {'#':<4} {'Tên phim':<35} {'Thể loại':<20} Trạng thái")
    sep("-")
    for i, m in enumerate(movies, 1):
        name = (m.get("movie_name") or "")[:34]
        cat  = (m.get("category") or "")[:19]
        status = m.get("status", "")
        print(f"  {i:<4} {name:<35} {cat:<20} {status}")
    sep()


def print_movie_details(movie: dict):
    sep("-", 50)
    print(f"  Tên phim  : {movie.get('movie_name', '')}")
    print(f"  Thể loại  : {movie.get('category', '')}")
    print(f"  Đạo diễn  : {movie.get('director', '') or 'Không rõ'}")
    print(f"  Diễn viên : {(movie.get('cast') or 'Không rõ')[:80]}")
    duration = movie.get('time', '')
    if duration:
        print(f"  Thời lượng: {duration} phút")
    release = movie.get('release_date', '')
    if release:
        print(f"  Khởi chiếu: {release}")
    desc = (movie.get('description') or '').strip()
    if desc:
        print(f"  Mô tả     : {desc[:200]}{'...' if len(desc) > 200 else ''}")
    sep("-", 50)


def print_schedules(schedules: list[dict]) -> int:
    total = 0
    for loc in schedules:
        print(f"\n📍 {loc.get('locality', 'Không rõ')}")
        sep("-", 50)
        for theatre in loc.get("theatres", []):
            print(f"\n  🎭 {theatre.get('theatre', '')}")
            for movie in theatre.get("movies", []):
                for day_data in movie.get("schedule", []):
                    times = day_data.get("showtimes", [])
                    total += len(times)
                    print(f"     📅 {day_data.get('day','')}: {'  |  '.join(times)}")
    return total



def print_discounts():
    print("\n⏳ Đang lấy khuyến mãi từ Cinestar...")
    discounts = get_discount()
    if isinstance(discounts, dict) and "error" in discounts:
        print(f"❌ {discounts['error']}")
        return

    if not discounts:
        print("⚠️  Không tìm thấy khuyến mãi nào.")
        return

    print(f"\n🎁 Khuyến mãi hiện có ({len(discounts)} chương trình):")
    sep("-", 50)
    for d in discounts:
        name = d.get("discount_name", "Không tên")
        link = d.get("discount_link", "")
        print(f"  • {name}")
        if link:
            print(f"    🔗 {link}")
    sep("-", 50)


def print_price_comparison(movie_name: str):
    print(f"\n⏳ Đang so sánh giá vé '{movie_name}' với các rạp khác...")
    result = compare_prices_google_search(movie_name)

    if result.get("status") == "error":
        print(f"❌ {result.get('message', 'Lỗi không xác định')}")
        return

    sep("-", 50)
    print(f"  Phim: {result.get('movie', movie_name)}")
    print(f"  Rạp rẻ nhất: {result.get('cheapest_cinema', 'N/A')} — {result.get('cheapest_price', '')}")
    sep("-", 50)
    print(f"  {'Rạp':<20} {'Giá':<20} Nguồn")
    sep("-", 50)
    for cinema, info in result.get("comparison", {}).items():
        price_str = info.get("formatted_price", "N/A")
        source = info.get("source_url", "")[:40]
        print(f"  {cinema:<20} {price_str:<20} {source}")
    sep("-", 50)
    note = result.get("note", "")
    if note:
        print(f"  ⚠️  {note}")


def print_ticket_prices(url: str):
    print("\n⏳ Đang lấy giá vé thật (Playwright)...")
    prices = get_ticket_prices_for_showtime(url)
    if not prices:
        print("⚠️  Không lấy được giá vé.")
        return
    print("\n🎟️  Giá vé (suất chiếu đầu tiên):")
    sep("-", 50)
    for p in prices:
        print(f"  {p['type']:<22} {p['category']:<6} {p['formatted']}")
    sep("-", 50)


def crawl_one(movie: dict, all_movies: list[dict], compare: bool = False):
    name = movie.get("movie_name", "")
    url  = movie.get("movie_url", "")
    movie_id = movie.get("movie_id")

    sep()
    print_movie_details(get_movie_details(movie_id, all_movies))

    print("⏳ Đang crawl lịch chiếu...")
    try:
        schedules = get_movie_schedules(url)
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return

    if not schedules:
        print("⚠️  Không tìm thấy lịch chiếu.")
    else:
        total = print_schedules(schedules)
        print(f"\n📊 Tổng: {total} suất chiếu")

    print_ticket_prices(url)

    if compare:
        print_price_comparison(name)

    if "--json" in sys.argv:
        print("\n--- RAW JSON ---")
        print(json.dumps(schedules, ensure_ascii=False, indent=2))

    sep()


def main():
    # Show discounts-only mode
    if "--discount" in sys.argv:
        print_discounts()
        return

    print("⏳ Lấy danh sách phim từ Cinestar...")
    movies = get_all_movies()

    if isinstance(movies, dict) and "error" in movies:
        print(f"❌ {movies['error']}")
        return

    now_showing = [m for m in movies if m.get("status") == "Đang chiếu"]
    print(f"✅ Tìm thấy {len(now_showing)} phim đang chiếu\n")

    compare = "--compare" in sys.argv

    # --all: crawl tất cả
    if "--all" in sys.argv:
        for m in now_showing:
            crawl_one(m, movies, compare=compare)
        return

    # Interactive: cho user chọn phim
    print_movie_list(now_showing)
    try:
        choice = input("Chọn số phim muốn xem lịch chiếu (Enter để thoát): ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not choice:
        return

    try:
        idx = int(choice) - 1
        if not (0 <= idx < len(now_showing)):
            print("❌ Số không hợp lệ.")
            return
    except ValueError:
        print("❌ Vui lòng nhập số.")
        return

    crawl_one(now_showing[idx], movies, compare=compare)


if __name__ == "__main__":
    main()
