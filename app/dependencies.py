# app/dependencies.py
from fastapi import Depends, HTTPException, status
from app.database import get_database
from app.security import get_current_user

async def get_current_admin(current_user=Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    return current_user