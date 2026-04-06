import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import api  # Import file api.py bạn vừa tạo

app = FastAPI(
    title="Cinestar AI Gateway",
    description="Backend AI Services cho Lab 3",
    version="1.0"
)

# Cấu hình CORS để cho phép Next.js (client) gọi API không bị lỗi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong production nên đổi thành localhost của Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ghép nối Router
app.include_router(api.router)

@app.get("/")
async def root():
    return {"message": "AI Gateway is running! Mở /docs để xem Swagger UI."}

if __name__ == "__main__":
    print("🚀 Khởi động Server AI tại: http://localhost:8000")
    print("👉 Xem tài liệu API tại: http://localhost:8000/docs")
    # Lệnh reload=True giúp tự update code khi bạn chỉnh sửa api.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)