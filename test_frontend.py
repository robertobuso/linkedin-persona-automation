#!/usr/bin/env python3
"""
Frontend Testing Script for LinkedIn Automation MVP.

Tests frontend functionality and integration with backend.
"""

import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FrontendTester:
    def __init__(self, base_url="http://localhost"):
        self.base_url = base_url
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver for testing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {str(e)}")
            logger.info("Please install ChromeDriver: https://chromedriver.chromium.org/")
            raise

    def test_homepage_loads(self):
        """Test that homepage loads correctly."""
        try:
            logger.info("Testing homepage load...")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "logo"))
            )
            
            # Check title
            assert "LinkedIn Automation MVP" in self.driver.title
            logger.info("✅ Homepage loads correctly")
            return True
            
        except Exception as e:
            logger.error(f"❌ Homepage test failed: {str(e)}")
            return False

    def test_user_registration(self):
        """Test user registration flow."""
        try:
            logger.info("Testing user registration...")
            
            # Find register link
            register_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Register')]"))
            )
            register_btn.click()
            
            # Fill registration form
            email_input = self.driver.find_element(By.NAME, "email")
            password_input = self.driver.find_element(By.NAME, "password")
            name_input = self.driver.find_element(By.NAME, "full_name")
            
            test_email = f"test_{int(time.time())}@example.com"
            email_input.send_keys(test_email)
            password_input.send_keys("TestPassword123!")
            name_input.send_keys("Test User")
            
            # Submit form
            submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_btn.click()
            
            # Wait for dashboard or success indicator
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            
            logger.info("✅ User registration test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Registration test failed: {str(e)}")
            return False

    def test_add_content_source(self):
        """Test adding a content source."""
        try:
            logger.info("Testing add content source...")
            
            # Navigate to sources tab
            sources_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Content Sources')]"))
            )
            sources_link.click()
            
            # Click add source button
            add_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add Source')]"))
            )
            add_btn.click()
            
            # Fill form
            name_input = self.driver.find_element(By.NAME, "name")
            url_input = self.driver.find_element(By.NAME, "url")
            description_input = self.driver.find_element(By.NAME, "description")
            
            name_input.send_keys("Test RSS Feed")
            url_input.send_keys("https://feeds.feedburner.com/oreilly/radar")
            description_input.send_keys("Test RSS feed for automation")
            
            # Submit
            submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_btn.click()
            
            # Wait for source to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), 'Test RSS Feed')]"))
            )
            
            logger.info("✅ Add content source test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Add content source test failed: {str(e)}")
            return False

    def test_navigation(self):
        """Test navigation between different tabs."""
        try:
            logger.info("Testing navigation...")
            
            tabs = [
                ("Overview", "📊 Overview"),
                ("Sources", "📡 Content Sources"),
                ("Feed", "📰 Content Feed"),
                ("Drafts", "✏️ Post Drafts")
            ]
            
            for tab_name, tab_text in tabs:
                tab_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{tab_text}')]"))
                )
                tab_link.click()
                
                # Wait for content to load
                time.sleep(1)
                
                # Check if we're on the right page
                assert tab_link.get_attribute('class') == 'active'
            
            logger.info("✅ Navigation test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Navigation test failed: {str(e)}")
            return False

    def test_responsive_design(self):
        """Test responsive design on mobile viewport."""
        try:
            logger.info("Testing responsive design...")
            
            # Set mobile viewport
            self.driver.set_window_size(375, 667)  # iPhone SE size
            
            # Reload page
            self.driver.refresh()
            
            # Check if mobile layout is applied
            dashboard = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard"))
            )
            
            # Mobile layout should stack vertically
            dashboard_style = dashboard.value_of_css_property('grid-template-columns')
            assert '1fr' in dashboard_style  # Should be single column
            
            # Reset to desktop
            self.driver.set_window_size(1200, 800)
            
            logger.info("✅ Responsive design test passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Responsive design test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all frontend tests."""
        logger.info("Starting comprehensive frontend tests...")
        
        tests = [
            ("Homepage Load", self.test_homepage_loads),
            ("User Registration", self.test_user_registration),
            ("Add Content Source", self.test_add_content_source),
            ("Navigation", self.test_navigation),
            ("Responsive Design", self.test_responsive_design),
        ]
        
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n--- Running {test_name} Test ---")
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"Test {test_name} crashed: {str(e)}")
                results.append((test_name, False))
        
        # Summary
        logger.info("\n" + "="*50)
        logger.info("FRONTEND TEST SUMMARY")
        logger.info("="*50)
        
        passed = 0
        for test_name, result in results:
            status = "PASSED" if result else "FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{len(tests)} frontend tests passed")
        return passed == len(tests)

    def cleanup(self):
        """Cleanup resources."""
        if self.driver:
            self.driver.quit()
            logger.info("Browser driver closed")

def main():
    """Main test function."""
    tester = None
    try:
        tester = FrontendTester()
        success = tester.run_all_tests()
        
        if success:
            logger.info("🎉 All frontend tests passed! Frontend is ready.")
            return True
        else:
            logger.error("❌ Some frontend tests failed. Check logs above.")
            return False
            
    except Exception as e:
        logger.error(f"Frontend testing failed: {str(e)}")
        return False
    finally:
        if tester:
            tester.cleanup()

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)