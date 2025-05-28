#!/usr/bin/env python3
"""
Full Stack Integration Test for LinkedIn Automation MVP.

Tests end-to-end functionality including frontend-backend integration.
"""

import asyncio
import requests
import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FullStackTester:
    def __init__(self):
        self.frontend_url = "http://localhost"
        self.api_url = "http://localhost:8000/api/v1"
        self.user_token = None
        self.user_email = f"test_{int(time.time())}@example.com"

    def test_services_health(self):
        """Test that all services are healthy."""
        try:
            # Test frontend
            response = requests.get(self.frontend_url, timeout=10)
            assert response.status_code == 200
            logger.info("✅ Frontend is accessible")

            # Test backend health
            response = requests.get(f"{self.api_url.replace('/api/v1', '')}/health", timeout=10)
            assert response.status_code == 200
            logger.info("✅ Backend health check passed")

            return True

        except Exception as e:
            logger.error(f"❌ Service health check failed: {str(e)}")
            return False

    def test_user_registration_and_login(self):
        """Test user registration and login flow."""
        try:
            # Register user
            register_data = {
                "email": self.user_email,
                "password": "TestPassword123!",
                "full_name": "Test User"
            }

            response = requests.post(f"{self.api_url}/auth/register", json=register_data)
            assert response.status_code == 201
            
            data = response.json()
            self.user_token = data["access_token"]
            logger.info("✅ User registration successful")

            # Test login
            login_data = {
                "username": self.user_email,
                "password": "TestPassword123!"
            }

            response = requests.post(
                f"{self.api_url}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            assert response.status_code == 200
            logger.info("✅ User login successful")

            return True

        except Exception as e:
            logger.error(f"❌ Auth flow test failed: {str(e)}")
            return False

    def test_content_source_workflow(self):
        """Test complete content source workflow."""
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}

            # Create content source
            source_data = {
                "name": "Test RSS Feed",
                "source_type": "rss_feed",
                "url": "https://feeds.feedburner.com/oreilly/radar",
                "description": "Test RSS feed for automation",
                "check_frequency_hours": 24
            }

            response = requests.post(f"{self.api_url}/content/sources", json=source_data, headers=headers)
            assert response.status_code == 201
            
            source = response.json()
            source_id = source["id"]
            logger.info("✅ Content source created successfully")

            # Get sources list
            response = requests.get(f"{self.api_url}/content/sources", headers=headers)
            assert response.status_code == 200
            
            sources = response.json()
            assert len(sources) >= 1
            assert any(s["id"] == source_id for s in sources)
            logger.info("✅ Content sources retrieved successfully")

            # Get content feed (may be empty initially)
            response = requests.get(f"{self.api_url}/content/feed", headers=headers)
            assert response.status_code == 200
            logger.info("✅ Content feed accessible")

            return True

        except Exception as e:
            logger.error(f"❌ Content source workflow test failed: {str(e)}")
            return False

    def test_draft_generation_workflow(self):
        """Test draft generation workflow."""
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}

            # Try batch generation (should work even with no content)
            response = requests.post(f"{self.api_url}/drafts/batch-generate", headers=headers)
            # May return empty list if no content available
            assert response.status_code == 200
            logger.info("✅ Batch draft generation endpoint accessible")

            # Get drafts list
            response = requests.get(f"{self.api_url}/drafts", headers=headers)
            assert response.status_code == 200
            logger.info("✅ Drafts list accessible")

            return True

        except Exception as e:
            logger.error(f"❌ Draft workflow test failed: {str(e)}")
            return False

    def test_api_error_handling(self):
        """Test API error handling."""
        try:
            # Test unauthorized access
            response = requests.get(f"{self.api_url}/content/sources")
            assert response.status_code == 401
            logger.info("✅ Unauthorized access properly rejected")

            # Test invalid endpoint
            headers = {"Authorization": f"Bearer {self.user_token}"}
            response = requests.get(f"{self.api_url}/invalid-endpoint", headers=headers)
            assert response.status_code == 404
            logger.info("✅ Invalid endpoints properly handled")

            return True

        except Exception as e:
            logger.error(f"❌ Error handling test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all full-stack tests."""
        logger.info("Starting full-stack integration tests...")

        tests = [
            ("Service Health Check", self.test_services_health),
            ("User Registration & Login", self.test_user_registration_and_login),
            ("Content Source Workflow", self.test_content_source_workflow),
            ("Draft Generation Workflow", self.test_draft_generation_workflow),
            ("API Error Handling", self.test_api_error_handling),
        ]

        results = []
        for test_name, test_func in tests:
            logger.info(f"\n--- Running {test_name} ---")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"Test {test_name} crashed: {str(e)}")
                results.append((test_name, False))

        # Summary
        logger.info("\n" + "="*60)
        logger.info("FULL-STACK INTEGRATION TEST SUMMARY")
        logger.info("="*60)

        passed = 0
        for test_name, result in results:
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1

        logger.info(f"\nOverall: {passed}/{len(tests)} integration tests passed")

        if passed == len(tests):
            logger.info("🎉 All integration tests passed! Full stack is working!")
            logger.info("\n📋 MVP is ready for user testing:")
            logger.info(f"🌐 Frontend: {self.frontend_url}")
            logger.info(f"🔧 Backend: {self.api_url}")
            logger.info(f"📚 API Docs: {self.api_url.replace('/api/v1', '')}/docs")
            return True
        else:
            logger.error("❌ Some integration tests failed.")
            return False

def main():
    """Main test function."""
    tester = FullStackTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)