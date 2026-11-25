"""Announcement listing and authenticated management endpoints."""

from datetime import date
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from ..database import announcements_collection
from .auth import require_session

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementInput(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    start_date: Optional[date] = None
    expires_at: date


def document_data(announcement: AnnouncementInput):
    message = announcement.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="A mensagem é obrigatória")
    if announcement.start_date and announcement.start_date > announcement.expires_at:
        raise HTTPException(status_code=422, detail="A data de início deve ser anterior ou igual à expiração")
    return {
        "message": message,
        "start_date": announcement.start_date.isoformat() if announcement.start_date else None,
        "expires_at": announcement.expires_at.isoformat(),
    }


def serialize(document):
    today = date.today().isoformat()
    status = "expired" if document["expires_at"] < today else (
        "scheduled" if document.get("start_date") and document["start_date"] > today else "active"
    )
    return {"id": str(document["_id"]), "message": document["message"],
            "start_date": document.get("start_date"), "expires_at": document["expires_at"], "status": status}


def object_id(announcement_id: str):
    try:
        return ObjectId(announcement_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")


@router.get("")
def active_announcements():
    """List announcements active today, including their start and expiration dates."""
    today = date.today().isoformat()
    query = {"expires_at": {"$gte": today}, "$or": [{"start_date": None}, {"start_date": {"$lte": today}}]}
    return [serialize(item) for item in announcements_collection.find(query).sort("_id", -1)]


@router.get("/all")
def all_announcements(teacher=Depends(require_session)):
    """List all announcements for an authenticated teacher."""
    return [serialize(item) for item in announcements_collection.find().sort("_id", -1)]


@router.post("", status_code=201)
def create_announcement(announcement: AnnouncementInput, teacher=Depends(require_session)):
    """Create an announcement with a required expiration date."""
    document = document_data(announcement)
    document["_id"] = announcements_collection.insert_one(document).inserted_id
    return serialize(document)


@router.put("/{announcement_id}")
def update_announcement(announcement_id: str, announcement: AnnouncementInput, teacher=Depends(require_session)):
    """Replace an existing announcement."""
    identifier = object_id(announcement_id)
    document = document_data(announcement)
    result = announcements_collection.update_one({"_id": identifier}, {"$set": document})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    return serialize({"_id": identifier, **document})


@router.delete("/{announcement_id}", status_code=204)
def delete_announcement(announcement_id: str, teacher=Depends(require_session)):
    """Delete an existing announcement."""
    result = announcements_collection.delete_one({"_id": object_id(announcement_id)})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    return Response(status_code=204)