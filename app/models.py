


#this is for the mongodb models 

from typing import Optional 
#AGAIN FOR NONE

from pydantic import BaseModel
#this is for the movie data model that automatically valideates the input data

from bson import ObjectId
#this is to get the object id from the mongodb object and 
#we are using this to return or use object id 

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(ObjectId(v))

class Movie(BaseModel):
    id: Optional[str]
    title:str
    description: str
    release_year:str
    genre: str
    
    class Config:
        json_encoders = {ObjectId: str}


