
import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

class SubjectCreate(BaseModel):
    """Input model for POST /subjects and PUT /subjects/{id}."""


    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"name": "Discrete Mathematics", "description": "Logic, sets, graphs"}
            ]
        },
    )

    name: str = Field(min_length=1, max_length=100)


    description: str | None = Field(default=None, max_length=500)

class SubjectRead(SubjectCreate):
    """Output model: everything in SubjectCreate plus the server-made id."""

    id: int

class TaskBase(BaseModel):
    """Fields shared by every task model, so we write them only once."""

    model_config = ConfigDict(extra="forbid")


    subject_id: int = Field(ge=1)


    title: str = Field(min_length=1, max_length=200)

    status: TaskStatus = TaskStatus.todo

    priority: int = Field(ge=1, le=3)


    due_date: datetime.date | None = None

    notes: str | None = Field(default=None, max_length=1000)


class TaskCreate(TaskBase):
    """Input model for POST /tasks (a NEW task)."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "subject_id": 1,
                    "title": "Read chapter 3",
                    "status": "todo",
                    "priority": 2,
                    "due_date": "2026-12-01",
                    "notes": "Focus on the proofs",
                }
            ]
        }
    )

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, value: datetime.date | None) -> datetime.date | None:
        if value is not None and value < datetime.date.today():
            raise ValueError("due_date cannot be in the past")
        return value


class TaskReplace(TaskBase):
    """Input model for PUT /tasks/{id}: a FULL replacement (all required
    fields must be sent again). No past-date check, see the note above."""


class TaskPatch(BaseModel):
    """Input model for PATCH /tasks/{id}: a PARTIAL update.

    Every field is optional. The router uses model_dump(exclude_unset=True)
    so only the fields the client actually sent are changed.
    """

    model_config = ConfigDict(extra="forbid")

    subject_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: TaskStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    due_date: datetime.date | None = None
    notes: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def required_fields_cannot_be_null(self) -> "TaskPatch":
        for name in ("subject_id", "title", "status", "priority"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class TaskRead(TaskBase):
    """Output model for every endpoint that returns a task."""

    id: int

class SessionCreate(BaseModel):
    """Input model for POST /sessions."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "subject_id": 1,
                    "task_id": 1,
                    "minutes": 45,
                    "date": "2026-10-09",
                    "notes": "Finished the exercises",
                }
            ]
        },
    )

    subject_id: int = Field(ge=1)

  
    task_id: int | None = Field(default=None, ge=1)

  
    minutes: int = Field(ge=1, le=600)

   
    date: datetime.date

    notes: str | None = Field(default=None, max_length=1000)


class SessionRead(SessionCreate):
    """Output model: the session plus its id."""

    id: int

class SubjectMinutes(BaseModel):
    """Minutes studied for ONE subject (one row of the summary)."""

    subject_id: int
    subject_name: str
    total_minutes: int


class StatsSummary(BaseModel):
    """Output model for GET /stats/summary."""

    total_minutes: int 
    subjects: list[SubjectMinutes]  