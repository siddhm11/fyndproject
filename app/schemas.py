from pydantic import BaseModel,EmailStr,Field # for data validation we use this 
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
    
class MovieUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    release_year: Optional[int] = None
    genre: Optional[str] = None
    
    
class UserBase(BaseModel):
    username:str
    email: EmailStr
    
    
class UserCreate(UserBase):
    password : str
    
    
class UserResponse(BaseModel):
    role : str
        
class Token(BaseModel):
    access_token : str
    token_type: str
    
class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None