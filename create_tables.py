#!/usr/bin/env python3
"""
Script to create database tables for LinkedIn Automation MVP
"""

import asyncio
import os
from pathlib import Path
from sqlalchemy import text

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Loaded environment variables from .env file")
    else:
        print("⚠️  No .env file found, using system environment variables")

# Load environment variables first
load_env_file()
from app.database.connection import init_database, db_manager
from app.models.user import User
from app.models.content import ContentSource, ContentItem, PostDraft
from app.models.engagement import EngagementOpportunity

async def create_tables():
    """Create all database tables."""
    print("🔧 Creating database tables...")
    
    # Show which database URL we're using
    database_url = os.getenv("DATABASE_URL", "Not set")
    print(f"📊 Using DATABASE_URL: {database_url}")
    
    # Initialize database connection
    await init_database()
    
    # Create all tables using SQLAlchemy metadata
    async with db_manager.engine.begin() as conn:
        # Import all models to ensure they're registered
        from app.database.connection import Base
        
        print("📋 Creating tables for models:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ All tables created successfully!")
    
    # Test the connection by creating a simple query
    async with db_manager.get_session_directly() as session:
        # Test that we can query the users table
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"✅ Users table verified (current count: {count})")
    
    print("🎉 Database setup complete!")

async def main():
    """Main function."""
    try:
        await create_tables()
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Close database connections
        from app.database.connection import close_database
        await close_database()
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)