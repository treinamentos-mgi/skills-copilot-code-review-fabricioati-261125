"""
Authentication endpoints for the High School Management System API
"""

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Dict, Any

from ..database import db, teachers_collection, verify_password

sessions_collection = db['sessions']


class LoginInput(BaseModel):
    username: str
    password: str

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


def require_session(session: str = Cookie(None)) -> Dict[str, Any]:
    if not session:
        raise HTTPException(status_code=401, detail="Authentication required")
    token_hash = hashlib.sha256(session.encode()).hexdigest()
    record = sessions_collection.find_one({
        "_id": token_hash, "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    teacher = teachers_collection.find_one({"_id": record["username"]}) if record else None
    if not teacher:
        raise HTTPException(status_code=401, detail="Authentication required")
    return teacher


@router.post("/login")
def login(credentials: LoginInput, request: Request, response: Response) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.find_one({"_id": credentials.username})

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), credentials.password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(32)
    sessions_collection.insert_one({
        "_id": hashlib.sha256(token.encode()).hexdigest(),
        "username": credentials.username,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=12),
    })
    response.set_cookie("session", token, httponly=True, samesite="strict",
                        secure=request.url.scheme == "https", max_age=43200, path="/")

    # Return teacher information (excluding password)
    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }


@router.get("/check-session")
def check_session(session: str = Cookie(None)) -> Dict[str, Any]:
    """Check the current authenticated session."""
    teacher = require_session(session)

    return {
        "username": teacher["username"],
        "display_name": teacher["display_name"],
        "role": teacher["role"]
    }


@router.post("/logout")
def logout(response: Response, session: str = Cookie(None)):
    """Invalidate the current session."""
    if session:
        sessions_collection.delete_one({"_id": hashlib.sha256(session.encode()).hexdigest()})
    response.delete_cookie("session", path="/")
    return {"message": "Logged out"}
