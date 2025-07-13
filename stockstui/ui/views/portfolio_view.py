from textual.containers import Vertical, Horizontal, Container
from textual.widgets import DataTable, Label, Button, Select, Input
from textual.app import ComposeResult, on
from textual.dom import NoMatches
from rich.text import Text

from stockstui.ui.modals import AddTickerModal, EditPortfolioModal, ConfirmDeleteModal

class PortfolioView(Vertical):
    """A view for displaying and managing portfolios of stocks."""
    
    def compose(self) -> ComposeResult:
        """Creates the layout for the portfolio view."""
        # Portfolio selector and management buttons
        with Horizontal(classes="portfolio-header"):
            yield Label("Portfolio:", classes="portfolio-label")
            yield Select([], id="portfolio-select")
            yield Button("New", id="new-portfolio")
            yield Button("Edit", id="edit-portfolio")
            yield Button("Delete", id="delete-portfolio", variant="error")
        
        # Stock table - group label and table in a container with reduced spacing
        with Vertical(classes="portfolio-content"):
            yield Label("Stocks in Portfolio", classes="section-header")
            yield DataTable(id="portfolio-table", zebra_stripes=True)
        
        # Stock management buttons
        with Horizontal(classes="stock-buttons"):
            yield Button("Add Stock", id="add-stock")
            yield Button("Remove Stock", id="remove-stock", variant="error")
    
    def on_mount(self) -> None:
        """Called when the PortfolioView is mounted."""
        # Set up the stock table
        stock_table = self.query_one("#portfolio-table", DataTable)
        stock_table.add_columns(
            "Ticker", "Description", "Price", "Change", "% Change", "Day's Range"
        )
        
        # Populate portfolio selector
        self._populate_portfolio_select()
    
    def _populate_portfolio_select(self) -> None:
        """Populates the portfolio selector with available portfolios."""
        portfolio_select = self.query_one("#portfolio-select", Select)
        portfolios = list(self.app.config.portfolios.keys())
        
        if portfolios:
            options = [(self.app.config.portfolios[p].get('name', p), p) for p in portfolios]
            portfolio_select.set_options(options)
            
            # Select the first portfolio by default
            portfolio_select.value = portfolios[0]
            self._load_portfolio(portfolios[0])
        else:
            # No portfolios available
            portfolio_select.set_options([("No portfolios available", "")])
            self._clear_portfolio_table()
    
    def _load_portfolio(self, portfolio_name: str) -> None:
        """Loads and displays the selected portfolio."""
        if not portfolio_name or portfolio_name not in self.app.config.portfolios:
            self._clear_portfolio_table()
            return
        
        portfolio_data = self.app.config.portfolios[portfolio_name]
        tickers = portfolio_data.get('tickers', [])
        
        # Clear the table
        self._clear_portfolio_table()
        
        if not tickers:
            # No stocks in this portfolio
            stock_table = self.query_one("#portfolio-table", DataTable)
            stock_table.add_row("[dim]No stocks in this portfolio[/dim]")
            return
        
        # Fetch price data for the tickers in this portfolio
        self.app.fetch_portfolio_prices(portfolio_name, tickers)
    
    def _clear_portfolio_table(self) -> None:
        """Clears the portfolio table."""
        stock_table = self.query_one("#portfolio-table", DataTable)
        stock_table.clear()
    
    def update_portfolio_data(self, portfolio_name: str, tickers: list[str], price_data: list[dict]) -> None:
        """Updates the portfolio table with the latest price data."""
        if not self.is_attached or self.query_one("#portfolio-select", Select).value != portfolio_name:
            return
        
        stock_table = self.query_one("#portfolio-table", DataTable)
        stock_table.clear()
        
        if not price_data:
            stock_table.add_row("[dim]No data available for stocks in this portfolio[/dim]")
            return
        
        # Get theme colors for styling
        price_color = self.app.theme_variables.get("price", "cyan")
        success_color = self.app.theme_variables.get("success", "green")
        error_color = self.app.theme_variables.get("error", "red")
        muted_color = self.app.theme_variables.get("text-muted", "dim")
        
        # Add rows for each ticker
        for item in price_data:
            symbol = item.get('symbol', 'N/A')
            
            # Style description based on content
            desc = item.get('description', 'N/A')
            if desc == 'Invalid Ticker':
                desc_text = Text(desc, style=error_color)
            elif desc == 'N/A':
                desc_text = Text(desc, style=muted_color)
            else:
                desc_text = Text(desc)
            
            # Format price
            price = item.get('price')
            price_text = Text(f"${price:,.2f}", style=price_color, justify="right") if price is not None else Text("N/A", style=muted_color, justify="right")
            
            # Calculate and format change
            prev_close = item.get('previous_close')
            if price is not None and prev_close is not None:
                change = price - prev_close
                change_percent = change / prev_close if prev_close != 0 else 0
                
                if change > 0:
                    change_text = Text(f"+{change:,.2f}", style=success_color, justify="right")
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
            
            # Format day's range
            day_low = item.get('day_low')
            day_high = item.get('day_high')
            if day_low is not None and day_high is not None:
                day_range = f"${day_low:,.2f} - ${day_high:,.2f}"
            else:
                day_range = "N/A"
            day_range_text = Text(day_range, style=muted_color if day_range == "N/A" else "", justify="right")
            
            # Add the row to the table
            stock_table.add_row(
                symbol, desc_text, price_text, change_text, 
                change_percent_text, day_range_text
            )
    
    @on(Select.Changed, "#portfolio-select")
    def on_portfolio_selected(self, event: Select.Changed) -> None:
        """Handles selection of a portfolio from the dropdown."""
        if event.value:
            self._load_portfolio(str(event.value))
    
    @on(Button.Pressed, "#new-portfolio")
    def on_new_portfolio_pressed(self) -> None:
        """Handles the 'New Portfolio' button press."""
        def on_modal_close(result: tuple[str, str] | None) -> None:
            if result:
                name, description = result
                
                # Create a new portfolio
                self.app.config.portfolios[name] = {
                    'name': name,
                    'description': description,
                    'tickers': []
                }
                self.app.config.save_portfolios()
                
                # Refresh the portfolio selector
                self._populate_portfolio_select()
                
                # Select the new portfolio
                portfolio_select = self.query_one("#portfolio-select", Select)
                portfolio_select.value = name
        
        self.app.push_screen(EditPortfolioModal("", ""), on_modal_close)
    
    @on(Button.Pressed, "#edit-portfolio")
    def on_edit_portfolio_pressed(self) -> None:
        """Handles the 'Edit Portfolio' button press."""
        portfolio_name = self.query_one("#portfolio-select", Select).value
        if not portfolio_name:
            self.app.notify("No portfolio selected.", severity="warning")
            return
        
        portfolio_data = self.app.config.portfolios.get(portfolio_name, {})
        name = portfolio_data.get('name', portfolio_name)
        description = portfolio_data.get('description', '')
        
        def on_modal_close(result: tuple[str, str] | None) -> None:
            if result:
                new_name, new_description = result
                
                # Update the portfolio
                self.app.config.portfolios[portfolio_name] = {
                    'name': new_name,
                    'description': new_description,
                    'tickers': portfolio_data.get('tickers', [])
                }
                self.app.config.save_portfolios()
                
                # Refresh the portfolio selector
                self._populate_portfolio_select()
        
        self.app.push_screen(EditPortfolioModal(name, description), on_modal_close)
    
    @on(Button.Pressed, "#delete-portfolio")
    def on_delete_portfolio_pressed(self) -> None:
        """Handles the 'Delete Portfolio' button press."""
        portfolio_name = self.query_one("#portfolio-select", Select).value
        if not portfolio_name:
            self.app.notify("No portfolio selected.", severity="warning")
            return
        
        portfolio_data = self.app.config.portfolios.get(portfolio_name, {})
        display_name = portfolio_data.get('name', portfolio_name)
        
        def on_modal_close(confirmed: bool) -> None:
            if confirmed:
                # Delete the portfolio
                del self.app.config.portfolios[portfolio_name]
                self.app.config.save_portfolios()
                
                # Refresh the portfolio selector
                self._populate_portfolio_select()
        
        self.app.push_screen(
            ConfirmDeleteModal(
                portfolio_name,
                f"Are you sure you want to delete the portfolio '{display_name}'?",
                require_typing=False
            ),
            on_modal_close
        )
    
    @on(Button.Pressed, "#add-stock")
    def on_add_stock_pressed(self) -> None:
        """Handles the 'Add Stock' button press."""
        portfolio_name = self.query_one("#portfolio-select", Select).value
        if not portfolio_name:
            self.app.notify("No portfolio selected.", severity="warning")
            return
        
        def on_modal_close(result: tuple[str, str, str] | None) -> None:
            if result:
                ticker, _, _ = result  # We only need the ticker
                
                # Add the ticker to the portfolio
                portfolio = self.app.config.portfolios[portfolio_name]
                tickers = portfolio.get('tickers', [])
                
                if ticker.upper() in [t.upper() for t in tickers]:
                    self.app.notify(f"Ticker '{ticker}' already exists in this portfolio.", severity="error")
                    return
                
                tickers.append(ticker.upper())
                portfolio['tickers'] = tickers
                self.app.config.save_portfolios()
                
                # Reload the portfolio
                self._load_portfolio(portfolio_name)
        
        self.app.push_screen(AddTickerModal(), on_modal_close)
    
    @on(Button.Pressed, "#remove-stock")
    def on_remove_stock_pressed(self) -> None:
        """Handles the 'Remove Stock' button press."""
        portfolio_name = self.query_one("#portfolio-select", Select).value
        if not portfolio_name:
            self.app.notify("No portfolio selected.", severity="warning")
            return
        
        stock_table = self.query_one("#portfolio-table", DataTable)
        if stock_table.cursor_row < 0:
            self.app.notify("No stock selected.", severity="warning")
            return
        
        # Get the ticker from the selected row
        ticker = stock_table.get_cell_at((stock_table.cursor_row, 0))
        if not ticker or ticker == "[dim]No stocks in this portfolio[/dim]":
            return
        
        def on_modal_close(confirmed: bool) -> None:
            if confirmed:
                # Remove the ticker from the portfolio
                portfolio = self.app.config.portfolios[portfolio_name]
                tickers = portfolio.get('tickers', [])
                
                if ticker in tickers:
                    tickers.remove(ticker)
                    portfolio['tickers'] = tickers
                    self.app.config.save_portfolios()
                    
                    # Reload the portfolio
                    self._load_portfolio(portfolio_name)
        
        self.app.push_screen(
            ConfirmDeleteModal(
                ticker,
                f"Are you sure you want to remove '{ticker}' from this portfolio?",
                require_typing=False
            ),
            on_modal_close
        )