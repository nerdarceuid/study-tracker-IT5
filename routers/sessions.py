import datetime
from typing import Annotated
 
from fastapi import APIRouter, HTTPException, Query, status
 
from dependencies import StorageDep
from schemas import SessionCreate, SessionRead
 
router = APIRouter(prefix="/sessions", tags=["sessions"])
 
@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session(session: SessionCreate, storage: StorageDep):
    if storage.subjects.get(session.subject_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject {session.subject_id} not found",
        )
 
    if session.task_id is not None:
        task = storage.tasks.get(session.task_id)

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {session.task_id} not found",
            )
 
        if task["subject_id"] != session.subject_id:
            raise HTTPException(
                status_code=422, 
                detail=(
                    f"Task {session.task_id} belongs to subject "
                    f"{task['subject_id']}, not {session.subject_id}"
                ),
            )
 
    return storage.sessions.create(session.model_dump())
 
 
@router.get("", response_model=list[SessionRead])
def list_sessions(
    storage: StorageDep,
    subject_id: Annotated[
        int | None, Query(ge=1, description="Only sessions of this subject")
    ] = None,
    date_from: Annotated[
        datetime.date | None,
        Query(description="Only sessions on or after this date (YYYY-MM-DD)"),
    ] = None,
    date_to: Annotated[
        datetime.date | None,
        Query(description="Only sessions on or before this date (YYYY-MM-DD)"),
    ] = None,
):

    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=422,  
            detail="date_from must not be after date_to",
        )
 
    sessions = storage.sessions.list_all()
 
    if subject_id is not None:
        sessions = [s for s in sessions if s["subject_id"] == subject_id]
 

    if date_from is not None:
        sessions = [s for s in sessions if s["date"] >= date_from]
 
    if date_to is not None:
        sessions = [s for s in sessions if s["date"] <= date_to]
 
    return sessions
 

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, storage: StorageDep):
    if not storage.sessions.delete(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
 
