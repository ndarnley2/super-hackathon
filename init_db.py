#!/usr/bin/env python3
"""
Database initialization script for GitHub Analytics
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in project root
project_root = Path(__file__).parent
dotenv_path = project_root / '.env'
if dotenv_path.exists():
    print(f"Loading environment variables from {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

# Override database URL to use postgres database instead of github_analytics
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/postgres"
print(f"Using database URL: {os.environ['DATABASE_URL']}")

# Import after environment variables are loaded
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Import models from the correct path
sys.path.append(str(project_root))  # Add project root to path

# Direct import to avoid import errors
from backend.models import Base, Commit, CacheStatus, CommitWordFrequency

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('init_db')

def init_database():
    """Initialize the database with required schema"""
    try:
        # Get database URL from environment
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            sys.exit(1)
            
        print(f"Connecting to database: {db_url}")
        
        # Create engine and initialize database
        engine = create_engine(db_url, echo=True)  # Enable SQL logging
        
        # Check existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        print(f"Existing tables before: {existing_tables}")
        
        # Drop all existing tables if they exist
        print("Dropping existing tables...")
        Base.metadata.drop_all(engine)
        
        # Create all tables
        print("Creating tables...")
        Base.metadata.create_all(engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        tables_after = inspector.get_table_names()
        print(f"Tables after creation: {tables_after}")
        
        # Display the expected tables from our models
        expected_tables = [Commit.__tablename__, CacheStatus.__tablename__, CommitWordFrequency.__tablename__]
        print(f"Expected tables: {expected_tables}")
        
        # Create session for any additional initialization if needed
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to initialize database: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
