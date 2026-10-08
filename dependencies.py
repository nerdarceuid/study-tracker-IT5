from collections.abc import Iterator
from typing import Annotated
 
from fastapi import Depends, Query
 
from storage import Storage, connect
 
def get_storage() -> Iterator[Storage]:
    """Open a database connection, hand a Storage to the endpoint, close it."""
    conn = connect()
    try:
        yield Storage(conn)  
    finally:
        conn.close()  

StorageDep = Annotated[Storage, Depends(get_storage)]
 
class Pagination:
    def __init__(
        self,
        
        skip: Annotated[
            int, Query(ge=0, description="How many items to skip")
        ] = 0,
        
        limit: Annotated[
            int, Query(ge=1, le=100, description="Maximum number of items to return")
        ] = 10,
    ) -> None:
        self.skip = skip
        self.limit = limit
 
 

PaginationDep = Annotated[Pagination, Depends()]
 
