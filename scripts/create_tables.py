# scripts/create_tables.py
#
# Simple database table creation script for development.
#
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Update sys.path to find buro module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def create_tables():
    """Create all database tables asynchronously."""
    from sqlalchemy import text
    from buro.core.database import engine
    from buro.models import Base

    print("🔧 Creating database tables...")

    try:
        # Create tables using SQLAlchemy metadata
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(create_tables())