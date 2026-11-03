from fastapi import FastAPI, HTTPException, Request
from backend.app.api.routes.auth import router as auth_router
from fastapi.responses import StreamingResponse
import json
import asyncio
app = FastAPI()
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from backend.ai.main import run_sales_agent

load_dotenv()

import os

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SESSION_SECRET"],
    session_cookie="sales_session",
    max_age=60 * 60 * 24,
    same_site="lax",
    https_only=os.getenv("ENVIRONMENT") == "production",
)

app.include_router(auth_router)


@app.post("/auth/chat")
async def chat(request: Request):
    data = await request.json()
    thread_id = data.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise HTTPException(status_code=400, detail="thread_id is required")

    def encode_sse(event: str, payload: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    async def event_stream():
        try:
            async for item in run_sales_agent(
                data.get("user_query"), data.get("selected_model"), thread_id
            ):
                yield encode_sse(item["event"], item["data"])
            yield encode_sse("done", {})
        except Exception as exc:
            yield encode_sse("error", {"message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
