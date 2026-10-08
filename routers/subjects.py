from fastapi import APIRouter, HTTPException, status
 
from dependencies import StorageDep
from schemas import SubjectCreate, SubjectRead

router = APIRouter(prefix="/subjects", tags=["subjects"])
 
 
def _subject_not_found(subject_id: int) -> HTTPException:
    """Build the 404 error. A helper so the message is identical everywhere.
    We RETURN the exception and the caller does `raise`, so it is obvious
    in the endpoint where the function stops."""
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Subject {subject_id} not found",
    )
 
@router.post("", response_model=SubjectRead, status_code=status.HTTP_201_CREATED)
def create_subject(subject: SubjectCreate, storage: StorageDep):
   
    return storage.subjects.create(subject.model_dump())
 
 

@router.get("", response_model=list[SubjectRead])
def list_subjects(storage: StorageDep):
    return storage.subjects.list_all()
 
@router.get("/{subject_id}", response_model=SubjectRead)
def get_subject(subject_id: int, storage: StorageDep):
    subject = storage.subjects.get(subject_id)
    if subject is None:
        raise _subject_not_found(subject_id)
    return subject
 

@router.put("/{subject_id}", response_model=SubjectRead)
def replace_subject(subject_id: int, subject: SubjectCreate, storage: StorageDep):
    updated = storage.subjects.replace(subject_id, subject.model_dump())
    if updated is None:
        raise _subject_not_found(subject_id)
    return updated
 

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, storage: StorageDep):
 
    if storage.subjects.get(subject_id) is None:
        raise _subject_not_found(subject_id)
 
    if storage.subject_in_use(subject_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Subject {subject_id} still has tasks or sessions; "
                "delete those first"
            ),
        )
 
    storage.subjects.delete(subject_id)
 
