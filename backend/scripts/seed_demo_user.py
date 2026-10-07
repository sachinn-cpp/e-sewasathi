import asyncio
from app.database.mongodb import connect_db, get_database, close_db
from app.database.collections import USERS
from app.utils.hashing import hash_password

async def seed():
    await connect_db()
    db = get_database()
    
    email = "citizen.demo@example.com"
    pwd = "Password123!"
    
    await db[USERS].update_one(
        {"email": email},
        {"$set": {
            "email": email,
            "name": "Aarav Sharma",
            "phone": "+9779812345678",
            "password_hash": hash_password(pwd),
            "role": "citizen",
            "preferred_language": "en",
            "is_active": True,
        }},
        upsert=True
    )
    print(f"Demo user ready: {email} / {pwd}")
    await close_db()

if __name__ == "__main__":
    asyncio.run(seed())
