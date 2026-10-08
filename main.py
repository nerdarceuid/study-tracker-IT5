from fastapi import FastAPI, HTTPException, status

app = FastAPI(title="Study Tracker ni Rhovic API ")


# Test first for all data access goes through this no database for now
class TaskStorage:
    def __init__(self):
        # fake database maps task id to task dictionary
        self._tasks: dict[int, dict] = {}

        #increment
        self._next_id: int = 1
    
    def create(self, data: dict) -> dict:
        #stored task, putting the id last so the user sends their own id then overwrite
        task = {**data, "id": self._next_id}
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def list_all(self) -> list[dict]:
        pass