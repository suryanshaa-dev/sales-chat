from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.db.dependencies import get_db
from backend.app.schemas.auth import LoginRequest
from backend.app.services.auth import authenticate_user
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me")
def current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in")
    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in")
    return {"id": user.id, "first_name": user.first_name, "email": user.email}


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}


@router.post("/login")
def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=str(credentials.email),
        password=credentials.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    request.session["user_id"] = user.id

    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "email": user.email,
        },
    }
