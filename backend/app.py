#!/usr/bin/env python3
"""
Main entry point for the GitHub Analytics backend application
"""
from flask_migrate import Migrate
from api import app, db
from models import Base, Commit, CacheStatus, CommitWordFrequency
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Create tables if they don't exist
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
