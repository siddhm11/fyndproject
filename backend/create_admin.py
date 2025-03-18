import asyncio
from main import pwd_context, db

async def create_admin():
    # Delete existing admin first
    await db.users.delete_one({"username": "admin"})
    
    admin_data = {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin",
        "disabled": False
    }  # Added closing brace
    
    await db.users.insert_one(admin_data)
    print("Admin user created successfully!")

if __name__ == "__main__":
    asyncio.run(create_admin())
