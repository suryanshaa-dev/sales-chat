from fastapi import FastAPI, HTTPException, Request
from backend.app.api.routes.auth import router as auth_router
from fastapi.responses import StreamingResponse
import json
import asyncio

app = FastAPI()
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from backend.ai.main import run_sales_agent
from backend.app.db.database import Base, engine, SessionLocal
from backend.app.models.user import User  # noqa: F401
from backend.app.models.chat import Chat, ChatMessage
from sqlalchemy import inspect, select, text

load_dotenv()

import os

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(","),
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


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
    # create_all creates new tables but does not add columns to existing ones.
    columns = {column["name"] for column in inspect(engine).get_columns("chat_messages")}
    if "sources" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE chat_messages ADD COLUMN sources TEXT"))


def authenticated_user_id(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Please log in")
    return int(user_id)


@app.get("/auth/chats")
def list_chats(request: Request):
    user_id = authenticated_user_id(request)
    with SessionLocal() as db:
        chats = db.scalars(select(Chat).where(Chat.user_id == user_id).order_by(Chat.updated_at.desc())).all()
        return [{"id": chat.id, "title": chat.title} for chat in chats]


@app.get("/auth/chats/{thread_id}/messages")
def get_chat_messages(thread_id: str, request: Request):
    user_id = authenticated_user_id(request)
    with SessionLocal() as db:
        chat = db.scalar(select(Chat).where(Chat.id == thread_id, Chat.user_id == user_id))
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        return [{"id": message.id, "role": message.role, "content": message.content,
                 "data": json.loads(message.data) if message.data else None,
                 "sources": json.loads(message.sources) if message.sources else [],
                 "query_type": message.query_type}
                for message in chat.messages]


@app.post("/auth/chat")
async def chat(request: Request):
    data = await request.json()
    user_id = authenticated_user_id(request)
    thread_id = data.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise HTTPException(status_code=400, detail="thread_id is required")
    query = data.get("user_query")
    if not isinstance(query, str) or not query.strip():
        raise HTTPException(status_code=400, detail="user_query is required")

    with SessionLocal() as db:
        chat_record = db.scalar(select(Chat).where(Chat.id == thread_id, Chat.user_id == user_id))
        if chat_record is None:
            chat_record = Chat(id=thread_id, user_id=user_id, title=query.strip()[:255])
            db.add(chat_record)
            db.flush()
        elif chat_record.title == "New chat":
            chat_record.title = query.strip()[:255]
        conversation_history = []
        for message in db.scalars(
            select(ChatMessage).where(ChatMessage.chat_id == thread_id).order_by(ChatMessage.id)
        ):
            content = message.content
            if message.role == "assistant" and message.data:
                structured_data = json.loads(message.data)
                content = structured_data if isinstance(structured_data, str) else json.dumps(
                    structured_data, ensure_ascii=False
                )
            conversation_history.append({"role": message.role, "content": content})
        db.add(ChatMessage(chat_id=thread_id, role="user", content=query))
        db.commit()

    def encode_sse(event: str, payload: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

    async def event_stream():
        assistant_content = ""
        assistant_data = None
        assistant_sources = []
        query_type = None
        try:
            async for item in run_sales_agent(
                query,
                data.get("selected_model"),
                thread_id,
                conversation_history=conversation_history,
            ):
                if item["event"] == "metadata":
                    query_type = item["data"].get("query_type")
                elif item["event"] == "delta":
                    assistant_content += item["data"].get("content", "")
                elif item["event"] == "complete":
                    assistant_data = item["data"].get("response")
                    if isinstance(assistant_data, str):
                        assistant_content = assistant_data
                    elif assistant_data is not None:
                        assistant_content = json.dumps(assistant_data, ensure_ascii=False)
                elif item["event"] == "sources":
                    assistant_sources = item["data"].get("documents", [])
                yield encode_sse(item["event"], item["data"])
            with SessionLocal() as db:
                chat_record = db.get(Chat, thread_id)
                if chat_record is not None:
                    from datetime import datetime, timezone
                    chat_record.updated_at = datetime.now(timezone.utc)
                db.add(ChatMessage(chat_id=thread_id, role="assistant", content=assistant_content,
                                   data=json.dumps(assistant_data, ensure_ascii=False) if assistant_data is not None else None,
                                   sources=json.dumps(assistant_sources, ensure_ascii=False),
                                   query_type=query_type))
                db.commit()
            yield encode_sse("done", {})
        except Exception as exc:
            if assistant_content:
                with SessionLocal() as db:
                    db.add(ChatMessage(chat_id=thread_id, role="assistant", content=assistant_content, query_type=query_type))
                    db.commit()
            yield encode_sse("error", {"message": str(exc)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}
