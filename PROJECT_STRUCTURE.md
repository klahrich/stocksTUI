# StocksTUI Technical Documentation

## 1. Project Overview

StocksTUI is a Terminal User Interface (TUI) application for monitoring stock prices, news, and historical data. It provides a lightweight, keyboard-driven interface for financial market data that can run in any terminal. The application has been extended with a portfolio tracking feature that allows users to group stocks for display purposes.

## 2. Architecture

### 2.1 High-Level Architecture

StocksTUI follows a Model-View-Controller (MVC) pattern with an event-driven architecture:

- **Model**: Data providers and data structures that represent the application state
- **View**: UI components built with the Textual framework
- **Controller**: The main application class that orchestrates data flow and user interactions

The application uses a reactive programming approach where changes to data trigger UI updates through an event system.

### 2.2 Key Components

1. **Main Application (`StocksTUI` class)**: Orchestrates the entire application
2. **Data Providers**: Fetch and manage data from external sources
3. **UI Components**: Display data and handle user interactions
4. **Configuration Manager**: Handles user settings and preferences
5. **Message System**: Facilitates communication between components

### 2.3 Design Patterns

- **Observer Pattern**: Implemented through Textual's event system
- **Factory Pattern**: Used for creating UI components
- **Singleton Pattern**: Used for the ConfigManager
- **Command Pattern**: Used for handling user actions
- **Worker Pattern**: Used for background tasks

## 3. Code Organization

### 3.1 Directory Structure

```
stockstui/
├── __init__.py
├── main.py                  # Main application entry point
├── main.css                 # Application styling
├── common.py                # Shared utilities and message classes
├── config_manager.py        # Configuration management
├── utils.py                 # Utility functions
├── data_providers/          # Data access layer
│   ├── __init__.py
│   ├── market_provider.py   # Market data provider
│   └── portfolio.py         # Portfolio data model
├── presentation/            # Formatting and display logic
│   ├── __init__.py
│   └── formatter.py         # Data formatting utilities
├── ui/                      # User interface components
│   ├── __init__.py
│   ├── modals.py            # Modal dialogs
│   ├── widgets/             # Custom widgets
│   └── views/               # Main view components
│       ├── __init__.py
│       ├── config_view.py   # Configuration view
│       ├── debug_view.py    # Debug view
│       ├── history_view.py  # Historical data view
│       ├── news_view.py     # News view
│       └── portfolio_view.py # Portfolio view
└── default_configs/         # Default configuration files
    ├── portfolios.json      # Default portfolios configuration
    └── ...                  # Other default configs
```

### 3.2 Key Files

- **main.py**: The main application class and entry point
- **config_manager.py**: Manages user configuration and settings
- **common.py**: Contains message classes for event handling
- **data_providers/market_provider.py**: Provides market data from external sources
- **data_providers/portfolio.py**: Portfolio data model
- **ui/views/portfolio_view.py**: UI component for displaying portfolios
- **ui/modals.py**: Modal dialogs for user interaction

## 4. Data Flow

### 4.1 General Data Flow

1. User interacts with the UI (e.g., selects a tab, clicks a button)
2. The main application handles the interaction and triggers appropriate actions
3. Background workers fetch data from external sources if needed
4. Data is processed and formatted
5. Messages are posted to update the UI
6. UI components receive messages and update their display

### 4.2 Portfolio Data Flow

1. User selects the Portfolio tab
2. The main application displays the PortfolioView
3. PortfolioView loads available portfolios from ConfigManager
4. User selects a portfolio
5. A background worker fetches price data for the portfolio's tickers
6. The worker posts a PortfolioDataUpdated message
7. The main application receives the message and forwards it to the PortfolioView
8. PortfolioView updates its display with the new data

## 5. Key Components in Detail

### 5.1 Main Application (`StocksTUI` class)

The `StocksTUI` class in `main.py` is the central controller of the application. It:

- Initializes the application state
- Composes the UI layout
- Handles user interactions
- Manages background workers
- Routes messages between components

Key methods:
- `compose()`: Creates the static layout
- `on_mount()`: Initializes dynamic content
- `_display_data_for_category()`: Routes content based on selected tab
- `fetch_portfolio_prices()`: Worker method to fetch portfolio data
- `on_portfolio_data_updated()`: Handles portfolio data updates

### 5.2 Configuration Manager

The `ConfigManager` class in `config_manager.py` manages user settings and configurations:

- Loads and saves configuration files
- Provides access to user settings
- Handles default configurations
- Manages portfolios configuration

### 5.3 Data Providers

#### 5.3.1 Market Provider

The `market_provider` module in `data_providers/market_provider.py` provides access to market data:

- Fetches price data from external sources (yfinance)
- Caches data to reduce API calls
- Provides methods for different types of market data (prices, news, historical)
- Includes portfolio-specific data methods

Key methods:
- `get_market_price_data()`: Fetches current price data
- `get_news_data()`: Fetches news articles
- `get_historical_data()`: Fetches historical price data
- `get_portfolio_price_data()`: Fetches price data for a portfolio

#### 5.3.2 Portfolio Model

The `Portfolio` class in `data_providers/portfolio.py` represents a portfolio of stocks:

- Stores portfolio metadata (name, description)
- Manages a list of tickers
- Provides methods for adding/removing tickers
- Handles serialization/deserialization

### 5.4 UI Components

#### 5.4.1 Portfolio View

The `PortfolioView` class in `ui/views/portfolio_view.py` displays portfolio data:

- Shows a selector for available portfolios
- Displays price data for the selected portfolio
- Provides buttons for portfolio management
- Updates dynamically when data changes

Key methods:
- `compose()`: Creates the view layout
- `on_mount()`: Initializes the view
- `update_portfolio_data()`: Updates the display with new data
- `on_portfolio_select_changed()`: Handles portfolio selection changes

#### 5.4.2 Edit Portfolio Modal

The `EditPortfolioModal` class in `ui/modals.py` allows users to create and edit portfolios:

- Provides inputs for portfolio name and description
- Allows adding and removing tickers
- Validates user input
- Saves changes to the configuration

## 6. Message System

The application uses a message-based system for communication between components:

1. **Message Classes**: Defined in `common.py`
2. **Message Posting**: Components post messages using `self.post_message()`
3. **Message Handling**: Components handle messages with `@on(MessageClass)` decorators

Key message classes:
- `PriceDataUpdated`: Signals new price data
- `NewsDataUpdated`: Signals new news data
- `HistoricalDataUpdated`: Signals new historical data
- `PortfolioDataUpdated`: Signals new portfolio data

## 7. Background Workers

The application uses Textual's worker system to perform tasks in the background:

1. **Worker Definition**: Methods decorated with `@work(exclusive=True, thread=True)`
2. **Worker Execution**: Workers are called like normal methods but run in separate threads
3. **Result Handling**: Workers post messages to communicate results

Key workers:
- `fetch_prices()`: Fetches price data
- `fetch_news()`: Fetches news data
- `fetch_historical_data()`: Fetches historical data
- `fetch_portfolio_prices()`: Fetches portfolio price data

## 8. Styling System

The application uses Textual's CSS-like styling system:

1. **CSS File**: Styles defined in `main.css`
2. **Theme System**: Dynamic themes with color variables
3. **Reactive Styling**: Style changes based on application state

Portfolio-specific styles:
- `#portfolio-container`: Main container for the portfolio view
- `.portfolio-controls`: Container for portfolio selector and buttons
- `#portfolio-table`: Table for displaying portfolio data
- `#edit-portfolio-modal`: Modal for editing portfolios

## 9. Configuration System

### 9.1 Configuration Files

- **User Config**: Stored in the user's config directory
- **Default Config**: Provided in the `default_configs` directory
- **Config Format**: JSON files for different configuration types

### 9.2 Portfolio Configuration

Portfolios are stored in `portfolios.json` with the following structure:

```json
{
  "My Portfolio": {
    "description": "My main portfolio",
    "tickers": ["AAPL", "MSFT", "GOOGL"]
  },
  "Watchlist": {
    "description": "Stocks I'm watching",
    "tickers": ["TSLA", "AMZN", "NFLX"]
  }
}
```

## 10. Integration Points

### 10.1 External Data Sources

- **yfinance**: Used for fetching market data
- **Market Calendars**: Used for determining market status

### 10.2 System Integration

- **Terminal**: The application runs in any terminal that supports Unicode
- **Clipboard**: Integration with system clipboard for copying data
- **File System**: Reading and writing configuration files

## 11. Extending the Application

### 11.1 Adding a New View

To add a new view to the application:

1. Create a new view class in `ui/views/`
2. Add the view to the tab list in `_setup_dynamic_tabs()`
3. Update `_display_data_for_category()` to handle the new view
4. Add any necessary message handlers to the main application

Example:
```python
# 1. Create a new view class
class MyNewView(Widget):
    def compose(self) -> ComposeResult:
        yield Container(
            Label("My New View"),
            id="my-new-view-container"
        )

# 2. Add to tab list in _setup_dynamic_tabs()
all_possible_categories = ["all"] + list(self.config.lists.keys()) + ["portfolio", "history", "news", "debug", "my_new_view"]

# 3. Update _display_data_for_category()
elif category == 'my_new_view':
    await output_container.mount(MyNewView())
```

### 11.2 Adding a New Data Provider

To add a new data provider:

1. Create a new module in `data_providers/`
2. Implement the necessary data fetching methods
3. Add worker methods to the main application
4. Create message classes in `common.py`
5. Add message handlers to the main application

Example:
```python
# 1. Create a new data provider module
# data_providers/my_provider.py
def get_my_data():
    # Fetch data from external source
    return {"data": "value"}

# 2. Add worker method to main application
@work(exclusive=True, thread=True)
def fetch_my_data(self):
    data = my_provider.get_my_data()
    self.post_message(MyDataUpdated(data))

# 3. Create message class in common.py
class MyDataUpdated(Message):
    def __init__(self, data):
        self.data = data
        super().__init__()

# 4. Add message handler to main application
@on(MyDataUpdated)
async def on_my_data_updated(self, message: MyDataUpdated):
    # Handle the data update
    pass
```

## 12. Troubleshooting

### 12.1 Common Issues

1. **Data Not Updating**: Check network connectivity and API rate limits
   - Solution: Implement retry logic and better error handling

2. **UI Not Responding**: Check for blocking operations in the main thread
   - Solution: Move operations to background workers

3. **Configuration Not Saving**: Check file permissions and paths
   - Solution: Add error handling for file operations

### 12.2 Debugging Tools

The application includes a debug tab with tools for:

- Testing network connectivity
- Measuring API latency
- Checking cache performance
- Comparing data sources

## 13. Technical Debt and Future Improvements

### 13.1 Current Technical Debt

1. **Type Annotations**: Some functions lack proper type annotations
   - Impact: IDE warnings and potential runtime errors
   - Solution: Add comprehensive type annotations

2. **Error Handling**: Some error cases are not properly handled
   - Impact: Potential crashes or silent failures
   - Solution: Implement consistent error handling

3. **Test Coverage**: Limited automated tests
   - Impact: Regressions may go undetected
   - Solution: Implement comprehensive test suite

### 13.2 Future Improvements

1. **Portfolio Performance Tracking**: Extend the portfolio feature to track performance over time
   - Approach: Store purchase prices and dates, calculate returns

2. **Data Source Alternatives**: Add support for alternative data sources
   - Approach: Create an abstraction layer for data providers

3. **Advanced Charting**: Improve the historical data visualization
   - Approach: Implement more sophisticated TUI charts

## 14. Conclusion

StocksTUI is a well-structured application that follows good software engineering practices. The MVC architecture, event-driven design, and modular organization make it maintainable and extensible. The newly implemented portfolio tracking feature demonstrates how to integrate new functionality into the existing architecture.

By understanding the patterns and principles outlined in this document, developers can effectively contribute to the project and implement new features that align with the established technical standards.

## 15. Recommended UI Improvements

### 15.1 Tab Naming Clarification

To better differentiate between the purpose of different tabs, the following naming changes are recommended:

1. Rename the "Stocks" tab to "Market Lists" to clarify that it displays predefined lists of market instruments
2. Keep the "Portfolio" tab as is, since its purpose is clear - to display user-defined portfolios

This change will help users understand the distinct purposes of each tab:
- **Market Lists**: For viewing predefined categories of market instruments (stocks, crypto, etc.)
- **Portfolio**: For viewing personalized groupings of instruments that users are tracking

### 15.2 Implementation Notes

To implement this change, modify the `_setup_dynamic_tabs()` method in `main.py` to display "Market Lists" instead of "Stocks" when creating the tab labels. This is a UI-only change that doesn't affect the underlying data structure, which still uses "stocks" as the category key.