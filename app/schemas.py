from pydantic import BaseModel # for data validation we use this 
#base model is its own model and we can create our own models by inheriting from it 


from typing import Optional

# optional is a type hint and no specific type so it can be none and all also 

class MovieBase(BaseModel):
    title: str
    description: str
    release_year : int 
    genre: str
    
#movie ase acts as a base model so other models can inherit from this 
# ensures movie related data follows a consistent struture
 
    
class MovieCreate(MovieBase):
    pass 

#used to create movies and it inherits moviebase's dataframe 


class MovieResponse(MovieBase):
    id: str
    #it is used to give responses and during that id is also given 
    
class UserCreate(BaseModel):
    username : str
    password : str
    email : str
    
    
class UserResponse(BaseModel):
    username : str
    role : str
    
    
    