# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB settings
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "movie_db")

# Auth settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

