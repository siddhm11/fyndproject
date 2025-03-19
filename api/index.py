from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import os
from mangum import Adapter
from jose import jwt, JWTError

# Create a new FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import your models, database connection, and other functions from main.py
# We're importing these directly rather than including the router
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os
from pymongo import TEXT
from bson import ObjectId
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

# Security setup (copy from your main.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.getenv("SECRET_KEY", "5ba6d2ba997729a5a8ed909ffd2d483d395401ceacb43dff82272c73cb010958")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "movie_db"
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

# Copy your models
class User(BaseModel):
    username: str
    email: EmailStr
    disabled: bool = False
    role: str = "user"

class UserInDB(User):
    hashed_password: str

class Movie(BaseModel):
    title: str
    year: int
    genre: str
    director: str
    cast: list[str]
    rating: float
    description: Optional[str] = None

class MovieInDB(Movie):
    id: str

# Copy your authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Define your routes (copy from main.py but on the new app)
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_doc = await db.users.find_one({"username": form_data.username})
    if not user_doc:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if not verify_password(form_data.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    access_token = create_access_token(
        data={"sub": user_doc["username"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# Copy all your other routes from main.py here...
# (Get users, create/get movies, etc.)

# Create the serverless handler
from mangum import Mangum
handler = Mangum(app)
