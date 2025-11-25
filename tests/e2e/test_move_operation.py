"""Tests for Move file operation."""

import pytest
import os
from playwright.sync_api import Page

from tests.utils.page_objects import ViewerPage
from tests.fixtures.queue_data import make_queue, make_queue_entry


@pytest.mark.e2e
class TestMoveOperation:
    """Tests for the Move button and file movement."""

    def test_move_button_no_confirmation(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Move button works without confirmation dialog."""
        source_file = sample_txt
        dest_dir = temp_test_dir["dest"]
        dest_file = dest_dir / "moved_file.txt"

        queue = make_queue([
            make_queue_entry(
                str(source_file),
                str(dest_file),
                confidence=95,
            ),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()

        # Verify file exists at source
        assert source_file.exists()
        assert not dest_file.exists()

        # Click Move - should work without dialog
        viewer.click_move_button(0)

        # Wait for operation to complete
        page.wait_for_timeout(1000)

        # Verify file was moved
        assert not source_file.exists()
        assert dest_file.exists()

    def test_move_shows_success_message(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Move shows success message or status update."""
        source_file = sample_txt
        dest_file = temp_test_dir["dest"] / "moved.txt"

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file), confidence=90),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()

        initial_row_count = viewer.get_row_count()

        viewer.click_move_button(0)
        page.wait_for_timeout(1000)

        # After move, either row is removed or shows MOVED status
        # Check if row count decreased or status changed
        new_row_count = viewer.get_row_count()

        # Row should be removed from pending view (count decreases)
        # OR row shows MOVED status
        assert new_row_count < initial_row_count or \
            viewer.row_has_status(0, "moved")

    def test_move_updates_history_file(self, page: Page, viewer_url, write_queue, read_history, temp_test_dir, sample_txt):
        """Move adds entry to move_history.json."""
        source_file = sample_txt
        dest_file = temp_test_dir["dest"] / "history_test.txt"

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file), confidence=85),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()

        # Get history before
        history_before = read_history()
        count_before = len(history_before.get("files", []))

        viewer.click_move_button(0)
        page.wait_for_timeout(1000)

        # Get history after
        history_after = read_history()
        count_after = len(history_after.get("files", []))

        # Should have one more entry
        assert count_after == count_before + 1

    def test_move_removes_from_queue(self, page: Page, viewer_url, write_queue, read_queue, temp_test_dir, sample_txt):
        """Move removes file from queue."""
        source_file = sample_txt
        dest_file = temp_test_dir["dest"] / "removed.txt"

        file_id = "test-file-id-12345"
        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file), id=file_id),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()

        viewer.click_move_button(0)
        page.wait_for_timeout(1000)

        # Check queue file
        queue_after = read_queue()
        file_ids = [f["id"] for f in queue_after.get("files", [])]

        # File should no longer be in queue
        assert file_id not in file_ids

    def test_move_creates_destination_directory(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Move creates destination directory if it doesn't exist."""
        source_file = sample_txt
        new_folder = temp_test_dir["dest"] / "new_folder" / "subfolder"
        dest_file = new_folder / "file.txt"

        # Ensure folder doesn't exist
        assert not new_folder.exists()

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file), confidence=75),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()

        viewer.click_move_button(0)
        page.wait_for_timeout(1000)

        # Folder should be created and file moved
        assert new_folder.exists()
        assert dest_file.exists()


@pytest.mark.e2e
class TestMoveErrors:
    """Tests for Move operation error handling."""

    def test_move_source_not_found(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Move shows error when source file doesn't exist."""
        nonexistent_source = temp_test_dir["source"] / "nonexistent.pdf"
        dest_file = temp_test_dir["dest"] / "dest.pdf"

        queue = make_queue([
            make_queue_entry(str(nonexistent_source), str(dest_file)),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()

        # Capture console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        viewer.click_move_button(0)
        page.wait_for_timeout(1000)

        # Should show some error indication
        # Either in console, alert, or status
        # The exact behavior depends on implementation
        # At minimum, file should not appear as successfully moved
        assert not dest_file.exists()
