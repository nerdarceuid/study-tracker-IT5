from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hi" : "Hello"}

@app.get("/items/{items.id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}