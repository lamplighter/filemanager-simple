#!/usr/bin/env python3
"""Test the viewer UI Move button behavior - no confirmation, shows MOVED status."""

from playwright.sync_api import sync_playwright
import time

def test_move_button():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Track if any confirm dialog appears (should not!)
        dialog_appeared = False
        def handle_dialog(dialog):
            nonlocal dialog_appeared
            dialog_appeared = True
            print(f"❌ FAIL: Confirmation dialog appeared: {dialog.message}")
            dialog.dismiss()

        page.on("dialog", handle_dialog)

        # Navigate to viewer
        print("📍 Navigating to viewer at http://localhost:8765/viewer.html")
        page.goto('http://localhost:8765/viewer.html')
        page.wait_for_load_state('networkidle')

        # Take initial screenshot
        print("📸 Taking initial screenshot...")
        page.screenshot(path='/tmp/viewer_before_move.png', full_page=True)

        # Find the first Move button
        move_buttons = page.locator('button.approve-btn:has-text("Move")').all()

        if not move_buttons:
            print("⚠️  No Move buttons found - queue might be empty")
            browser.close()
            return

        print(f"✅ Found {len(move_buttons)} Move button(s)")

        # Click the first Move button
        print("🖱️  Clicking first Move button...")
        move_buttons[0].click()

        # Wait for the action to complete
        time.sleep(2)

        # Take screenshot after move
        print("📸 Taking screenshot after move...")
        page.screenshot(path='/tmp/viewer_after_move.png', full_page=True)

        # Verify no dialog appeared
        if dialog_appeared:
            print("❌ TEST FAILED: Confirmation dialog appeared!")
        else:
            print("✅ TEST PASSED: No confirmation dialog")

        # Check if MOVED status appears
        moved_badges = page.locator('.status-badge.status-moved').all()
        if moved_badges:
            print(f"✅ TEST PASSED: Found {len(moved_badges)} MOVED status badge(s)")
        else:
            print("❌ TEST FAILED: No MOVED status badge found")

        # Check if the original Move button still exists for this file
        remaining_move_buttons = page.locator('button.approve-btn:has-text("Move")').all()
        if len(remaining_move_buttons) == len(move_buttons) - 1:
            print("✅ TEST PASSED: Move button removed from the row")
        else:
            print(f"⚠️  Move button count: before={len(move_buttons)}, after={len(remaining_move_buttons)}")

        print("\n📁 Screenshots saved:")
        print("   - /tmp/viewer_before_move.png")
        print("   - /tmp/viewer_after_move.png")

        browser.close()

if __name__ == "__main__":
    test_move_button()
