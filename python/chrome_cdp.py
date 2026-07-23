"""Chrome CDP Skill — Playwright-based browser automation."""
import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, Playwright


class ChromeCDPSkill:
    """Control Chrome via CDP using Playwright."""

    def __init__(self, headless: bool = False, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless, slow_mo=self.slow_mo
        )
        self.page = await self.browser.new_page()
        return self

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url: str, timeout: int = 30000) -> Dict[str, Any]:
        try:
            response = await self.page.goto(url, timeout=timeout, wait_until="networkidle")
            return {"success": True, "url": self.page.url, "status": response.status if response else None}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        try:
            await self.page.click(selector, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        try:
            await self.page.fill(selector, text)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def screenshot(self, path: Optional[str] = None, full_page: bool = False) -> Dict[str, Any]:
        try:
            if path:
                await self.page.screenshot(path=path, full_page=full_page)
                return {"success": True, "path": path}
            import base64
            b64 = base64.b64encode(await self.page.screenshot(full_page=full_page)).decode("utf-8")
            return {"success": True, "base64": b64}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_text(self, selector: str) -> Dict[str, Any]:
        try:
            text = await self.page.text_content(selector)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def evaluate(self, script: str, *args) -> Dict[str, Any]:
        try:
            result = await self.page.evaluate(script, *args)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_html(self) -> Dict[str, Any]:
        try:
            html = await self.page.content()
            return {"success": True, "html": html}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def send_cdp(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            result = await self.page._impl_obj._connection.send(method, params if params else {})
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict[str, Any]:
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
