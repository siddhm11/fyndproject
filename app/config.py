import os 
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL","mongodb://localhost:27017")
SECRET_KEY = os.getenv("SECRET_KEY","")