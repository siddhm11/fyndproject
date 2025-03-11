from typing import Optional 
#AGAIN FOR NONE

from pydantic import BaseModel
#this is for the movie data model that automatically valideates the input data

from bson import ObjectId
#this is to get the object id from the mongodb object and 
#we are using this to return or use object id 

class Movie(BaseModel):
    id: Optional[str]
    title:str
    description: str
    release_year:str
    genre: str
    
class Config:
    json_encoders = {ObjectId: StopIteration}


