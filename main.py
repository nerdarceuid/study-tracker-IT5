from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "sat na buhaton", "message": "Hi"}