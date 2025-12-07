"""Tests for Skip file operation."""

import pytest
from playwright.sync_api import Page

from tests.utils.page_objects import ViewerPage
from tests.fixtures.queue_data import make_queue, make_queue_entry


@pytest.mark.e2e
class TestSkipOperation:
    """Tests for the Skip button functionality."""

    def test_skip_button_no_confirmation(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Skip button works without confirmation dialog."""
        source_file = sample_txt

        queue = make_queue([
            make_queue_entry(str(source_file), "/some/dest/file.txt", confidence=80),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        initial_count = viewer.get_row_count()
        assert initial_count == 1

        # Click Skip - should work immediately
        viewer.click_skip_button(0)
        page.wait_for_timeout(1000)

        # Row should be removed
        assert viewer.get_row_count() < initial_count

    def test_skip_removes_from_queue(self, page: Page, viewer_url, write_queue, read_queue, temp_test_dir, sample_txt):
        """Skip removes entry from queue file."""
        source_file = sample_txt
        file_id = "skip-test-id-12345"

        queue = make_queue([
            make_queue_entry(str(source_file), "/some/dest/file.txt", id=file_id),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        viewer.click_skip_button(0)
        page.wait_for_timeout(1000)

        # Check queue file
        queue_after = read_queue()
        file_ids = [f["id"] for f in queue_after.get("files", [])]

        assert file_id not in file_ids

    def test_skip_file_moves_to_skipped_folder(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Skip moves file to Skipped folder."""
        import os
        source_file = sample_txt
        dest_path = temp_test_dir["dest"] / "should_not_exist.txt"
        skipped_folder = os.path.expanduser('~/Downloads/Skipped')

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_path), confidence=60),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Verify file exists at source before skip
        assert source_file.exists()

        viewer.click_skip_button(0)
        page.wait_for_timeout(1000)

        # File should NOT be at source anymore
        assert not source_file.exists()
        # File should NOT be at destination
        assert not dest_path.exists()
        # File should be in Skipped folder
        skipped_path = os.path.join(skipped_folder, source_file.name)
        assert os.path.exists(skipped_path)
        # Clean up
        os.remove(skipped_path)

    def test_skip_updates_skip_history(self, page: Page, viewer_url, write_queue, read_skip_history, temp_test_dir, sample_txt):
        """Skip adds entry to skip_history.json."""
        source_file = sample_txt

        queue = make_queue([
            make_queue_entry(str(source_file), "/some/dest/file.txt", confidence=70),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Get skip history before
        history_before = read_skip_history()
        count_before = len(history_before.get("files", []))

        viewer.click_skip_button(0)
        page.wait_for_timeout(1000)

        # Get skip history after
        history_after = read_skip_history()
        count_after = len(history_after.get("files", []))

        # Should have one more entry
        assert count_after == count_before + 1


@pytest.mark.e2e
class TestSkipMultipleFiles:
    """Tests for skipping multiple files."""

    def test_skip_multiple_files_sequentially(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Can skip multiple files one after another."""
        source_dir = temp_test_dir["source"]

        # Create multiple test files
        file1 = source_dir / "file1.txt"
        file2 = source_dir / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        queue = make_queue([
            make_queue_entry(str(file1), "/dest/file1.txt", id="id1"),
            make_queue_entry(str(file2), "/dest/file2.txt", id="id2"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        assert viewer.get_row_count() == 2

        # Skip first file
        viewer.click_skip_button(0)
        page.wait_for_timeout(500)

        # Should have one less row
        assert viewer.get_row_count() == 1

        # Skip second file
        viewer.click_skip_button(0)
        page.wait_for_timeout(500)

        # Should have no rows
        assert viewer.get_row_count() == 0

        # Both files should still exist
        assert file1.exists()
        assert file2.exists()
