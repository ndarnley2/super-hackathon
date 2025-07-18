-- PostgreSQL database schema for GitHub commit analytics application

-- Create the commits table
CREATE TABLE IF NOT EXISTS commits (
    id SERIAL PRIMARY KEY,
    sha VARCHAR(40) UNIQUE NOT NULL,
    author_name VARCHAR(255) NOT NULL,
    author_email VARCHAR(255),
    author_date TIMESTAMP NOT NULL,
    message_title TEXT NOT NULL,
    message_body TEXT,
    additions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    total_changes INTEGER DEFAULT 0,
    repository VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    z_score FLOAT
);

-- Create index on author_name for faster queries on author-specific data
CREATE INDEX IF NOT EXISTS idx_commits_author_name ON commits(author_name);

-- Create index on author_date for date range queries
CREATE INDEX IF NOT EXISTS idx_commits_author_date ON commits(author_date);

-- Create index on repository to filter by repo
CREATE INDEX IF NOT EXISTS idx_commits_repository ON commits(repository);

-- Create the cache_status table to track data fetch progress
CREATE TABLE IF NOT EXISTS cache_status (
    id SERIAL PRIMARY KEY,
    repository VARCHAR(255) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    last_cursor VARCHAR(255),
    completed BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (repository, start_date, end_date)
);

-- Create the commit word frequencies table for word cloud data
CREATE TABLE IF NOT EXISTS commit_word_frequencies (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    frequency INTEGER DEFAULT 0,
    repository VARCHAR(255) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    UNIQUE (word, repository, start_date, end_date)
);

-- Create index on word frequency for efficient retrieval
CREATE INDEX IF NOT EXISTS idx_word_frequency ON commit_word_frequencies(frequency DESC);

-- Ensure we're capturing stats for our DB
COMMENT ON TABLE commits IS 'Table storing GitHub commit data for analytics';
COMMENT ON TABLE cache_status IS 'Tracks progress of GitHub API data fetches for resumable operations';
COMMENT ON TABLE commit_word_frequencies IS 'Pre-computed word frequencies for commit messages';
