# Individual Report: Lab 3 - Chatbot vs ReAct Agent

**Student Name:** Nguyễn Triệu Gia Khánh  
**Student ID:** 2A202600225  
**Date:** 06/04/2026

## I. Technical Contribution (15 Points)

**Description:** Trong dự án Cinema Agent, em chịu trách nhiệm chính về thiết kế **API Gateway**, phân luồng dịch vụ AI và tích hợp giữa Chatbot Baseline và ReAct Agent. Ngoài ra, em cũng tham gia xây dựng flow tổng thể và tổng hợp báo cáo.

* **Modules Implemented:**
    * `api.py`: Xây dựng toàn bộ API Gateway (FastAPI).
    * `main.py`: Khởi tạo server, cấu hình middleware và router.
    * **Logic xử lý bổ trợ:** Domain Classifier (LLM), Timeout wrapper cho LLM, Baseline chatbot (không tool), và Endpoint ReAct Agent.

* **Code Highlights:**
    1.  **Domain Classifier:** Lọc các câu hỏi ngoài phạm vi hệ thống để giảm chi phí LLM và tránh xử lý thừa.
    2.  **Timeout Wrapper:** Sử dụng `ThreadPoolExecutor` để đảm bảo hệ thống không bị treo (block) khi LLM phản hồi chậm hoặc gặp sự cố mạng.
    3.  **Baseline & Agent Endpoints:** Tách biệt luồng xử lý giữa phản hồi trực tiếp (Baseline) và luồng suy luận có công cụ (ReAct).

* **Documentation:** API Gateway đóng vai trò trung gian: Nhận request từ Frontend → Điều phối tới ReAct Agent. Tại đây, Agent thực hiện vòng lặp **Thought → Action → Observation → Final Answer**. Khi cần dữ liệu thực tế (như lịch chiếu), Agent gọi các công cụ crawling; kết quả trả về được đưa lại vào context để tiếp tục reasoning cho đến khi có câu trả lời cuối cùng cho người dùng.

## II. Debugging Case Study (10 Points)

* **Problem Description:** Agent gặp lỗi logic khi xử lý các bài toán liên quan đến tiền tệ. Ví dụ, với câu hỏi *"Mua 2 vé giá 85,000 VND thì tổng là bao nhiêu?"*, Agent không thể thực hiện phép tính do giữ nguyên định dạng chuỗi có chứa dấu phẩy và ký tự đơn vị.

* **Log / Evidence Source:** Dựa trên log của Agent:
    > **Thought:** Need to calculate total price  
    > **Action:** multiply("85,000 VND", 2)  
    > **Observation:** Error / incorrect output (NaN hoặc lỗi kiểu dữ liệu)

* **Diagnosis:** Nguyên nhân xuất phát từ **Prompt Design**. LLM không tự động hiểu rằng nó cần làm sạch dữ liệu (loại bỏ ký tự phi số) trước khi truyền vào công cụ tính toán, dẫn đến việc công cụ nhận đầu vào là chuỗi văn bản thay vì số thực.

* **Solution:** Cập nhật **System Prompt** với chỉ dẫn cụ thể: *"Always strip out commas and currency symbols like 'VND' before performing any mathematical calculations."* Sau khi áp dụng, Agent đã thực hiện tiền xử lý dữ liệu đúng cách và trả về kết quả chính xác trong các test case.


## III. Personal Insights: Chatbot vs ReAct (10 Points)

* **Reasoning:** Chatbot thông thường trả lời dựa trên xác suất từ ngữ nên dễ bị **hallucination** (ảo tưởng thông tin). ReAct Agent với bước **Thought** buộc hệ thống phải phân tích vấn đề và lập kế hoạch trước khi hành động, giúp tăng tính minh bạch và độ chính xác của luồng suy luận.

* **Reliability:** ReAct Agent mạnh mẽ nhưng có thể kém ổn định hơn Chatbot trong các trường hợp: câu hỏi chitchat đơn giản, công cụ (tool) bị lỗi/timeout, hoặc Agent rơi vào vòng lặp vô hạn (infinite loop). Chatbot truyền thống thường nhanh và an toàn hơn cho các tương tác thông thường.

* **Observation:** Kết quả từ công cụ (**Observation**) đóng vai trò là "mỏ neo" thực tế. Nó trực tiếp định hướng bước tiếp theo của Agent, giúp giảm thiểu hoàn toàn việc LLM tự đoán mò thông tin không có sẵn trong tập huấn luyện.


## IV. Future Improvements (5 Points)

Để đưa hệ thống Agent này lên mức độ Production, em đề xuất các hướng cải tiến sau:

* **Scalability:** Sử dụng hàng đợi bất đồng bộ (**Celery / Kafka**) cho các tác vụ gọi tool tốn thời gian và tách biệt các service (LLM service, Crawling service) để dễ dàng scale độc lập.
* **Safety:** Triển khai một **Supervisor LLM** để kiểm duyệt đầu ra, thiết lập `max_iterations` để chặn loop vô hạn và kiểm tra chặt chẽ dữ liệu đầu vào/đầu ra của tool.
* **Performance:** Sử dụng **Vector Database** (FAISS/Pinecone) để quản lý bộ nhớ dài hạn và **Redis** để cache kết quả crawling, giúp giảm số lượng token tiêu thụ và tăng tốc độ phản hồi.
