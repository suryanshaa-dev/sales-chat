from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.db.dependencies import get_db
from backend.app.schemas.auth import LoginRequest
from backend.app.services.auth import authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/chat")
def chat():
    return {"message": "connected"}
