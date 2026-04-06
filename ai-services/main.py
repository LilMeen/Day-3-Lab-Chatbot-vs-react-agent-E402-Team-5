import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import api
from routers.chat import router as chat_router

app = FastAPI(
    title="Movie Theater ReAct Agent API",
    description="ReAct agent chatbot for movie theater domain — showtimes, prices, promotions.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router)        # /api/v1/baseline  /api/v1/agent
app.include_router(chat_router)       # /agent/chat  /agent/reset  /agent/health


@app.get("/")
async def root():
    return {
        "message": "Movie Theater ReAct Agent API is running!",
        "docs": "/docs",
        "endpoints": {
            "baseline": "POST /api/v1/baseline",
            "agent":    "POST /api/v1/agent",
            "chat":     "POST /agent/chat",
            "reset":    "POST /agent/reset",
            "health":   "GET  /agent/health",
        },
    }


if __name__ == "__main__":
    print("Starting Movie Theater ReAct Agent API at: http://localhost:8000")
    print("Swagger UI: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
