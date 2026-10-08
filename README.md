# Study Tracker API

IT5 Final Project with **FastAPI** and **SQLite** 
---

## 1. Requirements

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/) (recommended), or plain `pip`

## 2. Installation

From the project folder (the one containing `pyproject.toml`):

```bash
uv sync
```

Without uv:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate | fish: source .venv/bin/activate.fish
pip install "fastapi[standard]"
```

## NOTE: No database server is needed: SQLite is built into Python.
(_Note that the main.py auto creates .db file if it does not exists_)
## > To start from an empty database, stop the server, delete `study_tracker.db`, and start the server again.)

## 3. Running the application

Go into the folder that contains `main.py` and start the server:

```bash
uv run fastapi dev main.py
```

(or, with an activated virtual environment: `fastapi dev main.py`)

> Run the command from inside the folder that contains `main.py`.

Then open the interactive documentation in a browser:

**http://127.0.0.1:8000/docs**

This Swagger page lists every endpoint and lets you test them directly. To stop the server, press `Ctrl+C` in the terminal.


## 4. Using the API in Swagger (/docs)

Click an endpoint, press **Try it out**, edit the request body, then press **Execute**. The result appears under "Server response". A suggested order:

1. **Create a subject:** `POST /subjects`
   ```json
   {"name": "Discrete Mathematics", "description": "Logic, sets, graphs"}
   ```
   Expect **201** with `"id": 1`.

2. **Create a task:** `POST /tasks` (use a `due_date` of today or later)
   ```json
   {"subject_id": 1, "title": "Read chapter 3", "priority": 2, "due_date": "2030-12-01"}
   ```
   Expect **201**, with `"status": "todo"` filled in by default.

3. **Update only the status:** `PATCH /tasks/1`
   ```json
   {"status": "in_progress"}
   ```
   Expect **200**; the other fields stay the same.

4. **Log a study session:** `POST /sessions`
   ```json
   {"subject_id": 1, "task_id": 1, "minutes": 45, "date": "2026-10-09"}
   ```
   Expect **201**.

5. **See the statistics:** `GET /stats/summary`. Expect `total_minutes: 45` and a row for subject 1.

6. **Try the filters:** `GET /tasks`, then fill in the optional fields, for example `status = in_progress`, `q = chapter`, `limit = 5`.

7. **Try the error cases:**
   - `POST /tasks` with `"subject_id": 99` returns **404** (subject does not exist)
   - `POST /tasks` with `"priority": 5` returns **422** (priority must be 1 to 3)
   - `POST /sessions` with `"minutes": 601` returns **422** (minutes must be 1 to 600)
   - `POST /tasks` with a `due_date` in the past returns **422**
   - `DELETE /subjects/1` returns **409** while the subject still has tasks or sessions
