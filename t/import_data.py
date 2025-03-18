import asyncio
import json
from main import db

async def import_movies():
    with open('data/imdb.json', encoding='utf-8') as f:
        movies = json.load(f)

    formatted_movies = []
    for movie in movies:
        formatted_movie = {
            "title": movie.get("name", "Unknown Title"),
            "year": 2000,  # Default year (set manually or parse if available)
            "genre": ", ".join(movie.get("genre", [])),  # Convert list to string
            "director": movie.get("director", "Unknown Director"),
            "cast": [],  # Empty list; fill manually later if needed
            "rating": float(movie.get("imdb_score", 0.0)),
            "description": "",  # Optional, fill later if needed
        }
        formatted_movies.append(formatted_movie)

    result = await db.movies.insert_many(formatted_movies)
    print(f"Inserted {len(result.inserted_ids)} movies successfully.")

if __name__ == "__main__":
    asyncio.run(import_movies())
