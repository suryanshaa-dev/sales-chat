from fastapi import FastAPI, Request
from backend.app.api.routes.auth import router as auth_router
from fastapi.responses import StreamingResponse
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
    return StreamingResponse(
     run_sales_agent(data.get("user_query")),
        media_type="text/plain",
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
