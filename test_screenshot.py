#!/usr/bin/env python3
"""Take a screenshot showing the directory files section"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Navigate and open modal
    page.goto('http://localhost:8765/viewer.html')
    page.wait_for_load_state('networkidle')

    # Click first row
    page.locator('tbody tr').first.click()
    page.wait_for_selector('#modalOverlay.active')

    # Wait for directory files to load
    page.wait_for_timeout(2000)

    # Scroll the modal to show the directory files section
    page.evaluate('document.querySelector("#directoryFiles").scrollIntoView()')
    page.wait_for_timeout(500)

    # Take screenshot
    page.screenshot(path='/tmp/directory_files_section.png', full_page=True)
    print("Screenshot saved to /tmp/directory_files_section.png")

    browser.close()
