#!/bin/bash

# PostgreSQL Cleanup and Manual Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Cleaning up PostgreSQL and starting manually...${NC}"

# Step 1: Stop any existing PostgreSQL processes
echo -e "${BLUE}Step 1: Stopping existing PostgreSQL processes...${NC}"
brew services stop postgresql@14 2>/dev/null || true
brew services stop postgresql 2>/dev/null || true
pkill -f postgres 2>/dev/null || true
sleep 2

# Step 2: Clean up launch agents
echo -e "${BLUE}Step 2: Cleaning up launch agents...${NC}"
rm -f ~/Library/LaunchAgents/homebrew.mxcl.postgresql*.plist 2>/dev/null || true
launchctl remove homebrew.mxcl.postgresql 2>/dev/null || true
launchctl remove homebrew.mxcl.postgresql@14 2>/dev/null || true

# Step 3: Find PostgreSQL installation
echo -e "${BLUE}Step 3: Finding PostgreSQL installation...${NC}"
POSTGRES_VERSIONS=($(ls /opt/homebrew/var/postgresql* 2>/dev/null || ls /usr/local/var/postgresql* 2>/dev/null || true))

if [ ${#POSTGRES_VERSIONS[@]} -eq 0 ]; then
    echo -e "${RED}❌ No PostgreSQL data directories found.${NC}"
    echo -e "${YELLOW}Reinstalling PostgreSQL...${NC}"
    brew uninstall postgresql --ignore-dependencies 2>/dev/null || true
    brew install postgresql@14
    brew link postgresql@14 --force
    DATA_DIR="/opt/homebrew/var/postgresql@14"
    if [ ! -d "$DATA_DIR" ]; then
        DATA_DIR="/usr/local/var/postgresql@14"
    fi
else
    DATA_DIR="${POSTGRES_VERSIONS[0]}"
    echo -e "${GREEN}✅ Found PostgreSQL data directory: $DATA_DIR${NC}"
fi

# Step 4: Initialize database if needed
echo -e "${BLUE}Step 4: Checking database initialization...${NC}"
if [ ! -f "$DATA_DIR/PG_VERSION" ]; then
    echo -e "${YELLOW}⚠️  Database not initialized. Initializing...${NC}"
    initdb "$DATA_DIR" --locale=en_US.UTF-8 --encoding=UTF8
fi

# Step 5: Start PostgreSQL manually
echo -e "${BLUE}Step 5: Starting PostgreSQL manually...${NC}"

# Find the postgres binary
POSTGRES_BIN=""
POSSIBLE_PATHS=(
    "/opt/homebrew/bin/postgres"
    "/usr/local/bin/postgres"
    "/opt/homebrew/Cellar/postgresql@14/*/bin/postgres"
    "/usr/local/Cellar/postgresql@14/*/bin/postgres"
)

for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -x "$path" ] || ls $path >/dev/null 2>&1; then
        POSTGRES_BIN=$(ls $path 2>/dev/null | head -1)
        break
    fi
done

if [ -z "$POSTGRES_BIN" ]; then
    echo -e "${RED}❌ PostgreSQL binary not found.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found PostgreSQL binary: $POSTGRES_BIN${NC}"

# Create log directory
mkdir -p logs

# Start PostgreSQL manually in background
echo "Starting PostgreSQL server..."
nohup "$POSTGRES_BIN" -D "$DATA_DIR" > logs/postgresql.log 2>&1 &
POSTGRES_PID=$!
echo $POSTGRES_PID > logs/postgresql.pid

# Wait for PostgreSQL to start
echo "Waiting for PostgreSQL to start..."
sleep 5

# Test if PostgreSQL is running
if ps -p $POSTGRES_PID > /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL started successfully (PID: $POSTGRES_PID)${NC}"
else
    echo -e "${RED}❌ PostgreSQL failed to start. Check logs/postgresql.log${NC}"
    cat logs/postgresql.log
    exit 1
fi

# Step 6: Test connection and setup database
echo -e "${BLUE}Step 6: Testing connection and setting up database...${NC}"

# Wait a bit more for PostgreSQL to be ready
sleep 3

# Test connection with different users
TEST_USERS=("$(whoami)" "postgres")
WORKING_USER=""

for user in "${TEST_USERS[@]}"; do
    echo "Testing connection with user: $user"
    if psql -d postgres -U "$user" -c "SELECT 1;" >/dev/null 2>&1; then
        WORKING_USER="$user"
        echo -e "${GREEN}✅ Connection successful with user: $user${NC}"
        break
    fi
done

if [ -z "$WORKING_USER" ]; then
    echo -e "${YELLOW}⚠️  Creating database user...${NC}"
    createuser -s "$(whoami)" 2>/dev/null || true
    WORKING_USER="$(whoami)"
fi

# Create database
DB_NAME="linkedin_automation"
if ! psql -d postgres -U "$WORKING_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo "Creating database: $DB_NAME"
    createdb -U "$WORKING_USER" "$DB_NAME"
    echo -e "${GREEN}✅ Database '$DB_NAME' created${NC}"
else
    echo -e "${GREEN}✅ Database '$DB_NAME' already exists${NC}"
fi

# Step 7: Create .env file
echo -e "${BLUE}Step 7: Creating .env file...${NC}"

# Backup existing .env
if [ -f ".env" ]; then
    cp .env .env.backup
    echo -e "${YELLOW}⚠️  Backed up existing .env to .env.backup${NC}"
fi

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "your-secret-key-$(date +%s)")

cat > .env << EOL
# Database Configuration - FIXED FOR MANUAL POSTGRESQL
DATABASE_URL=postgresql+asyncpg://${WORKING_USER}@localhost:5432/${DB_NAME}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration  
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application Settings
DEBUG=true
CORS_ORIGINS=["http://localhost:3000", "http://localhost"]

# AI Services (Optional)
# OPENAI_API_KEY=your-openai-api-key
# ANTHROPIC_API_KEY=your-anthropic-api-key

# Content Processing
DEFAULT_CHECK_FREQUENCY_HOURS=24
MAX_CONTENT_AGE_DAYS=30
CONTENT_BATCH_SIZE=50
EOL

echo -e "${GREEN}✅ .env file created${NC}"

# Step 8: Final test
echo -e "${BLUE}Step 8: Final connection test...${NC}"
if psql -d "$DB_NAME" -U "$WORKING_USER" -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "${GREEN}🎉 PostgreSQL setup completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Your configuration:${NC}"
    echo "Database User: $WORKING_USER"
    echo "Database Name: $DB_NAME"
    echo "PostgreSQL PID: $POSTGRES_PID (running manually)"
    echo "Log file: logs/postgresql.log"
    echo ""
    echo -e "${GREEN}You can now run: honcho start${NC}"
    echo ""
    echo -e "${YELLOW}Note: PostgreSQL is running manually. To stop it later, run:${NC}"
    echo "kill $POSTGRES_PID"
    echo "or use the stop script: ./stop_postgres.sh"
else
    echo -e "${RED}❌ Final connection test failed${NC}"
    echo "Check logs/postgresql.log for errors"
    exit 1
fi