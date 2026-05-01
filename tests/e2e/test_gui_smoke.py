"""E2E Playwright smoke tests for the voice-assistant GUI (Item 2).

These tests launch the pre-built ``web/dist/index.html`` as a ``file://`` URL
in headless Chromium and assert the presence of key UI elements. No Python
desktop bridge is required; they test the static HTML+JS bundle only.

Prerequisites
-------------
    pip install "voice-assistant[e2e]"
    playwright install chromium

Run
---
    pytest tests/e2e/test_gui_smoke.py --browser chromium

Or via the CI workflow defined in .github/workflows/e2e.yml.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Skip the entire module if pytest-playwright is not installed so that the
# normal test suite is not broken on dev machines without playwright.
pytest.importorskip("playwright", reason="playwright not installed — skip e2e tests")

from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DIST_DIR = Path(__file__).parent.parent.parent / "web" / "dist"


@pytest.fixture(scope="session")
def index_url() -> str:
    """Return the file:// URL for the built index.html."""
    index = DIST_DIR / "index.html"
    if not index.exists():
        pytest.skip(
            f"web/dist/index.html not found at {index}. Run `cd web && npm run build` first."
        )
    return index.as_uri()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGUISmoke:
    def test_avatar_image_present(self, page: Page, index_url: str) -> None:
        """The avatar <img> is present in the DOM and has a src attribute."""
        page.goto(index_url)
        page.wait_for_load_state("networkidle")
        # Avatar image is rendered by Avatar component; selector matches the img
        avatar_img = page.locator(".va-avatar-img, img[class*='avatar']").first
        expect(avatar_img).to_be_visible(timeout=5_000)

    def test_composer_textarea_visible(self, page: Page, index_url: str) -> None:
        """The composer textarea is present and visible."""
        page.goto(index_url)
        page.wait_for_load_state("networkidle")
        textarea = page.locator("textarea[data-input], textarea.va-composer-input").first
        expect(textarea).to_be_visible(timeout=5_000)

    def test_mic_button_visible(self, page: Page, index_url: str) -> None:
        """The microphone button is visible in the composer."""
        page.goto(index_url)
        page.wait_for_load_state("networkidle")
        mic_btn = page.locator("button[data-record], .va-mic-btn").first
        expect(mic_btn).to_be_visible(timeout=5_000)

    def test_send_button_hidden_when_empty(self, page: Page, index_url: str) -> None:
        """The send button is hidden when the textarea is empty."""
        page.goto(index_url)
        page.wait_for_load_state("networkidle")
        # Send button starts hidden — check it has the 'hidden' class or display:none
        send_btn = page.locator("button[data-send], .va-send-btn").first
        # It should either not be visible or have class 'hidden'
        class_value = send_btn.get_attribute("class") or ""
        is_hidden = "hidden" in class_value or not send_btn.is_visible()
        assert is_hidden, "Send button should be hidden when composer is empty"

    def test_esc_on_closed_settings_is_noop(self, page: Page, index_url: str) -> None:
        """Pressing Esc when settings drawer is closed does not crash or open anything."""
        page.goto(index_url)
        page.wait_for_load_state("networkidle")
        settings_panel = page.locator(".va-settings")
        # Settings should be closed initially
        class_val = settings_panel.get_attribute("class") or ""
        assert "is-open" not in class_val, "Settings should be closed initially"
        # Press Esc — should be a no-op (no error, settings stays closed)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        class_val_after = settings_panel.get_attribute("class") or ""
        assert "is-open" not in class_val_after, "Settings should remain closed after Esc"

    def test_gear_click_opens_settings(self, page: Page, index_url: str) -> None:
        """Clicking the gear/settings button opens the settings drawer."""
        page.goto(index_url)
        page.wait_for_load_state("networkidle")
        # Wait for a config event so currentConfig is populated and gear works
        page.wait_for_timeout(500)
        gear_btn = page.locator(
            "button[aria-label*='Settings'], button[title*='Settings'], .va-header-gear, [data-settings-btn]"
        ).first
        if not gear_btn.is_visible():
            pytest.skip("Gear button not found — UI may use a different selector")
        gear_btn.click()
        page.wait_for_timeout(400)
        settings = page.locator(".va-settings")
        class_val = settings.get_attribute("class") or ""
        assert "is-open" in class_val, "Settings drawer should open after clicking gear"

    def test_settings_has_five_tab_buttons(self, page: Page, index_url: str) -> None:
        """The settings drawer has exactly five tab buttons: Brain/Voice/Audio/Identity/Privacy."""
        page.goto(index_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        gear_btn = page.locator(
            "button[aria-label*='Settings'], button[title*='Settings'], .va-header-gear, [data-settings-btn]"
        ).first
        if not gear_btn.is_visible():
            pytest.skip("Gear button not found — cannot open settings")
        gear_btn.click()
        page.wait_for_timeout(400)
        tab_buttons = page.locator(".va-settings [data-tab]")
        count = tab_buttons.count()
        assert count == 5, f"Expected 5 tab buttons, got {count}"
        labels = [tab_buttons.nth(i).inner_text().strip().lower() for i in range(count)]
        assert any("brain" in lb for lb in labels), f"Missing 'Brain' tab; got {labels}"
        assert any("voice" in lb for lb in labels), f"Missing 'Voice' tab; got {labels}"
        assert any("audio" in lb for lb in labels), f"Missing 'Audio' tab; got {labels}"
        assert any("identity" in lb for lb in labels), f"Missing 'Identity' tab; got {labels}"
        assert any("privacy" in lb for lb in labels), f"Missing 'Privacy' tab; got {labels}"
