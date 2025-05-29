#!/bin/bash

# PostgreSQL Stop Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping PostgreSQL...${NC}"

# Stop PostgreSQL using PID file
if [ -f "logs/postgresql.pid" ]; then
    PID=$(cat logs/postgresql.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping PostgreSQL (PID: $PID)..."
        kill $PID
        
        # Wait for process to stop
        count=0
        while ps -p $PID > /dev/null 2>&1 && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force killing PostgreSQL..."
            kill -9 $PID
        fi
        
        echo -e "${GREEN}✅ PostgreSQL stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  PostgreSQL was not running${NC}"
    fi
    rm -f logs/postgresql.pid
else
    echo -e "${YELLOW}⚠️  No PID file found, trying to kill any postgres processes...${NC}"
    pkill -f postgres && echo -e "${GREEN}✅ Killed postgres processes${NC}" || echo -e "${YELLOW}⚠️  No postgres processes found${NC}"
fi

echo -e "${GREEN}🎉 PostgreSQL shutdown complete${NC}"