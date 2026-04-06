import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


# Khởi tạo Router
router = APIRouter(prefix="/api/v1", tags=["AI Chat Services"])


# --- DATA MODELS ---
class ChatRequest(BaseModel):
    user_message: str


class ChatResponse(BaseModel):
    status: str
    bot_type: str
    reply: str



# --- ENDPOINTS ---
@router.post("/baseline", response_model=ChatResponse)
async def chat_baseline(request: ChatRequest):
    """Bot cơ bản, chỉ dùng não LLM, KHÔNG dùng tool"""
    try:
        #reply = llm.invoke(request.user_message).content
        reply = ""
        return ChatResponse(status="success", bot_type="baseline", reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent", response_model=ChatResponse)
async def chat_react_agent(request: ChatRequest):
    """Bot thông minh, dùng ReAct Agent và Tool để cào data thực tế"""
    try:
        # Cách gọi AI MỚI: dùng .invoke thay vì .run
        # response = agent_executor.invoke({"input": request.user_message})

        # Lấy câu trả lời cuối cùng từ Output
        reply = ""
        return ChatResponse(status="success", bot_type="react_agent", reply=reply)
    except Exception as e:
        # Nhánh Bonus (Fallback Path) khi có lỗi
        return ChatResponse(
            status="error",
            bot_type="fallback",
            reply="Hệ thống AI đang quá tải hoặc lỗi mạng. Vui lòng liên hệ nhân viên hỗ trợ."
        )