from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Book(BaseModel):
    name: str
    price: float
    is_offer: bool | None = None

@app.get("/")
def read_root(): # getting the root of the file
    return {"Hello": "Hi"} # this should print/shown in / 

@app.get("/books/{books_id}")
# Initialize the datatypes and for what I know about | None is that it would return to nothing instead of an error
def read_book(books_id: int, q: str | None = None):
    #this should appear on the docs
    return {"books_id": books_id, "q": q}


@app.put("/books/{books_id}") #the update function here
def update_book(books_id: int,  books: Book):
    return {"Book Title": books.name, "Book ID": books_id}
