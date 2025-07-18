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

-- Create the cache_status table
CREATE TABLE IF NOT EXISTS cache_status (
    id SERIAL PRIMARY KEY,
    repository VARCHAR(255) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    last_cursor VARCHAR(255),
    completed BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the commit_word_frequencies table
CREATE TABLE IF NOT EXISTS commit_word_frequencies (
    id SERIAL PRIMARY KEY,
    word VARCHAR(100) NOT NULL,
    frequency INTEGER DEFAULT 0,
    repository VARCHAR(255) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL
);

-- Add some indexes to improve query performance
CREATE INDEX IF NOT EXISTS idx_commits_author_date ON commits(author_date);
CREATE INDEX IF NOT EXISTS idx_commits_author_name ON commits(author_name);
CREATE INDEX IF NOT EXISTS idx_commits_repository ON commits(repository);
CREATE INDEX IF NOT EXISTS idx_cache_status_repository ON cache_status(repository);
CREATE INDEX IF NOT EXISTS idx_word_frequencies_word ON commit_word_frequencies(word);
