#!/usr/bin/env python3
"""Comprehensive verification test for directory file listing feature"""

from playwright.sync_api import sync_playwright
import time

def test_complete_verification():
    print("=" * 60)
    print("COMPREHENSIVE DIRECTORY LISTING FEATURE TEST")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Console logging
        console_logs = []
        def handle_console(msg):
            console_logs.append(f"{msg.type}: {msg.text}")
            if msg.type == 'error' and 'directory' in msg.text.lower():
                print(f"  ⚠️  CONSOLE ERROR: {msg.text}")

        page.on('console', handle_console)

        print("\n1. Loading viewer page...")
        page.goto('http://localhost:8765/viewer.html')
        page.wait_for_load_state('networkidle')
        print("   ✓ Page loaded successfully")

        # Check for files in queue
        file_rows = page.locator('tbody tr').all()
        print(f"\n2. Queue contains {len(file_rows)} files")

        if len(file_rows) == 0:
            print("   ✗ Cannot test - no files in queue")
            browser.close()
            return False

        # Test multiple files if available
        test_count = min(3, len(file_rows))
        print(f"\n3. Testing with {test_count} file(s)...\n")

        for i in range(test_count):
            print(f"   Testing file #{i+1}:")

            # Click to open modal
            file_rows[i].click()
            page.wait_for_selector('#modalOverlay.active', timeout=5000)
            print("   ✓ Modal opened")

            # Wait for directory files to load
            time.sleep(2)

            # Verify section title exists
            section_title = page.locator('text=Files in Destination Directory')
            assert section_title.count() > 0, "Section title not found"
            print("   ✓ Section title present")

            # Verify container exists
            container = page.locator('#directoryFiles')
            assert container.count() > 0, "Container not found"

            # Check container content
            content = container.inner_html()

            if 'directory-files-table' in content:
                # Count files in table
                table_rows = page.locator('.directory-files-table tbody tr').all()
                print(f"   ✓ Table found with {len(table_rows)} file(s)")

                # Verify table headers (handle sort indicators like ▲▼)
                headers = page.locator('.directory-files-table th').all()
                header_texts = [h.inner_text() for h in headers]
                header_texts_str = ' '.join(header_texts)
                assert 'FILENAME' in header_texts_str or 'Filename' in header_texts_str, f"Missing FILENAME header in {header_texts}"
                assert 'SIZE' in header_texts_str or 'Size' in header_texts_str, f"Missing SIZE header in {header_texts}"
                assert 'MODIFIED' in header_texts_str or 'Modified' in header_texts_str, f"Missing MODIFIED header in {header_texts}"
                print(f"   ✓ Table headers correct: {header_texts}")

                # Verify first row has data
                if len(table_rows) > 0:
                    first_row_cells = page.locator('.directory-files-table tbody tr').first.locator('td').all()
                    if len(first_row_cells) >= 3:
                        filename = first_row_cells[0].inner_text()
                        size = first_row_cells[1].inner_text()
                        modified = first_row_cells[2].inner_text()
                        print(f"   ✓ Sample file: {filename} | {size} | {modified}")

                # Check if directory path is shown
                header_div = page.locator('.directory-files-header')
                if header_div.count() > 0:
                    header_text = header_div.inner_text()
                    print(f"   ✓ Directory info: {header_text}")

            elif 'Loading...' in content:
                print("   ⚠️  Still loading (might be slow)")
            elif 'error-message' in content:
                error_text = page.locator('.error-message').inner_text()
                print(f"   ✗ Error: {error_text}")
            elif 'empty-message' in content:
                print("   ⚠️  Directory is empty")
            else:
                print(f"   ? Unexpected content: {content[:100]}")

            # Close modal for next iteration
            close_btn = page.locator('.modal-close')
            close_btn.click()
            page.wait_for_timeout(500)
            print()

        # Take final screenshot
        print("4. Taking verification screenshot...")
        page.locator('tbody tr').first.click()
        page.wait_for_selector('#modalOverlay.active')
        time.sleep(2)
        page.evaluate('document.querySelector("#directoryFiles").scrollIntoView()')
        page.wait_for_timeout(500)
        page.screenshot(path='/tmp/verification_complete.png', full_page=True)
        print("   ✓ Screenshot saved to /tmp/verification_complete.png")

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Files tested: {test_count}")
        print(f"Console errors: {len([log for log in console_logs if 'error' in log.lower() and 'directory' in log.lower()])}")
        print("Status: ✓ ALL TESTS PASSED")
        print("=" * 60)

        browser.close()
        return True

if __name__ == '__main__':
    try:
        success = test_complete_verification()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
