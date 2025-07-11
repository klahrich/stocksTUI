import re
import webbrowser
from typing import Union

from rich.text import Text
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Markdown
from textual.app import ComposeResult, on

from stockstui.ui.suggesters import TickerSuggester

class NewsView(Vertical):
    """A view for displaying news articles for a selected ticker, with link navigation."""

    # Key bindings specific to the NewsView for navigating and opening links
    BINDINGS = [
        Binding("tab", "cycle_links", "Cycle Links", show=False),
        Binding("shift+tab", "cycle_links_backward", "Cycle Links Backward", show=False),
        Binding("enter", "open_link", "Open Link", show=False),
    ]

    def __init__(self, **kwargs):
        """Initializes the NewsView, setting up internal state for link management."""
        super().__init__(**kwargs)
        self._link_urls: list[str] = [] # Stores URLs extracted from news articles
        self._current_link_index: int = -1 # Index of the currently highlighted link
        self._original_markdown: Union[str, Text] = "" # Stores the original markdown content

    def compose(self) -> ComposeResult:
        """Creates the layout for the news view."""
        # Prepare data for the ticker suggester
        all_tickers_data = [s for lst in self.app.config.lists.values() for s in lst]
        suggester_data = [(s['ticker'], s.get('note') or s.get('alias', s['ticker'])) for s in all_tickers_data]
        unique_suggester_data = list({t[0]: t for t in suggester_data}.values())
        suggester = TickerSuggester(unique_suggester_data, case_sensitive=False)

        # Ticker input field
        with Horizontal(classes="news-controls"):
            yield Input(
                placeholder="Enter a ticker...",
                suggester=suggester,
                id="news-ticker-input",
                value=self.app.news_ticker or "" # Pre-fill with last selected ticker
            )
        # Markdown widget to display news content
        yield Markdown(id="news-output-display")

    def on_mount(self) -> None:
        """Called when the NewsView is mounted. Sets up initial state and fetches news if a ticker is set."""
        # Make the Markdown widget focusable to allow it to capture key presses for link navigation
        markdown_widget = self.query_one(Markdown)
        markdown_widget.can_focus = True
        
        if self.app.news_ticker:
            # Check if the correct news is already cached in the app's main state
            if self.app._news_content_for_ticker == self.app.news_ticker and self.app._last_news_content:
                self.update_content(*self.app._last_news_content)
            else:
                # Otherwise, show loading and fetch it from the market provider
                markdown_widget.update("")
                markdown_widget.loading = True
                self.app.fetch_news(self.app.news_ticker)
            
    def _parse_ticker_from_input(self, value: str) -> str:
        """Extracts the ticker symbol from a suggestion string ('TICKER - Desc') or raw input."""
        if ' - ' in value:
            return value.strip().split(' - ')[0].upper()
        return value.strip().upper()

    def _reset_link_focus(self):
        """Resets the link navigation state, clearing any highlighted links."""
        self._current_link_index = -1
        self._link_urls = []
        self._original_markdown = "" # Reset original markdown to clear highlights
        
    @on(Input.Submitted, '#news-ticker-input')
    def on_news_ticker_submitted(self, event: Input.Submitted):
        """Handles submission of the ticker input, triggering news fetch."""
        self._reset_link_focus() # Reset link state for new news

        # Clear app-level cache so we don't show stale news when switching tickers
        self.app._last_news_content = None
        self.app._news_content_for_ticker = None

        if event.value:
            markdown_widget = self.query_one(Markdown)
            self.app.news_ticker = self._parse_ticker_from_input(event.value)
            markdown_widget.update("") # Clear current display
            markdown_widget.loading = True # Show loading indicator
            self.app.fetch_news(self.app.news_ticker)

    def update_content(self, markdown: Union[str, Text], urls: list[str]) -> None:
        """Receives new news content and associated URLs, then updates the display."""
        markdown_widget = self.query_one(Markdown)
        markdown_widget.loading = False # Hide loading indicator
        self._original_markdown = markdown # Store original for highlighting
        self._link_urls = urls # Store URLs for navigation
        self._current_link_index = -1 # Reset link highlight
        markdown_widget.update(markdown) # Update the Markdown display

    def _highlight_current_link(self):
        """
        Re-renders the markdown content with the currently selected link highlighted.
        It prepends a '➤ ' indicator to the link text.
        """
        markdown_widget = self.query_one(Markdown)

        # Guard against trying to process a non-string or when no link is selected
        if not isinstance(self._original_markdown, str) or self._current_link_index == -1:
            markdown_widget.update(self._original_markdown)
            return

        # Regex to find Markdown links: [text](url)
        link_pattern = re.compile(r'\[(.*?)\]\((.*?)\)')
        link_counter = 0

        def replacer(match):
            nonlocal link_counter
            original_text = match.group(1)
            url = match.group(2)
            # Remove the indicator from previous highlights before adding a new one
            clean_text = original_text.replace("➤ ", "")
            
            if link_counter == self._current_link_index:
                # Prepend a simple, safe indicator to the link text
                replacement = f"[{'➤ ' + clean_text}]({url})"
            else:
                replacement = f"[{clean_text}]({url})"
            
            link_counter += 1
            return replacement

        # We must re-run the replacement over the *original* markdown each time
        # to prevent indicators from stacking up.
        new_content = link_pattern.sub(replacer, self._original_markdown)
        markdown_widget.update(new_content)

        # Scroll the view to the highlighted link for better UX
        if self._link_urls and len(self._link_urls) > 1:
            scroll_percentage = (self._current_link_index / (len(self._link_urls) - 1)) * 100
            # Calculate scroll position based on widget's virtual size
            if markdown_widget.virtual_size.height > markdown_widget.container_size.height:
                max_scroll_y = markdown_widget.virtual_size.height - markdown_widget.container_size.height
                target_y = (scroll_percentage / 100) * max_scroll_y
                markdown_widget.scroll_to(y=target_y, duration=0.2)

    def action_cycle_links(self) -> None:
        """Cycles focus forward through the available links, highlighting the next one."""
        if not self._link_urls:
            return

        # Move focus away from the input widget so this view captures Enter keys.
        if self.query_one(Input).has_focus:
            self.query_one(Markdown).focus()

        self._current_link_index += 1
        if self._current_link_index >= len(self._link_urls):
            self._current_link_index = 0 # Wrap around to the first link
        
        self._highlight_current_link()

    def action_cycle_links_backward(self) -> None:
        """Cycles focus backward through the available links, highlighting the previous one."""
        if not self._link_urls:
            return

        # Move focus away from the input widget so this view captures Enter keys.
        if self.query_one(Input).has_focus:
            self.query_one(Markdown).focus()

        self._current_link_index -= 1
        if self._current_link_index < 0:
            self._current_link_index = len(self._link_urls) - 1 # Wrap around to the last link
        
        self._highlight_current_link()

    def action_open_link(self) -> None:
        """Opens the currently focused (highlighted) link in the default web browser."""
        if self._current_link_index == -1 or not self._link_urls:
            return

        try:
            url_to_open = self._link_urls[self._current_link_index]
            self.app.notify(f"Opening {url_to_open}...")
            webbrowser.open(url_to_open)
        except webbrowser.Error:
            # This is the most common and actionable error.
            self.app.notify(
                "No web browser found. Please configure your system's default browser.",
                severity="error",
                timeout=8
            )
        except IndexError:
            # This indicates a potential logic error in the app.
            self.app.notify("Internal error: Invalid link index.", severity="error")
        except Exception as e:
            # Catch any other unexpected errors.
            self.app.notify(f"An unexpected error occurred: {e}", severity="error")