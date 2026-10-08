from fastapi import APIRouter
 
from dependencies import StorageDep
from schemas import StatsSummary, SubjectMinutes
 
router = APIRouter(prefix="/stats", tags=["stats"])
 
 
@router.get("/summary", response_model=StatsSummary)
def stats_summary(storage: StorageDep):
   
    minutes = storage.minutes_per_subject()
 

    rows = [
        SubjectMinutes(
            subject_id=subject["id"],
            subject_name=subject["name"],
            total_minutes=minutes.get(subject["id"], 0),
        )
        for subject in storage.subjects.list_all()
    ]
 

    return StatsSummary(
        total_minutes=sum(row.total_minutes for row in rows),
        subjects=rows,
    )
