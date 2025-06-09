"""
Browser automation tools using Playwright
"""
import asyncio
import base64
from typing import Optional, Dict, Any, List, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from pathlib import Path
import uuid
from datetime import datetime

from core.config import settings
from core.models import WebElement, PageAnalysis
from core.logging import app_logger


class BrowserTool:
    """Advanced browser automation tool with computer vision capabilities"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_url: Optional[str] = None
        
    async def initialize(self) -> bool:
        """Initialize the browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Choose browser type
            if settings.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(
                    headless=settings.headless,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
            elif settings.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=settings.headless)
            else:  # webkit
                self.browser = await self.playwright.webkit.launch(headless=settings.headless)
            
            # Create context with proper settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set timeout
            self.page.set_default_timeout(settings.browser_timeout)
            
            app_logger.info(f"Browser initialized: {settings.browser_type}")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to initialize browser: {e}")
            return False
    
    async def navigate_to(self, url: str) -> bool:
        """Navigate to a URL"""
        try:
            if not self.page:
                await self.initialize()
            
            app_logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until="domcontentloaded")
            self.current_url = url
            
            # Wait for page to stabilize
            await asyncio.sleep(2)
            return True
            
        except Exception as e:
            app_logger.error(f"Navigation failed: {e}")
            return False
    
    async def take_screenshot(self, task_id: str) -> Optional[str]:
        """Take a screenshot and save it"""
        try:
            if not self.page:
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{task_id}_{timestamp}.png"
            screenshot_path = Path(settings.screenshot_path) / filename
            
            await self.page.screenshot(path=screenshot_path, full_page=True)
            app_logger.info(f"Screenshot saved: {screenshot_path}")
            
            return str(screenshot_path)
            
        except Exception as e:
            app_logger.error(f"Screenshot failed: {e}")
            return None
    
    async def click_element(self, selector: Optional[str] = None, 
                          coordinates: Optional[Tuple[int, int]] = None,
                          text: Optional[str] = None) -> bool:
        """Click an element by selector, coordinates, or text"""
        try:
            if not self.page:
                return False
            
            if coordinates:
                await self.page.mouse.click(coordinates[0], coordinates[1])
                app_logger.info(f"Clicked at coordinates: {coordinates}")
                
            elif selector:
                await self.page.click(selector)
                app_logger.info(f"Clicked element: {selector}")
                
            elif text:
                # Click by text content
                element = self.page.locator(f"text={text}").first
                await element.click()
                app_logger.info(f"Clicked element with text: {text}")
            
            await asyncio.sleep(1)  # Wait for action to complete
            return True
            
        except Exception as e:
            app_logger.error(f"Click failed: {e}")
            return False
    
    async def type_text(self, selector: str, text: str, clear_first: bool = True) -> bool:
        """Type text into an element"""
        try:
            if not self.page:
                return False
            
            if clear_first:
                await self.page.fill(selector, text)
            else:
                await self.page.type(selector, text)
            
            app_logger.info(f"Typed text into {selector}: {text[:50]}...")
            await asyncio.sleep(0.5)
            return True
            
        except Exception as e:
            app_logger.error(f"Type text failed: {e}")
            return False
    
    async def scroll_page(self, direction: str = "down", amount: int = 500) -> bool:
        """Scroll the page"""
        try:
            if not self.page:
                return False
            
            if direction == "down":
                await self.page.mouse.wheel(0, amount)
            elif direction == "up":
                await self.page.mouse.wheel(0, -amount)
            
            app_logger.info(f"Scrolled {direction} by {amount}px")
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            app_logger.error(f"Scroll failed: {e}")
            return False
    
    async def extract_page_text(self) -> Optional[str]:
        """Extract all text from the current page"""
        try:
            if not self.page:
                return None
            
            text_content = await self.page.inner_text("body")
            return text_content
            
        except Exception as e:
            app_logger.error(f"Text extraction failed: {e}")
            return None
    
    async def analyze_page(self) -> Optional[PageAnalysis]:
        """Analyze the current page and extract elements"""
        try:
            if not self.page:
                return None
            
            # Get page info
            url = self.page.url
            title = await self.page.title()
            
            # Extract interactive elements
            elements = []
            
            # Get clickable elements
            clickable_selectors = [
                "button", "a", "input[type='submit']", "input[type='button']",
                "[onclick]", "[role='button']", ".btn", ".button"
            ]
            
            for selector in clickable_selectors:
                element_handles = await self.page.query_selector_all(selector)
                for handle in element_handles[:20]:  # Limit to first 20
                    try:
                        bbox = await handle.bounding_box()
                        if bbox and await handle.is_visible():
                            text = await handle.inner_text()
                            attributes = await handle.evaluate("el => el.attributes")
                            
                            element = WebElement(
                                tag=await handle.evaluate("el => el.tagName.toLowerCase()"),
                                text=text.strip() if text else None,
                                attributes={attr['name']: attr['value'] for attr in attributes if attr},
                                coordinates=(int(bbox['x']), int(bbox['y'])),
                                size=(int(bbox['width']), int(bbox['height'])),
                                is_visible=True,
                                is_clickable=True
                            )
                            elements.append(element)
                    except:
                        continue
            
            # Take screenshot
            screenshot_path = await self.take_screenshot("page_analysis")
            
            return PageAnalysis(
                url=url,
                title=title,
                elements=elements,
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            app_logger.error(f"Page analysis failed: {e}")
            return None
    
    async def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """Wait for an element to appear"""
        try:
            if not self.page:
                return False
            
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
            
        except Exception as e:
            app_logger.error(f"Wait for element failed: {e}")
            return False
    
    async def close(self):
        """Close the browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            app_logger.info("Browser closed successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to close browser: {e}")


# Global browser instance
browser_tool = BrowserTool()
