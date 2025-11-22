#!/usr/bin/env python3
"""Test the directory file listing feature in the file viewer"""

from playwright.sync_api import sync_playwright
import time

def test_directory_listing():
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Listen for console messages
        def handle_console(msg):
            print(f"CONSOLE: {msg.type}: {msg.text}")

        page.on('console', handle_console)

        # Navigate to the viewer
        print("Opening viewer...")
        page.goto('http://localhost:8765/viewer.html')
        page.wait_for_load_state('networkidle')

        # Take initial screenshot
        page.screenshot(path='/tmp/viewer_initial.png', full_page=True)
        print("Initial screenshot saved to /tmp/viewer_initial.png")

        # Check if there are any files in the queue
        file_rows = page.locator('tbody tr').all()
        print(f"Found {len(file_rows)} files in the queue")

        if len(file_rows) == 0:
            print("No files in queue to test with")
            browser.close()
            return

        # Click the first file row to open the modal
        print("Clicking first file to open modal...")
        first_row = file_rows[0]
        first_row.click()

        # Wait for modal to appear
        page.wait_for_selector('#modalOverlay.active', timeout=5000)
        print("Modal opened")

        # Wait a moment for the directory files to load
        time.sleep(2)

        # Take screenshot of the modal
        page.screenshot(path='/tmp/viewer_modal.png', full_page=True)
        print("Modal screenshot saved to /tmp/viewer_modal.png")

        # Check if the "Files in Destination Directory" section exists
        section_title = page.locator('text=Files in Destination Directory')
        if section_title.count() > 0:
            print("✓ 'Files in Destination Directory' section found")
        else:
            print("✗ 'Files in Destination Directory' section NOT found")
            browser.close()
            return

        # Check if the directory files container exists
        container = page.locator('#directoryFiles')
        if container.count() > 0:
            print("✓ Directory files container found")

            # Get the content to see what's displayed
            content = container.inner_html()

            # Check if table exists
            if 'directory-files-table' in content:
                print("✓ Directory files table found")

                # Count how many file rows are in the table
                file_rows_in_table = page.locator('.directory-files-table tbody tr').all()
                print(f"✓ Found {len(file_rows_in_table)} files in destination directory")

            elif 'Loading...' in content:
                print("⚠ Still loading directory files")
            elif 'error-message' in content:
                print("✗ Error loading directory files")
                print(f"Error content: {content}")
            elif 'empty-message' in content:
                print("⚠ Directory is empty (no files)")
            else:
                print(f"? Unexpected content in container: {content[:200]}")
        else:
            print("✗ Directory files container NOT found")

        # Close browser
        browser.close()
        print("\nTest completed!")

if __name__ == '__main__':
    test_directory_listing()
