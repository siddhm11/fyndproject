from motor.motor_asyncio import AsyncIOMotorClient #enables async operations 
#for fast api and mongodb since both follow asyncthings 

from fastapi import FastAPI
import os
print("Connecting to MongoDB at:", os.getenv("MONGO_URL"))

#this is for mongodb connection 

MONGO_URL = os.getenv("MONGO_URL","mongodb://localhost:27017")

DB_NAME = "movie_db" # this is the data base in the mongodb instance 
# movies and citations and stuff like that is called as a collection over here 


client = AsyncIOMotorClient(MONGO_URL)

database = client[DB_NAME]

def get_database():
    return database
