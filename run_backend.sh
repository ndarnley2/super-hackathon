#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting backend with explicit environment variables...${NC}"

# Load GitHub token from .env if it exists
if [ -f ".env" ]; then
    source .env
    echo -e "${GREEN}Loaded environment from .env file${NC}"
else
    echo -e "${RED}Warning: No .env file found. Make sure GITHUB_TOKEN is set.${NC}"
fi

# Ensure GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}Error: GITHUB_TOKEN environment variable is not set${NC}"
    echo "Please set it in the .env file or export it manually"
    exit 1
fi

# Set explicit environment variables for local development
export DATABASE_URL="postgresql://postgres:postgres@localhost:5433/postgres"
export REDIS_URL="redis://localhost:6379/0"
export DEFAULT_REPO_OWNER="OpenRA"
export DEFAULT_REPO_NAME="OpenRA"

echo "GITHUB_TOKEN is set: ${GITHUB_TOKEN:0:5}..."
echo "DATABASE_URL: $DATABASE_URL"
echo "REDIS_URL: $REDIS_URL"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}Activated virtual environment${NC}"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}Activated virtual environment${NC}"
else
    echo -e "${YELLOW}No virtual environment found, using system Python${NC}"
fi

# Run the Flask app with the debug flag
cd backend
echo -e "${GREEN}Starting Flask app on port 5050...${NC}"
echo -e "${GREEN}API will be available at: http://localhost:5050/api/v1/health${NC}"
python app.py
