#!/bin/bash

# Exit on error
set -e

# Define terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Personal Work OS Starter ===${NC}"

# Function to stop background processes on exit
cleanup() {
    echo -e "\n${BLUE}Stopping all services...${NC}"
    kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT

# 1. Start the Backend
echo -e "${GREEN}Starting FastAPI Backend on http://localhost:8000...${NC}"
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
cd ..

# 2. Start the Frontend
echo -e "${GREEN}Starting Vite Frontend on http://localhost:5173...${NC}"
cd frontend
npm run dev &
cd ..

# Keep script running
wait
