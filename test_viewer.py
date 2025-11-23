#!/usr/bin/env python3
"""Test the file queue viewer layout and functionality"""

from playwright.sync_api import sync_playwright
import sys

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Load viewer via HTTP server
    print("Loading viewer from http://localhost:8765/viewer.html")
    page.goto('http://localhost:8765/viewer.html')
    page.wait_for_load_state('networkidle')

    # Take main screenshot
    screenshot_path = '/tmp/viewer_test.png'
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"📸 Screenshot saved to: {screenshot_path}")

    # Check table element
    table = page.locator('table')
    print(f"\n✓ Table found: {table.count()} table(s)")

    # Get all column headers and their widths
    print("\nColumn widths:")
    headers = page.locator('thead th').all()
    for i, header in enumerate(headers):
        text = header.text_content().strip()
        width = header.evaluate("el => window.getComputedStyle(el).width")
        print(f"  Column {i+1} ({text}): {width}")

    # Check for files in queue
    rows = page.locator('tbody tr')
    row_count = rows.count()
    print(f"\n✓ Found {row_count} file(s) in queue")

    # Check buttons
    if row_count > 0:
        approve_btns = page.locator('button:has-text("Approve")')
        reject_btns = page.locator('button:has-text("Reject")')
        print(f"✓ Found {approve_btns.count()} Approve buttons")
        print(f"✓ Found {reject_btns.count()} Reject buttons")

        # Check for alternatives indicators in main table
        print("\nChecking for alternatives indicators:")
        alternatives_indicators = page.locator('text=/\\(\\+\\d+ option').all()
        if len(alternatives_indicators) > 0:
            print(f"✓ Found {len(alternatives_indicators)} file(s) with alternatives indicator")
        else:
            print("  No alternatives indicators found (this is OK if no files have alternatives)")

        # Test modal
        print("\nTesting modal:")
        rows.first.click()
        page.wait_for_timeout(500)

        modal = page.locator('.modal-overlay.active')
        if modal.is_visible():
            print("✓ Modal opened")

            # Check for alternatives section
            alternatives_section = page.locator('.modal-section:has-text("Alternative Destinations")')
            if alternatives_section.count() > 0:
                print("✓ Alternatives section found in modal")

                # Count alternative items
                alternative_items = page.locator('.alternative-item').all()
                print(f"✓ Found {len(alternative_items)} alternative item(s)")

                # Check for confidence badges
                alt_confidence = page.locator('.alternative-confidence').all()
                print(f"✓ Found {len(alt_confidence)} alternative confidence badge(s)")

                # Check for differences and reasoning
                differences = page.locator('.alternative-detail:has-text("Differences:")').all()
                reasoning = page.locator('.alternative-detail:has-text("Why not primary:")').all()
                print(f"✓ Found {len(differences)} differences explanation(s)")
                print(f"✓ Found {len(reasoning)} reasoning explanation(s)")
            else:
                print("  No alternatives section (this is OK if file has no alternatives)")

            # Check directory files section
            dir_table = page.locator('.directory-files-table')
            if dir_table.is_visible():
                print("✓ Directory files table visible")

                # Check sortable headers
                sort_headers = page.locator('.directory-files-table th.sortable-header').all()
                print(f"✓ Found {len(sort_headers)} sortable columns")

                # Check column widths in directory table
                print("\nDirectory table column widths:")
                for i, header in enumerate(sort_headers):
                    text = header.text_content().strip()
                    width = header.evaluate("el => window.getComputedStyle(el).width")
                    print(f"  {text}: {width}")

            # Take modal screenshot
            modal_screenshot = '/tmp/viewer_test_modal.png'
            page.screenshot(path=modal_screenshot, full_page=True)
            print(f"\n📸 Modal screenshot saved to: {modal_screenshot}")

            # Close modal
            page.locator('.modal-close').click()
            page.wait_for_timeout(300)

    browser.close()
    print("\n✅ Test completed successfully!")
    print(f"\nMain screenshot: {screenshot_path}")
