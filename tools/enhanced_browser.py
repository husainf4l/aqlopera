"""
Enhanced browser automation tool using Playwright's full DOM capabilities
"""
import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Locator
from pathlib import Path
from datetime import datetime

from core.config import settings
from core.models import WebElement, PageAnalysis
from core.logging import app_logger


class EnhancedBrowserTool:
    """Enhanced browser automation tool using real DOM interaction instead of screenshots"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.current_url: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize the browser with enhanced capabilities"""
        try:
            self.playwright = await async_playwright().start()
            
            # Use Chromium for best web compatibility
            self.browser = await self.playwright.chromium.launch(
                headless=settings.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set reasonable timeouts
            self.page.set_default_timeout(30000)  # 30 seconds
            
            app_logger.info("Enhanced browser initialized successfully")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to initialize enhanced browser: {e}")
            return False
    
    async def navigate_to(self, url: str) -> bool:
        """Navigate to a URL and wait for page to be ready"""
        try:
            # Ensure browser is initialized
            if not self.page or not self.browser:
                app_logger.info("Browser not initialized, initializing now...")
                await self.initialize()
            
            app_logger.info(f"Navigating to: {url}")
            
            # Navigate and wait for the page to be fully loaded
            await self.page.goto(url, wait_until="domcontentloaded")
            
            # Wait for network to be idle (no requests for 500ms)
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            
            self.current_url = self.page.url
            
            app_logger.info(f"Successfully navigated to: {self.current_url}")
            return True
            
        except Exception as e:
            app_logger.error(f"Navigation failed: {e}")
            # Try to reinitialize browser on navigation failure
            try:
                await self.initialize()
                await self.page.goto(url, wait_until="domcontentloaded")
                await self.page.wait_for_load_state("networkidle", timeout=10000)
                self.current_url = self.page.url
                app_logger.info(f"Successfully navigated after reinit to: {self.current_url}")
                return True
            except Exception as retry_e:
                app_logger.error(f"Navigation retry failed: {retry_e}")
                return False
    
    async def get_interactive_elements(self) -> List[WebElement]:
        """Get all interactive elements on the page using DOM queries"""
        try:
            if not self.page:
                return []
            
            elements = []
            
            # Define comprehensive selectors for interactive elements
            selectors = {
                'links': 'a[href]',
                'buttons': 'button, input[type="button"], input[type="submit"]',
                'inputs': 'input:not([type="hidden"]), textarea, select',
                'clickable': '[onclick], [role="button"], [role="link"]',
                'forms': 'form',
                'images': 'img[alt], img[title]'
            }
            
            for element_type, selector in selectors.items():
                try:
                    # Get all elements matching the selector
                    locators = await self.page.locator(selector).all()
                    
                    for locator in locators[:10]:  # Limit to prevent overwhelming
                        try:
                            # Check if element is visible and enabled
                            if not await locator.is_visible():
                                continue
                                
                            # Get element properties
                            tag_name = await locator.evaluate("el => el.tagName.toLowerCase()")
                            text = await locator.inner_text() or ""
                            
                            # Get useful attributes
                            attrs = {}
                            for attr in ['id', 'class', 'name', 'type', 'href', 'value', 'placeholder', 'aria-label', 'title']:
                                try:
                                    value = await locator.get_attribute(attr)
                                    if value:
                                        attrs[attr] = value
                                except Exception:
                                    pass
                            
                            # Get bounding box for coordinates
                            bbox = await locator.bounding_box()
                            if not bbox:
                                continue
                            
                            # Create CSS selector for the element
                            element_selector = await self._generate_selector(locator)
                            
                            element = WebElement(
                                tag=tag_name,
                                text=text.strip()[:100] if text else None,  # Limit text length
                                attributes=attrs,
                                coordinates=(int(bbox['x']), int(bbox['y'])),
                                size=(int(bbox['width']), int(bbox['height'])),
                                selector=element_selector,
                                is_visible=True,
                                is_clickable=element_type in ['links', 'buttons', 'clickable'],
                                element_type=element_type
                            )
                            
                            elements.append(element)
                            
                        except Exception as e:
                            app_logger.debug(f"Error processing element: {e}")
                            continue
                
                except Exception as e:
                    app_logger.debug(f"Error with selector {selector}: {e}")
                    continue
            
            app_logger.info(f"Found {len(elements)} interactive elements")
            return elements
            
        except Exception as e:
            app_logger.error(f"Failed to get interactive elements: {e}")
            return []
    
    async def _generate_selector(self, locator: Locator) -> str:
        """Generate a robust CSS selector for an element"""
        try:
            # Try to get a unique selector
            selectors = await locator.evaluate("""
                el => {
                    const selectors = [];
                    
                    // Try ID first
                    if (el.id) {
                        selectors.push('#' + el.id);
                    }
                    
                    // Try data attributes
                    for (let attr of el.attributes) {
                        if (attr.name.startsWith('data-') && attr.value) {
                            selectors.push(`[${attr.name}="${attr.value}"]`);
                        }
                    }
                    
                    // Try class combinations
                    if (el.className && typeof el.className === 'string') {
                        const classes = el.className.trim().split(/\\s+/);
                        if (classes.length <= 3) {
                            selectors.push('.' + classes.join('.'));
                        }
                    }
                    
                    // Try tag + text content for buttons/links
                    if (['A', 'BUTTON', 'INPUT'].includes(el.tagName) && el.textContent) {
                        const text = el.textContent.trim().slice(0, 20);
                        if (text) {
                            selectors.push(`${el.tagName.toLowerCase()}:has-text("${text}")`);
                        }
                    }
                    
                    // Fallback to tag name
                    selectors.push(el.tagName.toLowerCase());
                    
                    return selectors;
                }
            """)
            
            # Return the first selector (most specific)
            return selectors[0] if selectors else "unknown"
            
        except Exception as e:
            app_logger.debug(f"Error generating selector: {e}")
            return "unknown"
    
    async def smart_click(self, target: str) -> bool:
        """Smart click that tries multiple strategies to find and click an element"""
        try:
            if not self.page:
                return False
            
            app_logger.info(f"Attempting to click: {target}")
            
            # Strategy 1: Try as CSS selector
            try:
                await self.page.click(target, timeout=5000)
                app_logger.info(f"Successfully clicked element with selector: {target}")
                return True
            except Exception:
                pass
            
            # Strategy 2: Try by text content
            try:
                await self.page.click(f'text="{target}"', timeout=5000)
                app_logger.info(f"Successfully clicked element by text: {target}")
                return True
            except Exception:
                pass
            
            # Strategy 3: Try by partial text
            try:
                await self.page.click(f'text*="{target}"', timeout=5000)
                app_logger.info(f"Successfully clicked element by partial text: {target}")
                return True
            except Exception:
                pass
            
            # Strategy 4: Try by aria-label or title
            try:
                await self.page.click(f'[aria-label*="{target}"], [title*="{target}"]', timeout=5000)
                app_logger.info(f"Successfully clicked element by aria-label/title: {target}")
                return True
            except Exception:
                pass
            
            # Strategy 5: Try by placeholder
            try:
                await self.page.click(f'[placeholder*="{target}"]', timeout=5000)
                app_logger.info(f"Successfully clicked element by placeholder: {target}")
                return True
            except Exception:
                pass
            
            app_logger.warning(f"Could not click element: {target}")
            return False
            
        except Exception as e:
            app_logger.error(f"Smart click failed: {e}")
            return False
    
    async def smart_fill(self, target: str, text: str) -> bool:
        """Smart fill that tries multiple strategies to find and fill an input"""
        try:
            if not self.page:
                app_logger.error("No page available for smart fill")
                return False
            
            app_logger.info(f"Attempting to fill '{target}' with: {text}")
            
            # Strategy 1: Try as exact CSS selector
            try:
                await self.page.fill(target, text, timeout=5000)
                app_logger.info(f"Successfully filled element with selector: {target}")
                return True
            except Exception as e:
                app_logger.debug(f"Strategy 1 failed: {e}")
            
            # Strategy 2: For Google search specifically, try multiple search box selectors
            if "google.com" in (self.current_url or ""):
                google_selectors = [
                    'input[name="q"]',
                    'textarea[name="q"]',
                    '[name="q"]',
                    'input[type="search"]',
                    '[role="combobox"]',
                    'input[aria-label*="Search"]',
                    'textarea[aria-label*="Search"]'
                ]
                
                for selector in google_selectors:
                    try:
                        await self.page.fill(selector, text, timeout=3000)
                        app_logger.info(f"Successfully filled Google search with selector: {selector}")
                        return True
                    except Exception as e:
                        app_logger.debug(f"Google selector {selector} failed: {e}")
            
            # Strategy 3: Try by placeholder
            try:
                await self.page.fill(f'[placeholder*="{target}"]', text, timeout=5000)
                app_logger.info(f"Successfully filled element by placeholder: {target}")
                return True
            except Exception as e:
                app_logger.debug(f"Strategy 3 failed: {e}")
            
            # Strategy 4: Try by name attribute (partial match)
            try:
                await self.page.fill(f'[name*="{target}"]', text, timeout=5000)
                app_logger.info(f"Successfully filled element by name: {target}")
                return True
            except Exception as e:
                app_logger.debug(f"Strategy 4 failed: {e}")
            
            # Strategy 5: Try by ID
            try:
                await self.page.fill(f'#{target}', text, timeout=5000)
                app_logger.info(f"Successfully filled element by ID: {target}")
                return True
            except Exception as e:
                app_logger.debug(f"Strategy 5 failed: {e}")
            
            # Strategy 6: Try common search input patterns
            search_selectors = [
                'input[type="text"]',
                'input[type="search"]',
                'textarea',
                'input:not([type="hidden"]):not([type="submit"]):not([type="button"])'
            ]
            
            for selector in search_selectors:
                try:
                    # Check if the input is visible and not disabled
                    elements = await self.page.locator(selector).all()
                    for element in elements[:3]:  # Try first 3 visible elements
                        if await element.is_visible() and await element.is_enabled():
                            await element.fill(text, timeout=3000)
                            app_logger.info(f"Successfully filled element with fallback selector: {selector}")
                            return True
                except Exception as e:
                    app_logger.debug(f"Fallback selector {selector} failed: {e}")
            
            app_logger.warning(f"Could not fill element: {target}")
            return False
            
        except Exception as e:
            app_logger.error(f"Smart fill failed: {e}")
            return False
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get comprehensive page information without screenshots"""
        try:
            if not self.page:
                return {}
            
            # Get basic page info
            info = {
                'url': self.page.url,
                'title': await self.page.title(),
                'ready_state': await self.page.evaluate("document.readyState"),
            }
            
            # Get page content summary
            try:
                # Get main headings
                headings = await self.page.locator('h1, h2, h3').all_text_contents()
                info['headings'] = headings[:5]  # Top 5 headings
                
                # Get form information
                forms = await self.page.locator('form').count()
                info['forms_count'] = forms
                
                # Get link count
                links = await self.page.locator('a[href]').count()
                info['links_count'] = links
                
                # Get input fields
                inputs = await self.page.locator('input:not([type="hidden"]), textarea, select').count()
                info['inputs_count'] = inputs
                
                # Check for common elements
                info['has_search'] = await self.page.locator('[type="search"], [placeholder*="search"], [name*="search"]').count() > 0
                info['has_login'] = await self.page.locator('[type="password"], [name*="login"], [name*="username"]').count() > 0
                
            except Exception as e:
                app_logger.debug(f"Error getting page content summary: {e}")
            
            return info
            
        except Exception as e:
            app_logger.error(f"Error getting page info: {e}")
            return {}
    
    async def wait_for_navigation(self, timeout: int = 30000) -> bool:
        """Wait for navigation to complete"""
        try:
            if not self.page:
                return False
            
            await self.page.wait_for_load_state("domcontentloaded", timeout=timeout)
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
            
        except Exception as e:
            app_logger.error(f"Wait for navigation failed: {e}")
            return False
    
    async def take_screenshot(self, task_id: str) -> Optional[str]:
        """Take a screenshot for debugging/monitoring purposes"""
        try:
            # Ensure browser is initialized
            if not self.page or not self.browser:
                app_logger.warning("Browser not available for screenshot, initializing...")
                await self.initialize()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{task_id}_{timestamp}.png"
            screenshot_path = Path(settings.screenshot_path) / filename
            
            await self.page.screenshot(path=screenshot_path, full_page=True)
            app_logger.info(f"Debug screenshot saved: {screenshot_path}")
            
            return str(screenshot_path)
            
        except Exception as e:
            app_logger.error(f"Screenshot failed: {e}")
            # Try to reinitialize and take screenshot
            try:
                await self.initialize()
                if self.page:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{task_id}_{timestamp}.png"
                    screenshot_path = Path(settings.screenshot_path) / filename
                    await self.page.screenshot(path=screenshot_path, full_page=True)
                    app_logger.info(f"Screenshot saved after reinit: {screenshot_path}")
                    return str(screenshot_path)
            except Exception as retry_e:
                app_logger.error(f"Screenshot retry failed: {retry_e}")
            return None
    
    async def scroll_page(self, direction: str = "down", amount: int = 500) -> bool:
        """Scroll the page"""
        try:
            if not self.page:
                return False
            
            if direction == "down":
                await self.page.mouse.wheel(0, amount)
            elif direction == "up":
                await self.page.mouse.wheel(0, -amount)
            
            await asyncio.sleep(1)  # Wait for scroll to complete
            app_logger.info(f"Scrolled {direction} by {amount}px")
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

    async def analyze_page(self) -> Optional[PageAnalysis]:
        """Analyze the current page and extract elements (enhanced version)"""
        try:
            # Ensure browser is initialized
            if not self.page or not self.browser:
                app_logger.warning("Browser not available for analysis, initializing...")
                await self.initialize()
            
            # Get page info
            url = self.page.url
            title = await self.page.title()
            
            # Get interactive elements using our enhanced method
            elements = await self.get_interactive_elements()
            
            # Take screenshot for monitoring (still useful for UI display)
            screenshot_path = await self.take_screenshot("page_analysis")
            
            return PageAnalysis(
                url=url,
                title=title,
                elements=elements,
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            app_logger.error(f"Enhanced page analysis failed: {e}")
            # Try to reinitialize and analyze
            try:
                await self.initialize()
                if self.page:
                    url = self.page.url if self.page else "unknown"
                    title = await self.page.title() if self.page else "unknown"
                    elements = await self.get_interactive_elements()
                    screenshot_path = await self.take_screenshot("page_analysis")
                    
                    return PageAnalysis(
                        url=url,
                        title=title,
                        elements=elements,
                        screenshot_path=screenshot_path
                    )
            except Exception as retry_e:
                app_logger.error(f"Page analysis retry failed: {retry_e}")
            return None

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
            
            app_logger.info("Enhanced browser closed successfully")
            
        except Exception as e:
            app_logger.error(f"Failed to close enhanced browser: {e}")


# Global enhanced browser instance
enhanced_browser_tool = EnhancedBrowserTool()
