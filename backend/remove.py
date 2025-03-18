import asyncio
from main import db

async def clear_movies():
    await db.movies.delete_many({})
    print("Cleared existing movies.")

asyncio.run(clear_movies())
