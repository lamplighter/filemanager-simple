#!/usr/bin/env python3
"""Test the file queue viewer table layout with HTTP server"""

from playwright.sync_api import sync_playwright
import subprocess
import time
import os
import signal

# Start a simple HTTP server
port = 8765
print(f"Starting HTTP server on port {port}...")
server_process = subprocess.Popen(
    ['python3', '-m', 'http.server', str(port)],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Wait for server to start
time.sleep(2)

try:
    viewer_url = f'http://localhost:{port}/viewer.html'
    print(f"Testing viewer at: {viewer_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console logs
        console_messages = []
        page.on('console', lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))

        # Navigate to the viewer
        page.goto(viewer_url)

        # Wait for the page to load and render
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(1000)

        # Print console messages if any errors
        errors = [msg for msg in console_messages if 'error' in msg.lower()]
        if errors:
            print("\nConsole errors:")
            for msg in errors:
                print(f"  {msg}")

        # Take a screenshot
        screenshot_path = '/tmp/viewer_table_test.png'
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"✓ Screenshot saved to: {screenshot_path}")

        # Verify table structure exists
        table = page.locator('table')
        if table.count() > 0:
            print("✓ Table element found")

            # Check for table headers
            headers = page.locator('thead th').all_text_contents()
            print(f"✓ Table headers: {headers}")

            expected_headers = ['Source', 'Destination', 'Confidence', 'Time of Evaluation']
            if headers == expected_headers:
                print("✓ Headers match expected columns")
            else:
                print(f"✗ Headers don't match. Expected: {expected_headers}, Got: {headers}")

            # Count rows
            rows = page.locator('tbody tr')
            row_count = rows.count()
            print(f"✓ Found {row_count} data rows")

            # Check first row structure if exists
            if row_count > 0:
                first_row_cells = page.locator('tbody tr:first-child td').all_text_contents()
                print(f"✓ First row has {len(first_row_cells)} cells")
                if len(first_row_cells) == 4:
                    print("✓ Row structure is correct (4 columns)")
                    print(f"\nFirst row sample:")
                    print(f"  Source: {first_row_cells[0][:50]}...")
                    print(f"  Destination: {first_row_cells[1][:50]}...")
                    print(f"  Confidence: {first_row_cells[2]}")
                    print(f"  Time: {first_row_cells[3]}")
                else:
                    print(f"✗ Expected 4 cells, got {len(first_row_cells)}")
        else:
            print("✗ No table element found")

        # Check for old card-based layout (should not exist)
        cards = page.locator('.file-card')
        if cards.count() == 0:
            print("✓ No old card-based layout found (correct)")
        else:
            print(f"✗ Found {cards.count()} card elements (should be 0)")

        # Test modal functionality
        if row_count > 0:
            print("\n--- Testing Modal ---")

            # Click first row to open modal
            page.locator('tbody tr:first-child').click()
            page.wait_for_timeout(500)

            # Check if modal is visible
            modal_overlay = page.locator('#modalOverlay')
            if modal_overlay.evaluate('el => el.classList.contains("active")'):
                print("✓ Modal opened on row click")

                # Check modal content
                modal_body = page.locator('#modalBody')
                modal_content = modal_body.inner_text()

                if 'CONFIDENCE' in modal_content.upper():
                    print("✓ Modal shows confidence section")
                if 'SOURCE PATH' in modal_content.upper():
                    print("✓ Modal shows source path")
                if 'DESTINATION PATH' in modal_content.upper():
                    print("✓ Modal shows destination path")
                if 'REASONING' in modal_content.upper():
                    print("✓ Modal shows reasoning")
                if 'METADATA' in modal_content.upper():
                    print("✓ Modal shows metadata")

                # Take screenshot with modal open
                modal_screenshot = '/tmp/viewer_modal_test.png'
                page.screenshot(path=modal_screenshot, full_page=True)
                print(f"✓ Modal screenshot saved to: {modal_screenshot}")

                # Test closing modal with X button
                page.locator('.modal-close').click()
                page.wait_for_timeout(300)

                if not modal_overlay.evaluate('el => el.classList.contains("active")'):
                    print("✓ Modal closes with X button")
                else:
                    print("✗ Modal didn't close with X button")

            else:
                print("✗ Modal didn't open on row click")

        browser.close()
        print("\n✓ Test complete!")
        print(f"\nView the screenshot at: {screenshot_path}")

finally:
    # Clean up server
    print("\nStopping HTTP server...")
    server_process.send_signal(signal.SIGTERM)
    server_process.wait(timeout=5)
