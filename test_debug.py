#!/usr/bin/env python3
"""Debug test to check for errors in the viewer"""

from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Not headless so we can see it
    page = browser.new_page()

    # Capture all console messages
    def handle_console(msg):
        print(f"CONSOLE [{msg.type}]: {msg.text}")

    page.on('console', handle_console)

    # Navigate to viewer
    print("Loading viewer at http://localhost:8765/viewer.html...")
    page.goto('http://localhost:8765/viewer.html')
    page.wait_for_load_state('networkidle')
    print("Page loaded\n")

    # Click first file
    print("Opening first file modal...")
    page.locator('tbody tr').first.click()
    page.wait_for_selector('#modalOverlay.active')
    print("Modal opened\n")

    # Wait for directory files
    print("Waiting for directory files to load...")
    time.sleep(3)

    # Check directory files container
    container = page.locator('#directoryFiles')
    content = container.inner_html()
    print(f"\nDirectory files container content:\n{content}\n")

    # Take screenshot
    page.screenshot(path='/tmp/debug_modal.png', full_page=True)
    print("Screenshot saved to /tmp/debug_modal.png")

    # Close browser (removed input() to allow pytest execution)
    browser.close()
