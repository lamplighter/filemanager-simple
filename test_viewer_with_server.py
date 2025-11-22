#!/usr/bin/env python3
"""Test the file queue viewer with approval functionality"""

from playwright.sync_api import sync_playwright
import subprocess
import time
import os
import signal
import json

# Start the viewer server with API
port = 8765
script_dir = os.path.dirname(os.path.abspath(__file__))
server_script = os.path.join(script_dir, 'scripts', 'viewer_server.py')

print(f"Starting viewer server on port {port}...")
server_process = subprocess.Popen(
    ['python3', server_script],
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

            expected_headers = ['Source', 'Destination', 'Confidence', 'Approval', 'Time of Evaluation']
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
                if len(first_row_cells) == 5:
                    print("✓ Row structure is correct (5 columns)")
                    print(f"\nFirst row sample:")
                    print(f"  Source: {first_row_cells[0][:50]}...")
                    print(f"  Destination: {first_row_cells[1][:50]}...")
                    print(f"  Confidence: {first_row_cells[2]}")
                    print(f"  Approval: {first_row_cells[3][:30]}...")
                    print(f"  Time: {first_row_cells[4]}")
                else:
                    print(f"✗ Expected 5 cells, got {len(first_row_cells)}")
        else:
            print("✗ No table element found")

        # Check for old card-based layout (should not exist)
        cards = page.locator('.file-card')
        if cards.count() == 0:
            print("✓ No old card-based layout found (correct)")
        else:
            print(f"✗ Found {cards.count()} card elements (should be 0)")

        # Test approval functionality
        if row_count > 0:
            print("\n--- Testing Approval Functionality ---")

            # Check for approval column
            approval_header = page.locator('th:has-text("Approval")')
            if approval_header.count() > 0:
                print("✓ Approval column exists in table")

                # Check for approve/reject buttons in first row
                first_row = page.locator('tbody tr:first-child')
                approve_btn = first_row.locator('.approve-btn')
                reject_btn = first_row.locator('.reject-btn')

                if approve_btn.count() > 0 and reject_btn.count() > 0:
                    print("✓ Approve and Reject buttons found")

                    # Read current queue file to verify before state
                    queue_file_path = os.path.join(script_dir, 'state', 'file_queue.json')
                    with open(queue_file_path, 'r') as f:
                        queue_before = json.load(f)

                    first_file_id = queue_before['files'][0]['id']
                    print(f"✓ File ID to approve: {first_file_id[:8]}...")

                    # Click approve button (without opening modal)
                    approve_btn.click()
                    page.wait_for_timeout(1000)  # Wait for API call

                    # Read queue file to verify status update
                    with open(queue_file_path, 'r') as f:
                        queue_after = json.load(f)

                    # Find the file and check status
                    approved_file = next((f for f in queue_after['files'] if f['id'] == first_file_id), None)

                    if approved_file and approved_file['status'] == 'approved':
                        print("✓ File status updated to 'approved' in JSON")

                        # Verify UI updated
                        page.wait_for_timeout(500)
                        first_row_cells = page.locator('tbody tr:first-child td').all_inner_texts()
                        if 'approved' in ' '.join(first_row_cells).lower():
                            print("✓ UI updated to show 'approved' status")
                        else:
                            print("✗ UI didn't update to show approved status")
                    else:
                        print("✗ File status not updated to approved")
                else:
                    print("✗ Approve/Reject buttons not found")
            else:
                print("✗ Approval column not found")

        # Test modal functionality
        if row_count > 1:  # Use second row since first is now approved
            print("\n--- Testing Modal ---")

            # Click second row to open modal
            page.locator('tbody tr:nth-child(2)').click()
            page.wait_for_timeout(500)

            # Check if modal is visible
            modal_overlay = page.locator('#modalOverlay')
            if modal_overlay.evaluate('el => el.classList.contains("active")'):
                print("✓ Modal opened on row click")

                # Check modal content
                modal_body = page.locator('#modalBody')
                modal_content = modal_body.inner_text()

                if 'APPROVAL REQUIRED' in modal_content.upper():
                    print("✓ Modal shows approval section for pending files")
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
