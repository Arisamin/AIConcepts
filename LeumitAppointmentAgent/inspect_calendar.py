"""
Inspect calendar HTML structure to understand how to interact with it.
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=".browser_profile",
            headless=False,
            args=["--start-maximized"]
        )
        
        page = await browser.new_page()
        await page.goto("https://online2.leumit.co.il/Online/Login/HomePage.aspx", timeout=30000)
        
        # Wait for user to be logged in and calendar to be visible
        print("Please navigate to the calendar screen and wait...")
        print("This script will inspect the calendar HTML...")
        await asyncio.sleep(5)
        
        # Try to find calendar elements
        print("\n" + "="*70)
        print("CALENDAR STRUCTURE ANALYSIS")
        print("="*70)
        
        # Get all date-related elements
        calendar_html = await page.content()
        
        # Look for common calendar patterns
        patterns = [
            ('data-date attribute', '[data-date]'),
            ('calendar class', '[class*="calendar"]'),
            ('table cells', 'td'),
            ('table rows', 'tr'),
            ('buttons with numbers', 'button:has-text(/^\\d{1,2}$/)'),
            ('divs with numbers', 'div:has-text(/^\\d{1,2}$/)'),
            ('links', 'a'),
            ('date input', 'input[type="date"]'),
            ('date picker', '[class*="picker"]'),
            ('day class', '[class*="day"]'),
            ('disabled', '[disabled]'),
            ('aria-label', '[aria-label*="202"]'),
        ]
        
        for pattern_name, selector in patterns:
            try:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"\n✓ Found {count} elements with: {pattern_name}")
                    print(f"  Selector: {selector}")
                    
                    # Get first few elements
                    elements = await page.locator(selector).all()[:3]
                    for i, elem in enumerate(elements):
                        try:
                            html = await elem.inner_html()
                            text = await elem.text_content()
                            print(f"    [{i}] Text: {text.strip()[:50]}")
                            # Get common attributes
                            for attr in ['data-date', 'class', 'id', 'onclick', 'data-value']:
                                val = await elem.get_attribute(attr)
                                if val:
                                    print(f"         {attr}: {val[:50]}")
                        except:
                            pass
            except Exception as e:
                pass
        
        print("\n" + "="*70)
        print("FULL CALENDAR CONTAINER")
        print("="*70)
        
        # Get calendar container
        containers = [
            '[class*="calendar"]',
            '[class*="picker"]',
            '[id*="calendar"]',
            'table',
            '[role="dialog"]',
            '.popup',
            '[class*="modal"]'
        ]
        
        for container_sel in containers:
            try:
                count = await page.locator(container_sel).count()
                if count > 0:
                    print(f"\nContainer found: {container_sel} (count: {count})")
                    container = await page.locator(container_sel).first
                    html = await container.inner_html()
                    print("HTML (first 500 chars):")
                    print(html[:500])
                    break
            except:
                pass
        
        print("\nInspection complete. Check the calendar screenshot and close the browser.")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
