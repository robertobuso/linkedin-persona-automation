#!/bin/bash

# PostgreSQL Setup Script for LinkedIn Automation MVP

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up PostgreSQL for LinkedIn Automation MVP...${NC}"

# Function to check if PostgreSQL is installed
check_postgresql() {
    if ! command -v psql >/dev/null 2>&1; then
        echo -e "${RED}❌ PostgreSQL is not installed.${NC}"
        echo -e "${YELLOW}Install with: brew install postgresql${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ PostgreSQL is installed${NC}"
}

# Function to start PostgreSQL if not running
start_postgresql() {
    if ! brew services list | grep -q "postgresql.*started"; then
        echo "Starting PostgreSQL..."
        brew services start postgresql
        sleep 3
    fi
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
}

# Function to test database connection and get the working username
test_connection() {
    local test_users=("$(whoami)" "postgres" "admin")
    local working_user=""
    
    echo -e "${BLUE}Testing database connections...${NC}"
    
    for user in "${test_users[@]}"; do
        echo "Testing connection with user: $user"
        if psql -d postgres -U "$user" -c "SELECT 1;" >/dev/null 2>&1; then
            working_user="$user"
            echo -e "${GREEN}✅ Connection successful with user: $user${NC}"
            break
        else
            echo -e "${YELLOW}⚠️  Connection failed with user: $user${NC}"
        fi
    done
    
    if [ -z "$working_user" ]; then
        echo -e "${RED}❌ Could not connect to PostgreSQL with any user.${NC}"
        echo -e "${YELLOW}You may need to create a PostgreSQL user:${NC}"
        echo "createuser -s \$(whoami)"
        echo "or"
        echo "createuser -s postgres"
        exit 1
    fi
    
    echo "$working_user"
}

# Function to create database and user if needed
setup_database() {
    local db_user="$1"
    local db_name="linkedin_automation"
    
    echo -e "${BLUE}Setting up database and user...${NC}"
    
    # Create database if it doesn't exist
    if ! psql -d postgres -U "$db_user" -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        echo "Creating database: $db_name"
        psql -d postgres -U "$db_user" -c "CREATE DATABASE $db_name;"
        echo -e "${GREEN}✅ Database '$db_name' created${NC}"
    else
        echo -e "${GREEN}✅ Database '$db_name' already exists${NC}"
    fi
    
    # Grant permissions if user is not the owner
    if [ "$db_user" != "$(whoami)" ] && [ "$db_user" != "postgres" ]; then
        psql -d postgres -U "$db_user" -c "GRANT ALL PRIVILEGES ON DATABASE $db_name TO $db_user;"
    fi
}

# Function to create/update .env file
create_env_file() {
    local db_user="$1"
    local db_name="linkedin_automation"
    
    echo -e "${BLUE}Creating .env file...${NC}"
    
    # Backup existing .env if it exists
    if [ -f ".env" ]; then
        cp .env .env.backup
        echo -e "${YELLOW}⚠️  Backed up existing .env to .env.backup${NC}"
    fi
    
    # Generate a secure secret key
    local secret_key=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    
    cat > .env << EOL
# Database Configuration - FIXED
DATABASE_URL=postgresql+asyncpg://${db_user}@localhost:5432/${db_name}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration  
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=${secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application Settings
DEBUG=true
CORS_ORIGINS=["http://localhost:3000", "http://localhost"]

# AI Services (Optional - add your keys here)
# OPENAI_API_KEY=your-openai-api-key
# ANTHROPIC_API_KEY=your-anthropic-api-key

# LinkedIn API (Optional - add your credentials here)
# LINKEDIN_CLIENT_ID=your-linkedin-client-id
# LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

# Content Processing
DEFAULT_CHECK_FREQUENCY_HOURS=24
MAX_CONTENT_AGE_DAYS=30
CONTENT_BATCH_SIZE=50
EOL

    echo -e "${GREEN}✅ .env file created with DATABASE_URL: postgresql+asyncpg://${db_user}@localhost:5432/${db_name}${NC}"
}

# Function to test the database connection with the new URL
test_final_connection() {
    local db_user="$1"
    local db_name="linkedin_automation"
    
    echo -e "${BLUE}Testing final database connection...${NC}"
    
    if psql -d "$db_name" -U "$db_user" -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Database connection test successful!${NC}"
        return 0
    else
        echo -e "${RED}❌ Database connection test failed${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}🚀 Starting PostgreSQL setup...${NC}"
    
    # Step 1: Check if PostgreSQL is installed
    check_postgresql
    
    # Step 2: Start PostgreSQL
    start_postgresql
    
    # Step 3: Test connections and find working user
    working_user=$(test_connection)
    echo -e "${GREEN}Using PostgreSQL user: $working_user${NC}"
    
    # Step 4: Setup database
    setup_database "$working_user"
    
    # Step 5: Create .env file
    create_env_file "$working_user"
    
    # Step 6: Test final connection
    if test_final_connection "$working_user"; then
        echo -e "${GREEN}🎉 PostgreSQL setup completed successfully!${NC}"
        echo ""
        echo -e "${BLUE}Your database configuration:${NC}"
        echo "Database User: $working_user"
        echo "Database Name: linkedin_automation"
        echo "Connection URL: postgresql+asyncpg://$working_user@localhost:5432/linkedin_automation"
        echo ""
        echo -e "${GREEN}You can now run: honcho start${NC}"
    else
        echo -e "${RED}❌ Setup completed but connection test failed.${NC}"
        echo "Please check your PostgreSQL installation and try again."
        exit 1
    fi
}

# Run the setup
main