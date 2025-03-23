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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("movie-api")

# Environment and configuration setup
port = int(os.getenv("PORT", 8000))  # Default to 8000 if PORT is not set
logger.info(f"Configured to run on port {port}")

# Security setup
# --------------
# We use bcrypt for password hashing, JWT for tokens, and OAuth2 for authentication flow
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "5ba6d2ba997729a5a8ed909ffd2d483d395401ceacb43dff82272c73cb010958"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logger.info("Security components initialized")

# FastAPI app setup
app = FastAPI(
    title="Movie Database API",
    description="An API for searching and managing movie information with user authentication",
    version="1.0.0",
)
from mangum import Mangum
handler = Mangum(app, lifespan="off")  # AWS Lambda handler

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)
logger.info("CORS middleware configured")

# MongoDB connection setup
MONGODB_URI = "mongodb+srv://admin:test1234%21@clusterfynd.bng6e.mongodb.net/?retryWrites=true&w=majority&appName=clusterfynd"
DB_NAME = "movie_db"

logger.info(f"Connecting to MongoDB database: {DB_NAME}")
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]
logger.info("MongoDB connection initialized")

# Data Models
# -----------
class User(BaseModel):
    """User data model containing basic user information"""
    username: str
    email: EmailStr
    disabled: bool = False
    role: str = "user"

class UserInDB(User):
    """Extended user model that includes password hash (only used internally)"""
    hashed_password: str

class Movie(BaseModel):
    """Movie data model with essential movie information"""
    title: str
    year: int
    genre: str
    director: str
    cast: List[str]
    rating: float
    description: Optional[str] = None

class MovieInDB(Movie):
    """Extended movie model that includes the database ID"""
    id: str

# Database Initialization
# ----------------------
@app.on_event("startup")
async def create_indexes():
    """Create text indexes on startup to enable efficient text search"""
    logger.info("Creating text indexes for movie search functionality")
    await db.movies.create_index([("title", TEXT), ("genre", TEXT), ("director", TEXT)])
    logger.info("Database indexes created successfully")

# Authentication Functions
# -----------------------
def verify_password(plain_password, hashed_password):
    """Verify a password against a hash using the configured password context"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a password hash for secure storage"""
    return pwd_context.hash(password)

def create_access_token(data: dict):
    """Create a JWT access token with expiration time"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.debug(f"Created access token for user: {data.get('sub')}")
    return token

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get the current authenticated user from a JWT token"""
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            logger.warning("Invalid token: missing subject claim")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    # Fetch the user from the database
    user = await db.users.find_one({"username": username})
    if not user:
        logger.warning(f"User not found in database: {username}")
        raise HTTPException(status_code=401, detail="User not found")
    
    logger.debug(f"Authenticated user: {username}")
    return UserInDB(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    """Dependency to verify the current user has admin role"""
    if current_user.role != "admin":
        logger.warning(f"Access denied: User {current_user.username} attempted admin action")
        raise HTTPException(status_code=403, detail="Admin access required")
    logger.debug(f"Admin access granted to: {current_user.username}")
    return current_user

# API Routes
# ----------

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and provide access token"""
    logger.info(f"Login attempt: {form_data.username}")
    
    # Find the user in the database
    user_doc = await db.users.find_one({"username": form_data.username})
    if not user_doc:
        logger.warning(f"Login failed: User not found - {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Verify password
    if not verify_password(form_data.password, user_doc["hashed_password"]):
        logger.warning(f"Login failed: Incorrect password for {form_data.username}")
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": user_doc["username"]}
    )
    
    logger.info(f"Login successful: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get information about the currently authenticated user"""
    logger.info(f"User info requested: {current_user.username}")
    return current_user

@app.post("/movies/", response_model=MovieInDB)
async def create_movie(movie: Movie, admin: User = Depends(get_admin_user)):
    """Create a new movie entry (admin only)"""
    logger.info(f"Adding new movie: {movie.title} ({movie.year}) by admin: {admin.username}")
    
    movie_dict = movie.dict()
    result = await db.movies.insert_one(movie_dict)
    logger.info(f"Movie created with ID: {result.inserted_id}")
    
    return {**movie_dict, "id": str(result.inserted_id)}

@app.get("/movies/", response_model=List[MovieInDB])
async def get_movies(search: Optional[str] = None):
    """Get a list of movies, optionally filtered by search term"""
    if search:
        logger.info(f"Searching movies with term: '{search}'")
        query = {"$text": {"$search": search}}
        movies = await db.movies.find(query).to_list(100)
        logger.info(f"Found {len(movies)} movies matching search term")
    else:
        logger.info("Fetching all movies (limited to 100)")
        movies = await db.movies.find().to_list(100)
        logger.info(f"Retrieved {len(movies)} movies total")
    
    # Transform the database objects to API response format
    movie_list = []
    for m in movies:
        movie_dict = {k: v for k, v in m.items() if k != "_id"}
        movie_dict["id"] = str(m["_id"])
        movie_list.append(movie_dict)
    
    return movie_list

@app.put("/movies/{movie_id}", response_model=MovieInDB)
async def update_movie(movie_id: str, movie: Movie, admin: User = Depends(get_admin_user)):
    """Update an existing movie by ID (admin only)"""
    logger.info(f"Updating movie {movie_id}: {movie.title} by admin: {admin.username}")
    
    try:
        movie_dict = movie.dict()
        result = await db.movies.update_one({"_id": ObjectId(movie_id)}, {"$set": movie_dict})
        
        if result.matched_count == 0:
            logger.warning(f"Movie not found for update: {movie_id}")
            raise HTTPException(status_code=404, detail="Movie not found")
            
        logger.info(f"Movie updated successfully: {movie_id}")
        
        # Get the updated movie
        updated_movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        if not updated_movie:
            logger.error(f"Updated movie not found after update: {movie_id}")
            raise HTTPException(status_code=404, detail="Movie not found after update")
        
        # Format for response
        movie_dict = {k: v for k, v in updated_movie.items() if k != "_id"}
        movie_dict["id"] = str(updated_movie["_id"])
        
        return movie_dict
    except Exception as e:
        logger.error(f"Error updating movie {movie_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating movie: {str(e)}")

@app.get("/movies/{movie_id}", response_model=MovieInDB)
async def get_movie(movie_id: str):
    """Get a specific movie by ID"""
    logger.info(f"Fetching movie by ID: {movie_id}")
    
    try:
        movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            logger.warning(f"Movie not found: {movie_id}")
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Format for response
        movie_dict = {k: v for k, v in movie.items() if k != "_id"}
        movie_dict["id"] = str(movie["_id"])
        
        logger.info(f"Retrieved movie: {movie['title']}")
        return movie_dict
    except Exception as e:
        logger.error(f"Error fetching movie {movie_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching movie: {str(e)}")

@app.post("/register/", response_model=User)
async def register_user(
    username: str,
    password: str,
    email: EmailStr,
    admin: User = Depends(get_admin_user)
):
    """Register a new user (admin only)"""
    logger.info(f"Registering new user: {username}, email: {email} by admin: {admin.username}")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"$or": [{"username": username}, {"email": email}]})
    if existing_user:
        logger.warning(f"Registration failed: Username or email already exists - {username}, {email}")
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Create new user
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
        logger.info(f"User registered successfully: {username} with ID {result.inserted_id}")
        
        # Return user data without password
        user_data_out = {k: v for k, v in user_data.items() if k != "hashed_password"}
        return user_data_out
    except Exception as e:
        logger.error(f"Error registering user {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

# Root route for testing connection
@app.get("/")
async def root():
    """Root endpoint for API status check"""
    logger.info("API status check")
    return {
        "message": "API is running! Connect to /movies/ to see data.",
        "search_info": "You can search for movies using GET /movies/?search=your_search_term",
        "Documentation" : "https://github.com/siddhm11/fyndproject/blob/main/README.md#movie-database-api",
        "endpoints": {
            "all_movies": "/movies/",
            "search_movies": "/movies/?search=your_search_term",
            "movie_by_id": "/movies/{movie_id}"
            
        },
        "version": "1.0.0",
        "status": "online"
    }
if __name__ == "__main__":
    # This block will execute when running directly with Python
    # It won't run when deployed as a serverless function
    import uvicorn
    logger.info(f"Starting API server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
