#!/bin/bash
# boot.sh - Script to launch the backend API and frontend (later)

# Configuration
BACKEND_DIR="./backend"
VENV_DIR="./venv"
DATA_DIR="./data"

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}GitHub Commit Analytics - Boot Script${NC}"
echo -e "${BLUE}========================================${NC}"

# Check if Docker is running
echo -e "\n${YELLOW}Checking if Docker is running...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker Desktop and try again.${NC}"
    exit 1
fi

# Check if containers are running
echo -e "\n${YELLOW}Checking if required services are running...${NC}"
docker-compose ps postgres redis > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Starting PostgreSQL and Redis services...${NC}"
    docker-compose up -d postgres redis
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 5
else
    echo -e "${GREEN}Services are already running.${NC}"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "\n${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv $VENV_DIR
    echo -e "${GREEN}Virtual environment created at $VENV_DIR${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

# Install dependencies
echo -e "\n${YELLOW}Installing backend dependencies...${NC}"
pip install -r $BACKEND_DIR/requirements.txt

# Set environment variables if .env file exists
if [ -f ".env" ]; then
    echo -e "\n${YELLOW}Loading environment variables from .env file...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "\n${RED}Warning: .env file not found. Using default values.${NC}"
    # Set default environment variables
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/github_analytics"
    export REDIS_URL="redis://localhost:6379/0"
    export DEFAULT_REPO_OWNER="OpenRA"
    export DEFAULT_REPO_NAME="OpenRA"
fi

# Create data directory if it doesn't exist
if [ ! -d "$DATA_DIR" ]; then
    echo -e "\n${YELLOW}Creating data directory...${NC}"
    mkdir -p $DATA_DIR
fi

# Start backend server
echo -e "\n${YELLOW}Starting backend server...${NC}"
cd $BACKEND_DIR
python app.py &
BACKEND_PID=$!
cd ..

echo -e "\n${GREEN}Backend server started with PID $BACKEND_PID${NC}"
echo -e "${GREEN}API URL: http://localhost:5000/api/v1${NC}"

# Function to handle script termination
function cleanup {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    echo -e "${GREEN}Goodbye!${NC}"
}

# Register the cleanup function for when the script exits
trap cleanup EXIT

# Keep the script running until user interrupts
echo -e "\n${BLUE}Press Ctrl+C to stop the servers${NC}"
wait $BACKEND_PID
