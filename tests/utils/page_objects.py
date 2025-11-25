"""Page Object Model for the file queue viewer."""

from playwright.sync_api import Page, expect


class ViewerPage:
    """Page Object for the file queue viewer."""

    def __init__(self, page: Page, base_url: str):
        """Initialize ViewerPage.

        Args:
            page: Playwright page object
            base_url: Server URL (required - no default to prevent accidental production access)
        """
        self.page = page
        self.base_url = base_url

    def navigate(self):
        """Navigate to the viewer page."""
        self.page.goto(f"{self.base_url}/viewer.html")
        self.page.wait_for_load_state("networkidle")

    # Selectors - Table
    @property
    def queue_table(self):
        return self.page.locator("table")

    @property
    def table_headers(self):
        return self.page.locator("thead th")

    @property
    def table_rows(self):
        return self.page.locator("tbody tr")

    # Selectors - Buttons
    @property
    def move_buttons(self):
        return self.page.locator("button.approve-btn")

    @property
    def skip_buttons(self):
        return self.page.locator("button.reject-btn")

    @property
    def delete_buttons(self):
        return self.page.locator("button.delete-btn")

    # Selectors - Modal
    @property
    def modal_overlay(self):
        return self.page.locator("#modalOverlay")

    @property
    def modal_body(self):
        return self.page.locator("#modalBody")

    @property
    def modal_close_button(self):
        return self.page.locator(".modal-close")

    # Selectors - Filters
    @property
    def confidence_filter(self):
        return self.page.locator("#confidenceFilter")

    @property
    def approval_filter(self):
        return self.page.locator("#approvalFilter")

    @property
    def sort_by(self):
        return self.page.locator("#sortBy")

    # Selectors - Info
    @property
    def queue_info(self):
        return self.page.locator("#queueInfo")

    # Actions - Table
    def get_row_count(self) -> int:
        """Get the number of rows in the table."""
        return self.table_rows.count()

    def get_header_texts(self) -> list[str]:
        """Get all column header texts."""
        return self.table_headers.all_text_contents()

    def click_row(self, index: int):
        """Click a specific row to open the modal."""
        self.table_rows.nth(index).click()
        self.page.wait_for_selector("#modalOverlay.active", timeout=5000)

    def get_row_text(self, index: int) -> str:
        """Get the text content of a specific row."""
        return self.table_rows.nth(index).text_content()

    # Actions - Buttons
    def click_move_button(self, index: int = 0):
        """Click a Move button by index."""
        self.move_buttons.nth(index).click()

    def click_skip_button(self, index: int = 0):
        """Click a Skip button by index."""
        self.skip_buttons.nth(index).click()

    def click_delete_button(self, index: int = 0):
        """Click a Delete button by index."""
        self.delete_buttons.nth(index).click()

    # Actions - Modal
    def close_modal(self):
        """Close the modal."""
        self.modal_close_button.click()
        self.page.wait_for_timeout(300)

    def is_modal_open(self) -> bool:
        """Check if the modal is open."""
        class_attr = self.modal_overlay.get_attribute("class") or ""
        return "active" in class_attr

    def get_modal_content(self) -> str:
        """Get the modal body content."""
        return self.modal_body.text_content()

    # Actions - Filters
    def filter_by_confidence(self, value: str):
        """Filter by confidence level (all, high, medium, low)."""
        self.confidence_filter.select_option(value)
        self.page.wait_for_timeout(200)

    def filter_by_approval(self, value: str):
        """Filter by approval status."""
        self.approval_filter.select_option(value)
        self.page.wait_for_timeout(200)

    def sort_by_option(self, value: str):
        """Sort by specified option."""
        self.sort_by.select_option(value)
        self.page.wait_for_timeout(200)

    # Assertions helpers
    def has_move_buttons(self) -> bool:
        """Check if Move buttons exist."""
        return self.move_buttons.count() > 0

    def has_skip_buttons(self) -> bool:
        """Check if Skip buttons exist."""
        return self.skip_buttons.count() > 0

    def has_table(self) -> bool:
        """Check if the queue table exists."""
        return self.queue_table.count() > 0

    def wait_for_row_count(self, count: int, timeout: int = 5000):
        """Wait for the table to have a specific number of rows."""
        self.page.wait_for_function(
            f"document.querySelectorAll('tbody tr').length === {count}",
            timeout=timeout
        )

    # Status helpers
    def get_status_badge_text(self, row_index: int) -> str:
        """Get the status badge text for a row."""
        badge = self.table_rows.nth(row_index).locator(".status-badge")
        if badge.count() > 0:
            return badge.text_content()
        return ""

    def row_has_status(self, row_index: int, status: str) -> bool:
        """Check if a row has a specific status."""
        row_text = self.get_row_text(row_index)
        return status.lower() in row_text.lower()

    # Bulk selection - Selectors
    @property
    def select_all_checkbox(self):
        """Get the select all checkbox in the header."""
        return self.page.locator("#selectAllCheckbox")

    @property
    def row_checkboxes(self):
        """Get all row checkboxes."""
        return self.page.locator(".row-checkbox")

    @property
    def bulk_action_bar(self):
        """Get the bulk action bar."""
        return self.page.locator("#bulkActionBar")

    @property
    def bulk_move_button(self):
        """Get the bulk move button."""
        return self.page.locator(".bulk-move-btn")

    @property
    def bulk_skip_button(self):
        """Get the bulk skip button."""
        return self.page.locator(".bulk-skip-btn")

    @property
    def bulk_clear_button(self):
        """Get the clear selection button."""
        return self.page.locator(".bulk-clear-btn")

    @property
    def selected_count(self):
        """Get the selected count element."""
        return self.page.locator("#selectedCount")

    # Bulk selection - Actions
    def select_row(self, index: int):
        """Select a row by clicking its checkbox."""
        self.row_checkboxes.nth(index).click()
        self.page.wait_for_timeout(100)

    def select_all(self):
        """Click select all checkbox."""
        self.select_all_checkbox.click()
        self.page.wait_for_timeout(100)

    def get_selected_count(self) -> int:
        """Get number of selected rows."""
        return self.page.locator(".row-checkbox:checked").count()

    def click_bulk_move(self):
        """Click bulk move button."""
        self.bulk_move_button.click()

    def click_bulk_skip(self):
        """Click bulk skip button."""
        self.bulk_skip_button.click()

    def click_clear_selection(self):
        """Click clear selection button."""
        self.bulk_clear_button.click()
        self.page.wait_for_timeout(100)

    def is_bulk_bar_visible(self) -> bool:
        """Check if bulk action bar is visible."""
        return self.bulk_action_bar.is_visible()

    def get_selected_count_text(self) -> str:
        """Get the selected count text from the bulk bar."""
        return self.selected_count.text_content()

    def is_row_selected(self, index: int) -> bool:
        """Check if a row is visually selected."""
        row = self.table_rows.nth(index)
        class_attr = row.get_attribute("class") or ""
        return "selected" in class_attr
