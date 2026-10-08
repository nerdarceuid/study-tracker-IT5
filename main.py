from contextlib import asynccontextmanager
 
from fastapi import FastAPI
 
from routers import sessions, stats, subjects, tasks
from storage import init_db
 
 
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  
    yield  
 

app = FastAPI(
    title="Study Tracker API ni Rhovic",
    version="beatrice",
    lifespan=lifespan,
)
 

app.include_router(subjects.router)
app.include_router(tasks.router)
app.include_router(sessions.router)
app.include_router(stats.router)
 

@app.get("/", tags=["root"])
def read_root():
    return {"message": "api is running"}
