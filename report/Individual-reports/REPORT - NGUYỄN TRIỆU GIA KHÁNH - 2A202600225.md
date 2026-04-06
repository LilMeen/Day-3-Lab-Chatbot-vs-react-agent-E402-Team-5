 

**Individual Report: Lab 3 \- Chatbot vs ReAct Agent**

**Student Name:** Nguyễn Triệu Gia Khánh  
 **Student ID:** 2A202600225  
 **Date:** 06/04/2026

 

**I. Technical Contribution (15 Points)**

**Mô tả đóng góp:**  
 Trong dự án Cinema Agent, em chịu trách nhiệm chính về thiết kế API Gateway, phân luồng dịch vụ AI và tích hợp giữa Chatbot Baseline và ReAct Agent. Ngoài ra, em cũng tham gia xây dựng flow tổng thể và tổng hợp báo cáo.

 

**Modules Implemented:**

* api.py — Xây dựng toàn bộ API Gateway (FastAPI)  
* main.py — Khởi tạo server, cấu hình middleware và router  
* Một phần logic xử lý:  
  * Domain Classifier (LLM)  
  * Timeout wrapper cho LLM  
  * Baseline chatbot (không tool)  
  * Endpoint ReAct Agent

 

**Code Highlights:**

**1\. Domain Classifier (lọc câu hỏi ngoài domain):**

def \_is\_out\_of\_domain(user\_message: str) \-\> bool:

	prompt \= \_DOMAIN\_CLASSIFIER\_PROMPT.format(message=user\_message)

	...

	return verdict.startswith("OUT")

👉 Giúp giảm chi phí LLM và tránh xử lý các câu hỏi không liên quan.

 

**2\. Timeout wrapper tránh treo hệ thống:**

def \_run\_with\_timeout(func, \*args):

	with ThreadPoolExecutor(max\_workers=1) as executor:

    	future \= executor.submit(func, \*args)

    	return future.result(timeout=LLM\_TIMEOUT\_SEC)

👉 Đảm bảo hệ thống không bị block khi LLM phản hồi chậm.

 

**3\. Endpoint Baseline (không dùng tool):**

@router.post("/baseline")

async def chat\_baseline(request: ChatRequest):

	reply \= \_run\_with\_timeout(\_call\_llm\_baseline, request.user\_message)

 

**4\. Endpoint ReAct Agent:**

@router.post("/agent")

async def chat\_react\_agent(request: ChatRequest):

	response \= \_react\_agent.run(session\_id, request.user\_message)

 

**Documentation (Cách code tương tác với ReAct loop):**

* API Gateway nhận request từ frontend → gọi ReAct Agent  
* ReAct Agent chạy theo vòng lặp:  
   **Thought → Action → Observation → Final Answer**  
* Khi cần dữ liệu:  
  * Agent sẽ gọi các tool crawling (ví dụ: get\_movie\_schedules)  
* Kết quả từ tool được đưa lại vào context → tiếp tục reasoning  
* API trả về final\_answer cho client

👉 Em đóng vai trò kết nối giữa Frontend ↔ LLM ↔ Tools ↔ Agent

 

**II. Debugging Case Study (10 Points)**

**Problem Description:**

Agent bị lỗi khi xử lý bài toán liên quan đến tiền tệ, ví dụ:

"Mua 2 vé giá 85,000 VND thì tổng là bao nhiêu?"

👉 Agent không tính đúng do giữ nguyên chuỗi "85,000 VND".

 

**Log Source (mô phỏng):**

Thought: Need to calculate total price

Action: multiply("85,000 VND", 2\)

Observation: Error / incorrect output

 

**Diagnosis:**

Nguyên nhân chính:

* LLM **không tự động xử lý dữ liệu dạng chuỗi tiền tệ**  
* Prompt chưa hướng dẫn rõ cách xử lý số

👉 Đây là lỗi từ **prompt design**, không phải tool hay model.

 

**Solution:**

Em đã cập nhật System Prompt:

"Always strip out commas and currency symbols like 'VND' before performing any mathematical calculations."

👉 Sau khi sửa:

* Agent xử lý đúng các phép tính  
* Không còn lỗi trong test case

 

**III. Personal Insights: Chatbot vs ReAct (10 Points)**

**Reasoning:**

* Chatbot thường trả lời trực tiếp → dễ bị **hallucination**  
* ReAct Agent có **Thought step**:  
  * Giúp phân tích vấn đề trước khi trả lời  
  * Quyết định khi nào cần gọi tool

👉 Thought giống như “suy nghĩ trung gian” → tăng độ chính xác

 

**Reliability:**

ReAct Agent có thể **kém hơn Chatbot** trong một số trường hợp:

* Câu hỏi đơn giản (chitchat)  
* Khi tool bị lỗi hoặc crawl thất bại  
* Khi Agent lặp vòng (infinite loop)

👉 Chatbot nhanh hơn, ổn định hơn trong câu hỏi đơn giản

 

**Observation:**

Observation (kết quả từ tool) có vai trò cực kỳ quan trọng:

* Cung cấp **data thực tế**  
* Giúp Agent điều chỉnh bước tiếp theo  
* Giảm hoàn toàn hallucination

Ví dụ:

* Không có Observation → LLM đoán  
* Có Observation → LLM trả lời chính xác

 

**IV. Future Improvements (5 Points)**

**Scalability:**

* Sử dụng **queue bất đồng bộ (Celery / Kafka)** cho tool calls  
* Tách riêng:  
  * LLM service  
  * Crawling service

 

**Safety:**

* Thêm **Supervisor LLM** để kiểm tra output  
* Giới hạn:  
  * max\_iterations (tránh loop vô hạn)  
* Validate input/output của tool

 

**Performance:**

* Dùng **Vector Database (FAISS / Pinecone)** để:  
  * Truy xuất tool nhanh hơn  
* Cache kết quả crawling  
* Giảm số lần gọi LLM

 

