# GitHub Commit Analytics

A full-stack application that fetches and analyzes GitHub commit data, providing visualizations and insights into coding patterns and repository activity.

## Overview

This application consists of:
- **Backend API**: A Flask-based API that interacts with GitHub's API to fetch commit data and provides analytics endpoints
- **Frontend**: A web interface for visualizing the analytics data

## Prerequisites

- **Docker & Docker Compose**: For running PostgreSQL and Redis services
- **Python 3.9+**: For running the backend API
- **GitHub Personal Access Token**: For authenticating with GitHub's API

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd super-hackathon
```

### 2. Create Environment File

Create a `.env` file in the project root with the following variables:

```
# GitHub Authentication
GITHUB_TOKEN=your_github_personal_access_token

# Database & Redis Configuration (these will be overridden by boot.sh)
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres
REDIS_URL=redis://localhost:6379/0

# Default Repository to Analyze
DEFAULT_REPO_OWNER=OpenRA
DEFAULT_REPO_NAME=OpenRA
```

### 3. Setup a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r backend/requirements.txt
pip install -r backend/tests/requirements.txt
```

### 5. Start PostgreSQL and Redis

```bash
docker-compose up -d
```

## Running the Application

### Running the Backend

Use the provided script to start the backend API:

```bash
./run_backend.sh
```

The API will be available at http://localhost:5050/api/v1

### Running the Frontend

Use the provided script to start the frontend development server:

```bash
./run_frontend.sh
```

The frontend will be available at http://localhost:5173

## Using the Application

1. Start both the backend and frontend servers.
2. Navigate to http://localhost:5173 in your browser.
3. Use the date range selector to specify a period for analysis.
4. Click the "Reload Data" button to fetch commit data from GitHub for the specified period.
5. Explore the different visualizations:
   - **Outliers Table**: Shows commits with unusual sizes (additions, deletions).
   - **Metrics Chart**: Visualizes commit activity by day of week.
   - **Word Cloud**: Displays frequently used words in commit messages.

### 6. Initialize the Database

Before running the application for the first time, initialize the database schema:

```bash
python init_db.py
```

This script creates the necessary tables in the PostgreSQL database.

## Running the Application

### Method 1: Using boot.sh (Recommended)

The `boot.sh` script automates the startup process:

```bash
./boot.sh
```

This script:
1. Loads environment variables from `.env`
2. Starts Docker containers for PostgreSQL and Redis if not already running
3. Installs Python dependencies in a virtual environment
4. Starts the backend API server

### Method 2: Using run_backend.sh

Alternatively, you can use the simplified script that just starts the backend:

```bash
./run_backend.sh
```

### Method 3: Manual Startup

You can also start each component manually:

1. **Start the database and Redis**:
   ```bash
   docker-compose up -d postgres redis
   ```

2. **Run the backend API**:
   ```bash
   cd backend
   python app.py
   ```

## API Endpoints

Once running, the API is available at: http://localhost:5050/api/v1

### Available Endpoints

- **Health Check**: `/health` - Simple endpoint to verify API is running
- **Author Analytics**: `/authors?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Get contribution data by author
- **Significant Deviations**: `/deviations?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Identify commits that deviate from normal patterns
- **Day of Week Activity**: `/day-of-week?metric_type=commits&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Analyze commit activity by day of week
- **Word Frequencies**: `/word-frequencies?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` - Analyze common terms in commit messages
- **Fetch Data**: `/fetch-data` (POST) - Fetch new data from GitHub API

## Troubleshooting

### Database Connection Issues

- The application uses the default `postgres` database instead of creating a custom database
- If you encounter database connection errors, run `init_db.py` to recreate the database schema

### Port Already in Use

If you get an "Address already in use" error:

```bash
lsof -i :5050 | grep LISTEN  # Find the process using port 5050
kill -9 <PID>                 # Kill the process
```

### GitHub API Rate Limiting

- Using a valid GitHub token increases your rate limit
- If you hit rate limits, the application will wait and retry

## Testing

The backend includes a comprehensive test suite organized by endpoint:

```bash
python -m pytest backend/tests/
```

Each endpoint has its own test file:
- `test_health.py` - Tests for the health endpoint
- `test_authors.py` - Tests for the authors analytics endpoint
- `test_deviations.py` - Tests for the significant deviations endpoint
- `test_day_of_week.py` - Tests for the day-of-week activity endpoint
- `test_word_frequencies.py` - Tests for the word frequencies endpoint
- `test_fetch_data.py` - Tests for the data fetching endpoint
- `test_utils.py` - Shared testing utilities
