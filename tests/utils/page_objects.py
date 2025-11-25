"""Page Object Model for the file queue viewer."""

from playwright.sync_api import Page, expect


class ViewerPage:
    """Page Object for the file queue viewer."""

    def __init__(self, page: Page, base_url: str = "http://localhost:8765"):
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
