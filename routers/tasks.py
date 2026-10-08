import datetime
from typing import Annotated
 
from fastapi import APIRouter, HTTPException, Query, status
 
from dependencies import PaginationDep, StorageDep
from schemas import TaskCreate, TaskPatch, TaskRead, TaskReplace, TaskStatus
from storage import Storage
 
router = APIRouter(prefix="/tasks", tags=["tasks"])
 
 
def _get_task_or_404(storage: Storage, task_id: int) -> dict:
    """Return the task, or raise 404 if it doesn't exist."""
    task = storage.tasks.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task
 
 
def _require_subject(storage: Storage, subject_id: int) -> None:
    """RULE: a task needs a subject that exists, otherwise 404."""
    if storage.subjects.get(subject_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject {subject_id} not found",
        )
 
 
@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, storage: StorageDep):
    _require_subject(storage, task.subject_id)
    return storage.tasks.create(task.model_dump())
 

@router.get("", response_model=list[TaskRead])
def list_tasks(
    storage: StorageDep,
    pagination: PaginationDep, 

    status_filter: Annotated[
        TaskStatus | None,
        Query(alias="status", description="Only tasks with this status"),
    ] = None,
    subject_id: Annotated[
        int | None, Query(ge=1, description="Only tasks of this subject")
    ] = None,

    due_before: Annotated[
        datetime.date | None,
        Query(description="Only tasks due BEFORE this date (YYYY-MM-DD)"),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            description="Search text in title or notes (case-insensitive)",
        ),
    ] = None,
):
    tasks = storage.tasks.list_all()
 
   
    if status_filter is not None:
        tasks = [t for t in tasks if t["status"] == status_filter]
 
    if subject_id is not None:
        tasks = [t for t in tasks if t["subject_id"] == subject_id]
 
    if due_before is not None:
        tasks = [
            t for t in tasks if t["due_date"] is not None and t["due_date"] < due_before
        ]
 
    if q is not None:
        needle = q.lower()  
        tasks = [
            t
            for t in tasks
            if needle in t["title"].lower()
            
            or (t["notes"] is not None and needle in t["notes"].lower())
        ]

    return tasks[pagination.skip : pagination.skip + pagination.limit]

@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, storage: StorageDep):
    return _get_task_or_404(storage, task_id)
 

@router.put("/{task_id}", response_model=TaskRead)
def replace_task(task_id: int, task: TaskReplace, storage: StorageDep):
    _get_task_or_404(storage, task_id)  # 404 if the task doesnt exist
    _require_subject(storage, task.subject_id)  
    return storage.tasks.replace(task_id, task.model_dump())
 
@router.patch("/{task_id}", response_model=TaskRead)
def patch_task(task_id: int, patch: TaskPatch, storage: StorageDep):
    _get_task_or_404(storage, task_id)
 
    changes = patch.model_dump(exclude_unset=True)
 
 
    if "subject_id" in changes:
        _require_subject(storage, changes["subject_id"])
 
    return storage.tasks.update(task_id, changes)
 
 
# DELETE ----------------------------------------------------------------------
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, storage: StorageDep):
    _get_task_or_404(storage, task_id)
    storage.tasks.delete(task_id)

    storage.detach_task_from_sessions(task_id)
 
