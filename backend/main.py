# main.py
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import TEXT
from bson import ObjectId
import os
from typing import Optional, List
from dotenv import load_dotenv
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # Load .env file

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.getenv("SECRET_KEY", "5ba6d2ba997729a5a8ed909ffd2d483d395401ceacb43dff82272c73cb010958")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create FastAPI app without root_path for local development
# Vercel handles the routing with vercel.json
app = FastAPI()
from mangum import Mangum
handler = Mangum(app)

# Add CORS middleware BEFORE routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (temporary for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# MongoDB setup - ensure consistent connection string format
MONGODB_URI = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
# Ensure we have the database name in the connection string
DB_NAME = "movie_db"
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

# Models
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
    cast: List[str]
    rating: float
    description: Optional[str] = None

class MovieInDB(Movie):
    id: str

# Create indexes
@app.on_event("startup")
async def create_indexes():
    await db.movies.create_index([("title", TEXT), ("genre", TEXT), ("director", TEXT)])

# Auth functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserInDB(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Routes
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_doc = await db.users.find_one({"username": form_data.username})
    if not user_doc:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Password verification
    if not verify_password(form_data.password, user_doc["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": user_doc["username"]}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/movies/", response_model=MovieInDB)
async def create_movie(movie: Movie, admin: User = Depends(get_admin_user)):
    movie_dict = movie.dict()
    result = await db.movies.insert_one(movie_dict)
    return {**movie_dict, "id": str(result.inserted_id)}

@app.get("/movies/", response_model=List[MovieInDB])
async def get_movies(search: Optional[str] = None):
    if search:
        query = {"$text": {"$search": search}}
        movies = await db.movies.find(query).to_list(100)
    else:
        movies = await db.movies.find().to_list(100)
    
    # Fix the ID handling in the return
    movie_list = []
    for m in movies:
        movie_dict = {k: v for k, v in m.items() if k != "_id"}
        movie_dict["id"] = str(m["_id"])
        movie_list.append(movie_dict)
    
    return movie_list

@app.put("/movies/{movie_id}", response_model=MovieInDB)
async def update_movie(movie_id: str, movie: Movie, admin: User = Depends(get_admin_user)):
    movie_dict = movie.dict()
    await db.movies.update_one({"_id": ObjectId(movie_id)}, {"$set": movie_dict})
    updated_movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
    if not updated_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Fix the ID handling in the return
    movie_dict = {k: v for k, v in updated_movie.items() if k != "_id"}
    movie_dict["id"] = str(updated_movie["_id"])
    
    return movie_dict

@app.get("/movies/{movie_id}", response_model=MovieInDB)
async def get_movie(movie_id: str):
    movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Fix the ID handling in the return
    movie_dict = {k: v for k, v in movie.items() if k != "_id"}
    movie_dict["id"] = str(movie["_id"])
    
    return movie_dict

@app.post("/register/", response_model=User)
async def register_user(
    username: str,
    password: str,
    email: EmailStr,
    admin: User = Depends(get_admin_user)
):
    # Check if user exists
    if await db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed_password = get_password_hash(password)
    user_data = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "role": "user",
        "disabled": False
    }
    
    result = await db.users.insert_one(user_data)
    user_data_out = {k: v for k, v in user_data.items() if k != "hashed_password"}
    return user_data_out

# Root route for testing connection
@app.get("/")
async def root():
    return {"message": "API is running! Connect to /movies/ to see data."}
