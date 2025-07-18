#!/bin/bash

# Frontend startup script for GitHub analytics project

# Navigate to the frontend directory
cd "$(dirname "$0")/frontend"

echo "Starting the frontend application..."

# Check if package-lock.json exists - if not, run npm install
if [ ! -f "node_modules/.package-lock.json" ]; then
  echo "Installing dependencies..."
  npm install
fi

# Start the development server
echo "Starting development server..."
npm run dev

echo "Frontend server stopped."
