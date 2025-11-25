"""Tests for bulk Move/Skip operations."""

import pytest
from playwright.sync_api import Page

from tests.utils.page_objects import ViewerPage
from tests.fixtures.queue_data import make_queue, make_queue_entry


@pytest.mark.e2e
class TestBulkSelection:
    """Tests for checkbox selection functionality."""

    def test_checkbox_column_exists(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Checkbox column appears in the table."""
        source_file = sample_txt
        dest_file = temp_test_dir["dest"] / "test.txt"

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file)),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Select all checkbox should exist in header
        assert viewer.select_all_checkbox.count() == 1
        # Row checkbox should exist
        assert viewer.row_checkboxes.count() == 1

    def test_select_individual_row(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Selecting a row checkbox selects that row."""
        source_file = sample_txt
        dest_file = temp_test_dir["dest"] / "test.txt"

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file)),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Initially not selected
        assert viewer.get_selected_count() == 0
        assert not viewer.is_bulk_bar_visible()

        # Select row
        viewer.select_row(0)

        # Should be selected
        assert viewer.get_selected_count() == 1
        assert viewer.is_bulk_bar_visible()
        assert viewer.is_row_selected(0)

    def test_select_all(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Select all checkbox selects all rows."""
        source_dir = temp_test_dir["source"]
        dest_dir = temp_test_dir["dest"]

        # Create multiple test files
        files = []
        for i in range(3):
            txt_file = source_dir / f"test{i}.txt"
            txt_file.write_text(f"Content {i}")
            files.append(txt_file)

        queue = make_queue([
            make_queue_entry(str(files[i]), str(dest_dir / f"dest{i}.txt"))
            for i in range(3)
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Initially no selection
        assert viewer.get_selected_count() == 0

        # Click select all
        viewer.select_all()

        # All should be selected
        assert viewer.get_selected_count() == 3
        assert viewer.is_bulk_bar_visible()
        assert "3 files selected" in viewer.get_selected_count_text()

    def test_deselect_all(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Clicking select all again deselects all rows."""
        source_dir = temp_test_dir["source"]
        dest_dir = temp_test_dir["dest"]

        # Create multiple test files
        files = []
        for i in range(2):
            txt_file = source_dir / f"test{i}.txt"
            txt_file.write_text(f"Content {i}")
            files.append(txt_file)

        queue = make_queue([
            make_queue_entry(str(files[i]), str(dest_dir / f"dest{i}.txt"))
            for i in range(2)
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Select all
        viewer.select_all()
        assert viewer.get_selected_count() == 2

        # Deselect all
        viewer.select_all()
        assert viewer.get_selected_count() == 0
        assert not viewer.is_bulk_bar_visible()

    def test_clear_selection_button(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Clear selection button clears all selections."""
        source_file = sample_txt
        dest_file = temp_test_dir["dest"] / "test.txt"

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file)),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Select row
        viewer.select_row(0)
        assert viewer.get_selected_count() == 1

        # Clear selection
        viewer.click_clear_selection()
        assert viewer.get_selected_count() == 0
        assert not viewer.is_bulk_bar_visible()

    def test_bulk_bar_visibility(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Bulk action bar appears when files selected, hides when none."""
        source_file = sample_txt
        dest_file = temp_test_dir["dest"] / "test.txt"

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file)),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Initially hidden
        assert not viewer.is_bulk_bar_visible()

        # Select - should show
        viewer.select_row(0)
        assert viewer.is_bulk_bar_visible()

        # Deselect - should hide
        viewer.select_row(0)  # Toggle off
        assert not viewer.is_bulk_bar_visible()


@pytest.mark.e2e
class TestBulkMove:
    """Tests for bulk move operation."""

    def test_bulk_move_multiple_files(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Bulk move moves multiple selected files."""
        source_dir = temp_test_dir["source"]
        dest_dir = temp_test_dir["dest"]

        # Create test files
        files = []
        dest_files = []
        for i in range(3):
            txt_file = source_dir / f"test{i}.txt"
            txt_file.write_text(f"Content {i}")
            files.append(txt_file)
            dest_files.append(dest_dir / f"dest{i}.txt")

        queue = make_queue([
            make_queue_entry(str(files[i]), str(dest_files[i]))
            for i in range(3)
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Verify source files exist
        for f in files:
            assert f.exists()

        # Select all and bulk move
        viewer.select_all()
        viewer.click_bulk_move()
        page.wait_for_timeout(2000)

        # All files should be moved
        for i in range(3):
            assert not files[i].exists()
            assert dest_files[i].exists()

    def test_bulk_move_updates_history(self, page: Page, viewer_url, write_queue, read_history, temp_test_dir):
        """Bulk move adds all entries to history."""
        source_dir = temp_test_dir["source"]
        dest_dir = temp_test_dir["dest"]

        # Create test files
        files = []
        for i in range(2):
            txt_file = source_dir / f"test{i}.txt"
            txt_file.write_text(f"Content {i}")
            files.append(txt_file)

        queue = make_queue([
            make_queue_entry(str(files[i]), str(dest_dir / f"dest{i}.txt"))
            for i in range(2)
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        history_before = read_history()
        count_before = len(history_before.get("files", []))

        # Select all and move
        viewer.select_all()
        viewer.click_bulk_move()
        page.wait_for_timeout(2000)

        history_after = read_history()
        count_after = len(history_after.get("files", []))

        # Should have 2 more entries
        assert count_after == count_before + 2

    def test_bulk_move_clears_queue(self, page: Page, viewer_url, write_queue, read_queue, temp_test_dir):
        """Bulk move removes moved files from queue."""
        source_dir = temp_test_dir["source"]
        dest_dir = temp_test_dir["dest"]

        # Create test files
        files = []
        for i in range(2):
            txt_file = source_dir / f"test{i}.txt"
            txt_file.write_text(f"Content {i}")
            files.append(txt_file)

        queue = make_queue([
            make_queue_entry(str(files[i]), str(dest_dir / f"dest{i}.txt"), id=f"file-{i}")
            for i in range(2)
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Select all and move
        viewer.select_all()
        viewer.click_bulk_move()
        page.wait_for_timeout(2000)

        # Check queue is empty
        queue_after = read_queue()
        assert len(queue_after.get("files", [])) == 0


@pytest.mark.e2e
class TestBulkSkip:
    """Tests for bulk skip operation."""

    def test_bulk_skip_multiple_files(self, page: Page, viewer_url, write_queue, read_skip_history, temp_test_dir):
        """Bulk skip skips multiple selected files."""
        source_dir = temp_test_dir["source"]
        dest_dir = temp_test_dir["dest"]

        # Create test files
        files = []
        for i in range(2):
            txt_file = source_dir / f"test{i}.txt"
            txt_file.write_text(f"Content {i}")
            files.append(txt_file)

        queue = make_queue([
            make_queue_entry(str(files[i]), str(dest_dir / f"dest{i}.txt"), id=f"skip-{i}")
            for i in range(2)
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        skip_before = read_skip_history()
        count_before = len(skip_before.get("files", []))

        # Select all and skip
        viewer.select_all()
        viewer.click_bulk_skip()
        page.wait_for_timeout(2000)

        # Files should still exist at source (not moved)
        for f in files:
            assert f.exists()

        # Skip history should have entries
        skip_after = read_skip_history()
        count_after = len(skip_after.get("files", []))
        assert count_after == count_before + 2

    def test_bulk_skip_clears_queue(self, page: Page, viewer_url, write_queue, read_queue, temp_test_dir):
        """Bulk skip removes skipped files from queue."""
        source_dir = temp_test_dir["source"]
        dest_dir = temp_test_dir["dest"]

        # Create test files
        files = []
        for i in range(2):
            txt_file = source_dir / f"test{i}.txt"
            txt_file.write_text(f"Content {i}")
            files.append(txt_file)

        queue = make_queue([
            make_queue_entry(str(files[i]), str(dest_dir / f"dest{i}.txt"), id=f"file-{i}")
            for i in range(2)
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Select all and skip
        viewer.select_all()
        viewer.click_bulk_skip()
        page.wait_for_timeout(2000)

        # Check queue is empty
        queue_after = read_queue()
        assert len(queue_after.get("files", [])) == 0


@pytest.mark.e2e
class TestBulkErrors:
    """Tests for bulk operation error handling."""

    def test_bulk_move_stops_on_error(self, page: Page, viewer_url, write_queue, read_queue, temp_test_dir):
        """Bulk move stops on first error (source not found)."""
        source_dir = temp_test_dir["source"]
        dest_dir = temp_test_dir["dest"]

        # First file exists, second doesn't
        existing_file = source_dir / "exists.txt"
        existing_file.write_text("Content")
        nonexistent_file = source_dir / "nonexistent.txt"

        queue = make_queue([
            make_queue_entry(str(existing_file), str(dest_dir / "dest1.txt"), id="file-1"),
            make_queue_entry(str(nonexistent_file), str(dest_dir / "dest2.txt"), id="file-2"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Select all and try to move
        viewer.select_all()

        # Handle alert
        page.on("dialog", lambda dialog: dialog.accept())

        viewer.click_bulk_move()
        page.wait_for_timeout(2000)

        # First file should be moved
        assert not existing_file.exists()
        assert (dest_dir / "dest1.txt").exists()

        # Queue should be reloaded and show remaining file
        # (the one that failed should still be in queue OR an error shown)
