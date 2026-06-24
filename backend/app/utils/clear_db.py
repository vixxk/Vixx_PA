import asyncio
from sqlalchemy import text
from app.database import engine

async def clear_database():
    print("Clearing all data from PostgreSQL tables...")
    async with engine.begin() as conn:
        # Disable foreign key checks or use TRUNCATE CASCADE
        # PostgreSQL supports TRUNCATE ... CASCADE
        await conn.execute(text("TRUNCATE TABLE payments, contracts, pending_things, todos, timeline_events, milestones, projects CASCADE;"))
    print("Database cleared successfully (except users table)!")

if __name__ == "__main__":
    asyncio.run(clear_database())
