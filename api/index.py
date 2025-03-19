# Use the cleaned up and fixed main.py from the backend folder
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from jose import jwt, JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from pymongo import TEXT
from bson import ObjectId
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import traceback

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.getenv("SECRET_KEY", "5ba6d2ba997729a5a8ed909ffd2d483d395401ceacb43dff82272c73cb010958")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create a new FastAPI app - no root_path for Vercel
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup - ensure consistent connection string format
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://admin:test1234%21@clusterfynd.bng6e.mongodb.net/?retryWrites=true&w=majority&appName=clusterfynd")
# Print the connection string for debugging (remove in production)
print(f"MongoDB URL: {MONGODB_URL}")

# Ensure we have the database name in the connection string
DB_NAME = "movie_db"
try:
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DB_NAME]
    print("MongoDB connection successful")
except Exception as e:
    print(f"MongoDB connection error: {str(e)}")
    print(traceback.format_exc())
    # Create a dummy DB object to prevent the app from crashing
    client = None
    db = None

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
    try:
        if db is not None:
            await db.movies.create_index([("title", TEXT), ("genre", TEXT), ("director", TEXT)])
            print("Indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")
        print(traceback.format_exc())

# Authentication functions
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
    try:
        print(f"Login attempt for user: {form_data.username}")
        user_doc = await db.users.find_one({"username": form_data.username})
        if not user_doc:
            print(f"User not found: {form_data.username}")
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        
        if not verify_password(form_data.password, user_doc["hashed_password"]):
            print(f"Invalid password for user: {form_data.username}")
            raise HTTPException(status_code=400, detail="Incorrect password")
        
        access_token = create_access_token(
            data={"sub": user_doc["username"]}
        )
        print(f"Login successful for user: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        print(f"Login error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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
    try:
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
    except Exception as e:
        print(f"Error fetching movies: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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

# Error handling middleware
@app.middleware("http")
async def add_error_handling(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"Unhandled exception: {str(e)}")
        print(traceback.format_exc())
        return HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Create the serverless handler
# Create the serverless handler
from mangum import Mangum
handler = Mangum(app)
