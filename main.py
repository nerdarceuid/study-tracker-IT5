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
        return list(self._tasks.values())
    
    def get(self, task_id: int) -> dict | None:
        
        if task_id not in self._tasks:
            return None
        task = {**data, "id": task_id} #keep the original one and ignore id in body

        self._tasks[task_id] = task
        return task

    def delete(self, task_id: int) -> bool:

        return self._tasks.pop(task_id, None) is not None

#only lives in memory
storage = TaskStorage()

@app.get("/")
def read_root():
    return {"message": "the api is working/running"}

@app.post("/task", status_code=status.HTTP_201_CREATED)
def create_task(task: dict):
    return storage.create(task)

@app.get("/tasks")
def list_tasks():
    return storage.list_all()

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = storage.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task ID:{task_id} not found"
        )
    return task

@app.put("/tasks/{task_id}")
def replace_task(task_id: int, task: dict):
    updated = storage.replace(task_id, task)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task ID:{task_id} not found"
        )
    return updated

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    if not storage.delete(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task ID:{task_id} not found"
        )