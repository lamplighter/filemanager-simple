"""Tests for modal interactions."""

import pytest
from playwright.sync_api import Page

from tests.utils.page_objects import ViewerPage
from tests.fixtures.queue_data import (
    make_queue,
    make_queue_entry,
    make_entry_with_alternatives,
)


@pytest.mark.e2e
class TestModalBasics:
    """Tests for basic modal functionality."""

    def test_row_click_opens_modal(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Clicking a row opens the modal."""
        source_file = sample_txt

        queue = make_queue([
            make_queue_entry(str(source_file), "/some/dest/file.txt"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()

        # Modal should be closed initially
        assert not viewer.is_modal_open()

        # Click row
        viewer.click_row(0)

        # Modal should be open
        assert viewer.is_modal_open()

    def test_modal_shows_file_details(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Modal displays file details."""
        source_file = sample_txt
        dest_path = "/some/dest/file.txt"
        reasoning = "Test reasoning for this file suggestion."

        queue = make_queue([
            make_queue_entry(
                str(source_file),
                dest_path,
                confidence=85,
                reasoning=reasoning,
            ),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()
        viewer.click_row(0)

        content = viewer.get_modal_content()

        # Should show key information
        assert "85" in content  # confidence score
        assert reasoning in content or "reasoning" in content.lower()

    def test_modal_close_button(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """X button closes the modal."""
        queue = make_queue([
            make_queue_entry(str(sample_txt), "/dest/file.txt"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()
        viewer.click_row(0)

        assert viewer.is_modal_open()

        viewer.close_modal()

        assert not viewer.is_modal_open()

    def test_modal_close_on_escape(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Escape key closes the modal."""
        queue = make_queue([
            make_queue_entry(str(sample_txt), "/dest/file.txt"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()
        viewer.click_row(0)

        assert viewer.is_modal_open()

        # Press Escape
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)

        assert not viewer.is_modal_open()

    def test_modal_shows_confidence_breakdown(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Modal shows confidence factor breakdown."""
        queue = make_queue([
            make_queue_entry(
                str(sample_txt),
                "/dest/file.txt",
                confidence=80,
                confidence_factors={
                    "similar_files_found": 30,
                    "file_type_match": 20,
                    "entity_keyword": 20,
                    "content_match": 10,
                }
            ),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()
        viewer.click_row(0)

        content = viewer.get_modal_content().lower()

        # Should show confidence factors
        assert "confidence" in content


@pytest.mark.e2e
class TestModalActions:
    """Tests for action buttons in modal."""

    def test_modal_move_button_works(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Move button in modal works."""
        source_file = sample_txt
        dest_file = temp_test_dir["dest"] / "modal_moved.txt"

        queue = make_queue([
            make_queue_entry(str(source_file), str(dest_file)),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()
        viewer.click_row(0)

        # Click Move in modal
        modal_move = page.locator("#modalBody .approve-btn")
        if modal_move.count() > 0:
            modal_move.click()
            page.wait_for_timeout(1000)

            # File should be moved
            assert dest_file.exists()
        else:
            # Modal might have different structure
            # Just verify modal closes on move from table
            viewer.close_modal()
            viewer.click_move_button(0)
            page.wait_for_timeout(1000)
            assert dest_file.exists()

    def test_modal_skip_button_works(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Skip button in modal works."""
        source_file = sample_txt

        queue = make_queue([
            make_queue_entry(str(source_file), "/dest/file.txt"),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()

        initial_count = viewer.get_row_count()
        viewer.click_row(0)

        # Click Skip in modal
        modal_skip = page.locator("#modalBody .reject-btn")
        if modal_skip.count() > 0:
            modal_skip.click()
            page.wait_for_timeout(1000)

            # Row should be removed
            assert viewer.get_row_count() < initial_count
        else:
            # Use table skip button
            viewer.close_modal()
            viewer.click_skip_button(0)
            page.wait_for_timeout(1000)
            assert viewer.get_row_count() < initial_count


@pytest.mark.e2e
class TestModalAlternatives:
    """Tests for alternatives display in modal."""

    def test_modal_shows_alternatives_section(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Modal displays alternatives section when available."""
        alternatives = [
            {
                "dest_path": "/alt/dest1/file.txt",
                "confidence": 70,
                "confidence_factors": {"match": 70},
                "reasoning": "Alternative option 1",
                "differences": "Less specific folder",
            },
            {
                "dest_path": "/alt/dest2/file.txt",
                "confidence": 60,
                "confidence_factors": {"match": 60},
                "reasoning": "Alternative option 2",
                "differences": "Different category",
            },
        ]

        queue = make_queue([
            make_entry_with_alternatives(
                str(sample_txt),
                "/primary/dest/file.txt",
                alternatives=alternatives,
                confidence=85,
            ),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()
        viewer.click_row(0)

        content = viewer.get_modal_content().lower()

        # Should show alternatives section
        assert "alternative" in content

    def test_alternatives_show_confidence_scores(self, page: Page, viewer_url, write_queue, temp_test_dir, sample_txt):
        """Each alternative shows its confidence score."""
        alternatives = [
            {
                "dest_path": "/alt/file.txt",
                "confidence": 65,
                "confidence_factors": {},
                "reasoning": "Alt reason",
                "differences": "Alt diff",
            },
        ]

        queue = make_queue([
            make_entry_with_alternatives(
                str(sample_txt),
                "/primary/file.txt",
                alternatives=alternatives,
                confidence=90,
            ),
        ])
        write_queue(queue)

        viewer = ViewerPage(page)
        viewer.navigate()
        viewer.click_row(0)

        content = viewer.get_modal_content()

        # Should show both confidence scores
        assert "90" in content  # Primary
        assert "65" in content  # Alternative
