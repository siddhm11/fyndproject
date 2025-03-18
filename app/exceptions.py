# app/exceptions.py
from fastapi import HTTPException, status

class MovieNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found in the database"
        )

class InvalidMovieIDException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid movie ID format"
        )