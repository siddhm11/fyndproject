   
from fastapi import FastAPI
from app.routes.movies import router as movies_router
from app.routes.auth import router as auth_router


app = FastAPI(TITLE = "Movie API",version = "1.0")

app.include_router(movies_router , prefix = "/movies",tags = ["Movies"])
app.include_router(auth_router, prefix="/auth", tags = ["Authentication"])

@app.get("/")
def read_root():
    return {"message" , "Welcome to the Movies API cmon"}
