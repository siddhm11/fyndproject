import json
import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from passlib.context import CryptContext

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "movie_db"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def import_movies():
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Read the JSON file
    with open('app/imdb.json', 'r') as file:
        movies_data = json.load(file)
    
    # Transform data to match your schema
    movies_to_insert = []
    for movie in movies_data:
        # Convert genre list to string
        genre_str = ", ".join(genre.strip() for genre in movie["genre"])
        
        # Create a movie document
        movie_doc = {
            "title": movie["name"],
            "description": f"A {genre_str} film directed by {movie['director']}",
            "release_year": 2000,  # Default to 2000 since your data doesn't have years
            "genre": genre_str,
            "director": movie["director"],
            "imdb_score": movie["imdb_score"]
        }
        movies_to_insert.append(movie_doc)
    
    # Delete existing movies (optional)
    await db.movies.delete_many({})
    
    # Insert movies
    if movies_to_insert:
        result = await db.movies.insert_many(movies_to_insert)
        print(f"Inserted {len(result.inserted_ids)} movies into the database.")
    
    # Create an admin user
    admin_exists = await db.users.find_one({"username": "admin"})
    if not admin_exists:
        admin_user = {
            "username": "admin",
            "email": "admin@example.com",
            "password": get_password_hash("admin123"),
            "role": "admin"
        }
        await db.users.insert_one(admin_user)
        print("Created admin user (username: admin, password: admin123)")

# Run the import function
if __name__ == "__main__":
    asyncio.run(import_movies())