from textual.message import Message
from textual.validation import Validator, ValidationResult

class PriceDataUpdated(Message):
    """Posted when price data has been updated."""
    def __init__(self, data: list[dict], category: str) -> None:
        self.data = data
        self.category = category
        super().__init__()

class NewsDataUpdated(Message):
    """Posted when news data for a specific ticker is updated."""
    def __init__(self, ticker: str, data: list[dict]) -> None:
        self.ticker = ticker
        self.data = data
        super().__init__()

class MarketStatusUpdated(Message):
    """Posted when market status is updated with detailed info"""
    def __init__(self, status: dict) -> None:
        self.status = status
        super().__init__()

class HistoricalDataUpdated(Message):
    """Posted when historical data for a ticker has been fetched."""
    def __init__(self, data) -> None: # Data will likely be a pandas DataFrame
        self.data = data
        super().__init__()

class TickerInfoComparisonUpdated(Message):
    """Posted when fast and slow info for a ticker has been fetched for comparison."""
    def __init__(self, fast_info: dict, slow_info: dict) -> None:
        self.fast_info = fast_info
        self.slow_info = slow_info
        super().__init__()

class TickerDebugDataUpdated(Message):
    """Posted when the individual ticker performance test is complete."""
    def __init__(self, data: list[dict], total_time: float) -> None:
        self.data, self.total_time = data, total_time; super().__init__()

class ListDebugDataUpdated(Message):
    """Posted when the list batch performance test is complete."""
    def __init__(self, data: list[dict], total_time: float) -> None:
        self.data, self.total_time = data, total_time; super().__init__()

class CacheTestDataUpdated(Message):
    """Posted when the cache retrieval test is complete."""
    def __init__(self, data: list[dict], total_time: float) -> None:
        self.data, self.total_time = data, total_time; super().__init__()

class PortfolioDataUpdated(Message):
    """Posted when portfolio data has been updated."""
    def __init__(self, portfolio_name: str, tickers: list[str], price_data: list[dict]) -> None:
        self.portfolio_name = portfolio_name
        self.tickers = tickers
        self.price_data = price_data
        super().__init__()

class NotEmpty(Validator):
    def validate(self, value: str) -> ValidationResult:
        if value.strip(): return self.success()
        return self.failure("This field cannot be empty.")