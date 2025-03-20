import logging
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

# Log setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("movie-api")

# Config
port = int(os.getenv("PORT", 8000))
logger.info(f"Port: {port}")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "5ba6d2ba997729a5a8ed909ffd2d483d395401ceacb43dff82272c73cb010958"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger.info("Security ready")

# FastAPI setup
app = FastAPI(
    title="Movie Database API",
    description="An API for searching and managing movie information with user authentication",
    version="1.0.0",
)
from mangum import Mangum
handler = Mangum(app, lifespan="off")  # Lambda handler

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS ready")

# MongoDB
MONGODB_URI = "mongodb+srv://admin:test1234%21@clusterfynd.bng6e.mongodb.net/?retryWrites=true&w=majority&appName=clusterfynd"
DB_NAME = "movie_db"

logger.info(f"DB: {DB_NAME}")
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
logger.info("MongoDB ready")

# Models
class User(BaseModel):
    """User data"""
    username: str
    email: EmailStr
    disabled: bool = False
    role: str = "user"

class UserInDB(User):
    """User + password"""
    hashed_password: str

class Movie(BaseModel):
    """Movie data"""
    title: str
    year: int
    genre: str
    director: str
    cast: List[str]
    rating: float
    description: Optional[str] = None

class MovieInDB(Movie):
    """Movie + ID"""
    id: str

# DB init
@app.on_event("startup")
async def create_indexes():
    """Create search indexes"""
    logger.info("Creating indexes")
    await db.movies.create_index([("title", TEXT), ("genre", TEXT), ("director", TEXT)])
    logger.info("Indexes ready")

# Auth funcs
def verify_password(plain_password, hashed_password):
    """Check password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash password"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """JWT token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Token created: {data.get('sub')}")
    return token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get user from token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            logger.warning("Bad token")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError as e:
        logger.warning(f"JWT fail: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"username": username})
    if not user:
        logger.warning(f"User not found: {username}")
        raise HTTPException(status_code=401, detail="User not found")
    
    logger.debug(f"Auth ok: {username}")
    return UserInDB(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    """Check admin rights"""
    if current_user.role != "admin":
        logger.warning(f"Access denied: {current_user.username}")
        raise HTTPException(status_code=403, detail="Admin access required")
    logger.debug(f"Admin ok: {current_user.username}")
    return current_user

# Routes

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login"""
    logger.info(f"Login: {form_data.username}")
    
    user_doc = await db.users.find_one({"username": form_data.username})
    if not user_doc:
        logger.warning(f"Login fail: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if not verify_password(form_data.password, user_doc["hashed_password"]):
        logger.warning(f"Bad password: {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(
        data={"sub": user_doc["username"]}
    )
    
    logger.info(f"Login ok: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """User profile"""
    logger.info(f"Profile: {current_user.username}")
    return current_user

@app.post("/movies/", response_model=MovieInDB)
async def create_movie(movie: Movie, admin: User = Depends(get_admin_user)):
    """Add movie (admin)"""
    logger.info(f"New movie: {movie.title} ({movie.year}) by {admin.username}")
    
    movie_dict = movie.dict()
    result = await db.movies.insert_one(movie_dict)
    logger.info(f"Movie ID: {result.inserted_id}")
    
    return {**movie_dict, "id": str(result.inserted_id)}

@app.get("/movies/", response_model=List[MovieInDB])
async def get_movies(search: Optional[str] = None):
    """Get movies"""
    if search:
        logger.info(f"Search: '{search}'")
        query = {"$text": {"$search": search}}
        movies = await db.movies.find(query).to_list(100)
        logger.info(f"Found: {len(movies)}")
    else:
        logger.info("All movies")
        movies = await db.movies.find().to_list(100)
        logger.info(f"Total: {len(movies)}")
    
    movie_list = []
    for m in movies:
        movie_dict = {k: v for k, v in m.items() if k != "_id"}
        movie_dict["id"] = str(m["_id"])
        movie_list.append(movie_dict)
    
    return movie_list

@app.put("/movies/{movie_id}", response_model=MovieInDB)
async def update_movie(movie_id: str, movie: Movie, admin: User = Depends(get_admin_user)):
    """Update movie (admin)"""
    logger.info(f"Update movie {movie_id}: {movie.title} by {admin.username}")
    
    try:
        movie_dict = movie.dict()
        result = await db.movies.update_one({"_id": ObjectId(movie_id)}, {"$set": movie_dict})
        
        if result.matched_count == 0:
            logger.warning(f"Movie not found: {movie_id}")
            raise HTTPException(status_code=404, detail="Movie not found")
            
        logger.info(f"Update ok: {movie_id}")
        
        updated_movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        if not updated_movie:
            logger.error(f"Updated movie missing: {movie_id}")
            raise HTTPException(status_code=404, detail="Movie not found after update")
        
        movie_dict = {k: v for k, v in updated_movie.items() if k != "_id"}
        movie_dict["id"] = str(updated_movie["_id"])
        
        return movie_dict
    except Exception as e:
        logger.error(f"Update error {movie_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating movie: {str(e)}")

@app.get("/movies/{movie_id}", response_model=MovieInDB)
async def get_movie(movie_id: str):
    """Get movie by ID"""
    logger.info(f"Get movie: {movie_id}")
    
    try:
        movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            logger.warning(f"Movie not found: {movie_id}")
            raise HTTPException(status_code=404, detail="Movie not found")
        
        movie_dict = {k: v for k, v in movie.items() if k != "_id"}
        movie_dict["id"] = str(movie["_id"])
        
        logger.info(f"Found: {movie['title']}")
        return movie_dict
    except Exception as e:
        logger.error(f"Error getting movie {movie_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching movie: {str(e)}")

@app.post("/register/", response_model=User)
async def register_user(
    username: str,
    password: str,
    email: EmailStr,
    admin: User = Depends(get_admin_user)
):
    """Register user (admin)"""
    logger.info(f"Register: {username}, email: {email} by {admin.username}")
    
    existing_user = await db.users.find_one({"$or": [{"username": username}, {"email": email}]})
    if existing_user:
        logger.warning(f"Register fail: {username}, {email}")
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    hashed_password = get_password_hash(password)
    user_data = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "role": "user",
        "disabled": False
    }
    
    try:
        result = await db.users.insert_one(user_data)
        logger.info(f"User added: {username} with ID {result.inserted_id}")
        
        user_data_out = {k: v for k, v in user_data.items() if k != "hashed_password"}
        return user_data_out
    except Exception as e:
        logger.error(f"Register error {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

# Root route
@app.get("/")
async def root():
    """API info"""
    logger.info("Status check")
    return {
        "message": "API is running! Connect to /movies/ to see data.",
        "search_info": "Search: GET /movies/?search=your_search_term",
        "endpoints": {
            "all_movies": "/movies/",
            "search_movies": "/movies/?search=your_search_term",
            "movie_by_id": "/movies/{movie_id}"
        },
        "version": "1.0.0",
        "status": "online"
    }
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Server starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
