"""Tests for queue display functionality."""

import pytest
from playwright.sync_api import Page, expect

from tests.utils.page_objects import ViewerPage
from tests.fixtures.queue_data import (
    make_queue,
    make_queue_entry,
    make_empty_queue,
)


@pytest.mark.e2e
class TestQueueDisplay:
    """Tests for basic queue display."""

    def test_loads_empty_queue(self, page: Page, viewer_url, write_queue):
        """Empty queue shows appropriate message or empty table."""
        write_queue(make_empty_queue())

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Either no table (empty state message) or table with no rows
        if viewer.has_table():
            assert viewer.get_row_count() == 0
        else:
            # Viewer shows empty state message instead of table
            page_content = page.content()
            assert "0 total" in page_content or "no files" in page_content.lower()

    def test_loads_queue_with_files(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Queue with files displays table rows."""
        source = str(temp_test_dir["source"])
        dest = str(temp_test_dir["dest"])

        queue = make_queue([
            make_queue_entry(f"{source}/file1.pdf", f"{dest}/file1.pdf", confidence=95),
            make_queue_entry(f"{source}/file2.pdf", f"{dest}/file2.pdf", confidence=75),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        assert viewer.has_table()
        assert viewer.get_row_count() == 2

    def test_displays_correct_columns(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Table has correct column headers."""
        source = str(temp_test_dir["source"])
        dest = str(temp_test_dir["dest"])

        queue = make_queue([
            make_queue_entry(f"{source}/file.pdf", f"{dest}/file.pdf"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        headers = viewer.get_header_texts()
        expected = ["Source", "Destination", "Confidence", "Approval", "Time of Evaluation"]
        assert headers == expected

    def test_displays_move_and_skip_buttons(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Pending files show Move and Skip buttons."""
        source = str(temp_test_dir["source"])
        dest = str(temp_test_dir["dest"])

        queue = make_queue([
            make_queue_entry(f"{source}/file.pdf", f"{dest}/file.pdf", status="pending"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        assert viewer.has_move_buttons()
        assert viewer.has_skip_buttons()

    def test_queue_info_shows_counts(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Queue info shows total and pending counts."""
        source = str(temp_test_dir["source"])
        dest = str(temp_test_dir["dest"])

        queue = make_queue([
            make_queue_entry(f"{source}/file1.pdf", f"{dest}/file1.pdf", status="pending"),
            make_queue_entry(f"{source}/file2.pdf", f"{dest}/file2.pdf", status="pending"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        info_text = viewer.queue_info.text_content()
        assert "2 total" in info_text
        assert "2 pending" in info_text


@pytest.mark.e2e
class TestQueueFiltering:
    """Tests for queue filtering functionality."""

    def test_confidence_filter_high(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """High confidence filter shows only 90%+ files."""
        source = str(temp_test_dir["source"])
        dest = str(temp_test_dir["dest"])

        queue = make_queue([
            make_queue_entry(f"{source}/high.pdf", f"{dest}/high.pdf", confidence=95),
            make_queue_entry(f"{source}/low.pdf", f"{dest}/low.pdf", confidence=50),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        # Initially shows all files
        assert viewer.get_row_count() == 2

        # Filter to high confidence
        viewer.filter_by_confidence("high")
        assert viewer.get_row_count() == 1

        # Verify it's the high confidence file
        row_text = viewer.get_row_text(0)
        assert "high.pdf" in row_text

    def test_confidence_filter_low(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Low confidence filter shows only <50% files."""
        source = str(temp_test_dir["source"])
        dest = str(temp_test_dir["dest"])

        queue = make_queue([
            make_queue_entry(f"{source}/high.pdf", f"{dest}/high.pdf", confidence=95),
            make_queue_entry(f"{source}/low.pdf", f"{dest}/low.pdf", confidence=30),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        viewer.filter_by_confidence("low")
        assert viewer.get_row_count() == 1

        row_text = viewer.get_row_text(0)
        assert "low.pdf" in row_text


@pytest.mark.e2e
class TestQueueSorting:
    """Tests for queue sorting functionality."""

    def test_sort_by_confidence_highest_first(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Sort by confidence puts highest first."""
        source = str(temp_test_dir["source"])
        dest = str(temp_test_dir["dest"])

        queue = make_queue([
            make_queue_entry(f"{source}/low.pdf", f"{dest}/low.pdf", confidence=50),
            make_queue_entry(f"{source}/high.pdf", f"{dest}/high.pdf", confidence=95),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        viewer.sort_by_option("confidence")

        # First row should be the high confidence file
        first_row = viewer.get_row_text(0)
        assert "high.pdf" in first_row

    def test_sort_by_confidence_lowest_first(self, page: Page, viewer_url, write_queue, temp_test_dir):
        """Sort by confidence ascending puts lowest first."""
        source = str(temp_test_dir["source"])
        dest = str(temp_test_dir["dest"])

        queue = make_queue([
            make_queue_entry(f"{source}/high.pdf", f"{dest}/high.pdf", confidence=95),
            make_queue_entry(f"{source}/low.pdf", f"{dest}/low.pdf", confidence=50),
        ])
        write_queue(queue)

        viewer = ViewerPage(page, viewer_url)
        viewer.navigate()

        viewer.sort_by_option("confidence-asc")

        # First row should be the low confidence file
        first_row = viewer.get_row_text(0)
        assert "low.pdf" in first_row
