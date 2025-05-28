# LinkedIn Presence Automation MVP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)
[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)](https://www.docker.com)

> **AI-powered LinkedIn content automation platform** that discovers relevant content from RSS feeds and generates personalized LinkedIn posts automatically.

![LinkedIn Automation MVP](https://img.shields.io/badge/Status-MVP%20Ready-brightgreen.svg)

## 🚀 Quick Start

**Get the MVP running in 3 commands:**

```bash
# 1. Setup frontend files
chmod +x setup_frontend.sh && ./setup_frontend.sh

# 2. Start the full stack
chmod +x start_mvp.sh && ./start_mvp.sh

# 3. Test everything works
python test_full_stack.py
```

**Access your LinkedIn automation platform:**
- 🌐 **Frontend**: http://localhost
- 🔧 **Backend API**: http://localhost:8000
- 📚 **API Documentation**: http://localhost:8000/docs

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage Guide](#-usage-guide)
- [API Reference](#-api-reference)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🔥 Core MVP Features
- **📡 Content Discovery**: Automatically monitors RSS feeds and LinkedIn profiles
- **🤖 AI-Powered Generation**: Creates personalized LinkedIn posts from discovered content
- **✏️ Draft Management**: Review, edit, and approve generated content before publishing
- **⏰ Scheduling**: Schedule posts for optimal engagement times
- **📊 Content Analytics**: Track post performance and engagement metrics
- **🎯 Personalization**: Learns from your writing style and preferences

### 💻 Technical Features
- **🌐 Modern Web Interface**: Responsive React frontend with intuitive design
- **⚡ FastAPI Backend**: High-performance async Python API
- **🐳 Docker Ready**: One-command deployment with Docker Compose
- **🔐 Secure Authentication**: JWT-based user authentication and authorization
- **📚 Auto-Generated API Docs**: Interactive OpenAPI documentation
- **🧪 Comprehensive Testing**: Unit, integration, and end-to-end tests

### 🛡️ Production Ready
- **🔄 Background Processing**: Celery-based task queue for content ingestion
- **💾 PostgreSQL Database**: Robust data persistence with migrations
- **📈 Redis Caching**: Fast session management and task queuing
- **🚨 Error Handling**: Graceful fallbacks and comprehensive error reporting
- **📱 Mobile Responsive**: Works perfectly on desktop and mobile devices

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Frontend"
        UI[React SPA]
        NGINX[Nginx Proxy]
    end
    
    subgraph "Backend Services"
        API[FastAPI Application]
        WORKER[Celery Workers]
        BEAT[Celery Beat Scheduler]
    end
    
    subgraph "Data Layer"
        DB[(PostgreSQL)]
        REDIS[(Redis)]
    end
    
    subgraph "External Services"
        RSS[RSS Feeds]
        LINKEDIN[LinkedIn API]
        AI[AI Services]
    end
    
    UI --> NGINX
    NGINX --> API
    API --> DB
    API --> REDIS
    WORKER --> DB
    WORKER --> REDIS
    WORKER --> RSS
    WORKER --> LINKEDIN
    WORKER --> AI
    BEAT --> REDIS
```

### 🧩 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | React 18, Vanilla CSS | User interface and experience |
| **Backend** | FastAPI, Python 3.11+ | REST API and business logic |
| **Database** | PostgreSQL 15 | Data persistence and integrity |
| **Cache/Queue** | Redis 7 | Session management and task queue |
| **Task Processing** | Celery | Background content processing |
| **Containerization** | Docker, Docker Compose | Deployment and orchestration |
| **Web Server** | Nginx | Frontend serving and API proxy |

---

## 📋 Prerequisites

### Required Software
- **Docker**: 20.10+ and Docker Compose 2.0+
- **Python**: 3.11+ (for local development)
- **Git**: For cloning the repository

### Optional for Development
- **Chrome/Chromium**: For frontend testing with Selenium
- **Node.js**: For advanced frontend development
- **PostgreSQL Client**: For direct database access

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet access for content discovery
- **OS**: Linux, macOS, or Windows with WSL2

---

## 🔧 Installation

### Method 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/linkedin-automation-mvp.git
cd linkedin-automation-mvp

# Quick setup and start
chmod +x setup_frontend.sh && ./setup_frontend.sh
chmod +x start_mvp.sh && ./start_mvp.sh

# Verify installation
python test_full_stack.py
```

### Method 2: Local Development

```bash
# Clone and setup
git clone https://github.com/your-username/linkedin-automation-mvp.git
cd linkedin-automation-mvp

# Install Python dependencies
pip install -r backend/requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Start databases with Docker
docker-compose up -d postgres redis

# Run database migrations
python -c "import asyncio; from app.database.connection import run_migrations; asyncio.run(run_migrations())"

# Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# In another terminal, start Celery beat
celery -A app.core.celery_app beat --loglevel=info

# Serve frontend (simple HTTP server)
cd frontend && python -m http.server 3000
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/linkedin_automation
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-jwt-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application Settings
DEBUG=true
CORS_ORIGINS=["http://localhost:3000", "http://localhost"]

# AI Services (Optional)
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# LinkedIn API (Optional)
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

# Content Processing
DEFAULT_CHECK_FREQUENCY_HOURS=24
MAX_CONTENT_AGE_DAYS=30
CONTENT_BATCH_SIZE=50
```

### Docker Configuration

The application uses Docker Compose for orchestration. Key services:

```yaml
services:
  postgres:    # Database (port 5432)
  redis:       # Cache/Queue (port 6379)
  app:         # FastAPI Backend (port 8000)
  frontend:    # React/Nginx Frontend (port 80)
  celery-worker: # Background tasks
  celery-beat:   # Task scheduler
```

---

## 📖 Usage Guide

### 🔐 User Authentication

1. **Register a New Account**
   - Navigate to http://localhost
   - Click "Register"
   - Fill in email, password, and full name
   - Password must be 8+ characters with uppercase, lowercase, and digit

2. **Login**
   - Use your email and password
   - Receive JWT token for API access
   - Token expires after 24 hours

### 📡 Content Source Management

1. **Add RSS Feed Source**
   ```
   Name: Tech News
   Type: RSS Feed
   URL: https://feeds.feedburner.com/oreilly/radar
   Description: Technology news and insights
   Check Frequency: 24 hours
   ```

2. **Configure Content Filters** (Optional)
   ```json
   {
     "min_content_length": 200,
     "max_content_age_days": 30,
     "keywords_include": ["AI", "technology", "innovation"],
     "keywords_exclude": ["spam", "ads"],
     "language": "en"
   }
   ```

### ✏️ Draft Generation and Management

1. **Generate from Content Feed**
   - Browse discovered content in "Content Feed"
   - Click "Generate Draft" on interesting articles
   - AI creates personalized LinkedIn post

2. **Batch Generation**
   - Click "Generate Drafts" in the Drafts tab
   - Automatically creates multiple posts from high-relevance content
   - Configurable batch size and relevance threshold

3. **Edit and Customize**
   - Review generated content
   - Edit text, hashtags, and styling
   - Save changes before publishing

4. **Publishing**
   - Click "Publish" to mark as ready
   - Schedule for later (optional)
   - Track publication status

### 📊 Content Discovery Process

The system automatically:
1. **Monitors** configured RSS feeds every 24 hours
2. **Extracts** article content and metadata
3. **Filters** content based on your preferences
4. **Analyzes** relevance and quality scores
5. **Stores** high-quality content for draft generation

---

## 🔌 API Reference

### Authentication Endpoints

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
PUT  /api/v1/auth/me
POST /api/v1/auth/change-password
```

### Content Management

```http
GET    /api/v1/content/sources
POST   /api/v1/content/sources
GET    /api/v1/content/sources/{id}
PUT    /api/v1/content/sources/{id}
DELETE /api/v1/content/sources/{id}
GET    /api/v1/content/feed
POST   /api/v1/content/trigger-ingestion
```

### Draft Management

```http
GET    /api/v1/drafts
POST   /api/v1/drafts
GET    /api/v1/drafts/{id}
PUT    /api/v1/drafts/{id}
DELETE /api/v1/drafts/{id}
POST   /api/v1/drafts/{id}/publish
POST   /api/v1/drafts/{id}/regenerate
POST   /api/v1/drafts/batch-generate
```

### Example API Usage

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'

# Add content source
curl -X POST http://localhost:8000/api/v1/content/sources \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Blog",
    "source_type": "rss_feed",
    "url": "https://example.com/feed.xml",
    "description": "Technology insights"
  }'

# Generate draft
curl -X POST http://localhost:8000/api/v1/drafts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_item_id": "content-uuid-here"
  }'
```

**📚 Interactive Documentation**: Visit http://localhost:8000/docs for full API documentation with try-it-yourself interface.

---

## 👩‍💻 Development

### Project Structure

```
linkedin-automation-mvp/
├── app/                          # Backend application
│   ├── api/v1/endpoints/         # API route handlers
│   ├── core/                     # Core configuration
│   ├── database/                 # Database connections
│   ├── models/                   # SQLAlchemy models
│   ├── repositories/             # Data access layer
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Business logic
│   ├── tasks/                    # Celery tasks
│   └── utils/                    # Utilities
├── frontend/                     # Frontend application
│   ├── index.html               # React SPA
│   ├── nginx.conf               # Nginx configuration
│   └── Dockerfile               # Frontend container
├── alembic/                     # Database migrations
├── tests/                       # Test suite
├── docker-compose.yml           # Container orchestration
├── Dockerfile                   # Backend container
└── requirements.txt             # Python dependencies
```

### Adding New Features

1. **Backend API Endpoint**
   ```python
   # app/api/v1/endpoints/new_feature.py
   from fastapi import APIRouter, Depends
   
   router = APIRouter()
   
   @router.get("/new-endpoint")
   async def new_endpoint():
       return {"message": "Hello World"}
   ```

2. **Database Model**
   ```python
   # app/models/new_model.py
   from sqlalchemy import Column, String, DateTime
   from app.database.connection import Base
   
   class NewModel(Base):
       __tablename__ = "new_table"
       
       id = Column(String, primary_key=True)
       name = Column(String, nullable=False)
   ```

3. **Frontend Component**
   ```jsx
   // Add to frontend/index.html React components
   const NewComponent = () => {
       return <div>New Feature</div>;
   };
   ```

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/
mypy app/

# Run tests
pytest tests/

# Check security
bandit -r app/
```

---

## 🧪 Testing

### Automated Test Suite

```bash
# Backend tests
python test_mvp.py                    # Core functionality
python test_full_stack.py            # End-to-end integration

# Frontend tests (requires Chrome)
python test_frontend.py              # UI functionality

# Individual test categories
pytest tests/test_auth.py            # Authentication
pytest tests/test_content.py         # Content processing
pytest tests/test_drafts.py          # Draft management
```

### Manual Testing Checklist

- [ ] **User Registration**: Can create new account
- [ ] **User Login**: Can authenticate with valid credentials
- [ ] **Add Content Source**: Can add RSS feed successfully
- [ ] **Content Discovery**: Background processing works
- [ ] **View Content Feed**: Can browse discovered content
- [ ] **Generate Drafts**: Can create posts from content
- [ ] **Edit Drafts**: Can modify generated content
- [ ] **Publish Posts**: Can mark drafts as published
- [ ] **Mobile Responsive**: UI works on mobile devices
- [ ] **Error Handling**: Graceful error messages displayed

### Performance Testing

```bash
# Load testing with Apache Bench
ab -n 100 -c 10 http://localhost:8000/api/v1/content/feed

# Database query analysis
docker-compose exec postgres psql -U postgres -d linkedin_automation
EXPLAIN ANALYZE SELECT * FROM content_items WHERE relevance_score > 70;
```

---

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Production environment variables
   export DATABASE_URL=postgresql://user:pass@prod-db:5432/linkedin
   export REDIS_URL=redis://prod-redis:6379/0
   export SECRET_KEY=your-production-secret-key
   export DEBUG=false
   ```

2. **Docker Deployment**
   ```bash
   # Build and deploy
   docker-compose -f docker-compose.prod.yml up -d
   
   # Scale workers
   docker-compose up -d --scale celery-worker=3
   ```

3. **Database Migrations**
   ```bash
   # Run migrations in production
   docker-compose exec app python -c "
   import asyncio
   from app.database.connection import run_migrations
   asyncio.run(run_migrations())
   "
   ```

### Monitoring and Maintenance

```bash
# Monitor logs
docker-compose logs -f app
docker-compose logs -f celery-worker

# Database backup
docker-compose exec postgres pg_dump -U postgres linkedin_automation > backup.sql

# Health checks
curl http://localhost:8000/health
curl http://localhost/health
```

### Security Considerations

- **Environment Variables**: Never commit secrets to version control
- **Database**: Use strong passwords and SSL connections
- **API**: Implement rate limiting and input validation
- **HTTPS**: Use SSL certificates in production
- **Updates**: Regularly update dependencies for security patches

---

## 🔧 Troubleshooting

### Common Issues

#### "Database connection failed"
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### "Celery workers not processing tasks"
```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Restart workers
docker-compose restart celery-worker celery-beat

# Check worker logs
docker-compose logs celery-worker
```

#### "Frontend not loading"
```bash
# Check if frontend container is running
docker-compose ps frontend

# Check nginx logs
docker-compose logs frontend

# Verify API proxy
curl http://localhost/api/v1/health
```

#### "Permission denied" errors
```bash
# Fix script permissions
chmod +x setup_frontend.sh
chmod +x start_mvp.sh

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
```

### Debugging Tips

1. **Enable Debug Mode**
   ```bash
   export DEBUG=true
   docker-compose restart app
   ```

2. **Database Shell Access**
   ```bash
   docker-compose exec postgres psql -U postgres linkedin_automation
   ```

3. **Application Shell**
   ```bash
   docker-compose exec app python
   >>> from app.database.connection import get_db_session
   ```

4. **Check Service Health**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost/health
   ```

### Getting Help

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Documentation**: Check API docs at `/docs`
- **Logs**: Always include relevant log outputs when reporting issues

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR-USERNAME/linkedin-automation-mvp.git
cd linkedin-automation-mvp

# Create feature branch
git checkout -b feature/amazing-feature

# Setup development environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r backend/requirements.txt
pip install -r requirements-dev.txt
```

### Contribution Guidelines

1. **Code Style**: Follow PEP 8 and use provided formatting tools
2. **Testing**: Add tests for new features and bug fixes
3. **Documentation**: Update relevant documentation
4. **Commits**: Use conventional commit messages
5. **Pull Requests**: Provide clear description and link related issues

### Development Workflow

```bash
# Make your changes
# Add tests
pytest tests/

# Format code
black app/
isort app/

# Commit changes
git add .
git commit -m "feat: add amazing new feature"

# Push and create PR
git push origin feature/amazing-feature
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 LinkedIn Automation MVP

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- **FastAPI**: For the excellent async Python framework
- **React**: For the powerful frontend library
- **PostgreSQL**: For reliable data persistence
- **Redis**: For efficient caching and task queuing
- **Docker**: For simplified deployment and development
- **Open Source Community**: For the amazing tools and libraries

---

## 📊 Project Status

| Feature | Status | Notes |
|---------|--------|-------|
| 🔐 User Authentication | ✅ Complete | JWT-based with refresh tokens |
| 📡 Content Discovery | ✅ Complete | RSS feeds with background processing |
| 🤖 AI Draft Generation | ✅ Complete | With graceful fallbacks |
| ✏️ Draft Management | ✅ Complete | Full CRUD operations |
| 📊 Basic Analytics | ✅ Complete | Draft statistics and metrics |
| 🔗 LinkedIn Integration | ⏳ Simulated | Real API integration pending |
| 📈 Advanced Analytics | 📋 Planned | Engagement tracking and insights |
| 👥 Team Collaboration | 📋 Planned | Multi-user workspace features |

---

## 🚀 Getting Started Checklist

- [ ] Clone the repository
- [ ] Run `./setup_frontend.sh`
- [ ] Run `./start_mvp.sh`
- [ ] Visit http://localhost
- [ ] Register a new account
- [ ] Add an RSS feed source
- [ ] Generate your first draft
- [ ] 🎉 You're automating LinkedIn content!

**Ready to revolutionize your LinkedIn presence? Let's get started!** 🚀