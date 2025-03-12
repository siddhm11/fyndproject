from fastapi import APIRouter, HTTPException, Depends
from datetime import timedelta
from ..schemas import UserCreate, UserResponse
from app.database import get_database
from app.security import get_password_hash , verify_password , create_access_token
import logging 


router = APIRouter()
logging.basicConfig(level= logging.DEBUG)


@router.post("/register")
async def register(user:UserCreate , db = Depends(get_database)):
    try:
        existing_user = await db.users.find_one({"username":user.username})
        if existing_user:
            raise HTTPException(status_code = 400 , detail = "User already exists")
        
        hashed_password = get_password_hash(user.password)
        user_dict = user.model_dump()
        user_dict["password"] = hashed_password
        user_dict["role"] = "user"
        
        await db.users.insert_one(user_dict)
        return {"message":"user registered successfully"}
    
    except Exception as e :
        logging.error(f"error in register endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")    
    
@router.post("/login")
async def login(username:str , password: str,db = Depends(get_database)):
    user = await db.users.find_one({"username":username})
    if not user or not verify_password(password , user["password"]):
        raise HTTPException(status_code = 400 , detail= "Invalid Credentials")
    
    access_token = create_access_token(data={"sub":username , "role":user["role"]})
    
    return {"Access_token":access_token , "token_type":"bearer"}
    
    