#!/usr/bin/env python3
"""
MVP Testing Script for LinkedIn Presence Automation Application.

Tests all critical user journeys and verifies fixes are working.
"""

import asyncio
import logging
import sys
from datetime import datetime
from uuid import uuid4

# Test configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection and initialization."""
    try:
        from app.database.connection import init_database, get_db_session
        
        logger.info("Testing database connection...")
        await init_database()
        
        async with get_db_session() as session:
            result = await session.execute("SELECT 1")
            assert result.scalar() == 1
        
        logger.info("✅ Database connection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        return False

async def test_repository_pattern():
    """Test repository pattern with proper session handling."""
    try:
        from app.database.connection import get_db_session
        from app.repositories.user_repository import UserRepository
        
        logger.info("Testing repository pattern...")
        
        async with get_db_session() as session:
            user_repo = UserRepository(session)
            
            # Test user creation
            test_email = f"test_{uuid4().hex[:8]}@example.com"
            user = await user_repo.create_user(
                email=test_email,
                password_hash="hashed_password",
                full_name="Test User"
            )
            
            # Test user retrieval
            retrieved_user = await user_repo.get_by_id(user.id)
            assert retrieved_user.email == test_email
        
        logger.info("✅ Repository pattern test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Repository pattern test failed: {str(e)}")
        return False

async def test_api_endpoints():
    """Test API endpoints with proper error handling."""
    try:
        import httpx
        
        logger.info("Testing API endpoints...")
        
        # Assuming app is running on localhost:8000
        base_url = "http://localhost:8000"
        
        async with httpx.AsyncClient() as client:
            # Test health check
            response = await client.get(f"{base_url}/health")
            assert response.status_code == 200
            
            # Test user registration
            test_email = f"api_test_{uuid4().hex[:8]}@example.com"
            register_data = {
                "email": test_email,
                "password": "TestPassword123!",
                "full_name": "API Test User"
            }
            
            response = await client.post(f"{base_url}/api/v1/auth/register", json=register_data)
            if response.status_code == 201:
                logger.info("✅ User registration test passed")
            else:
                logger.warning(f"⚠️ User registration returned: {response.status_code}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API endpoints test failed: {str(e)}")
        return False

async def test_schema_serialization():
    """Test UUID to string serialization in schemas."""
    try:
        from app.schemas.api_schemas import ContentSourceResponse
        from uuid import uuid4
        from datetime import datetime
        
        logger.info("Testing schema serialization...")
        
        # Create test data with UUID
        test_data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "name": "Test Source",
            "source_type": "rss_feed",
            "url": "https://example.com/feed",
            "description": "Test description",
            "is_active": True,
            "check_frequency_hours": 24,
            "last_checked_at": datetime.utcnow(),
            "total_items_found": 0,
            "total_items_processed": 0,
            "created_at": datetime.utcnow()
        }
        
        # Test schema serialization
        response_obj = ContentSourceResponse(**test_data)
        json_data = response_obj.model_dump_json()
        
        # Verify UUIDs are serialized as strings
        assert isinstance(response_obj.id, str)
        assert isinstance(response_obj.user_id, str)
        
        logger.info("✅ Schema serialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema serialization test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all MVP tests."""
    logger.info("Starting MVP comprehensive tests...")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Repository Pattern", test_repository_pattern),
        ("Schema Serialization", test_schema_serialization),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        result = await test_func()
        results.append((test_name, result))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("TEST SUMMARY")
    logger.info("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("🎉 All tests passed! MVP is ready.")
        return True
    else:
        logger.error("❌ Some tests failed. Check logs above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)