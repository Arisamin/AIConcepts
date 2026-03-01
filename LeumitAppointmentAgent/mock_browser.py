import asyncio
from typing import Any
from browser_interface import BrowserInterface


class MockElement:
    """Mock DOM element"""
    def __init__(self, text=None, visible=True):
        self._text = text or ""
        self._visible = visible
        self._filled = None
        self._clicked = False
        self._count = 1

    async def wait_for(self, timeout=5000, state="visible"):
        await asyncio.sleep(0)
        if not self._visible:
            raise Exception("Element not visible")
        return self

    async def click(self, timeout=5000):
        self._clicked = True
        await asyncio.sleep(0)

    async def fill(self, value):
        self._filled = value
        await asyncio.sleep(0)

    async def text_content(self):
        return self._text

    async def get_attribute(self, name):
        return None

    async def count(self):
        return self._count

    async def is_visible(self):
        return self._visible


class MockLocator:
    """Represents a Playwright Locator object (non-async)"""
    def __init__(self, text=None, visible=True):
        self.element = MockElement(text=text, visible=visible)
        self.first = self.element  # Locator.first returns another Locator/Element

    async def click(self, timeout=5000):
        return await self.element.click(timeout)

    async def fill(self, value):
        return await self.element.fill(value)

    async def wait_for(self, timeout=5000, state="visible"):
        return await self.element.wait_for(timeout, state)

    async def text_content(self):
        return await self.element.text_content()

    async def get_attribute(self, name):
        return await self.element.get_attribute(name)

    async def count(self):
        return await self.element.count()

    async def is_visible(self):
        return await self.element.is_visible()


class MockFrame:
    def __init__(self, url="", elements=None):
        self.url = url
        self._elements = elements or {}

    async def query_selector(self, selector):
        return self._elements.get(selector, MockElement())

    async def query_selector_all(self, selector):
        return [self._elements.get(selector, MockElement())]


class MockBrowser(BrowserInterface):
    def __init__(self, scenario=None):
        # scenario: dict describing what to return for each method/selector
        self._scenario = scenario or {}
        self._url = self._scenario.get("url", "http://mock")
        self._frames = self._scenario.get("frames", [])
        self._elements = self._scenario.get("elements", {})
        self._log = []

    def _element_for_selector(self, selector: str) -> MockElement:
        return self._elements.get(selector, MockElement(visible=False))

    def _element_for_text(self, text: str, exact: bool = False) -> MockElement:
        for element in self._elements.values():
            try:
                element_text = getattr(element, "_text", "") or ""
                if exact and element_text == text:
                    return element
                if not exact and text in element_text:
                    return element
            except Exception:
                continue
        return MockElement(text=text, visible=False)

    async def goto(self, url: str, wait_until: str = "domcontentloaded") -> Any:
        self._url = url
        self._log.append(f"goto:{url}")
        await asyncio.sleep(0)
        return self

    async def fill(self, selector: str, value: str) -> Any:
        self._log.append(f"fill:{selector}={value}")
        await asyncio.sleep(0)
        return self

    async def click(self, selector: str) -> Any:
        self._log.append(f"click:{selector}")
        await asyncio.sleep(0)
        return self

    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> Any:
        self._log.append(f"wait_for_selector:{selector}")
        await asyncio.sleep(0)
        return self._element_for_selector(selector)

    def get_by_text(self, text: str, exact: bool = False) -> Any:
        self._log.append(f"get_by_text:{text}")
        element = self._element_for_text(text, exact=exact)
        return MockLocator(text=element._text, visible=element._visible)

    async def reload(self, wait_until: str = "domcontentloaded") -> Any:
        self._log.append("reload")
        await asyncio.sleep(0)
        return self

    async def screenshot(self, path: str, full_page: bool = False) -> Any:
        self._log.append(f"screenshot:{path}")
        await asyncio.sleep(0)
        return path

    @property
    def frames(self) -> Any:
        return self._frames

    @property
    def url(self) -> str:
        return self._url

    def locator(self, selector: str) -> Any:
        self._log.append(f"locator:{selector}")
        element = self._element_for_selector(selector)
        return MockLocator(text=element._text, visible=element._visible)

    def get_log(self):
        return self._log