#!/usr/bin/env python3
"""
Test script for the enhanced browser automation
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.enhanced_browser import enhanced_browser_tool
from core.logging import app_logger


async def test_enhanced_browser():
    """Test the enhanced browser functionality"""
    app_logger.info("Testing Enhanced Browser Tool")
    
    try:
        # Initialize browser
        app_logger.info("1. Initializing browser...")
        success = await enhanced_browser_tool.initialize()
        if not success:
            app_logger.error("Failed to initialize browser")
            return False
        
        # Navigate to a test site
        app_logger.info("2. Navigating to Google...")
        success = await enhanced_browser_tool.navigate_to("https://www.google.com")
        if not success:
            app_logger.error("Failed to navigate to Google")
            return False
        
        # Get page info
        app_logger.info("3. Getting page info...")
        page_info = await enhanced_browser_tool.get_page_info()
        app_logger.info(f"Page Title: {page_info.get('title')}")
        app_logger.info(f"Page URL: {page_info.get('url')}")
        app_logger.info(f"Forms: {page_info.get('forms_count')}")
        app_logger.info(f"Links: {page_info.get('links_count')}")
        
        # Get interactive elements
        app_logger.info("4. Getting interactive elements...")
        elements = await enhanced_browser_tool.get_interactive_elements()
        app_logger.info(f"Found {len(elements)} interactive elements")
        
        for i, element in enumerate(elements[:5]):  # Show first 5
            app_logger.info(f"  Element {i+1}: {element.tag} - {element.text[:50] if element.text else 'No text'}")
        
        # Test smart click on search box
        app_logger.info("5. Testing smart fill on search box...")
        success = await enhanced_browser_tool.smart_fill("search", "enhanced browser test")
        if success:
            app_logger.info("Successfully filled search box")
        else:
            app_logger.warning("Failed to fill search box")
        
        # Take a screenshot
        app_logger.info("6. Taking screenshot...")
        screenshot_path = await enhanced_browser_tool.take_screenshot("enhanced_test")
        if screenshot_path:
            app_logger.info(f"Screenshot saved: {screenshot_path}")
        else:
            app_logger.warning("Failed to take screenshot")
        
        app_logger.info("Enhanced browser test completed successfully!")
        return True
        
    except Exception as e:
        app_logger.error(f"Enhanced browser test failed: {e}")
        return False
    finally:
        # Cleanup
        await enhanced_browser_tool.close()


if __name__ == "__main__":
    success = asyncio.run(test_enhanced_browser())
    if success:
        print("✅ Enhanced browser test passed!")
        sys.exit(0)
    else:
        print("❌ Enhanced browser test failed!")
        sys.exit(1)
