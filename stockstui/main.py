import datetime
from pathlib import Path
import copy
import json
import logging
import time
from typing import Union
import sys
import os
import shutil
import subprocess

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.actions import SkipAction
from textual.containers import Container, Horizontal, Vertical
from textual.dom import NoMatches
from textual.reactive import reactive
from textual.theme import Theme
from textual.widgets import (Button, Checkbox, DataTable, Footer,
                             Input, Label, ListView, ListItem,
                             Select, Static, Tab, Tabs, Markdown, Switch, RadioButton)
from textual import on, work
from rich.text import Text

from stockstui.config_manager import ConfigManager
from stockstui.common import (PriceDataUpdated, NewsDataUpdated,
                              TickerDebugDataUpdated, ListDebugDataUpdated, CacheTestDataUpdated,
                              MarketStatusUpdated, HistoricalDataUpdated, TickerInfoComparisonUpdated)
from stockstui.ui.widgets.search_box import SearchBox
from stockstui.ui.views.config_view import ConfigView
from stockstui.ui.views.history_view import HistoryView
from stockstui.ui.views.news_view import NewsView
from stockstui.ui.views.debug_view import DebugView
from stockstui.data_providers import market_provider
from stockstui.presentation import formatter
from stockstui.utils import extract_cell_text

# A base template for all themes. It defines the required keys and uses
# placeholder variables (e.g., '$blue') that will be substituted with
# concrete colors from a specific theme's palette.
BASE_THEME_STRUCTURE = {
    "dark": False,
    "primary": "$blue",
    "secondary": "$cyan",
    "accent": "$orange",
    "success": "$green",
    "warning": "$yellow",
    "error": "$red",
    "background": "$bg3",
    "surface": "$bg2",
    "panel": "$bg1",
    "foreground": "$fg0",
    "variables": {
        "price": "$cyan",
        "latency-high": "$red",
        "latency-medium": "$yellow",
        "latency-low": "$blue",
        "text-muted": "$fg1",
        "status-open": "$green",
        "status-pre": "$yellow",
        "status-post": "$yellow",
        "status-closed": "$red",
        "button-foreground": "$fg3",
        "scrollbar": "$bg0",
        "scrollbar-hover": "$fg2",
    }
}

def substitute_colors(template: dict, palette: dict) -> dict:
    """
    Recursively substitutes color variables (e.g., '$blue') in a theme
    structure with concrete color values from a palette.
    """
    resolved = {}
    for key, value in template.items():
        if isinstance(value, dict):
            # Recurse for nested dictionaries (like 'variables').
            resolved[key] = substitute_colors(value, palette)
        elif isinstance(value, str) and value.startswith('$'):
            # If the value is a variable, look it up in the palette.
            color_name = value[1:]
            resolved[key] = palette.get(color_name, f"UNDEFINED_{color_name.upper()}")
        else:
            # Otherwise, use the value as is.
            resolved[key] = value
    return resolved

class StocksTUI(App):
    """
    The main application class for the Stocks Terminal User Interface.
    This class orchestrates the entire application, including UI composition,
    state management, data fetching, and event handling.
    """
    # The CSS file is now inside the package, so we need to tell Textual to load it from there
    CSS_PATH = "main.css"
    ENABLE_COMMAND_PALETTE = False
    
    # Define all key bindings for the application.
    # Bindings with 'show=False' are active but not displayed in the footer.
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True, show=True),
        Binding("Z", "quit", "Quit", priority=True, show=False),
        Binding("r", "refresh(True)", "Refresh", show=True),
        Binding("R", "refresh_all", "Refresh All", show=True),
        Binding("s", "enter_sort_mode", "Sort", show=True),
        Binding("/", "focus_search", "Search", show=True),
        Binding("?", "toggle_help", "Toggle Help", show=True),
        Binding("i", "focus_input", "Input", show=False),
        Binding("d", "handle_sort_key('d')", "Sort by Description/Date", show=False),
        Binding("p", "handle_sort_key('p')", "Sort by Price", show=False),
        Binding("c", "handle_sort_key('c')", "Sort by Change/Close", show=False),
        Binding("e", "handle_sort_key('e')", "Sort by % Change", show=False),
        Binding("t", "handle_sort_key('t')", "Sort by Ticker", show=False),
        Binding("u", "handle_sort_key('u')", "Undo Sort", show=False),
        Binding("o", "handle_sort_key('o')", "Sort by Open", show=False),
        Binding("H", "handle_sort_key('H')", "Sort by High", show=False),
        Binding("L", "handle_sort_key('L')", "Sort by Low", show=False),
        Binding("v", "handle_sort_key('v')", "Sort by Volume", show=False),
        Binding("ctrl+c", "copy_text", "Copy", show=False),
        Binding("ctrl+C", "copy_text", "Copy", show=False),
        Binding("escape,ctrl+[", "clear_sort_mode", "Dismiss or Focus Tabs", show=False, priority=True),
        Binding("k,up", "move_cursor('up')", "Up", show=False),
        Binding("j,down", "move_cursor('down')", "Down", show=False),
        Binding("h,left", "move_cursor('left')", "Left", show=False),
        Binding("l,right", "move_cursor('right')", "Right", show=False),
    ]

    # Reactive variables trigger UI updates when their values change.
    active_list_category = reactive(None)
    news_ticker = reactive(None)
    history_ticker = reactive(None)
    search_target_table = reactive(None)

    def __init__(self):
        """Initializes the application state and loads configurations."""
        super().__init__()
        # ConfigManager now needs the path to the package root to find default_configs
        self.config = ConfigManager(Path(__file__).resolve().parent)
        self.refresh_timer = None
        
        # Internal state management variables
        self._last_refresh_times = {}
        self._available_theme_names = []
        self._processed_themes = {}
        self.theme_variables = {}
        self._original_table_data = []
        self._last_historical_data = None
        self._news_content_for_ticker: str | None = None
        self._last_news_content: tuple[Union[str, Text], list[str]] | None = None
        self._sort_column_key: str | None = None
        self._sort_reverse: bool = False
        self._history_sort_column_key: str | None = None
        self._history_sort_reverse: bool = False
        self._history_period = "1mo"
        self._sort_mode = False
        self._original_status_text = None
        
        self._setup_dynamic_tabs()

    def compose(self) -> ComposeResult:
        """
        Creates the static layout of the application.
        Widgets are mounted here, but their content is populated later.
        """
        with Vertical(id="app-body"):
            yield Tabs(id="tabs-container")
            with Container(id="app-grid"):
                yield Container(id="output-container")
                yield ConfigView(id="config-container")
            with Horizontal(id="status-bar-container"):
                yield Label("Market Status: Unknown", id="market-status")
                yield Label("Last Refresh: Never", id="last-refresh-time")
        yield Footer()

    def on_mount(self) -> None:
        """
        Called when the app is first mounted.
        This is where we initialize dynamic content and start background tasks.
        """
        logging.info("Application mounting.")
        
        # Load and set up themes and initial config settings.
        self._load_and_register_themes()
        active_theme = self.config.get_setting("theme", "gruvbox_soft_dark")
        self.app.theme = active_theme
        self._update_theme_variables(active_theme)
        
        # Populate the config view with current settings.
        config_view = self.query_one(ConfigView)
        config_view.query_one("#theme-select", Select).set_options([(t, t) for t in self._available_theme_names])
        config_view.query_one("#theme-select", Select).value = active_theme
        config_view.query_one("#auto-refresh-switch", Switch).value = self.config.get_setting("auto_refresh", False)
        config_view.query_one("#refresh-interval-input", Input).value = str(self.config.get_setting("refresh_interval", 300.0))
        config_view.query_one("#market-calendar-select", Select).value = self.config.get_setting("market_calendar", "NYSE")

        # Perform initial setup and data fetch.
        self.call_after_refresh(self._rebuild_app)
        self.call_after_refresh(self._manage_refresh_timer)
        self.call_after_refresh(self.action_refresh, force=True)
        logging.info("Application mount complete.")
        
    def on_unmount(self) -> None:
        """Clean up background tasks when the app is closed."""
        self.workers.cancel_all()

    #region UI and App State Management
    def _get_alias_map(self) -> dict[str, str]:
        """Creates a mapping from ticker symbol to its user-defined alias."""
        alias_map = {}
        for list_data in self.config.lists.values():
            for item in list_data:
                ticker = item.get('ticker')
                alias = item.get('alias')
                if ticker and alias:
                    alias_map[ticker] = alias
        return alias_map

    def _load_and_register_themes(self):
        """
        Loads theme palettes from config, resolves them against the base structure,
        and registers them with Textual so they can be used.
        """
        valid_themes = {}
        for name, theme_data in self.config.themes.items():
            palette = theme_data.get("palette")
            if not palette:
                logging.warning(f"Theme '{name}' has no 'palette' defined. Skipping.")
                continue

            try:
                # Create a resolved theme by substituting palette colors into the base template.
                resolved_theme_dict = copy.deepcopy(BASE_THEME_STRUCTURE)
                resolved_theme_dict = substitute_colors(resolved_theme_dict, palette)
                resolved_theme_dict['dark'] = theme_data.get('dark', False)
                
                # Ensure all color variables were resolved.
                resolved_json = json.dumps(resolved_theme_dict)
                if "UNDEFINED_" in resolved_json:
                    raise ValueError(f"Theme '{name}' is missing one or more required color definitions in its palette.")

                self.register_theme(Theme(name=name, **resolved_theme_dict))
                valid_themes[name] = resolved_theme_dict
            except Exception as e:
                self.notify(f"Theme '{name}' failed to load: {e}", severity="error", timeout=10)
        
        self._processed_themes = valid_themes
        self._available_theme_names = sorted(list(valid_themes.keys()))

    def _update_theme_variables(self, theme_name: str):
        """
        Updates the internal theme variable snapshot for programmatic styling
        (e.g., dynamically coloring rows in a DataTable).
        """
        if theme_name in self._processed_themes:
            theme_dict = self._processed_themes[theme_name]
            self.theme_variables = {
                "primary": theme_dict.get("primary"),
                "secondary": theme_dict.get("secondary"),
                "accent": theme_dict.get("accent"),
                "success": theme_dict.get("success"),
                "warning": theme_dict.get("warning"),
                "error": theme_dict.get("error"),
                "foreground": theme_dict.get("foreground"),
                "background": theme_dict.get("background"),
                "surface": theme_dict.get("surface"),
                **theme_dict.get("variables", {})
            }

    def _setup_dynamic_tabs(self):
        """
        Generates the list of tabs to be displayed based on user configuration
        (i.e., defined lists and hidden tabs).
        """
        self.tab_map = []
        hidden_tabs = set(self.config.get_setting("hidden_tabs", []))
        all_possible_categories = ["all"] + list(self.config.lists.keys()) + ["history", "news", "debug"]
        for category in all_possible_categories:
            if category not in hidden_tabs: self.tab_map.append({'name': category.replace("_", " ").capitalize(), 'category': category})
        self.tab_map.append({'name': "Configs", 'category': 'configs'})

    async def _rebuild_app(self, new_active_category: str | None = None):
        """
        Rebuilds dynamic parts of the UI, primarily the tabs and config screen widgets.
        This is called on startup and after any change that affects tabs or lists.
        """
        self._setup_dynamic_tabs()
        tabs_widget = self.query_one(Tabs)
        current_active_cat = new_active_category or self.get_active_category()
        await tabs_widget.clear()
        
        # Recreate the tabs.
        for i, tab_data in enumerate(self.tab_map, start=1):
            await tabs_widget.add_tab(Tab(f"{i}: {tab_data['name']}", id=f"tab-{i}"))
        self._update_tab_bindings()
        
        # Determine which tab should be active after the rebuild.
        try:
            idx_to_activate = next(i for i, t in enumerate(self.tab_map, start=1) if t['category'] == current_active_cat)
        except (StopIteration, NoMatches):
            default_cat = self.config.get_setting("default_tab_category", "all")
            try:
                idx_to_activate = next(i for i, t in enumerate(self.tab_map, start=1) if t['category'] == default_cat)
            except (StopIteration, NoMatches):
                idx_to_activate = 1
        
        if tabs_widget.tab_count >= idx_to_activate:
            tabs_widget.active = f"tab-{idx_to_activate}"
        
        # Repopulate the selects and checkboxes in the ConfigView.
        config_view = self.query_one(ConfigView)
        default_tab_select = config_view.query_one("#default-tab-select", Select)
        options = [(t['name'], t['category']) for t in self.tab_map if t['category'] not in ['configs', 'history', 'news', 'debug']]
        default_tab_select.set_options(options)
        default_cat_value = self.config.get_setting("default_tab_category", "all")
        valid_option_values = [opt[1] for opt in options]
        if default_cat_value in valid_option_values:
            default_tab_select.value = default_cat_value
        elif options:
            default_tab_select.value = options[0][1]
        else:
            default_tab_select.clear()
        
        vis_container = config_view.query_one("#visible-tabs-container")
        await vis_container.remove_children()
        all_cats_for_toggle = ["all"] + list(self.config.lists.keys()) + ["history", "news", "debug"]
        hidden = set(self.config.get_setting("hidden_tabs", []))
        for cat in all_cats_for_toggle:
            checkbox = Checkbox(cat.replace("_", " ").capitalize(), cat not in hidden, name=cat)
            await vis_container.mount(checkbox)
            
        self._populate_symbol_list_view()

    def get_active_category(self) -> str | None:
        """Returns the category string (e.g., 'stocks', 'crypto') of the currently active tab."""
        try:
            active_tab_id = self.query_one(Tabs).active
            if active_tab_id:
                # e.g., 'tab-1' -> index 0
                return self.tab_map[int(active_tab_id.split('-')[1]) - 1]['category']
        except (NoMatches, IndexError, ValueError):
            return None
            
    def _update_tab_bindings(self):
        """Binds number keys (1-9, 0) to select the corresponding tab."""
        for i in range(1, 10): self.bind(str(i), f"select_tab({i})", description=f"Tab {i}", show=False)
        self.bind("0", "select_tab(10)", description="Tab 10", show=False)

    def action_select_tab(self, tab_index: int):
        """Action to switch to a tab by its number."""
        try:
            tabs = self.query_one(Tabs)
            if tab_index <= tabs.tab_count:
                tabs.active = f"tab-{tab_index}"
        except NoMatches:
            pass

    def action_copy_text(self) -> None:
        """Copies the currently selected text to the system clipboard."""
        selection = self.screen.get_selected_text()
        if selection is None:
            raise SkipAction()
        self.copy_to_clipboard(selection)

    def _manage_refresh_timer(self):
        """Starts or stops the auto-refresh timer based on the user's config."""
        if self.refresh_timer:
            self.refresh_timer.stop()
        if self.config.get_setting("auto_refresh", False):
            try:
                interval = float(self.config.get_setting("refresh_interval", 300.0))
                self.refresh_timer = self.set_interval(interval, lambda: self.action_refresh(force=True))
            except (ValueError, TypeError):
                logging.error("Invalid refresh interval.")

    def _populate_symbol_list_view(self):
        """Populates the list of symbol categories in the Config view."""
        try:
            config_view = self.query_one(ConfigView)
            view = config_view.query_one("#symbol-list-view", ListView)
            current_idx = view.index
            view.clear()
            categories = list(self.config.lists.keys())
            if not categories:
                self.active_list_category = None
                return
            for category in categories:
                view.append(ListItem(Label(category.replace("_", " ").capitalize()), name=category))
            if current_idx is not None and len(view.children) > current_idx:
                view.index = current_idx
            elif view.children and self.active_list_category is None:
                view.index = 0
                self.active_list_category = view.children[0].name
            
            config_view._update_list_highlight()
        except NoMatches:
            pass
    
    def action_refresh_all(self) -> None:
        """Action to force-refresh all price data, bypassing the cache."""
        self.action_refresh(force=True, force_all=True)

    def action_refresh(self, force: bool = False, force_all: bool = False):
        """
        Refreshes data for the current view.
        - force: Bypasses the cache for the current tab's symbols.
        - force_all: Bypasses the cache for *all* symbols across all lists.
        """
        self.fetch_market_status()
        
        if force_all:
            self.notify("Force refreshing all symbols in the background...")
            all_symbols = list(set(s['ticker'] for lst in self.config.lists.values() for s in lst))
            if all_symbols:
                self.fetch_prices(all_symbols, force=True, category='all')
        else:
            category = self.get_active_category()
            if category and category not in ["history", "news", "debug", "configs"]:
                symbols = [s['ticker'] for s in self.config.lists.get(category, [])] if category != 'all' else [s['ticker'] for lst in self.config.lists.values() for s in lst]
                if symbols:
                    try:
                        price_table = self.query_one("#price-table", DataTable)
                        if force:
                            price_table.loading = True
                    except NoMatches:
                        pass
                    self.fetch_prices(symbols, force=force, category=category)

    def action_toggle_help(self) -> None:
        """Action to show or hide the help panel."""
        if self.query("HelpPanel"): self.action_hide_help_panel()
        else: self.action_show_help_panel()

    def action_move_cursor(self, direction: str) -> None:
        """
        Handles unified hjkl/arrow key navigation.
        It prioritizes moving the cursor in the currently focused widget.
        If the widget doesn't support cursor movement, it falls back to scrolling
        the main content area.
        """
        category = self.get_active_category()
        # In news view, up/down/j/k should always scroll the content.
        if category == 'news' and direction in ('up', 'down'):
            if (scrollable := self._get_active_scrollable_widget()):
                if direction == "up":
                    scrollable.scroll_up(duration=0.5)
                else:
                    scrollable.scroll_down(duration=0.5)
                return

        # Priority 1: Main Tabs navigation
        if self.focused and isinstance(self.focused, Tabs):
            if direction == 'left': self.focused.action_previous_tab()
            elif direction == 'right': self.focused.action_next_tab()
            return

        # Priority 2: Generic cursor movement for widgets that support it.
        if self.focused and hasattr(self.focused, f"action_cursor_{direction}"):
            getattr(self.focused, f"action_cursor_{direction}")()
            return

        # Priority 3: Fallback to scrolling the container for up/down
        if direction in ("up", "down"):
            if (scrollable := self._get_active_scrollable_widget()):
                if direction == "up": scrollable.scroll_up(duration=0.5)
                else: scrollable.scroll_down(duration=0.5)
    
    def _get_active_scrollable_widget(self) -> Container | None:
        """
        Determines the currently visible main container that should be scrolled
        by the fallback `move_cursor` logic.
        """
        config_container = self.query_one("#config-container")
        if config_container.display: return config_container
        output_container = self.query_one("#output-container")
        if output_container.display:
            try: return output_container.query_one("#news-output-display")
            except NoMatches: pass
            try: return output_container.query_one("#history-display-container")
            except NoMatches: pass
            return output_container
        return None
    #endregion

    #region Data Flow
    async def _display_data_for_category(self, category: str):
        """
        Renders the main content area based on the selected tab's category.
        This method is the router that decides whether to show a price table,
        the history view, the news view, etc.
        """
        output_container = self.query_one("#output-container")
        config_container = self.query_one("#config-container")
        await output_container.remove_children()

        # Toggle visibility between the main output and config screens.
        is_config_tab = category == "configs"
        config_container.display = is_config_tab
        output_container.display = not is_config_tab
        self.query_one("#status-bar-container").display = not is_config_tab
        if is_config_tab:
            return

        if category == 'history':
            await output_container.mount(HistoryView())
        elif category == 'news':
            await output_container.mount(NewsView())
        elif category == 'debug':
            await output_container.mount(DebugView())
        else: # This is a price view for 'all' or a specific list
            await output_container.mount(DataTable(id="price-table", zebra_stripes=True))
            price_table = self.query_one("#price-table", DataTable)
            price_table.add_column("Description", key="Description")
            price_table.add_column("Price", key="Price")
            price_table.add_column("Change", key="Change")
            price_table.add_column("% Change", key="% Change")
            price_table.add_column("Day's Range", key="Day's Range")
            price_table.add_column("52-Wk Range", key="52-Wk Range")
            price_table.add_column("Ticker", key="Ticker")

            symbols = [s['ticker'] for s in self.config.lists.get(category, [])] if category != 'all' else [s['ticker'] for lst in self.config.lists.values() for s in lst]
            
            # If there's no cached data for this tab's symbols, trigger a fetch.
            if symbols and not any(s.upper() in market_provider._price_cache for s in symbols):
                price_table.loading = True
                self.fetch_prices(symbols, force=False, category=category)
            else: # Otherwise, populate the table from the existing cache.
                cached_data = [market_provider._price_cache[s.upper()][1] for s in symbols if s.upper() in market_provider._price_cache]
                if cached_data:
                    alias_map = self._get_alias_map()
                    rows = formatter.format_price_data_for_table(cached_data, alias_map)
                    self._style_and_populate_price_table(price_table, rows)
                    self._apply_price_table_sort()
                elif not symbols:
                    price_table.add_row(f"[dim]No symbols in list '{category}'[/dim]")

    @work(exclusive=True, thread=True)
    def fetch_prices(self, symbols: list[str], force: bool, category: str):
        """Worker to fetch market price data in the background."""
        try:
            data = market_provider.get_market_price_data(symbols, force_refresh=force)
            self.post_message(PriceDataUpdated(data, category))
        except Exception as e:
            logging.error(f"Worker fetch_prices failed for category '{category}': {e}")

    @work(exclusive=True, thread=True)
    def fetch_market_status(self):
        """Worker to fetch the current market status."""
        calendar = self.config.get_setting("market_calendar", "NYSE")
        try:
            status = market_provider.get_market_status(calendar)
            self.post_message(MarketStatusUpdated(status))
        except Exception as e:
            logging.error(f"Market status worker failed: {e}")

    @work(exclusive=True, thread=True)
    def fetch_news(self, ticker: str):
        """Worker to fetch news data for a specific ticker."""
        try:
            data = market_provider.get_news_data(ticker)
            self.post_message(NewsDataUpdated(ticker, data))
        except Exception as e:
            logging.error(f"Worker fetch_news failed for {ticker}: {e}")
            # On ANY exception, send None to signal a failure to the UI.
            self.post_message(NewsDataUpdated(ticker, None))
            
    @work(exclusive=True, thread=True)
    def fetch_historical_data(self, ticker: str, period: str, interval: str = "1d"):
        """Worker to fetch historical price data for a specific ticker."""
        try:
            data = market_provider.get_historical_data(ticker, period, interval)
            self.post_message(HistoricalDataUpdated(data))
        except Exception as e:
            logging.error(f"Worker fetch_historical_data failed for {ticker} over {period} with interval {interval}: {e}")

    @work(exclusive=True, thread=True)
    def run_info_comparison_test(self, ticker: str):
        """Worker to fetch fast vs slow ticker info for the debug tab."""
        data = market_provider.get_ticker_info_comparison(ticker)
        self.post_message(TickerInfoComparisonUpdated(fast_info=data['fast'], slow_info=data['slow']))

    @work(exclusive=True, thread=True)
    def run_ticker_debug_test(self, symbols: list[str]):
        """Worker to run the individual ticker latency test."""
        start_time = time.perf_counter()
        data = market_provider.run_ticker_debug_test(symbols)
        total_time = time.perf_counter() - start_time
        self.post_message(TickerDebugDataUpdated(data, total_time))
        
    @work(exclusive=True, thread=True)
    def run_list_debug_test(self, lists: dict[str, list[str]]):
        """Worker to run the list batch network test."""
        start_time = time.perf_counter()
        data = market_provider.run_list_debug_test(lists)
        total_time = time.perf_counter() - start_time
        self.post_message(ListDebugDataUpdated(data, total_time))

    @work(exclusive=True, thread=True)
    def run_cache_test(self, lists: dict[str, list[str]]):
        """Worker to run the local cache speed test."""
        start_time = time.perf_counter()
        data = market_provider.run_cache_test(lists)
        total_time = time.perf_counter() - start_time
        self.post_message(CacheTestDataUpdated(data, total_time))

    def _style_and_populate_price_table(self, price_table: DataTable, rows: list[tuple]):
        """
        Applies dynamic styling (colors) to the raw data and populates
        the main price table.
        """
        price_color = self.theme_variables.get("price", "cyan")
        success_color = self.theme_variables.get("success", "green")
        error_color = self.theme_variables.get("error", "red")
        muted_color = self.theme_variables.get("text-muted", "dim")

        for row_data in rows:
            desc, price, change, change_percent, day_range, week_range, symbol = row_data
            
            # Style description based on content
            if desc == 'Invalid Ticker':
                desc_text = Text(desc, style=error_color)
            elif desc == 'N/A':
                desc_text = Text(desc, style=muted_color)
            else:
                desc_text = Text(desc)
            
            price_text = Text(f"${price:,.2f}", style=price_color, justify="right") if price is not None else Text("N/A", style=muted_color, justify="right")
            
            # Color the change and % change based on whether it's positive or negative.
            if change is not None and change_percent is not None:
                if change > 0:
                    change_text = Text(f"{change:,.2f}", style=success_color, justify="right")
                    change_percent_text = Text(f"+{change_percent:.2%}", style=success_color, justify="right")
                elif change < 0:
                    change_text = Text(f"{change:,.2f}", style=error_color, justify="right")
                    change_percent_text = Text(f"{change_percent:.2%}", style=error_color, justify="right")
                else:
                    change_text = Text("0.00", justify="right")
                    change_percent_text = Text("0.00%", justify="right")
            else:
                change_text = Text("N/A", style=muted_color, justify="right")
                change_percent_text = Text("N/A", style=muted_color, justify="right")
            
            day_range_text = Text(day_range, style=muted_color if day_range == "N/A" else "", justify="right")
            week_range_text = Text(week_range, style=muted_color if week_range == "N/A" else "", justify="right")
            ticker_text = Text(symbol, style=muted_color)
            price_table.add_row(desc_text, price_text, change_text, change_percent_text, day_range_text, week_range_text, ticker_text, key=symbol)

    @on(PriceDataUpdated)
    async def on_price_data_updated(self, message: PriceDataUpdated):
        """Handles the arrival of new price data from a worker."""
        # Update last refresh time.
        now_str = f"Last Refresh: {datetime.datetime.now():%H:%M:%S}"
        if message.category == 'all':
            for cat in list(self.config.lists.keys()) + ['all']:
                self._last_refresh_times[cat] = now_str
        else:
            self._last_refresh_times[message.category] = now_str
        
        # Check if the updated data is for the currently active tab.
        active_category = self.get_active_category()
        is_relevant = (active_category == message.category) or \
                      (message.category == 'all' and active_category not in ['history', 'news', 'debug', 'configs'])

        if not is_relevant:
            return

        try:
            dt = self.query_one("#price-table", DataTable)
            dt.loading = False
            dt.clear()
            
            # Determine which symbols should be displayed on the current active tab
            symbols_to_display = []
            if active_category == 'all':
                symbols_to_display = [s['ticker'] for lst in self.config.lists.values() for s in lst]
            elif active_category:
                symbols_to_display = [s['ticker'] for s in self.config.lists.get(active_category, [])]

            # Filter the cached data to only what should be on the current tab.
            data_for_table = [
                market_provider._price_cache[s.upper()][1] 
                for s in symbols_to_display 
                if s.upper() in market_provider._price_cache
            ]

            if not data_for_table and symbols_to_display:
                 dt.add_row("[dim]Could not fetch data for any symbols in this list.[/dim]")
                 return

            # Format, style, and populate the table.
            alias_map = self._get_alias_map()
            rows = formatter.format_price_data_for_table(data_for_table, alias_map)
            self._style_and_populate_price_table(dt, rows)
            self._apply_price_table_sort()
            self.query_one("#last-refresh-time").update(now_str)
        except NoMatches: pass
    
    @on(MarketStatusUpdated)
    async def on_market_status_updated(self, message: MarketStatusUpdated):
        """Handles the arrival of new market status data."""
        try:
            status_parts = formatter.format_market_status(message.status)
            if not status_parts:
                self.query_one("#market-status").update(Text("Market: Unknown", style="dim"))
                return

            calendar, status, holiday = status_parts
            status_color_map = {
                "open": self.theme_variables.get("status-open", "green"),
                "pre": self.theme_variables.get("status-pre", "yellow"),
                "post": self.theme_variables.get("status-post", "yellow"),
                "closed": self.theme_variables.get("status-closed", "red"),
            }
            status_text_map = {"open": "Open", "pre": "Pre-Market", "post": "After Hours", "closed": "Closed"}
            status_color = status_color_map.get(status, "dim")
            status_display = status_text_map.get(status, "Unknown")
            
            # Assemble the final text with colors.
            text = Text.assemble(f"{calendar}: ", (f"{status_display}", status_color))
            if holiday and status == 'closed':
                holiday_display = holiday[:20] + '...' if len(holiday) > 20 else holiday
                text.append(f" ({holiday_display})", style=self.theme_variables.get("text-muted", "dim"))
            
            self.query_one("#market-status").update(text)
        except NoMatches: pass

    @on(HistoricalDataUpdated)
    async def on_historical_data_updated(self, message: HistoricalDataUpdated):
        """Handles arrival of historical data, then tells the history view to render it."""
        try:
            self.query_one("#history-display-container").loading = False
        except NoMatches: return

        self._last_historical_data = message.data
        try:
            history_view = self.query_one(HistoryView)
            await history_view._render_historical_data()
        except NoMatches: pass

    @on(NewsDataUpdated)
    async def on_news_data_updated(self, message: NewsDataUpdated):
        """Handles arrival of news data, then tells the news view to render it."""
        self._news_content_for_ticker = message.ticker
        
        # `None` is the universal signal for any failure (invalid ticker, network error, etc.)
        if message.data is None:
            # Create a string using standard Markdown syntax.
            error_markdown = (
                f"**Error:** Could not retrieve news for '{message.ticker}'.\n\n"
                "This may be due to an invalid symbol or a network connectivity issue."
            )
            self._last_news_content = (error_markdown, [])
        else: # Ticker was valid and data was fetched, format the news data
            self._last_news_content = formatter.format_news_for_display(message.data)
        
        if self.get_active_category() == 'news' and self.news_ticker == message.ticker:
            try:
                news_view = self.query_one(NewsView)
                news_view.update_content(*self._last_news_content)
            except NoMatches:
                pass

    @on(TickerInfoComparisonUpdated)
    async def on_ticker_info_comparison_updated(self, message: TickerInfoComparisonUpdated):
        """Handles arrival of the fast/slow info comparison test data."""
        try:
            # Re-enable the test buttons.
            for button in self.query(".debug-buttons Button"):
                button.disabled = False
            
            dt = self.query_one("#debug-table", DataTable)
            dt.loading = False
            dt.clear()
            
            rows = formatter.format_info_comparison(message.fast_info, message.slow_info)
            muted_color = self.theme_variables.get("text-muted", "dim")
            warning_color = self.theme_variables.get("warning", "yellow")

            for key, fast_val, slow_val, is_mismatch in rows:
                if is_mismatch:
                    fast_text = Text(fast_val, style=warning_color)
                    slow_text = Text(slow_val, style=warning_color)
                else:
                    fast_text = Text(fast_val, style=muted_color if fast_val == "N/A" else "")
                    slow_text = Text(slow_val, style=muted_color if slow_val == "N/A" else "")
                
                dt.add_row(key, fast_text, slow_text)
        except NoMatches:
            pass
    
    @on(TickerDebugDataUpdated)
    async def on_ticker_debug_data_updated(self, message: TickerDebugDataUpdated):
        """Handles arrival of the individual ticker latency test data."""
        try:
            for button in self.query(".debug-buttons Button"): button.disabled = False
            dt = self.query_one("#debug-table", DataTable); dt.loading = False; dt.clear()
            rows = formatter.format_ticker_debug_data_for_table(message.data)
            success_color = self.theme_variables.get("success", "green"); error_color = self.theme_variables.get("error", "red"); lat_high = self.theme_variables.get("latency-high", "red"); lat_med = self.theme_variables.get("latency-medium", "yellow"); lat_low = self.theme_variables.get("latency-low", "blue"); muted_color = self.theme_variables.get("text-muted", "dim")
            for symbol, is_valid, description, latency in rows:
                valid_text = Text("Yes", style=success_color) if is_valid else Text("No", style=f"bold {error_color}")
                if latency > 2.0: latency_style = lat_high
                elif latency > 0.5: latency_style = lat_med
                else: latency_style = lat_low
                latency_text = Text(f"{latency:.3f}s", style=latency_style, justify="right")
                desc_text = Text(description, style=muted_color if not is_valid or description == 'N/A' else "")
                dt.add_row(symbol, valid_text, desc_text, latency_text)
            total_time_text = Text.assemble("Test Completed. Total time: ", (f"{message.total_time:.2f}s", f"bold {self.theme_variables.get('warning')}"))
            self.query_one("#last-refresh-time").update(total_time_text)
        except NoMatches: pass
            
    @on(ListDebugDataUpdated)
    async def on_list_debug_data_updated(self, message: ListDebugDataUpdated):
        """Handles arrival of the list batch network test data."""
        try:
            for button in self.query(".debug-buttons Button"): button.disabled = False
            dt = self.query_one("#debug-table", DataTable); dt.loading = False; dt.clear()
            rows = formatter.format_list_debug_data_for_table(message.data)
            lat_high = self.theme_variables.get("latency-high", "red"); lat_med = self.theme_variables.get("latency-medium", "yellow"); lat_low = self.theme_variables.get("latency-low", "blue"); muted_color = self.theme_variables.get("text-muted", "dim")
            for list_name, ticker_count, latency in rows:
                if latency > 5.0: latency_style = lat_high
                elif latency > 2.0: latency_style = lat_med
                else: latency_style = lat_low
                latency_text = Text(f"{latency:.3f}s", style=latency_style, justify="right")
                list_name_text = Text(list_name, style=muted_color if list_name == 'N/A' else "")
                dt.add_row(list_name_text, str(ticker_count), latency_text)
            total_time_text = Text.assemble("Test Completed. Total time: ", (f"{message.total_time:.2f}s", f"bold {self.theme_variables.get('warning')}"))
            self.query_one("#last-refresh-time").update(total_time_text)
        except NoMatches: pass

    @on(CacheTestDataUpdated)
    async def on_cache_test_data_updated(self, message: CacheTestDataUpdated):
        """Handles arrival of the local cache speed test data."""
        try:
            for button in self.query(".debug-buttons Button"): button.disabled = False
            dt = self.query_one("#debug-table", DataTable); dt.loading = False; dt.clear()
            rows = formatter.format_cache_test_data_for_table(message.data)
            price_color = self.theme_variables.get("price", "cyan"); muted_color = self.theme_variables.get("text-muted", "dim")
            for list_name, ticker_count, latency in rows:
                latency_text = Text(f"{latency * 1000:.3f} ms", style=price_color, justify="right")
                list_name_text = Text(list_name, style=muted_color if list_name == 'N/A' else "")
                dt.add_row(list_name_text, str(ticker_count), latency_text)
            total_time_text = Text.assemble("Test Completed. Total time: ", (f"{message.total_time * 1000:.2f} ms", f"bold {self.theme_variables.get('price')}"))
            self.query_one("#last-refresh-time").update(total_time_text)
        except NoMatches: pass
    
    def _apply_price_table_sort(self) -> None:
        """Applies the current sort order to the price table."""
        if self._sort_column_key is None: return
        try:
            table = self.query_one("#price-table", DataTable)
            def sort_key(row_values: tuple) -> tuple[int, any]:
                column_index = table.get_column_index(self._sort_column_key)
                if column_index >= len(row_values): return (1, 0)
                cell_value = row_values[column_index]
                text_content = extract_cell_text(cell_value)
                if text_content in ("N/A", "Invalid Ticker"): return (1, 0)
                if self._sort_column_key in ("Description", "Ticker"):
                    return (0, text_content.lower())
                cleaned_text = text_content.replace("$", "").replace(",", "").replace("%", "").replace("+", "")
                try: return (0, float(cleaned_text))
                except (ValueError, TypeError): return (1, 0)
            table.sort(key=sort_key, reverse=self._sort_reverse)
        except (NoMatches, KeyError): logging.error(f"Could not find table or column for sort key '{self._sort_column_key}'")
            
    def _apply_history_table_sort(self) -> None:
        """Applies the current sort order to the history table."""
        if self._history_sort_column_key is None: return
        try:
            table = self.query_one("#history-table", DataTable)
            def sort_key(row_values: tuple) -> tuple[int, any]:
                column_index = table.get_column_index(self._history_sort_column_key)
                if column_index >= len(row_values): return (1, 0)
                text_content = extract_cell_text(row_values[column_index])
                if self._history_sort_column_key == "Date":
                    try: return (0, text_content)
                    except (ValueError, TypeError): return (1, "")
                cleaned_text = text_content.replace("$", "").replace(",", "")
                try: return (0, float(cleaned_text))
                except (ValueError, TypeError): return (1, 0)
            table.sort(key=sort_key, reverse=self._history_sort_reverse)
        except (NoMatches, KeyError): logging.error(f"Could not find history table or column for sort key '{self._history_sort_column_key}'")
    #endregion

    #region Event Handlers & Actions
    @on(Tabs.TabActivated)
    async def on_tabs_tab_activated(self, event: Tabs.TabActivated):
        """Handles tab switching. Resets sort state and displays new content."""
        self._sort_column_key = None; self._sort_reverse = False
        self._history_sort_column_key = None; self._history_sort_reverse = False
        
        active_category = self.get_active_category()
        await self._display_data_for_category(active_category)

        # Update the 'Last Refresh' status label.
        try:
            status_label = self.query_one("#last-refresh-time")
            if active_category in ['history', 'news', 'debug', 'configs']:
                status_label.update("")
            else:
                refresh_time = self._last_refresh_times.get(active_category, "Last Refresh: Never")
                status_label.update(refresh_time)
        except NoMatches:
            pass
        
    @on(DataTable.RowSelected, "#price-table")
    def on_main_datatable_row_selected(self, event: DataTable.RowSelected):
        """When a row is selected on the price table, set it as the active ticker for other views."""
        if event.row_key.value: 
            self.news_ticker = event.row_key.value
            self.history_ticker = event.row_key.value
            self.notify(f"Selected {self.news_ticker} for news/history tabs.")

    @on(DataTable.HeaderSelected, "#price-table")
    def on_price_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handles header clicks to sort the price table."""
        self._set_and_apply_sort(str(event.column_key.value), "click")

    def _set_and_apply_sort(self, column_key_str: str, source: str) -> None:
        """Sets the sort key and direction for the price table and applies it."""
        sortable_columns = {"Description", "Price", "Change", "% Change", "Ticker"}
        if column_key_str not in sortable_columns: return

        if self._sort_column_key == column_key_str:
            # If same column is selected, reverse the sort order.
            self._sort_reverse = not self._sort_reverse
        else:
            # If new column is selected, set it and default the direction.
            self._sort_column_key = column_key_str
            self._sort_reverse = column_key_str not in ("Description", "Ticker")
        self._apply_price_table_sort()
        
    def _set_and_apply_history_sort(self, column_key_str: str, source: str) -> None:
        """Sets the sort key and direction for the history table and applies it."""
        if self._history_sort_column_key == column_key_str:
            self._history_sort_reverse = not self._history_sort_reverse
        else:
            self._history_sort_column_key = column_key_str
            self._history_sort_reverse = column_key_str == "Date" # Default sort for date is descending.
        self._apply_history_table_sort()

    def action_enter_sort_mode(self) -> None:
        """Enters 'sort mode', displaying available sort keys in the status bar."""
        if self._sort_mode:
            return

        category = self.get_active_category()
        # Only enter sort mode on views with sortable tables.
        if category == 'history' or (category and category not in ['news', 'debug', 'configs']):
            self._sort_mode = True
            try:
                status_label = self.query_one("#last-refresh-time", Label)
                self._original_status_text = status_label.renderable
                if category == 'history':
                    status_label.update("SORT BY: \\[d]ate, \\[o]pen, \\[H]igh, \\[L]ow, \\[c]lose, \\[v]olume, \\[ESC]ape")
                else:
                    status_label.update("SORT BY: \\[d]escription, \\[p]rice, \\[c]hange, p\\[e]rcent, \\[t]icker, \\[u]ndo, \\[ESC]ape")
            except NoMatches: self._sort_mode = False
        else:
            self.bell() # Signal that sorting is not available.

    async def _undo_sort(self) -> None:
        """Restores the price table to its original, unsorted order."""
        self._sort_column_key = None
        self._sort_reverse = False
        await self._display_data_for_category(self.get_active_category())

    def action_clear_sort_mode(self) -> None:
        """
        Clears sort mode or dismisses the search box.
        This action is bound to 'escape'.
        """
        # Priority 1: Exit sort mode.
        if self._sort_mode:
            self._sort_mode = False
            try:
                status_label = self.query_one("#last-refresh-time", Label)
                if self._original_status_text is not None:
                    status_label.update(self._original_status_text)
            except NoMatches:
                pass
            return

        # Priority 2: Dismiss search box and restore original table rows.
        try:
            search_box = self.query_one(SearchBox)
            if self._original_table_data:
                self.search_target_table.clear()
                for row_key, row_data in self._original_table_data:
                    self.search_target_table.add_row(*row_data, key=row_key.value)
            search_box.remove()
            return
        except NoMatches:
            pass

        # Priority 3: Fallback to focusing the main tabs.
        try:
            self.query_one(Tabs).focus()
        except NoMatches:
            pass

    def action_focus_input(self) -> None:
        """Focus the primary input widget of the current view (e.g., ticker input)."""
        category = self.get_active_category()
        target_widget = None
        try:
            if category == 'history':
                target_widget = self.query_one('#history-ticker-input')
            elif category == 'news':
                target_widget = self.query_one('#news-ticker-input')
            elif category == 'configs':
                target_widget = self.query_one('#symbol-list-view')
            elif category == 'debug':
                target_widget = self.query_one('#debug-table')
            elif category and category not in ['configs', 'history', 'news', 'debug']:
                target_widget = self.query_one('#price-table')
        except NoMatches:
            pass

        if target_widget:
            target_widget.focus()

    async def action_handle_sort_key(self, key: str) -> None:
        """Handles a key press while in sort mode to apply a specific sort."""
        if not self._sort_mode:
            return

        target_view = 'history' if self.get_active_category() == 'history' else 'price'

        if key == 'u': # 'u' for 'undo'
            if target_view == 'price':
                await self._undo_sort()
                self.action_clear_sort_mode()
            return

        # Map the key press to the column key.
        column_map = {'d': {'price': 'Description', 'history': 'Date'}, 'p': {'price': 'Price'}, 'c': {'price': 'Change', 'history': 'Close'}, 'e': {'price': '% Change'}, 't': {'price': 'Ticker'}, 'o': {'history': 'Open'}, 'H': {'history': 'High'}, 'L': {'history': 'Low'}, 'v': {'history': 'Volume'},}

        if key not in column_map or target_view not in column_map[key]:
            return
        
        column_key_str = column_map[key][target_view]
        if target_view == 'history':
            self._set_and_apply_history_sort(column_key_str, f"key '{key}'")
        else:
            self._set_and_apply_sort(column_key_str, f"key '{key}'")
        
        self.action_clear_sort_mode()

    def action_focus_search(self):
        """Activates the search box for the current table view."""
        # If a search box is already on screen, just focus it.
        try:
            self.query_one(SearchBox).focus()
            return
        except NoMatches:
            # No search box exists, so we will create one if the view is searchable.
            pass

        # Determine which table is active and searchable.
        category = self.get_active_category()
        target_id = ""
        if category and category not in ['history', 'news', 'configs', 'debug']:
            target_id = "#price-table"
        elif category == 'debug':
            target_id = "#debug-table"
        elif category == 'configs':
            target_id = "#ticker-table"
        
        if not target_id:
            self.bell() # Indicate that search is not available on this tab.
            return

        try:
            table = self.query_one(target_id, DataTable)
            self.search_target_table = table
            # Store the original table data so we can restore it after search.
            self._original_table_data = []
            for row_key, row_data in table.rows.items():
                self._original_table_data.append((row_key, table.get_row(row_key)))
            
            # Mount and focus a new search box.
            search_box = SearchBox()
            self.mount(search_box)
            search_box.focus()
        except NoMatches:
            # This can happen if the target table exists but hasn't been populated yet.
            self.bell()

    @on(Input.Changed, '#search-box')
    def on_search_changed(self, event: Input.Changed):
        """Filters the target table as the user types in the search box."""
        query = event.value
        if not self.search_target_table: return
        from textual.fuzzy import Matcher
        matcher = Matcher(query)
        self.search_target_table.clear()
        
        if not query:
            # If query is empty, restore the original table.
            for row_key, row_data in self._original_table_data: self.search_target_table.add_row(*row_data, key=row_key.value)
            return
            
        # Filter rows based on fuzzy matching.
        for row_key, row_data in self._original_table_data:
            searchable_string = " ".join(extract_cell_text(cell) for cell in row_data)
            if matcher.match(searchable_string) > 0: self.search_target_table.add_row(*row_data, key=row_key.value)

    @on(Input.Submitted, '#search-box')
    def on_search_submitted(self, event: Input.Submitted):
        """Removes the search box when the user presses Enter."""
        try:
            self.query_one(SearchBox).remove()
        except NoMatches:
            pass
    #endregion

def show_help():
    """Displays the help file content using a pager like 'less' if available."""
    # This path is relative to the location of main.py inside the package
    help_path = Path(__file__).resolve().parent / "documents" / "help.txt"
    try:
        # Use shutil.which to find the path to 'less' in a cross-platform way.
        pager = shutil.which('less')
        if pager:
            # Use subprocess.run for a more robust way to call external commands.
            subprocess.run([pager, str(help_path)])
        else:
            # Fallback to just printing the content if 'less' is not found.
            with open(help_path, 'r') as f:
                print(f.read())
    except FileNotFoundError:
        print(f"Error: Help file not found at {help_path}")
    except Exception as e:
        print(f"An unexpected error occurred while trying to show help: {e}")

def main():
    """The main entry point for the application."""
    # Check for '-h' or '--help' before initializing the Textual app
    if "-h" in sys.argv or "--help" in sys.argv:
        show_help()
        return

    app = StocksTUI()
    app.run()

if __name__ == "__main__":
    main()