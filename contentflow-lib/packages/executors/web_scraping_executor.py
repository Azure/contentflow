"""Web Scraping executor using Playwright for extracting content from web pages."""

import asyncio
import base64
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

try:
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError:
    raise ImportError(
        "playwright is required for web scraping. "
        "Install it with: pip install playwright && playwright install"
    )

from agent_framework import WorkflowContext
from .base import BaseExecutor
from ..models import Content, ContentIdentifier

logger = logging.getLogger(__name__)


class WebScrapingExecutor(BaseExecutor):
    """
    Scrape and extract content from web pages using Playwright.
    
    This executor retrieves web pages, renders JavaScript (optional), and extracts
    content using CSS selectors. It supports basic crawling (following links)
    and rate limiting.
    
    Configuration (settings dict):
        - start_urls (list): List of explicit URLs to start scraping from
          Required: True (unless provided in input)
          Default: None
        - link_patterns (list): List of URL patterns that followed links must match
          Default: None (no filtering if not specified)
          Example: ["https://example.com/blog/*", "https://example.com/article/*"]
        - selectors (dict): Dictionary of field names to CSS/XPath selectors
          Default: {"title": "title", "body": "body"}
        - render_js (bool): Whether to wait for JavaScript rendering (network idle)
          Default: True
        - follow_links (bool): Whether to follow links matching the pattern
          Default: False
        - max_depth (int): Maximum crawl depth
          Default: 1
        - rate_limit (float): Requests per second (approximate)
          Default: 1.0
        - max_pages (int): Maximum number of pages to scrape
          Default: 100
        - wait_for_selector (str): Specific selector to wait for before extracting
          Default: None
        - include_html (bool): Include full HTML in output
            Default: False
        - user_agent (str): Custom User-Agent string
            Default: None
        - screenshot_enabled (bool): Capture page screenshot and include as base64
            Default: False
        - screenshot_full_page (bool): Capture full page (otherwise viewport)
            Default: True
        - screenshot_selector (str): Optional selector to screenshot a specific element
            Default: None
        - screenshot_type (str): Screenshot image type
            Default: "png"
            Options: "png", "jpeg"
        - screenshot_quality (int): Quality (1-100) for JPEG screenshots
            Default: None
        - screenshot_save_to_file (bool): Save screenshots to local files
            Default: False
        - screenshot_output_dir (str): Directory to save screenshots
            Default: "./screenshots"
        - screenshot_filename_template (str): Template for screenshot filenames
            Default: "{timestamp}_{index}.{ext}"
        - output_field (str): Field name for extracted data
            Default: "web_scraping_output"
    
    Example:
        ```yaml
        - id: web_scraper
          type: web_scraping_executor
          settings:
            start_urls:
              - "https://news.ycombinator.com/"
              - "https://news.ycombinator.com/newest"
            link_patterns:
              - "https://news.ycombinator.com/*"
            selectors:
              title: "title"
              items: ".athing .titleline > a"
            follow_links: true
            render_js: true
            rate_limit: 0.5
        ```
    
    Input:
        None (if used as source) OR
        Content item(s) with 'url' field (if used as transformation)
    
    Output:
        List[Content] items with extracted fields in `data`:
        - data['web_scraping_output']['url']: Page URL
        - data['web_scraping_output']['title']: Page title
        - data['web_scraping_output']['extracted_fields']: Dictionary of extracted fields based on selectors
        - data['web_scraping_output']['html']: Full HTML (if include_html is True)
        - data['web_scraping_output']['screenshot_base64']: Base64 encoded screenshot (if enabled)
        - data['web_scraping_output']['screenshot_path']: Path to saved screenshot file (if save_to_file is True)
        - data['web_scraping_output']['timestamp']: Scrape timestamp
        - summary_data['pages_scraped']: Number of pages scraped
        - summary_data['extraction_status']: "success" or error info
    """
    
    def __init__(
        self,
        id: str,
        settings: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        fail_on_error: bool = False,
        debug_mode: bool = False,
        **kwargs
    ):
        super().__init__(
            id=id,
            settings=settings,
            enabled=enabled,
            fail_on_error=fail_on_error,
            debug_mode=debug_mode,
            **kwargs
        )
        
        # URL configuration
        self.start_urls = self.get_setting("start_urls", default=None)
        self.link_patterns = self.get_setting("link_patterns", default=None)
        
        self.selectors = self.get_setting("selectors", default={"title": "title", "body": "body"})
        self.render_js = self.get_setting("render_js", default=True)
        self.follow_links = self.get_setting("follow_links", default=False)
        self.max_depth = self.get_setting("max_depth", default=1)
        self.rate_limit = self.get_setting("rate_limit", default=1.0)
        self.max_pages = self.get_setting("max_pages", default=100)
        self.wait_for_selector = self.get_setting("wait_for_selector")
        self.include_html = self.get_setting("include_html", default=False)
        self.user_agent = self.get_setting("user_agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
        self.screenshot_enabled = self.get_setting("screenshot_enabled", default=False)
        self.screenshot_full_page = self.get_setting("screenshot_full_page", default=True)
        self.screenshot_selector = self.get_setting("screenshot_selector")
        self.screenshot_type = self.get_setting("screenshot_type", default="png")
        self.screenshot_quality = self.get_setting("screenshot_quality")
        self.screenshot_save_to_file = self.get_setting("screenshot_save_to_file", default=False)
        self.screenshot_output_dir = self.get_setting("screenshot_output_dir", default="./screenshots")
        self.screenshot_filename_template = self.get_setting("screenshot_filename_template", default="{timestamp}_{index}.{ext}")
        self.output_field = self.get_setting("output_field", default="web_scraping_output")
        
        # Create screenshot directory if saving to file
        if self.screenshot_save_to_file and self.screenshot_enabled:
            Path(self.screenshot_output_dir).mkdir(parents=True, exist_ok=True)
        
        # Compile regex patterns for link filtering
        self.link_regex_patterns = []
        
        # Use link_patterns if provided
        patterns_to_compile = [pattern.strip() for pattern in self.link_patterns.split(",")] if self.link_patterns else []
        
        for pattern in patterns_to_compile:
            if pattern and "*" in pattern:
                # Convert glob-like pattern to regex
                regex_pattern = re.escape(pattern).replace("\\*", ".*")
                self.link_regex_patterns.append(re.compile(f"^{regex_pattern}$"))
        
        if self.debug_mode:
            logger.debug(f"[{self.id}] Compiled {len(self.link_regex_patterns)} link filter patterns")

    async def process_input(
        self,
        input: Union[Content, List[Content]],
        ctx: WorkflowContext
    ) -> Union[Content, List[Content]]:
        """
        Process input or start scraping from configured URL.
        """
        start_urls = []
        
        # Priority 1: Use explicit start_urls if provided
        if self.start_urls:
            start_urls.extend([url.strip() for url in self.start_urls.split(",")])
        
        # Priority 2: If input is provided, check for URLs
        if input:
            inputs = input if isinstance(input, list) else [input]
            for item in inputs:
                if isinstance(item, Content):
                    url = item.data.get("url") or item.data.get("source_url")
                    if url:
                        start_urls.append(url)
        
        if not start_urls:
            logger.warning(f"[{self.id}] No start URLs found. Configure 'start_urls' or provide input with 'url' field.")
            return []

        # Remove duplicates
        start_urls = list(set(start_urls))
        
        logger.info(f"[{self.id}] Starting scrape with {len(start_urls)} URLs. Max depth: {self.max_depth}, Max pages: {self.max_pages}")
        
        results: List[Content] = []
        visited_urls = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=self.user_agent)
            
            try:
                # Queue for crawling: (url, depth)
                queue = [(url, 0) for url in start_urls]
                
                while queue and len(results) < self.max_pages:
                    url, depth = queue.pop(0)
                    
                    if url in visited_urls:
                        continue
                    
                    visited_urls.add(url)
                    
                    # Check if URL matches link patterns (if patterns are set and URL is not a start URL)
                    if self.link_regex_patterns and url not in start_urls:
                        matches_pattern = any(pattern.match(url) for pattern in self.link_regex_patterns)
                        if not matches_pattern:
                            logger.debug(f"[{self.id}] Skipping {url} (does not match any link pattern)")
                            continue

                    # Rate limiting
                    if self.rate_limit > 0 and len(visited_urls) > 1:
                        await asyncio.sleep(1.0 / self.rate_limit)
                    
                    try:
                        page_content = await self._scrape_page(context, url, len(results))
                        
                        if page_content:
                            # Create Content object following doc intelligence pattern
                            content_item = Content(
                                id=ContentIdentifier(
                                    canonical_id=url,
                                    unique_id=self.generate_sha1_hash(f"{url}-{datetime.now(timezone.utc).isoformat()}"),
                                    source_name="web_scraper",
                                    source_type="webpage",
                                ),
                                data={}
                            )
                            
                            # Build output data structure
                            output_data = {
                                "url": url,
                                "title": page_content.get("title"),
                                "links": page_content.get("links"),
                                "extracted_fields": page_content.get("data"),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            
                            if self.include_html:
                                output_data["html"] = page_content.get("html")
                            
                            if self.screenshot_enabled:
                                if page_content.get("screenshot_base64"):
                                    output_data["screenshot_base64"] = page_content.get("screenshot_base64")
                                if page_content.get("screenshot_path"):
                                    output_data["screenshot_path"] = page_content.get("screenshot_path")
                            
                            # Store in output field
                            content_item.data[self.output_field] = output_data
                            
                            # Update summary data
                            content_item.summary_data['extraction_status'] = "success"
                            content_item.summary_data['url'] = url
                                
                            results.append(content_item)
                            
                            # Follow links
                            if self.follow_links and depth < self.max_depth:
                                links = page_content.get("links", [])
                                for link in links:
                                    if link not in visited_urls:
                                        queue.append((link, depth + 1))
                                        
                    except Exception as e:
                        logger.error(f"[{self.id}] Error scraping {url}: {str(e)}")
                        if self.fail_on_error:
                            raise e
            
            finally:
                await context.close()
                await browser.close()
        
        # Update summary for all results
        if results:
            for content in results:
                content.summary_data['pages_scraped'] = len(results)
                
        return results

    async def _scrape_page(self, context: BrowserContext, url: str, index: int) -> Optional[Dict[str, Any]]:
        """Scrape a single page."""
        page = await context.new_page()
        try:
            logger.debug(f"[{self.id}] Navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded")
            
            if self.wait_for_selector:
                try:
                    await page.wait_for_selector(self.wait_for_selector, timeout=10000)
                except Exception:
                    logger.warning(f"[{self.id}] Timeout waiting for selector {self.wait_for_selector} on {url}")

            # Extract data based on selectors
            extracted_data = {}
            for field, selector in self.selectors.items():
                try:
                    # Try to get multiple elements if it looks like a list selector?
                    # For now, just get text content or attribute
                    # Simple heuristic: if selector ends with @attr, get attribute
                    attr = None
                    clean_selector = selector
                    if "@" in selector:
                        parts = selector.rsplit("@", 1)
                        if len(parts) == 2:
                            clean_selector = parts[0].strip()
                            attr = parts[1].strip()
                    
                    if clean_selector:
                        element = page.locator(clean_selector).first
                        if await element.count() > 0:
                            if attr:
                                value = await element.get_attribute(attr)
                            else:
                                value = await element.text_content()
                            extracted_data[field] = value.strip() if value else None
                    else:
                        # If selector was just @attr (e.g. on body?), unlikely but possible
                        pass
                        
                except Exception as e:
                    logger.warning(f"[{self.id}] Failed to extract field '{field}' with selector '{selector}': {e}")
                    extracted_data[field] = None

            # Extract title
            title = await page.title()
            
            # Extract HTML if needed
            html = await page.content() if self.include_html else None

            screenshot_base64 = None
            screenshot_path = None
            if self.screenshot_enabled:
                screenshot_result = await self._capture_screenshot(page, url, index)
                if screenshot_result:
                    screenshot_base64 = screenshot_result.get("base64")
                    screenshot_path = screenshot_result.get("path")
            
            # Extract links for crawling
            links = []
            if self.follow_links:
                hrefs = await page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
                # loop through hrefs and handle relative links
                for href in hrefs:
                    if href.startswith("http"):
                        links.append(href)
                    elif href.startswith("/"):
                        # Handle relative links
                        base_url = re.match(r"(https?://[^/]+)", url)
                        if base_url:
                            full_url = base_url.group(1) + href
                            links.append(full_url)

            return {
                "title": title,
                "data": extracted_data,
                "html": html,
                "links": links,
                "screenshot_base64": screenshot_base64,
                "screenshot_path": screenshot_path,
            }
            
        except Exception as e:
            logger.error(f"[{self.id}] Failed to process page {url}: {e}")
            raise e
        finally:
            await page.close()

    async def _capture_screenshot(self, page: Page, url: str, index: int) -> Optional[Dict[str, str]]:
        """Capture a screenshot and return it as base64 string and/or save to file."""
        try:
            shot_bytes = None
            
            if self.screenshot_selector:
                locator = page.locator(self.screenshot_selector).first
                if await locator.count() == 0:
                    logger.warning(f"[{self.id}] Screenshot selector not found: {self.screenshot_selector}")
                    return None
                shot_bytes = await locator.screenshot(
                    type=self.screenshot_type,
                    quality=self.screenshot_quality if self.screenshot_type == "jpeg" else None,
                )
            else:
                shot_bytes = await page.screenshot(
                    full_page=self.screenshot_full_page,
                    type=self.screenshot_type,
                    quality=self.screenshot_quality if self.screenshot_type == "jpeg" else None,
                )
            
            if not shot_bytes:
                return None
            
            result = {}
            
            # Always generate base64 if not saving to file, or if explicitly requested
            if not self.screenshot_save_to_file:
                result["base64"] = base64.b64encode(shot_bytes).decode("utf-8")
            
            # Save to file if requested
            if self.screenshot_save_to_file:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                ext = self.screenshot_type
                
                filename = self.screenshot_filename_template.format(
                    timestamp=timestamp,
                    index=index,
                    ext=ext,
                    url=url.replace("://", "_").replace("/", "_")[:50]  # Safe URL in filename
                )
                
                filepath = os.path.join(self.screenshot_output_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(shot_bytes)
                
                result["path"] = filepath
                
                if self.debug_mode:
                    logger.debug(f"[{self.id}] Screenshot saved to {filepath}")
                
                # Optionally also include base64 if user wants both
                # For now, only save to file to save memory
            
            return result
            
        except Exception as e:
            logger.warning(f"[{self.id}] Failed to capture screenshot: {e}")
            return None
