from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Commit(Base):
    """
    Represents a commit from GitHub.
    Stores all relevant data about the commit.
    """
    __tablename__ = 'commits'

    id = Column(Integer, primary_key=True)
    sha = Column(String(40), unique=True, nullable=False)
    author_name = Column(String(255), nullable=False)
    author_email = Column(String(255), nullable=True)
    author_date = Column(DateTime, nullable=False)
    message_title = Column(Text, nullable=False)
    message_body = Column(Text, nullable=True)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    total_changes = Column(Integer, default=0)  # Calculated field (additions + deletions)
    repository = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Statistical data
    z_score = Column(Float, nullable=True)  # For endpoint 2 - significant deviations

    def __repr__(self):
        return f"<Commit sha={self.sha} author={self.author_name}>"


class CacheStatus(Base):
    """
    Tracks the status of GitHub API data fetches for caching purposes.
    Used to resume fetches in case of interruptions.
    """
    __tablename__ = 'cache_status'

    id = Column(Integer, primary_key=True)
    repository = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    last_cursor = Column(String(255), nullable=True)  # For pagination
    completed = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CacheStatus repo={self.repository} completed={self.completed}>"


class CommitWordFrequency(Base):
    """
    Stores word frequency data for commit messages.
    Pre-computed for faster retrieval.
    """
    __tablename__ = 'commit_word_frequencies'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False)
    frequency = Column(Integer, default=0)
    repository = Column(String(255), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    def __repr__(self):
        return f"<CommitWordFrequency word={self.word} frequency={self.frequency}>"
