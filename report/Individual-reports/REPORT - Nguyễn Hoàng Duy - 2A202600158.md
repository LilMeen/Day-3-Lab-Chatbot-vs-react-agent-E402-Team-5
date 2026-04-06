# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Hoàng Duy
- **Student ID**: 2A202600158
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

Tôi chịu trách nhiệm toàn bộ tầng AI của hệ thống — từ thu thập dữ liệu, thiết kế công cụ, xây dựng ReAct agent cho đến expose REST API. Phạm vi công việc bao gồm toàn bộ thư mục `ai-services/`.

**Các module đã triển khai:**
- `ai-services/agent/` — ReAct agent engine, memory, prompt templates, data models
- `ai-services/tools/` — Tool registry pattern và 6 công cụ Cinestar
- `ai-services/crawling/crawl.py` — Crawler lịch chiếu và giá vé dùng Playwright
- `ai-services/CrawData.py` — Scraper danh sách phim, khuyến mãi từ trang chủ
- `ai-services/api.py` — FastAPI với các endpoint chat và tool
- `ai-services/routers/chat.py` — Định tuyến Baseline vs Agent
- `ai-services/config.py` — Cấu hình tải `.env` theo đường dẫn tương đối

**Điểm nổi bật trong code:**

- Thiết kế và triển khai vòng lặp **ReAct 5 trường**: `Reflection → Plan → Thought → Action → Output`, kèm stop-token parser để trích xuất từng trường từ văn bản LLM trả về.
- Xây dựng **short-term memory kiểu CyBench** (`ShortTermMemory`) lưu 3 lượt hội thoại gần nhất theo session dưới dạng cặp `(tin nhắn người dùng, phản hồi agent)`, inject vào REACT_PROMPT làm lịch sử quan sát.
- Triển khai **tool registry pattern** (`register_tool` / `execute_tool`) cho phép mỗi module tự đăng ký công cụ khi được import; mô tả công cụ được tổng hợp tự động cho LLM qua `get_tool_descriptions()`.
- Thiết kế và đăng ký **6 công cụ Cinestar thực tế**: `get_all_movies`, `get_movie_details`, `get_discount`, `get_movie_schedule`, `get_movie_prices`, `get_locations` — tất cả dùng dữ liệu crawl thật, không mock JSON.
- Tích hợp **fuzzy matching tên phim** bằng `difflib.SequenceMatcher` (ưu tiên: khớp chính xác → khớp một phần → fuzzy >0.45) để người dùng gõ gần đúng vẫn ra kết quả đúng.
- Xây dựng **lấy giá vé thật bằng Playwright** (`get_ticket_prices_for_showtime`): Chromium headless điều hướng đến trang phim, click vào nút suất chiếu đầu tiên (`.item-time`), chờ thẻ giá render, parse loại vé (Đơn/Đôi) và giá từ DOM — hoàn toàn bỏ qua Cinestar REST API vì API yêu cầu xác thực.
- Parse JSON `__NEXT_DATA__` nhúng sẵn trong trang phim để lấy lịch chiếu đầy đủ (`room_type_name_vn`, `showtime_id`, `theater_name_vn`) mà không cần API key.
- Expose **6 REST GET endpoint** dưới `/api/v1/` trong `api.py`, bọc trong `ThreadPoolExecutor` timeout để tránh LLM call block vô hạn.
- Sửa `config.py` dùng `Path(__file__).parent / ".env"` để luôn tìm được `.env` bất kể thư mục làm việc hiện tại là gì.

**Cách tầng AI tương tác với hệ thống:**
- Backend NestJS chuyển tin nhắn + session ID đến `POST /api/v1/agent`.
- `ReActAgent.run()` xây dựng system prompt từ mô tả công cụ và memory session, gọi LLM, parse phản hồi 5 trường, thực thi công cụ nếu cần, đưa kết quả trở lại làm observation mới và lặp (tối đa 3 vòng).
- `Output` cuối cùng trả về NestJS dưới dạng `AgentResponse`, được lưu và gửi lên frontend.
- Cơ chế phát hiện follow-up ngắn tự động viết lại input mơ hồ (ví dụ: "lịch") thành observation đầy đủ hơn (ví dụ: "lịch của Mario") bằng cách trích xuất tên phim từ trường `Output` gần nhất trong memory.

---

## II. Debugging Case Study (10 Points)

Bug nghiêm trọng nhất tôi xử lý là sự kết hợp giữa URL trang phim sai và pipeline context-memory bị hỏng khiến agent liên tục quên phim đang được thảo luận.

**Vấn đề 1 — 404 trên trang phim:**
- `CrawData.py` tạo URL phim dạng `/phim/{uuid}` — tất cả trả về HTTP 404.
- Không thể lấy lịch chiếu cho bất kỳ bộ phim nào.
- **Fix**: Kiểm tra trình duyệt thủ công phát hiện Cinestar dùng `/movie/{uuid}`. Đổi template URL; tất cả trang phim trả về 200 với đầy đủ `__NEXT_DATA__`.

**Vấn đề 2 — Agent quên context khi người dùng hỏi ngắn:**
- Luồng: "phim mario" → agent hỏi muốn biết gì → người dùng trả lời "lịch" → agent hỏi lại "Bạn muốn xem lịch của phim nào?"
- **Nguyên nhân**: Các ví dụ trong SYSTEM_PROMPT chứa lời gọi công cụ `smart_followup` đã bị xóa khỏi tool registry. LLM làm theo ví dụ, gọi `smart_followup`, nhận `Error: Tool 'smart_followup' not found`, bị rối, lượt tiếp theo không có Output hợp lệ trong memory — phá vỡ chuỗi trích xuất context.
- **Fix (2 bước):**
  1. Cập nhật tất cả ví dụ trong prompt để loại bỏ `smart_followup`. Ví dụ 1 giờ cho thấy agent hỏi câu làm rõ trực tiếp qua `Output` (Action: None), tên phim in đậm để regex extractor tìm được sau.
  2. Trong `react_agent.py`, thêm `_is_short_followup()` + `_extract_movie_from_memory()` để phát hiện tin nhắn mơ hồ và viết lại với tên phim trích từ text `**bold**` trong Output gần nhất trước khi gửi LLM.

**Vấn đề 3 — Merge conflict trong crawl.py gây IndentationError:**
- Tồn tại hai phiên bản `get_movie_schedules` cùng lúc trong file (indent tab và space) do merge conflict chưa giải quyết. Pylance báo lỗi, Python từ chối chạy module.
- **Fix**: Giữ phiên bản space-indent, xóa bản tab-indent và các helper không dùng (`_extract_movie_description`, `_extract_movie_poster`).

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

Làm việc trực tiếp trên phần triển khai agent cho tôi cái nhìn thực tế về sự khác biệt giữa hai cách tiếp cận.

**1. Khả năng suy luận — Trường `Thought` giúp ích như thế nào?**

Trường `Thought` buộc mô hình lý luận trước khi hành động. Khi LLM viết được `Thought` rõ ràng như *"Phim là Bẫy Tiền từ lịch sử, tôi sẽ lấy lịch chiếu ngay"*, `Action` tiếp theo hầu như luôn đúng. Baseline đôi khi bịa thông tin lịch chiếu thay vì thừa nhận không biết. Trường `Reflection` cũng hữu ích như bước kiểm tra nội bộ, tránh gọi cùng một công cụ hai lần.

**2. Độ tin cậy — Khi nào Agent kém hơn Chatbot?**

Độ trễ của agent cao hơn rõ rệt — mỗi lần gọi công cụ tốn thêm một round-trip đầy đủ (LLM → parse → thực thi → LLM lại). Với câu chào hỏi đơn giản, baseline nhanh hơn 2–3 lần với chất lượng tương đương. Khi Playwright gặp lỗi (CDN Cinestar chậm), `get_movie_prices` timeout và agent trả về kết quả suy giảm, trong khi baseline không có phụ thuộc ngoài luôn trả về gì đó.

**3. Quan sát — Phản hồi từ môi trường ảnh hưởng thế nào?**

Kết quả công cụ trực tiếp quyết định hành động tiếp theo của agent. Khi `get_movie_schedule` trả về `"no_schedule"`, agent tự động chuyển sang gợi ý dùng `get_locations`. Loại phân nhánh thích nghi này không thể thực hiện với baseline không có trạng thái. Ngoài ra, chất lượng observation cũng ảnh hưởng trực tiếp đến output: khi tôi giảm payload lịch chiếu từ JSON lồng nhau đầy đủ xuống dạng compact `locality → theatre → day → showtimes`, phần tóm tắt của agent trở nên chính xác và dễ đọc hơn rõ rệt.

---

## IV. Future Improvements (5 Points)

**Khả năng mở rộng:**
- Thay `@lru_cache` trên `_fetch_movies()` bằng Redis cache có TTL (10 phút) để tất cả worker process dùng chung và tự làm mới khi Cinestar cập nhật.
- Thay `ShortTermMemory` dict trong process bằng session store (Redis/PostgreSQL) để memory tồn tại qua các lần restart và hỗ trợ horizontal scaling.

**Bảo mật:**
- Thêm sanitization input trước khi đưa tin nhắn vào LLM prompt, đặc biệt ngăn prompt injection qua tên phim được craft cố tình.
- Thêm hallucination guard: nếu Output chứa giờ chiếu hoặc giá vé không có trong bất kỳ kết quả công cụ nào trong session, tự động cờ hoặc ẩn thông tin đó.

**Hiệu năng:**
- Playwright cold-start tốn 2–4 giây mỗi lần. Pre-warm browser pool lúc khởi động và tái sử dụng page để giảm thời gian truy vấn giá vé.
- Cache kết quả Playwright theo `movie_url` với TTL 30 phút để tránh khởi động lại trình duyệt cho cùng một phim.
- Thêm streaming support cho agent API để frontend hiển thị `Output` dần dần thay vì chờ toàn bộ phản hồi 5 trường.
