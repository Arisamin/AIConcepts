from typing import Any

class BrowserInterface:
    """
    Abstract interface for browser/page operations used by PersistentAgent.
    Allows for real or mock implementations for integration testing.
    """
    async def goto(self, url: str, wait_until: str = "domcontentloaded") -> Any:
        raise NotImplementedError

    async def fill(self, selector: str, value: str) -> Any:
        raise NotImplementedError

    async def click(self, selector: str) -> Any:
        raise NotImplementedError

    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> Any:
        raise NotImplementedError

    async def get_by_text(self, text: str, exact: bool = False) -> Any:
        raise NotImplementedError

    async def screenshot(self, path: str, full_page: bool = False) -> Any:
        raise NotImplementedError

    @property
    def frames(self) -> Any:
        raise NotImplementedError

    @property
    def url(self) -> str:
        raise NotImplementedError

    def locator(self, selector: str) -> Any:
        raise NotImplementedError