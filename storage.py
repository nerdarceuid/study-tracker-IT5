import datetime
import sqlite3
from enum import Enum
from pathlib import Path

DB_PATH = str(Path(__file__).parent / "study_tracker.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS subjects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 100),
    description TEXT
);
 
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    title      TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 200),
    status     TEXT NOT NULL DEFAULT 'todo'
               CHECK (status IN ('todo', 'in_progress', 'done')),
    priority   INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 3),
    due_date   TEXT,
    notes      TEXT
);
 
CREATE TABLE IF NOT EXISTS sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    task_id    INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    minutes    INTEGER NOT NULL CHECK (minutes BETWEEN 1 AND 600),
    date       TEXT NOT NULL,
    notes      TEXT
);
"""
 
def connect() -> sqlite3.Connection:
    """Open a NEW connection to the database file.
 
    We open one connection per request (see dependencies.py) and close it
    afterwards. That is the simplest safe pattern for SQLite + FastAPI.
    """

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
 
    conn.row_factory = sqlite3.Row
 

    conn.execute("PRAGMA foreign_keys = ON")
    return conn
 
 
def init_db() -> None:
    """Create the tables if they don't exist yet. Called once at startup."""
    conn = connect()
    try:
        conn.executescript(SCHEMA) 
        conn.commit()
    finally:
        conn.close()
 
 
def _to_db(value):
    """Convert a Python value into something SQLite can store.
 
    Pydantic hands us Enum members (TaskStatus.todo) and date objects, which
    SQLite doesn't understand, so we turn them into plain text first.
    """
    if isinstance(value, Enum):
        return value.value  
    if isinstance(value, datetime.date):
        return value.isoformat()  
    return value  
 
class Table:
    """CRUD operations for ONE table. Used three times (subjects, tasks,
    sessions) so the SQL is written once.
 
    A row is returned as a plain dict, e.g. {"id": 1, "title": "Read", ...},
    exactly like the in-memory version did.
    """
 
    def __init__(
        self,
        conn: sqlite3.Connection,
        name: str,
        columns: tuple[str, ...],
        date_columns: tuple[str, ...] = (),
    ) -> None:
        self._conn = conn
        self._name = name  
  
        self._columns = columns
        self._date_columns = date_columns
 

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        data = dict(row)
        for col in self._date_columns:
            if data[col] is not None:
                data[col] = datetime.date.fromisoformat(data[col])
        return data
 
    def _check_columns(self, data: dict) -> None:
        unknown = set(data) - set(self._columns)
        if unknown:
            raise ValueError(f"Unknown column(s) for {self._name}: {unknown}")
 

    def create(self, data: dict) -> dict:
        self._check_columns(data)
        cols = list(data)
        sql = (
            f"INSERT INTO {self._name} ({', '.join(cols)}) "
            f"VALUES ({', '.join('?' for _ in cols)})"
        )
        cursor = self._conn.execute(sql, [_to_db(data[c]) for c in cols])
        self._conn.commit()
    
        return self.get(cursor.lastrowid)
 
    def get(self, row_id: int) -> dict | None:
        row = self._conn.execute(
            f"SELECT * FROM {self._name} WHERE id = ?", (row_id,)
        ).fetchone() 
        return None if row is None else self._row_to_dict(row)
 
    def list_all(self) -> list[dict]:
        rows = self._conn.execute(
            f"SELECT * FROM {self._name} ORDER BY id"
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]
 
    def replace(self, row_id: int, data: dict) -> dict | None:
        # PUT: overwrite EVERY column with the new values.
        self._check_columns(data)
        assignments = ", ".join(f"{c} = ?" for c in data)  
        cursor = self._conn.execute(
            f"UPDATE {self._name} SET {assignments} WHERE id = ?",
            [_to_db(v) for v in data.values()] + [row_id],
        )
        self._conn.commit()
    
        return self.get(row_id) if cursor.rowcount else None
 
    def update(self, row_id: int, changes: dict) -> dict | None:
        
        if not changes:
            return self.get(row_id)
        return self.replace(row_id, changes) 
 
    def delete(self, row_id: int) -> bool:
        cursor = self._conn.execute(
            f"DELETE FROM {self._name} WHERE id = ?", (row_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0  
 
 
class Storage:
    """What the routers receive: three tables plus the few queries that need
    to look ACROSS tables."""
 
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.subjects = Table(conn, "subjects", ("name", "description"))
        self.tasks = Table(
            conn,
            "tasks",
            ("subject_id", "title", "status", "priority", "due_date", "notes"),
            date_columns=("due_date",),
        )
        self.sessions = Table(
            conn,
            "sessions",
            ("subject_id", "task_id", "minutes", "date", "notes"),
            date_columns=("date",),
        )
 
    def subject_in_use(self, subject_id: int) -> bool:
        """True if any task or session still belongs to this subject.
        Used by DELETE /subjects/{id} to answer 409 Conflict."""
        row = self._conn.execute(
            """
            SELECT EXISTS (SELECT 1 FROM tasks    WHERE subject_id = ?)
                OR EXISTS (SELECT 1 FROM sessions WHERE subject_id = ?)
            """,
            (subject_id, subject_id),
        ).fetchone()
        return bool(row[0])  # EXISTS gives 1 or 0
 
    def detach_task_from_sessions(self, task_id: int) -> None:
        """Make sessions that pointed at this task point at nothing.
        The database already does this by itself (ON DELETE SET NULL); this
        explicit UPDATE keeps the behaviour visible in the code."""
        self._conn.execute(
            "UPDATE sessions SET task_id = NULL WHERE task_id = ?", (task_id,)
        )
        self._conn.commit()
 
    def minutes_per_subject(self) -> dict[int, int]:
        """Return {subject_id: total minutes studied}.
        The database does the adding: SUM(...) with GROUP BY subject_id.
        Subjects with no sessions don't appear; the stats router adds 0."""
        rows = self._conn.execute(
            "SELECT subject_id, SUM(minutes) AS total "
            "FROM sessions GROUP BY subject_id"
        ).fetchall()
        return {row["subject_id"]: row["total"] for row in rows}
 
