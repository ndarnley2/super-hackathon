from flask import Flask, request, jsonify
from flask_smorest import Api, Blueprint, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy import func, extract, desc
from sqlalchemy.sql import text
from datetime import datetime, timedelta
import os
import logging
import numpy as np
from collections import defaultdict
import redis

# Local imports
from models import Commit, CacheStatus, CommitWordFrequency
from github_client import GitHubAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure the app
app.config["API_TITLE"] = "GitHub Analytics API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.2"

# Database configuration
# Always use localhost since API runs directly on the host
DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/postgres")
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Redis configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Initialize extensions
db = SQLAlchemy(app)
api = Api(app)

# Initialize GitHub client
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
print(f"GITHUB_TOKEN is {'set' if GITHUB_TOKEN else 'NOT set'}")
print(f"DB_URL = {DB_URL}")
print(f"REDIS_URL = {REDIS_URL}")

try:
    print("Initializing GitHub client...")
    github_client = GitHubAPIClient(token=GITHUB_TOKEN, redis_url=REDIS_URL, db_url=DB_URL)
    print("GitHub client initialized successfully")
except Exception as e:
    print(f"Error initializing GitHub client: {e}")
    # Create a dummy client for testing - we'll only support the health endpoint
    github_client = None

# Default repository (can be overridden via environment variable)
DEFAULT_REPO_OWNER = os.environ.get("DEFAULT_REPO_OWNER", "OpenRA")
DEFAULT_REPO_NAME = os.environ.get("DEFAULT_REPO_NAME", "OpenRA")

# Define Schemas for request validation
class DateRangeSchema(Schema):
    start_date = fields.Date(required=False, 
                            missing=lambda: datetime.utcnow() - timedelta(days=365))
    end_date = fields.Date(required=False,
                          missing=lambda: datetime.utcnow() - timedelta(days=1))


class AuthorsRequestSchema(DateRangeSchema):
    pass


class DeviationRequestSchema(DateRangeSchema):
    pass


class DayOfWeekRequestSchema(DateRangeSchema):
    metric_type = fields.Str(required=True, 
                            validate=validate.OneOf(['commits', 'additions', 'deletions', 'total_changes']))
    author = fields.Str(required=False, allow_none=True)


class WordFrequencyRequestSchema(DateRangeSchema):
    pass


class FetchDataRequestSchema(DateRangeSchema):
    repo_owner = fields.Str(required=False, missing=DEFAULT_REPO_OWNER)
    repo_name = fields.Str(required=False, missing=DEFAULT_REPO_NAME)
    use_cache = fields.Bool(required=False, missing=True)


# Create Blueprint
blp = Blueprint(
    "analytics", 
    "analytics", 
    url_prefix="/api/v1",
    description="GitHub commit analytics API"
)

@blp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "message": "API is running"}


# Endpoint 1: Get unique commit authors
@blp.route("/authors", methods=["GET"])
@blp.arguments(AuthorsRequestSchema, location="query")
def get_authors(args):
    """
    Get a list of unique commit authors within the date range
    """
    start_date = args.get("start_date")
    end_date = args.get("end_date")
    
    try:
        # Query for unique authors
        authors = db.session.query(Commit.author_name).filter(
            Commit.author_date >= start_date,
            Commit.author_date <= end_date
        ).distinct().all()
        
        # Extract author names from result tuples
        author_list = [author[0] for author in authors]
        
        return {"authors": author_list, "count": len(author_list)}
    
    except Exception as e:
        logger.error(f"Error getting authors: {e}")
        abort(500, message=str(e))

# Endpoint 2: Get commits with significant deviations
@blp.route("/deviations", methods=["GET"])
@blp.arguments(DeviationRequestSchema, location="query")
def get_deviations(args):
    """
    Get commits with significant deviations (z-score > 2)
    """
    start_date = args.get("start_date")
    end_date = args.get("end_date")
    
    try:
        # Query for commits with z-score > 2
        significant_commits = db.session.query(
            Commit.sha,
            Commit.message_title,
            Commit.author_name,
            Commit.author_date,
            Commit.additions,
            Commit.deletions,
            Commit.total_changes,
            Commit.z_score
        ).filter(
            Commit.author_date >= start_date,
            Commit.author_date <= end_date,
            Commit.z_score > 2  # Significant deviation threshold
        ).order_by(desc(Commit.z_score)).all()
        
        # Format results
        result = []
        for commit in significant_commits:
            result.append({
                "sha": commit.sha,
                "title": commit.message_title,
                "author": commit.author_name,
                "date": commit.author_date.isoformat(),
                "additions": commit.additions,
                "deletions": commit.deletions,
                "total_changes": commit.total_changes,
                "z_score": round(commit.z_score, 2)
            })
        
        return {"commits": result, "count": len(result)}
    
    except Exception as e:
        logger.error(f"Error getting deviations: {e}")
        abort(500, message=str(e))

# Endpoint 3: Get day of week activity
@blp.route("/day-of-week", methods=["GET"])
@blp.arguments(DayOfWeekRequestSchema, location="query")
def get_day_of_week_activity(args):
    """
    Get activity by day of week
    """
    start_date = args.get("start_date")
    end_date = args.get("end_date")
    metric_type = args.get("metric_type")
    author = args.get("author")
    
    try:
        # Build the base query
        query = db.session.query(
            extract('dow', Commit.author_date).label('day_of_week'),
        )
        
        # Add the appropriate column based on metric_type
        if metric_type == 'commits':
            query = query.add_columns(func.count(Commit.id).label('value'))
        elif metric_type == 'additions':
            query = query.add_columns(func.sum(Commit.additions).label('value'))
        elif metric_type == 'deletions':
            query = query.add_columns(func.sum(Commit.deletions).label('value'))
        elif metric_type == 'total_changes':
            query = query.add_columns(func.sum(Commit.total_changes).label('value'))
        else:
            abort(400, message=f"Invalid metric_type: {metric_type}")
        
        # Apply filters
        query = query.filter(
            Commit.author_date >= start_date,
            Commit.author_date <= end_date
        )
        
        # Apply author filter if provided
        if author:
            query = query.filter(Commit.author_name == author)
        
        # Group by day of week and execute
        results = query.group_by('day_of_week').all()
        
        # Convert to shortened day names and fill in missing days
        # Use shortened day names to match frontend expectations
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        day_activity = {day: 0 for day in day_names}
        
        for row in results:
            day_index = int(row.day_of_week)
            day_name = day_names[day_index]
            day_activity[day_name] = int(row.value) if row.value else 0
            
        # Add debug output
        logger.info(f"Day activity data: {day_activity}")
        
        return {
            "metric": metric_type,
            "author": author,
            "day_activity": day_activity
        }
    
    except Exception as e:
        logger.error(f"Error getting day of week activity: {e}")
        abort(500, message=str(e))

# Endpoint 4: Get word frequencies
@blp.route("/word-frequencies", methods=["GET"])
@blp.arguments(WordFrequencyRequestSchema, location="query")
def get_word_frequencies(args):
    """
    Get word frequencies from commit messages
    """
    start_date = args.get("start_date")
    end_date = args.get("end_date")
    
    try:
        # Check if we have pre-computed word frequencies
        word_freqs = db.session.query(
            CommitWordFrequency.word, 
            CommitWordFrequency.frequency
        ).filter(
            CommitWordFrequency.start_date <= start_date,
            CommitWordFrequency.end_date >= end_date
        ).order_by(CommitWordFrequency.frequency.desc()).limit(100).all()
        
        # If we have pre-computed data, return it
        if word_freqs:
            result = {word: freq for word, freq in word_freqs}
            return {"word_frequencies": result}
        
        # Otherwise, compute the word frequencies on the fly
        # This is a backup option - the GitHub client should pre-compute these
        owner = DEFAULT_REPO_OWNER
        repo = DEFAULT_REPO_NAME
        
        word_freqs = github_client.calculate_word_frequencies(
            owner=owner,
            repo=repo,
            start_date=start_date,
            end_date=end_date
        )
        
        return {"word_frequencies": word_freqs}
    
    except Exception as e:
        logger.error(f"Error getting word frequencies: {e}")
        abort(500, message=str(e))

# Fetch data from GitHub API endpoint
@blp.route("/fetch-data", methods=["POST"])
@blp.arguments(FetchDataRequestSchema)
def fetch_data(args):
    """
    Fetch commit data from GitHub API
    """
    # Parse date strings into datetime objects
    try:
        # If the dates come as strings (e.g. from JSON request), convert to datetime
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
        repo_owner = args.get("repo_owner", DEFAULT_REPO_OWNER)
        repo_name = args.get("repo_name", DEFAULT_REPO_NAME)
        use_cache = args.get("use_cache", True)
        
        logger.debug(f"Parsed dates: start={start_date}, end={end_date}")
    except Exception as e:
        logger.error(f"Error parsing dates: {e}")
        abort(400, message=f"Invalid date format: {str(e)}")
    
    try:
        # Check cache status
        session = db.session
        repository = f"{repo_owner}/{repo_name}"
        
        cache_status = None
        if use_cache:
            cache_status = session.query(CacheStatus).filter(
                CacheStatus.repository == repository,
                CacheStatus.start_date <= start_date,
                CacheStatus.end_date >= end_date,
                CacheStatus.completed == True
            ).first()
        
        if cache_status:
            return {
                "status": "success",
                "message": "Using cached data",
                "cache_used": True,
                "repository": repository,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        
        # Fetch data in a separate thread/process to avoid blocking
        # For simplicity, we'll do it synchronously here
        # In a production environment, consider using Celery or a similar task queue
        
        commits = github_client.fetch_commits(
            owner=repo_owner,
            repo=repo_name,
            start_date=start_date,
            end_date=end_date,
            use_cache=use_cache
        )
        
        # Calculate statistics
        stats = github_client.calculate_commit_statistics(
            owner=repo_owner,
            repo=repo_name,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate word frequencies
        github_client.calculate_word_frequencies(
            owner=repo_owner,
            repo=repo_name,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "status": "success",
            "message": "Data fetched successfully",
            "cache_used": False,
            "commit_count": len(commits),
            "statistics": stats,
            "repository": repository,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        abort(500, message=str(e))

# Register blueprint with the API
api.register_blueprint(blp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
