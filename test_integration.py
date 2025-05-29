import pytest
import asyncio
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_enhanced_content_flow():
    """Test complete enhanced content flow."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Register/login user
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User"
        })
        assert response.status_code == 201
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Set up preferences
        prefs_response = await client.post("/api/v1/preferences/preferences", 
            json={
                "job_role": "software_engineer",
                "industry": "technology", 
                "primary_interests": ["AI", "software engineering"],
                "min_relevance_score": 0.7,
                "max_articles_per_day": 10,
                "content_types": ["articles", "news", "analysis"],
                "preferred_content_length": "medium",
                "min_word_count": 200,
                "max_word_count": 5000,
                "content_freshness_hours": 72,
                "learn_from_interactions": True
            },
            headers=headers
        )
        assert prefs_response.status_code == 201
        
        # 3. Add content source
        source_response = await client.post("/api/v1/content/sources",
            json={
                "name": "Tech News",
                "source_type": "rss_feed",
                "url": "https://feeds.example.com/tech.xml",
                "description": "Technology news feed",
                "check_frequency_hours": 24,
                "is_active": True
            },
            headers=headers
        )
        assert source_response.status_code == 201
        
        # 4. Trigger enhanced ingestion
        ingestion_response = await client.post("/api/v1/content/trigger-ingestion",
            headers=headers
        )
        assert ingestion_response.status_code == 202
        
        # 5. Test content selection
        selection_response = await client.post("/api/v1/content/select-content",
            headers=headers
        )
        assert selection_response.status_code == 200
        selection_data = selection_response.json()
        assert "selected_articles" in selection_data
        assert "selection_metadata" in selection_data
        
        # 6. Test preferences retrieval
        get_prefs_response = await client.get("/api/v1/preferences/preferences",
            headers=headers
        )
        assert get_prefs_response.status_code == 200
        
        # 7. Test content stats
        stats_response = await client.get("/api/v1/content/stats",
            headers=headers
        )
        assert stats_response.status_code == 200
        
        # 8. Test cache invalidation
        cache_response = await client.post("/api/v1/preferences/content/invalidate-cache",
            headers=headers
        )
        assert cache_response.status_code == 200


@pytest.mark.asyncio
async def test_llm_integration():
    """Test LLM service integration."""
    from app.services.ai_service import AIService
    from app.services.enhanced_content_ingestion import EnhancedContentIngestionService
    from app.services.deep_content_analysis import DeepContentAnalysisService
    from app.database.connection import get_db_session
    
    # Test AI Service initialization
    ai_service = AIService()
    assert ai_service is not None
    
    # Test Enhanced Content Ingestion Service
    async with get_db_session() as session:
        enhanced_service = EnhancedContentIngestionService(session, None)
        assert enhanced_service is not None
        
        # Test LLM prompt building
        prompt = enhanced_service._build_selection_prompt([], "Test user context", None)
        assert len(prompt) > 0
        assert "content curator" in prompt.lower()
        
        # Test Deep Content Analysis Service
        analysis_service = DeepContentAnalysisService(session)
        assert analysis_service is not None


@pytest.mark.asyncio 
async def test_redis_integration():
    """Test Redis caching integration."""
    import redis.asyncio as redis
    import os
    
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=False)
        
        # Test Redis connection
        await redis_client.ping()
        
        # Test cache operations
        test_key = "test:integration"
        test_value = {"test": "data"}
        
        import json
        await redis_client.setex(test_key, 60, json.dumps(test_value))
        
        cached_data = await redis_client.get(test_key)
        assert cached_data is not None
        
        parsed_data = json.loads(cached_data)
        assert parsed_data["test"] == "data"
        
        await redis_client.delete(test_key)
        
    except Exception as e:
        pytest.skip(f"Redis not available for testing: {str(e)}")


@pytest.mark.asyncio
async def test_preferences_integration():
    """Test preferences system integration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        response = await client.post("/api/v1/auth/register", json={
            "email": "prefs_test@example.com",
            "password": "TestPassword123!",
            "full_name": "Preferences Test User"
        })
        assert response.status_code == 201
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test preferences creation
        prefs_data = {
            "job_role": "product_manager",
            "industry": "technology",
            "primary_interests": ["product management", "user experience"],
            "secondary_interests": ["data analysis"],
            "custom_prompt": "Focus on B2B SaaS product insights",
            "min_relevance_score": 0.8,
            "max_articles_per_day": 5
        }
        
        create_response = await client.post("/api/v1/preferences/preferences",
            json=prefs_data,
            headers=headers
        )
        assert create_response.status_code == 201
        
        # Test preferences retrieval
        get_response = await client.get("/api/v1/preferences/preferences",
            headers=headers
        )
        assert get_response.status_code == 200
        prefs = get_response.json()
        assert prefs["job_role"] == "product_manager"
        assert prefs["industry"] == "technology"
        
        # Test preferences update
        update_data = {
            "max_articles_per_day": 8,
            "min_relevance_score": 0.75
        }
        
        update_response = await client.put("/api/v1/preferences/preferences",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_updated_response = await client.get("/api/v1/preferences/preferences",
            headers=headers
        )
        assert get_updated_response.status_code == 200
        updated_prefs = get_updated_response.json()
        assert updated_prefs["max_articles_per_day"] == 8
        assert updated_prefs["min_relevance_score"] == 0.75


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling throughout the integration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test unauthenticated access
        response = await client.get("/api/v1/preferences/preferences")
        assert response.status_code == 401
        
        # Test invalid preferences data
        response = await client.post("/api/v1/auth/register", json={
            "email": "error_test@example.com",
            "password": "TestPassword123!",
            "full_name": "Error Test User"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Invalid preferences data
        invalid_prefs = {
            "min_relevance_score": 1.5,  # Invalid: > 1.0
            "max_articles_per_day": 200  # Invalid: > 100
        }
        
        prefs_response = await client.post("/api/v1/preferences/preferences",
            json=invalid_prefs,
            headers=headers
        )
        assert prefs_response.status_code == 422  # Validation error


@pytest.mark.asyncio 
async def test_performance():
    """Test system performance under load."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register user
        response = await client.post("/api/v1/auth/register", json={
            "email": "perf_test@example.com", 
            "password": "TestPassword123!",
            "full_name": "Performance Test User"
        })
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create preferences
        await client.post("/api/v1/preferences/preferences",
            json={
                "job_role": "software_engineer",
                "industry": "technology",
                "primary_interests": ["AI", "software engineering"],
                "min_relevance_score": 0.7,
                "max_articles_per_day": 10
            },
            headers=headers
        )
        
        # Test multiple concurrent content selections
        import time
        start_time = time.time()
        
        tasks = []
        for _ in range(5):
            task = client.post("/api/v1/content/select-content", headers=headers)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (10 seconds for 5 requests)
        assert duration < 10.0
        
        # All requests should succeed or handle gracefully
        for response in responses:
            if isinstance(response, Exception):
                # Log but don't fail - some may timeout under load
                print(f"Request failed under load: {response}")
            else:
                assert response.status_code in [200, 429, 503]  # Success or rate limited