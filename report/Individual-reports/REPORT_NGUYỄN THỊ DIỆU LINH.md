# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Thị Diệu Linh
- **Student ID**: 2A2026002090
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implemented**: `client/components/ChatUI.tsx`, `client/components/Sidebar.tsx`, `client/components/ChatArea.tsx`, `client/components/MovieInfo.tsx`, CSS modules trong `client/components/*.module.css`
- **Code Highlights**:
    - `ChatUI.tsx`: điều phối hội thoại, gọi backend, quản lý trạng thái UI (sidebar, movieInfo, chọn model).
    - `ChatArea.tsx`: danh sách tin nhắn, ô nhập, các điều khiển header (toggle sidebar, chọn model, toggle movie-info).
    - `Sidebar.tsx`: danh sách lịch sử chat và hành động "New Chat"; header có nút collapse.
    - `MovieInfo.tsx`: hiển thị lịch chiếu phim do backend trả về khi có.
- **Documentation**: UI gửi tin nhắn người dùng tới endpoint `/chat` của backend với tùy chọn `model` (`agent` hoặc `baseline`). Thông tin phim (`movieInfo`) chỉ hiển thị khi response từ backend có payload `movieInfo`.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Trong quá trình làm mượt UI, các nút toggle của sidebar và header dùng `position: absolute` gây lỗi layout - các nút bị "bay" ra khỏi vị trí. Khi thu gọn sidebar, nút mở lại không truy cập được từ header, và khu vực chat hiển thị trạng thái rỗng bị chia đôi (khối trắng phía trên, khối xám nhạt phía dưới).
- **Log / Evidence Source**:
    - DevTools trình duyệt - Console: không có lỗi runtime JS.
    - DevTools - Elements: nhận thấy các nút toggle được render ngoài header do style absolute.
    - Ảnh chụp màn hình trong quá trình test UI cho thấy các nút nổi và trạng thái rỗng bị chia.
- **Diagnosis**:
    - Nguyên nhân chính là CSS: các nút toggle đặt `position: absolute` so với container không đúng, dẫn đến chồng chéo và vị trí không nhất quán trên các kích thước responsive.
    - Giao diện trạng thái rỗng do container tin nhắn và vùng input dùng nền khác nhau, tạo cảm giác chia đôi. Một placeholder trạng thái rỗng trước đó cũng không được căn giữa theo chiều dọc.
- **Solution**:
    - Di chuyển nút collapse của `Sidebar` vào header của `Sidebar.tsx` và thêm nút expand tương ứng trong header của `ChatArea` để luôn có control khi sidebar bị ẩn.
    - Loại bỏ các nút toggle absolute trong `ChatUI.tsx`, truyền callback toggle qua props cho `ChatArea` và `Sidebar` để các control nằm trong luồng layout tự nhiên.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1. **Reasoning**: ReAct với block `Thought` buộc agent phân rã vấn đề thành chuỗi hành động và quan sát. Với các task cần tool (ví dụ tìm lịch, đặt vé), cách này dễ theo dõi và debug hơn so với một câu trả lời chat đơn lẻ.
2. **Reliability**: Agent có thể hoạt động kém hơn khi tool gây nhiễu hoặc chậm (timeout) - Chatbot thường trả lời an toàn, còn Agent có thể gọi tool liên tục dẫn tới kết quả không nhất quán.
3. **Observation**: Các quan sát từ gọi tool (ví dụ kết quả tìm kiếm) trực tiếp định hướng hành động tiếp theo; agent có thể lập lại kế hoạch (gọi tool khác) trong khi chatbot thì không.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Thiết kế hàng đợi bất đồng bộ cho các tool chạy lâu (ví dụ API đặt vé), và lưu trạng thái hội thoại vào database (Postgres) thay vì file phẳng.
- **Safety**: Thêm lọc/sanitize input ở client và server, rate-limiting, và audit log dựa trên LLM để đánh dấu hành động khả nghi trước khi thực thi.
- **Performance**: Cache các response API lịch chiếu phim, và dùng store in-memory (Redis) cho routing session và rate limiting.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
