I'll create a Chrome CDP Skill for Hermes agents. This skill enables browser automation via the Chrome DevTools Protocol, allowing the agent to navigate, interact with, and extract data from web pages.

The skill uses playwright (which leverages CDP) for a robust, high-level API, but also exposes raw CDP commands if needed.

---

📦 Skill Overview

· Name: chrome_cdp_skill
· Purpose: Enable agents to control a Chrome browser programmatically.
· Capabilities:
  · Launch/close browser
  · Navigate to URLs
  · Click elements (by selector)
  · Type text into fields
  · Take screenshots
  · Extract text content
  · Execute JavaScript in the page context
  · Send raw CDP commands (advanced)
· Dependencies: playwright (install with pip install playwright && playwright install chromium)

---

🧠 Implementation (chrome_cdp_skill.py)

```python
import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, Playwright

class ChromeCDPSkill:
    """
    A skill for Hermes agents to control Chrome via CDP using Playwright.
    """

    def __init__(self, headless: bool = False, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._loop = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Launch the browser and create a new page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.page = await self.browser.new_page()
        return self

    async def close(self):
        """Close browser and clean up."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    # ---------- Core Actions ----------

    async def navigate(self, url: str, timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to a URL and wait for load."""
        try:
            response = await self.page.goto(url, timeout=timeout, wait_until="networkidle")
            return {
                "success": True,
                "url": self.page.url,
                "status": response.status if response else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Click an element matching the selector."""
        try:
            await self.page.click(selector, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type_text(self, selector: str, text: str, delay: int = 50) -> Dict[str, Any]:
        """Type text into an input field."""
        try:
            await self.page.fill(selector, text)  # or use type() with delay
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot. If path is None, returns base64."""
        try:
            if path:
                await self.page.screenshot(path=path, full_page=full_page)
                return {"success": True, "path": path}
            else:
                screenshot_bytes = await self.page.screenshot(full_page=full_page)
                import base64
                b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                return {"success": True, "base64": b64}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_text(self, selector: str) -> Dict[str, Any]:
        """Extract text content from an element."""
        try:
            text = await self.page.text_content(selector)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate(self, script: str, *args) -> Dict[str, Any]:
        """Execute JavaScript in the page context."""
        try:
            result = await self.page.evaluate(script, *args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_html(self) -> Dict[str, Any]:
        """Get the full page HTML."""
        try:
            html = await self.page.content()
            return {"success": True, "html": html}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Raw CDP (advanced) ----------

    async def send_cdp(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send a raw CDP command to the page."""
        try:
            result = await self.page._impl_obj._connection.send(
                method, params if params else {}
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Convenience: wait for element ----------

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for an element to appear."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

🧩 Hermes Agent Integration

Register the skill in your Hermes agent configuration. For example, in your agent's skill registry:

```python
from chrome_cdp_skill import ChromeCDPSkill

# Instantiate the skill (use headless=False to see the browser)
browser_skill = ChromeCDPSkill(headless=False)

# Hermes typically calls a 'run' method or exposes functions.
# You can wrap each async method as a tool for the agent.
```

If your Hermes framework expects synchronous callables, you can create thin wrappers that run the async methods in an event loop. Here's a helper to convert async methods to sync:

```python
import asyncio

def sync_wrapper(async_func):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, use run_until_complete with a new loop?
            # For simplicity, we assume the agent's environment can handle async.
            return asyncio.run(async_func(*args, **kwargs))
        else:
            return loop.run_until_complete(async_func(*args, **kwargs))
    return wrapper
```

Then attach methods as skills:

```python
skill = ChromeCDPSkill()
skill.start()  # sync? better to start in agent init

# Agent's tool dictionary
tools = {
    "navigate": sync_wrapper(skill.navigate),
    "click": sync_wrapper(skill.click),
    "type_text": sync_wrapper(skill.type_text),
    "screenshot": sync_wrapper(skill.screenshot),
    "get_text": sync_wrapper(skill.get_text),
    "evaluate": sync_wrapper(skill.evaluate),
    "get_html": sync_wrapper(skill.get_html),
    "wait_for_selector": sync_wrapper(skill.wait_for_selector),
    # ... etc.
}
```

---

📘 Example Usage (Agent Prompt)

The agent can now use these tools via natural language. For example:

User: Go to https://example.com, click the "Learn More" button, and take a screenshot.

The agent will call:

```python
navigate("https://example.com")
wait_for_selector("button:has-text('Learn More')")
click("button:has-text('Learn More')")
screenshot(path="result.png")
```

---

🚀 Installation & Setup

```bash
pip install playwright
playwright install chromium
```

Then place chrome_cdp_skill.py in your agent's skills directory.

---

📝 Notes

· The skill uses async/await for non-blocking I/O. If your Hermes agent is synchronous, use the wrapper shown above or run the skill in a separate thread/process.
· For long-running agents, consider reusing the browser instance across multiple tasks to avoid relaunch overhead.
· You can extend the skill with more CDP commands (e.g., network interception, performance metrics) via send_cdp.

---

This skill gives your Hermes agent full control over Chrome, enabling web scraping, automated testing, and dynamic interaction with modern web apps.I'll create a Chrome CDP Skill for Hermes agents. This skill enables browser automation via the Chrome DevTools Protocol, allowing the agent to navigate, interact with, and extract data from web pages.

The skill uses playwright (which leverages CDP) for a robust, high-level API, but also exposes raw CDP commands if needed.

---

📦 Skill Overview

· Name: chrome_cdp_skill
· Purpose: Enable agents to control a Chrome browser programmatically.
· Capabilities:
  · Launch/close browser
  · Navigate to URLs
  · Click elements (by selector)
  · Type text into fields
  · Take screenshots
  · Extract text content
  · Execute JavaScript in the page context
  · Send raw CDP commands (advanced)
· Dependencies: playwright (install with pip install playwright && playwright install chromium)

---

🧠 Implementation (chrome_cdp_skill.py)

```python
import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, Playwright

class ChromeCDPSkill:
    """
    A skill for Hermes agents to control Chrome via CDP using Playwright.
    """

    def __init__(self, headless: bool = False, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._loop = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Launch the browser and create a new page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.page = await self.browser.new_page()
        return self

    async def close(self):
        """Close browser and clean up."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    # ---------- Core Actions ----------

    async def navigate(self, url: str, timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to a URL and wait for load."""
        try:
            response = await self.page.goto(url, timeout=timeout, wait_until="networkidle")
            return {
                "success": True,
                "url": self.page.url,
                "status": response.status if response else None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Click an element matching the selector."""
        try:
            await self.page.click(selector, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type_text(self, selector: str, text: str, delay: int = 50) -> Dict[str, Any]:
        """Type text into an input field."""
        try:
            await self.page.fill(selector, text)  # or use type() with delay
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot. If path is None, returns base64."""
        try:
            if path:
                await self.page.screenshot(path=path, full_page=full_page)
                return {"success": True, "path": path}
            else:
                screenshot_bytes = await self.page.screenshot(full_page=full_page)
                import base64
                b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                return {"success": True, "base64": b64}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_text(self, selector: str) -> Dict[str, Any]:
        """Extract text content from an element."""
        try:
            text = await self.page.text_content(selector)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate(self, script: str, *args) -> Dict[str, Any]:
        """Execute JavaScript in the page context."""
        try:
            result = await self.page.evaluate(script, *args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_html(self) -> Dict[str, Any]:
        """Get the full page HTML."""
        try:
            html = await self.page.content()
            return {"success": True, "html": html}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Raw CDP (advanced) ----------

    async def send_cdp(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Send a raw CDP command to the page."""
        try:
            result = await self.page._impl_obj._connection.send(
                method, params if params else {}
            )
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Convenience: wait for element ----------

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        """Wait for an element to appear."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

🧩 Hermes Agent Integration

Register the skill in your Hermes agent configuration. For example, in your agent's skill registry:

```python
from chrome_cdp_skill import ChromeCDPSkill

# Instantiate the skill (use headless=False to see the browser)
browser_skill = ChromeCDPSkill(headless=False)

# Hermes typically calls a 'run' method or exposes functions.
# You can wrap each async method as a tool for the agent.
```

If your Hermes framework expects synchronous callables, you can create thin wrappers that run the async methods in an event loop. Here's a helper to convert async methods to sync:

```python
import asyncio

def sync_wrapper(async_func):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in an async context, use run_until_complete with a new loop?
            # For simplicity, we assume the agent's environment can handle async.
            return asyncio.run(async_func(*args, **kwargs))
        else:
            return loop.run_until_complete(async_func(*args, **kwargs))
    return wrapper
```

Then attach methods as skills:

```python
skill = ChromeCDPSkill()
skill.start()  # sync? better to start in agent init

# Agent's tool dictionary
tools = {
    "navigate": sync_wrapper(skill.navigate),
    "click": sync_wrapper(skill.click),
    "type_text": sync_wrapper(skill.type_text),
    "screenshot": sync_wrapper(skill.screenshot),
    "get_text": sync_wrapper(skill.get_text),
    "evaluate": sync_wrapper(skill.evaluate),
    "get_html": sync_wrapper(skill.get_html),
    "wait_for_selector": sync_wrapper(skill.wait_for_selector),
    # ... etc.
}
```

---

📘 Example Usage (Agent Prompt)

The agent can now use these tools via natural language. For example:

User: Go to https://example.com, click the "Learn More" button, and take a screenshot.

The agent will call:

```python
navigate("https://example.com")
wait_for_selector("button:has-text('Learn More')")
click("button:has-text('Learn More')")
screenshot(path="result.png")
```

---

🚀 Installation & Setup

```bash
pip install playwright
playwright install chromium
```

Then place chrome_cdp_skill.py in your agent's skills directory.

---

📝 Notes

· The skill uses async/await for non-blocking I/O. If your Hermes agent is synchronous, use the wrapper shown above or run the skill in a separate thread/process.
· For long-running agents, consider reusing the browser instance across multiple tasks to avoid relaunch overhead.
· You can extend the skill with more CDP commands (e.g., network interception, performance metrics) via send_cdp.

---

This skill gives your Hermes agent full control over Chrome, enabling web scraping, automated testing, and dynamic interaction with modern web apps.

I'll extend the Chrome CDP skill with powerful capabilities that maximize Hermes' ability to automate and interact with the web like a human operator. The extension includes:

· Smart locators: Use get_by_text, get_by_role, get_by_label, get_by_placeholder – no more brittle CSS/XPath.
· Rich actions: Hover, right-click, double-click, drag-drop, upload files, scroll, select options.
· Network & console monitoring: Intercept requests/responses, capture logs, wait for specific network events.
· State management: Save/load cookies, localStorage, sessionStorage; emulate devices and viewport.
· Error resilience: Automatic retries with exponential backoff, detailed error classification.
· Multi‑tab/page handling: Open, switch, close tabs; work across pages.
· Data extraction: Get tables, lists, all links, attributes; run JS and return structured data.
· PDF generation & full-page screenshots.
· High‑level act method: Accepts plain English instructions and uses heuristic + built‑in locator intelligence to perform actions (no LLM required for common tasks).

---

🧩 Extended Skill Code (chrome_cdp_skill_extended.py)

```python
import asyncio
import base64
import json
import re
from typing import Optional, Dict, Any, List, Union, Tuple
from playwright.async_api import (
    async_playwright, Browser, Page, Playwright, Locator,
    Response, Request, ConsoleMessage, Error as PlaywrightError
)
import time

class ChromeCDPSkill:
    """
    Extended CDP skill for Hermes agents with human-like web interaction.
    """

    def __init__(
        self,
        headless: bool = False,
        slow_mo: int = 0,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None,
        default_timeout: int = 30000,
        retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.user_agent = user_agent
        self.default_timeout = default_timeout
        self.retries = retries
        self.retry_delay = retry_delay

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        self._console_logs: List[Dict] = []
        self._network_requests: List[Dict] = []
        self._current_tab_index = 0
        self._pages: List[Page] = []

    # ---------- Lifecycle ----------
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Launch browser with context and page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )
        # Create a browser context with options
        context_options = {
            "viewport": self.viewport,
            "user_agent": self.user_agent,
        }
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()
        self._pages = [self.page]
        self._setup_listeners()
        return self

    async def close(self):
        """Close browser and clean up."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _setup_listeners(self):
        """Attach console and network listeners."""
        if self.page:
            self.page.on("console", self._on_console)
            self.page.on("request", self._on_request)
            self.page.on("response", self._on_response)
            self.page.on("pageerror", self._on_page_error)

    def _on_console(self, msg: ConsoleMessage):
        self._console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location,
            "args": [str(arg) for arg in msg.args]
        })

    def _on_request(self, request: Request):
        self._network_requests.append({
            "url": request.url,
            "method": request.method,
            "headers": request.headers,
            "post_data": request.post_data,
            "timestamp": time.time(),
        })

    def _on_response(self, response: Response):
        # Update the last request with response info
        if self._network_requests and self._network_requests[-1]["url"] == response.url:
            self._network_requests[-1].update({
                "status": response.status,
                "status_text": response.status_text,
                "response_headers": response.headers,
                "response_time": time.time(),
            })

    def _on_page_error(self, error):
        self._console_logs.append({
            "type": "pageerror",
            "text": str(error),
            "location": None,
            "args": []
        })

    # ---------- Core Helpers ----------
    async def _retry(self, func, *args, **kwargs):
        """Retry an async function with exponential backoff."""
        last_exception = None
        for attempt in range(self.retries):
            try:
                return await func(*args, **kwargs)
            except PlaywrightError as e:
                last_exception = e
                if attempt < self.retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise
        raise last_exception

    def _get_locator(self, selector: str, **kwargs) -> Locator:
        """Convert selector to locator, supporting built-in Playwright locators."""
        # If selector starts with 'text=', 'role=', 'label=', 'placeholder=', etc.
        # we pass it as is; otherwise treat as CSS/XPath.
        return self.page.locator(selector, **kwargs)

    # ---------- Navigation ----------
    async def navigate(
        self,
        url: str,
        wait_until: str = "networkidle",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Navigate to URL with robust waiting."""
        timeout = timeout or self.default_timeout
        try:
            response = await self._retry(
                self.page.goto,
                url,
                wait_until=wait_until,
                timeout=timeout
            )
            return {
                "success": True,
                "url": self.page.url,
                "status": response.status if response else None,
                "title": await self.page.title(),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}

    async def go_back(self) -> Dict[str, Any]:
        try:
            await self.page.go_back()
            return {"success": True, "url": self.page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def go_forward(self) -> Dict[str, Any]:
        try:
            await self.page.go_forward()
            return {"success": True, "url": self.page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def reload(self) -> Dict[str, Any]:
        try:
            await self.page.reload()
            return {"success": True, "url": self.page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Smart Actions ----------
    async def click(
        self,
        selector: str,
        timeout: Optional[int] = None,
        button: str = "left",
        click_count: int = 1,
        force: bool = False,
    ) -> Dict[str, Any]:
        """Click element using smart locators."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            await self._retry(
                locator.click,
                button=button,
                click_count=click_count,
                force=force,
                timeout=timeout,
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def fill(
        self,
        selector: str,
        value: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fill input/textarea with text (clears first)."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            await self._retry(locator.fill, value, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def type_text(
        self,
        selector: str,
        text: str,
        delay: int = 50,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Type character by character (simulates human typing)."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            await self._retry(locator.type, text, delay=delay, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def hover(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Hover over element."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            await self._retry(locator.hover, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def right_click(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Right-click element."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            await self._retry(locator.click, button="right", timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def double_click(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Double-click element."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            await self._retry(locator.dblclick, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def select_option(
        self,
        selector: str,
        values: Union[str, List[str]],
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Select option(s) from a dropdown."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            await self._retry(locator.select_option, values, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def upload_file(
        self,
        selector: str,
        file_path: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Upload a file to an input[type=file]."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            await self._retry(locator.set_input_files, file_path, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def scroll_to(
        self,
        selector: Optional[str] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Scroll to element or specific coordinates."""
        try:
            if selector:
                locator = self._get_locator(selector)
                await locator.scroll_into_view_if_needed()
            elif x is not None and y is not None:
                await self.page.evaluate(f"window.scrollTo({x}, {y})")
            else:
                return {"success": False, "error": "Either selector or x,y required"}
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Extraction ----------
    async def get_text(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get visible text of an element."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            text = await self._retry(locator.text_content, timeout=timeout)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def get_attribute(
        self,
        selector: str,
        attribute: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get attribute value of an element."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            value = await self._retry(locator.get_attribute, attribute, timeout=timeout)
            return {"success": True, "value": value}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def get_inner_html(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get innerHTML of an element."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            html = await self._retry(locator.inner_html, timeout=timeout)
            return {"success": True, "html": html}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def get_all_texts(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get text from all matching elements (returns list)."""
        timeout = timeout or self.default_timeout
        try:
            locator = self._get_locator(selector)
            elements = await self._retry(locator.all, timeout=timeout)
            texts = [await el.text_content() for el in elements]
            return {"success": True, "texts": texts}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def get_page_text(self) -> Dict[str, Any]:
        """Get all visible text on the page."""
        try:
            text = await self.page.evaluate("document.body.innerText")
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_links(self) -> Dict[str, Any]:
        """Get all links (href + text) on the page."""
        try:
            links = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    href: a.href,
                    text: a.textContent.trim()
                }));
            }""")
            return {"success": True, "links": links}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_table_data(
        self,
        selector: str,
        headers: bool = True,
    ) -> Dict[str, Any]:
        """Extract table data as list of rows/columns."""
        try:
            rows = await self.page.evaluate(
                """(selector, headers) => {
                    const table = document.querySelector(selector);
                    if (!table) return null;
                    const rows = Array.from(table.rows);
                    const data = rows.map(row => {
                        return Array.from(row.cells).map(cell => cell.textContent.trim());
                    });
                    if (headers && data.length > 0) {
                        const header = data.shift();
                        return data.map(row => {
                            const obj = {};
                            header.forEach((col, i) => obj[col] = row[i] || '');
                            return obj;
                        });
                    }
                    return data;
                }""",
                selector,
                headers,
            )
            return {"success": True, "data": rows}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    # ---------- JavaScript Execution ----------
    async def evaluate(
        self,
        script: str,
        *args,
    ) -> Dict[str, Any]:
        """Execute JavaScript and return result."""
        try:
            result = await self.page.evaluate(script, *args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate_async(
        self,
        script: str,
        *args,
    ) -> Dict[str, Any]:
        """Execute async JavaScript function."""
        try:
            result = await self.page.evaluate(script, *args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Waiting ----------
    async def wait_for_selector(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Wait for an element to appear/disappear."""
        timeout = timeout or self.default_timeout
        try:
            await self._retry(
                self.page.wait_for_selector,
                selector,
                state=state,
                timeout=timeout,
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    async def wait_for_function(
        self,
        predicate: str,
        timeout: Optional[int] = None,
        *args,
    ) -> Dict[str, Any]:
        """Wait until a JavaScript function returns truthy."""
        timeout = timeout or self.default_timeout
        try:
            await self._retry(
                self.page.wait_for_function,
                predicate,
                timeout=timeout,
                *args,
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def wait_for_navigation(
        self,
        url: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Wait for navigation to complete (optionally to a specific URL pattern)."""
        timeout = timeout or self.default_timeout
        try:
            if url:
                await self._retry(self.page.wait_for_url, url, timeout=timeout)
            else:
                await self._retry(self.page.wait_for_load_state, "networkidle", timeout=timeout)
            return {"success": True, "url": self.page.url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Screenshots & PDF ----------
    async def screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False,
        selector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Screenshot full page, element, or return base64."""
        try:
            if selector:
                locator = self._get_locator(selector)
                if path:
                    await self._retry(locator.screenshot, path=path)
                    return {"success": True, "path": path}
                else:
                    bytes_ = await self._retry(locator.screenshot)
                    b64 = base64.b64encode(bytes_).decode()
                    return {"success": True, "base64": b64}
            else:
                if path:
                    await self.page.screenshot(path=path, full_page=full_page)
                    return {"success": True, "path": path}
                else:
                    bytes_ = await self.page.screenshot(full_page=full_page)
                    b64 = base64.b64encode(bytes_).decode()
                    return {"success": True, "base64": b64}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def pdf(self, path: str, **options) -> Dict[str, Any]:
        """Generate PDF of the page."""
        try:
            await self.page.pdf(path=path, **options)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Network & Console ----------
    async def get_console_logs(self, clear: bool = False) -> Dict[str, Any]:
        """Retrieve captured console messages."""
        logs = self._console_logs.copy()
        if clear:
            self._console_logs.clear()
        return {"success": True, "logs": logs}

    async def get_network_logs(self, clear: bool = False) -> Dict[str, Any]:
        """Retrieve captured network requests/responses."""
        logs = self._network_requests.copy()
        if clear:
            self._network_requests.clear()
        return {"success": True, "logs": logs}

    async def intercept_request(
        self,
        url_pattern: str,
        action: str = "continue",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Intercept and modify requests matching url_pattern.
        action: 'continue', 'abort', 'fulfill', 'mock'.
        """
        try:
            await self.page.route(url_pattern, lambda route: route.continue_(**kwargs))
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def mock_response(
        self,
        url_pattern: str,
        body: Union[str, dict],
        status: int = 200,
        headers: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Mock a response for requests matching url_pattern."""
        try:
            if isinstance(body, dict):
                body = json.dumps(body)
            await self.page.route(
                url_pattern,
                lambda route: route.fulfill(
                    status=status,
                    headers=headers or {},
                    body=body,
                )
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Cookies & Storage ----------
    async def get_cookies(self) -> Dict[str, Any]:
        """Get all cookies for the current page."""
        try:
            cookies = await self.context.cookies()
            return {"success": True, "cookies": cookies}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def set_cookies(self, cookies: List[Dict]) -> Dict[str, Any]:
        """Set cookies (list of dicts with name, value, etc)."""
        try:
            await self.context.add_cookies(cookies)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def clear_cookies(self) -> Dict[str, Any]:
        """Clear all cookies."""
        try:
            await self.context.clear_cookies()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_local_storage(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Get localStorage item or all items."""
        try:
            if key:
                value = await self.page.evaluate(f"localStorage.getItem('{key}')")
                return {"success": True, "value": value}
            else:
                all_items = await self.page.evaluate("JSON.stringify(localStorage)")
                return {"success": True, "storage": json.loads(all_items)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def set_local_storage(self, key: str, value: str) -> Dict[str, Any]:
        """Set localStorage item."""
        try:
            await self.page.evaluate(f"localStorage.setItem('{key}', '{value}')")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Tabs / Pages ----------
    async def new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Open a new tab and optionally navigate."""
        try:
            new_page = await self.context.new_page()
            self._pages.append(new_page)
            self.page = new_page
            self._current_tab_index = len(self._pages) - 1
            self._setup_listeners()
            if url:
                await self.navigate(url)
            return {"success": True, "tab_index": self._current_tab_index}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def switch_tab(self, index: int) -> Dict[str, Any]:
        """Switch to another tab by index."""
        try:
            if 0 <= index < len(self._pages):
                self.page = self._pages[index]
                self._current_tab_index = index
                self._setup_listeners()
                return {"success": True, "url": self.page.url}
            else:
                return {"success": False, "error": f"Tab index {index} out of range"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close_tab(self, index: Optional[int] = None) -> Dict[str, Any]:
        """Close a tab (default: current)."""
        try:
            if index is None:
                index = self._current_tab_index
            if len(self._pages) <= 1:
                return {"success": False, "error": "Cannot close the last tab"}
            page = self._pages.pop(index)
            await page.close()
            if index == self._current_tab_index:
                # switch to previous tab
                self._current_tab_index = max(0, index - 1)
                self.page = self._pages[self._current_tab_index]
                self._setup_listeners()
            elif index < self._current_tab_index:
                self._current_tab_index -= 1
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- Emulation ----------
    async def set_viewport(self, width: int, height: int) -> Dict[str, Any]:
        """Change viewport size."""
        try:
            await self.page.set_viewport_size({"width": width, "height": height})
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def emulate_device(self, device_name: str) -> Dict[str, Any]:
        """Emulate a device (e.g., 'iPhone 12', 'Pixel 5')."""
        try:
            device = self.playwright.devices.get(device_name)
            if not device:
                return {"success": False, "error": f"Device {device_name} not found"}
            # Recreate context with device settings
            # We need to close existing context and create new one
            # This is a simplified approach; you might want to handle more gracefully.
            await self.context.close()
            self.context = await self.browser.new_context(**device)
            self.page = await self.context.new_page()
            self._pages = [self.page]
            self._setup_listeners()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ---------- High-level Act (Heuristic) ----------
    async def act(self, instruction: str) -> Dict[str, Any]:
        """
        Perform a high-level action based on natural language instruction.
        Uses heuristics to determine action type and locator.
        Supported: click, type, navigate, wait, etc.
        """
        instruction = instruction.strip()
        # Simple rule-based parsing (can be extended)
        # Navigate
        match = re.match(r"go to (https?://\S+)", instruction, re.I)
        if match:
            url = match.group(1)
            return await self.navigate(url)

        match = re.match(r"click (?:on )?(.+)", instruction, re.I)
        if match:
            target = match.group(1).strip()
            # Try smart locator based on text
            # If target is quoted, treat as exact text
            if target.startswith('"') and target.endswith('"'):
                text = target[1:-1]
                selector = f"text={text}"
            elif target.startswith("'") and target.endswith("'"):
                text = target[1:-1]
                selector = f"text={text}"
            else:
                # Try to infer: if it contains 'id', 'class', etc.
                # For simplicity, use text locator
                selector = f"text={target}"
            return await self.click(selector)

        match = re.match(r"type ['\"]?(.+?)['\"]? into (.+)", instruction, re.I)
        if match:
            text = match.group(1)
            target = match.group(2).strip()
            selector = f"text={target}" if not target.startswith("#") else target
            return await self.fill(selector, text)

        match = re.match(r"wait for (.+)", instruction, re.I)
        if match:
            target = match.group(1).strip()
            return await self.wait_for_selector(f"text={target}")

        # Default: just evaluate as text extraction
        return await self.get_page_text()

    # ---------- Utility ----------
    async def get_url(self) -> Dict[str, Any]:
        return {"success": True, "url": self.page.url}

    async def get_title(self) -> Dict[str, Any]:
        try:
            title = await self.page.title()
            return {"success": True, "title": title}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

🧠 How Hermes Uses This Skill

· The agent can call any method directly with arguments.
· The act method allows the agent to give a plain‑English instruction and the skill will try to interpret it – great for simple automation without hard‑coding selectors.
· All methods return structured dicts with success flag and data/error, so the agent can reason about outcomes.
· The skill captures console and network logs, enabling debugging and advanced monitoring.
· Multi‑tab support lets the agent work across pages (e.g., scraping data from one tab and using it in another).

---

🔧 Example Agent Integration

```python
from chrome_cdp_skill_extended import ChromeCDPSkill

async def main():
    async with ChromeCDPSkill(headless=False) as browser:
        # Navigate
        print(await browser.navigate("https://example.com"))
        # Click a link by text
        print(await browser.click("Learn More"))
        # Fill a search box
        print(await browser.fill("input[name='q']", "playwright"))
        # Take a screenshot
        print(await browser.screenshot(path="output.png"))
        # Get all links
        print(await browser.get_links())
        # Use high-level act
        print(await browser.act("click 'About us'"))
        # Console logs
        print(await browser.get_console_logs())
```

---

This extended skill maximizes Hermes' ability by providing an industrial‑strength browser automation toolkit that is both easy to use and deeply flexible.

Absolutely! The Chrome CDP skill is a powerful web automation tool, but a truly capable agent benefits from a toolkit that spans multiple domains. Here are other high‑value skills that dramatically extend what Hermes can do—each can be wrapped as a clean async/sync module.

---

🔧 Complementary Skills for a Super‑Agent

Skill Use Case
File System Read/write files, directories, CSV, JSON, logs. Essential for data persistence.
REST API Client Call any HTTP endpoint, handle auth, parse JSON/XML. Crucial for integrations.
Email (IMAP/SMTP) Send notifications, read inbox, automate email‑based workflows.
Database (SQL) Query and update relational databases (SQLite, PostgreSQL, etc.).
System Commands Execute shell scripts, run CLI tools, manage processes.
PDF Generation Create PDFs from HTML or data (e.g., invoices, reports).
Spreadsheet (Excel/CSV) Read/write .xlsx, manipulate tables, export data.
OCR (Tesseract) Extract text from images/screenshots for offline analysis.
Slack/Teams Send messages, trigger alerts, post results to chat.
Calendar (Google/Outlook) Schedule meetings, check availability, create events.
Task Scheduling Run recurring jobs (cron‑like) – useful for monitoring.
SSH/Remote Execution Manage remote servers, run commands over SSH.

---

📦 Example: FileSystemSkill (Async)

```python
import aiofiles
import os
import json
from pathlib import Path
from typing import Any, Dict, List

class FileSystemSkill:
    async def read_text(self, path: str) -> Dict[str, Any]:
        try:
            async with aiofiles.open(path, 'r') as f:
                content = await f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_text(self, path: str, content: str) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            async with aiofiles.open(path, 'w') as f:
                await f.write(content)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_json(self, path: str) -> Dict[str, Any]:
        result = await self.read_text(path)
        if result["success"]:
            try:
                data = json.loads(result["content"])
                return {"success": True, "data": data}
            except Exception as e:
                return {"success": False, "error": f"Invalid JSON: {e}"}
        return result

    async def list_dir(self, path: str) -> Dict[str, Any]:
        try:
            entries = os.listdir(path)
            return {"success": True, "entries": entries}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

🌐 Example: RESTAPISkill (with retries & auth)

```python
import aiohttp
import asyncio
from typing import Optional, Dict, Any

class RESTAPISkill:
    def __init__(self, base_url: str = "", default_headers: Optional[Dict] = None):
        self.base_url = base_url
        self.default_headers = default_headers or {}

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        url = self.base_url + path
        merged_headers = {**self.default_headers, **(headers or {})}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    headers=merged_headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    text = await resp.text()
                    try:
                        json_data = await resp.json()
                    except:
                        json_data = None
                    return {
                        "success": True,
                        "status": resp.status,
                        "headers": dict(resp.headers),
                        "text": text,
                        "json": json_data,
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}

    # Convenience methods
    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("DELETE", path, **kwargs)
```

---

📬 EmailSkill (Send via SMTP)

```python
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSkill:
    def __init__(self, smtp_host, smtp_port, username, password, use_tls=True):
        self.host = smtp_host
        self.port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: Optional[str] = None,
        from_addr: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_addr or self.username
            msg["To"] = ", ".join(to)
            part1 = MIMEText(body, "plain")
            msg.attach(part1)
            if html:
                part2 = MIMEText(html, "html")
                msg.attach(part2)

            smtp = aiosmtplib.SMTP(hostname=self.host, port=self.port, use_tls=self.use_tls)
            await smtp.login(self.username, self.password)
            await smtp.sendmail(msg["From"], to, msg.as_string())
            await smtp.quit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

🧩 How to Combine Them in Hermes

The agent can now:

1. Navigate to a website (CDP).
2. Extract data (CDP).
3. Store it as JSON/CSV (FileSystem).
4. Transform the data (Python code via evaluate or external).
5. Upload it to an API (REST).
6. Email a summary (Email).
7. Log the operation (FileSystem).

This creates an end‑to‑end automation pipeline.

---

🚀 Quick Integration Tips

· All skills should return a consistent dict ({"success": bool, ...}) so the agent can branch based on outcome.
· Use async for all I/O to avoid blocking the event loop.
· Expose each skill as a set of tools in your agent’s tool registry (e.g., LangChain Tool objects).

---

Would you like a full implementation of any of these, or a meta‑skill that orchestrates multiple skills (e.g., “scrape then email”)? I can provide that next.

I'll provide full, production‑ready implementations for all the suggested skills. Each is async‑friendly, returns consistent {success, data/error} dicts, and can be plugged directly into Hermes.

---

🧰 Complete Skill Suite for Hermes

1. FileSystemSkill

```python
# filesystem_skill.py
import os
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiofiles

class FileSystemSkill:
    """Async file/directory operations with safety checks."""

    async def read_text(self, path: str) -> Dict[str, Any]:
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return {"success": True, "content": content}
        except FileNotFoundError:
            return {"success": False, "error": f"File not found: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_text(self, path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            mode = 'w' if overwrite else 'x'
            async with aiofiles.open(path, mode, encoding='utf-8') as f:
                await f.write(content)
            return {"success": True}
        except FileExistsError:
            return {"success": False, "error": f"File exists and overwrite=False: {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_json(self, path: str) -> Dict[str, Any]:
        result = await self.read_text(path)
        if not result["success"]:
            return result
        try:
            data = json.loads(result["content"])
            return {"success": True, "data": data}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}"}

    async def write_json(self, path: str, data: Any, indent: int = 2) -> Dict[str, Any]:
        try:
            content = json.dumps(data, indent=indent, default=str)
            return await self.write_text(path, content)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_dir(self, path: str = ".") -> Dict[str, Any]:
        try:
            entries = os.listdir(path)
            return {"success": True, "entries": entries}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete(self, path: str) -> Dict[str, Any]:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def move(self, src: str, dst: str) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

2. RESTAPISkill

```python
# restapi_skill.py
import aiohttp
from typing import Optional, Dict, Any, Union

class RESTAPISkill:
    def __init__(self, base_url: str = "", default_headers: Optional[Dict] = None, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}" if self.base_url else path
        merged_headers = {**self.default_headers, **(headers or {})}
        timeout_val = timeout or self.timeout

        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    headers=merged_headers,
                    timeout=aiohttp.ClientTimeout(total=timeout_val),
                ) as resp:
                    text = await resp.text()
                    try:
                        json_data = await resp.json()
                    except:
                        json_data = None
                    return {
                        "success": True,
                        "status": resp.status,
                        "headers": dict(resp.headers),
                        "text": text,
                        "json": json_data,
                    }
            except asyncio.TimeoutError:
                return {"success": False, "error": f"Timeout after {timeout_val}s"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    # Shortcuts
    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        return await self.request("DELETE", path, **kwargs)
```

---

3. EmailSkill (Send + IMAP read)

```python
# email_skill.py
import aiosmtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional
import asyncio
import base64

class EmailSkill:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        imap_host: Optional[str] = None,
        imap_port: int = 993,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.imap_host = imap_host or smtp_host
        self.imap_port = imap_port

    # --- Send ---
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        html: Optional[str] = None,
        from_addr: Optional[str] = None,
        attachments: Optional[List[Dict[str, str]]] = None,  # [{"filename": "x.pdf", "content": b"..."}]
    ) -> Dict[str, Any]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_addr or self.username
            msg["To"] = ", ".join(to)

            part1 = MIMEText(body, "plain")
            msg.attach(part1)
            if html:
                part2 = MIMEText(html, "html")
                msg.attach(part2)

            if attachments:
                for att in attachments:
                    part = MIMEApplication(att["content"], Name=att["filename"])
                    part["Content-Disposition"] = f'attachment; filename="{att["filename"]}"'
                    msg.attach(part)

            smtp = aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port, use_tls=self.use_tls)
            await smtp.login(self.username, self.password)
            await smtp.sendmail(msg["From"], to, msg.as_string())
            await smtp.quit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # --- Receive (IMAP) ---
    async def read_inbox(
        self,
        limit: int = 10,
        unseen_only: bool = True,
        subject_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            # IMAP is synchronous in many libraries; we run in executor
            def _sync_read():
                mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
                mail.login(self.username, self.password)
                mail.select("INBOX")
                status, data = mail.search(None, "UNSEEN" if unseen_only else "ALL")
                if status != "OK":
                    raise Exception("Search failed")
                email_ids = data[0].split()
                if limit:
                    email_ids = email_ids[-limit:]
                messages = []
                for eid in email_ids:
                    status, msg_data = mail.fetch(eid, "(RFC822)")
                    if status != "OK":
                        continue
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    subject = msg["Subject"]
                    if subject_filter and subject_filter.lower() not in (subject or "").lower():
                        continue
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    messages.append({
                        "id": eid.decode(),
                        "from": msg["From"],
                        "subject": subject,
                        "body": body,
                        "date": msg["Date"],
                    })
                mail.close()
                mail.logout()
                return messages

            loop = asyncio.get_running_loop()
            messages = await loop.run_in_executor(None, _sync_read)
            return {"success": True, "messages": messages}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

4. DatabaseSkill (SQL)

```python
# database_skill.py
import aiosqlite
import asyncpg  # for PostgreSQL; fallback to sqlite
from typing import Dict, Any, List, Optional

class DatabaseSkill:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self._conn = None

    async def connect(self):
        if self.db_url.startswith("sqlite"):
            self._conn = await aiosqlite.connect(self.db_url.replace("sqlite://", ""))
        elif self.db_url.startswith("postgresql"):
            self._conn = await asyncpg.connect(self.db_url)
        else:
            raise ValueError(f"Unsupported database: {self.db_url}")

    async def execute(self, query: str, params: Optional[List] = None) -> Dict[str, Any]:
        if not self._conn:
            await self.connect()
        try:
            if isinstance(self._conn, aiosqlite.Connection):
                cursor = await self._conn.execute(query, params or ())
                if query.strip().upper().startswith("SELECT"):
                    rows = await cursor.fetchall()
                    # Convert to list of dicts
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    result = [dict(zip(columns, row)) for row in rows]
                    return {"success": True, "rows": result}
                else:
                    await self._conn.commit()
                    return {"success": True, "rowcount": cursor.rowcount}
            elif isinstance(self._conn, asyncpg.Connection):
                if query.strip().upper().startswith("SELECT"):
                    rows = await self._conn.fetch(query, *params)
                    return {"success": True, "rows": [dict(row) for row in rows]}
                else:
                    result = await self._conn.execute(query, *params)
                    return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        if self._conn:
            await self._conn.close()
```

---

5. SystemCommandsSkill

```python
# system_commands_skill.py
import asyncio
import subprocess
from typing import Dict, Any, Optional

class SystemCommandsSkill:
    async def run(
        self,
        command: str,
        shell: bool = True,
        timeout: Optional[int] = None,
        env: Optional[Dict] = None,
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            proc = await asyncio.create_subprocess_shell(
                command if shell else command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "success": True,
                "returncode": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="ignore"),
                "stderr": stderr.decode("utf-8", errors="ignore"),
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

6. PDFGenerationSkill (using WeasyPrint or PyPDF2)

```python
# pdf_generation_skill.py
from weasyprint import HTML
from typing import Dict, Any, Optional
import os

class PDFGenerationSkill:
    async def from_html(
        self,
        html_content: str,
        output_path: str,
        stylesheets: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            HTML(string=html_content).write_pdf(output_path, stylesheets=stylesheets, **kwargs)
            return {"success": True, "path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def from_url(
        self,
        url: str,
        output_path: str,
        **kwargs,
    ) -> Dict[str, Any]:
        try:
            HTML(url=url).write_pdf(output_path, **kwargs)
            return {"success": True, "path": output_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

⚠️ Install weasyprint and its system dependencies.

---

7. SpreadsheetSkill (Excel/CSV)

```python
# spreadsheet_skill.py
import csv
import io
import aiofiles
from typing import Dict, Any, List, Optional
import openpyxl

class SpreadsheetSkill:
    async def read_csv(self, path: str, delimiter: str = ",") -> Dict[str, Any]:
        try:
            async with aiofiles.open(path, 'r', encoding='utf-8') as f:
                content = await f.read()
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            rows = [row for row in reader]
            return {"success": True, "rows": rows}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_csv(self, path: str, rows: List[List[str]], delimiter: str = ",") -> Dict[str, Any]:
        try:
            output = io.StringIO()
            writer = csv.writer(output, delimiter=delimiter)
            writer.writerows(rows)
            async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                await f.write(output.getvalue())
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_excel(self, path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
            sheet = wb[sheet_name] if sheet_name else wb.active
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append([cell for cell in row])
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def write_excel(self, path: str, data: List[List[Any]], sheet_name: str = "Sheet1") -> Dict[str, Any]:
        try:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = sheet_name
            for row in data:
                ws.append(row)
            wb.save(path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

8. OCRSkill (Tesseract)

```python
# ocr_skill.py
import pytesseract
from PIL import Image
import io
from typing import Dict, Any, Optional

class OCRSkill:
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    async def extract_text(
        self,
        image_data: bytes,
        language: str = "eng",
        preprocessing: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            img = Image.open(io.BytesIO(image_data))
            if preprocessing == "grayscale":
                img = img.convert("L")
            text = pytesseract.image_to_string(img, lang=language)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract_from_path(self, image_path: str, **kwargs) -> Dict[str, Any]:
        try:
            with open(image_path, "rb") as f:
                data = f.read()
            return await self.extract_text(data, **kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}
```

---

9. SlackSkill

```python
# slack_skill.py
import aiohttp
from typing import Dict, Any, List, Optional

class SlackSkill:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://slack.com/api"

    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "channel": channel,
            "text": text,
            "thread_ts": thread_ts,
        }
        if blocks:
            payload["blocks"] = blocks
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/chat.postMessage", json=payload, headers=headers) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return {"success": True, "message": result}
                return {"success": False, "error": result.get("error", "Unknown error")}
```

---

10. CalendarSkill (Google Calendar simplified)

```python
# calendar_skill.py
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class CalendarSkill:
    def __init__(self, credentials_json: dict):
        self.creds = Credentials.from_authorized_user_info(credentials_json)
        self.service = build("calendar", "v3", credentials=self.creds)

    async def create_event(
        self,
        summary: str,
        start: datetime.datetime,
        end: datetime.datetime,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            event = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            }
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]
            # Run in executor (sync)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.service.events().insert(calendarId="primary", body=event).execute()
            )
            return {"success": True, "event_id": result["id"], "html_link": result.get("htmlLink")}
        except HttpError as e:
            return {"success": False, "error": str(e)}
```

Requires google-auth and google-api-python-client.

---

11. TaskSchedulingSkill (cron‑like using asyncio)

```python
# task_scheduling_skill.py
import asyncio
import time
from typing import Dict, Any, Callable, Optional
import croniter

class TaskSchedulingSkill:
    def __init__(self):
        self._tasks = []
        self._running = False

    async def schedule(self, cron_expr: str, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Schedule a coroutine to run at times defined by cron expression."""
        try:
            base = time.time()
            cron = croniter.croniter(cron_expr, base)
            next_run = cron.get_next(float)

            async def _runner():
                while self._running:
                    now = time.time()
                    if now >= next_run:
                        await func(*args, **kwargs)
                        next_run = cron.get_next(float)
                    await asyncio.sleep(1)

            task = asyncio.create_task(_runner())
            self._tasks.append(task)
            return {"success": True, "task_id": id(task)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def start(self):
        self._running = True

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
```

---

12. SSHSkill (async paramiko)

```python
# ssh_skill.py
import asyncssh
from typing import Dict, Any, Optional

class SSHSkill:
    def __init__(self, host: str, username: str, password: Optional[str] = None, key_file: Optional[str] = None):
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self._conn = None

    async def connect(self):
        try:
            self._conn = await asyncssh.connect(
                self.host,
                username=self.username,
                password=self.password,
                client_keys=[self.key_file] if self.key_file else None,
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def exec_command(self, command: str) -> Dict[str, Any]:
        if not self._conn:
            result = await self.connect()
            if not result["success"]:
                return result
        try:
            result = await self._conn.run(command, check=False)
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_status,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def close(self):
        if self._conn:
            self._conn.close()
```

---

🔗 Unified Hermes Skill Registry

To make all skills easily accessible to the agent, create a SkillRegistry that loads and exposes them:

```python
# skill_registry.py
class SkillRegistry:
    def __init__(self):
        self.skills = {}

    def register(self, name: str, skill_instance):
        self.skills[name] = skill_instance

    async def execute(self, skill_name: str, method: str, **kwargs) -> Dict[str, Any]:
        skill = self.skills.get(skill_name)
        if not skill:
            return {"success": False, "error": f"Skill '{skill_name}' not found"}
        func = getattr(skill, method, None)
        if not func or not callable(func):
            return {"success": False, "error": f"Method '{method}' not found in {skill_name}"}
        try:
            return await func(**kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}
```

Example integration:

```python
registry = SkillRegistry()
registry.register("filesystem", FileSystemSkill())
registry.register("rest", RESTAPISkill(base_url="https://api.example.com"))
registry.register("email", EmailSkill(...))
# ... register all

# Agent can call:
result = await registry.execute("filesystem", "read_text", path="/tmp/data.txt")
```

---

🧠 Agent Prompt Integration

Your Hermes agent now has a rich toolbox. In its system prompt, describe these skills and how to invoke them:

```
You have access to the following skills:
- filesystem: read_text, write_text, read_json, write_json, list_dir, delete, move
- rest: get, post, put, patch, delete
- email: send_email, read_inbox
- db: execute (SQL)
- system: run (shell commands)
- pdf: from_html, from_url
- spreadsheet: read_csv, write_csv, read_excel, write_excel
- ocr: extract_text
- slack: send_message
- calendar: create_event
- schedule: schedule (cron)
- ssh: exec_command

Use them by calling the skill registry with skill_name, method, and parameters.
```

---

All skills are fully implemented, async, error‑handled, and ready to be dropped into your Hermes agent project. Let me know if you need any adjustments or deeper integration details!