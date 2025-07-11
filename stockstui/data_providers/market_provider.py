import yfinance as yf
import logging
from datetime import datetime, timedelta
import time
import pandas as pd
from requests.exceptions import RequestException

# In-memory cache for storing fetched market data to reduce API calls.
# Keys are ticker symbols (uppercase), values are tuples of (timestamp, data).
_price_cache = {}
_news_cache = {}

# Duration for which cached data is considered fresh (in seconds).
CACHE_DURATION_SECONDS = 86400  # 24 hours

# Duration after which stale cache entries are removed entirely.
CACHE_EXPIRY_SECONDS = CACHE_DURATION_SECONDS * 2 # Cache clean is 2 days

try:
    # pandas_market_calendars is an optional dependency for market status checks.
    import pandas_market_calendars as mcal
except ImportError:
    mcal = None

def _clean_cache():
    """Removes entries from the price and news caches that have expired."""
    now = datetime.now()
    # Identify and remove expired price data
    expired_prices = [k for k, (ts, _) in _price_cache.items() if now - ts > timedelta(seconds=CACHE_EXPIRY_SECONDS)]
    for k in expired_prices:
        del _price_cache[k]
    # Identify and remove expired news data
    expired_news = [k for k, (ts, _) in _news_cache.items() if now - ts > timedelta(seconds=CACHE_EXPIRY_SECONDS)]
    for k in expired_news:
        del _news_cache[k]

def get_market_price_data(tickers: list[str], force_refresh: bool = False) -> list[dict]:
    """
    Fetches current market price information for a list of tickers.

    This function uses a cache to avoid redundant API calls. It checks which tickers
    need refreshing and only fetches data for those. The final list of data
    is returned in the same order as the input tickers.

    Args:
        tickers: A list of ticker symbols to fetch data for.
        force_refresh: If True, bypasses the cache for all tickers.

    Returns:
        A list of dictionaries, each containing price data for a ticker.
    """
    # Deduplicate and validate tickers, preserving order
    seen = set()
    valid_tickers = []
    for t in tickers:
        if t:
            upper_t = t.upper()
            if upper_t not in seen:
                seen.add(upper_t)
                valid_tickers.append(upper_t)
    
    if not valid_tickers:
        return []

    # Determine which tickers need to be fetched from the API
    to_fetch = []
    if force_refresh:
        to_fetch = valid_tickers
    else:
        now = datetime.now()
        for ticker in valid_tickers:
            if ticker in _price_cache:
                timestamp, _ = _price_cache[ticker]
                # Check if the cached data is still fresh
                if now - timestamp < timedelta(seconds=CACHE_DURATION_SECONDS):
                    continue
            to_fetch.append(ticker)

    # Fetch data for the tickers that need it and update the cache
    if to_fetch:
        fetched_data = get_market_price_data_uncached(to_fetch)
        now = datetime.now()
        for item in fetched_data:
            _price_cache[item['symbol']] = (now, item)
    
    # Assemble the final list of data from the cache, preserving the original order
    final_data = []
    for ticker in valid_tickers:
        if ticker in _price_cache:
            final_data.append(_price_cache[ticker][1])
    
    return final_data

def get_market_price_data_uncached(tickers: list[str]) -> list[dict]:
    """
    Fetches market data directly from the yfinance API using the .info property.

    This method is called by `get_market_price_data` when a cache miss occurs.
    It always returns an entry for every ticker requested, even if the API call fails,
    to prevent repeated lookups for invalid tickers.

    Args:
        tickers: A list of ticker symbols to fetch data for.

    Returns:
        A list of dictionaries with price data.
    """
    _clean_cache() # Periodically clean the cache before making new API calls
    data = []
    if not tickers:
        return []
        
    try:
        # Use yf.Tickers for efficient batch fetching
        ticker_objects = yf.Tickers(" ".join(tickers))
        for ticker_symbol in ticker_objects.tickers:
            try:
                info = ticker_objects.tickers[ticker_symbol].info
                
                # Handle cases where the ticker is invalid or data is missing
                if not info or info.get('currency') is None:
                    logging.warning(f"Could not retrieve info for ticker: {ticker_symbol}")
                    data.append({
                        "symbol": ticker_symbol, "description": "Invalid Ticker",
                        "price": None, "previous_close": None, "day_low": None,
                        "day_high": None, "fifty_two_week_low": None,
                        "fifty_two_week_high": None,
                    })
                    continue

                # Extract relevant price information
                last_price = info.get('currentPrice', info.get('regularMarketPrice'))
                
                data.append({
                    "symbol": ticker_symbol,
                    "description": info.get('longName', ticker_symbol),
                    "price": last_price,
                    "previous_close": info.get('previousClose'),
                    "day_low": info.get('dayLow'),
                    "day_high": info.get('dayHigh'),
                    "fifty_two_week_low": info.get('fiftyTwoWeekLow'),
                    "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
                })
            # Catch errors for a single ticker, allowing the batch to continue.
            except (RequestException, ValueError, KeyError) as e:
                logging.warning(f"Data retrieval failed for ticker {ticker_symbol}: {type(e).__name__}")
                data.append({
                    "symbol": ticker_symbol, "description": "Data Unavailable",
                    "price": None, "previous_close": None, "day_low": None,
                    "day_high": None, "fifty_two_week_low": None,
                    "fifty_two_week_high": None,
                })

    # Catch network errors affecting the entire batch request.
    except RequestException as e:
        logging.error(f"Network error fetching market prices batch: {type(e).__name__}")
    # Catch any truly unexpected errors and log with a full stack trace.
    except Exception:
        logging.exception("An unexpected error occurred in get_market_price_data_uncached.")
    return data

def get_market_status(calendar_name='NYSE') -> dict:
    """
    Gets the current status of a major stock market exchange.

    Uses the pandas_market_calendars library to determine if the market is open,
    closed, or in pre/post-market sessions. Also checks for holidays.

    Args:
        calendar_name: The name of the market calendar to check (e.g., 'NYSE').

    Returns:
        A dictionary containing the status, holiday info, and calendar name.
    """
    if mcal is None:
        logging.error("pandas_market_calendars is not installed. Market status is unavailable.")
        return {'status': 'closed', 'is_open': False, 'holiday': 'dependency missing', 'calendar': calendar_name}
    try:
        cal = mcal.get_calendar(calendar_name)
        now = pd.Timestamp.now(tz=cal.tz)
        today = now.normalize().date()

        # Check if today is a public holiday
        holidays_obj = cal.holidays()
        holiday_dates = pd.DatetimeIndex(holidays_obj.holidays)
        
        today_ts = pd.Timestamp(today).normalize()
        
        if today_ts in holiday_dates:
            return {'status': 'closed', 'is_open': False, 'holiday': 'Holiday', 'calendar': calendar_name}

        # Get the market open and close times for today
        schedule = cal.schedule(start_date=today, end_date=today)
        if schedule.empty:
            return {'status': 'closed', 'is_open': False, 'holiday': 'Weekend', 'calendar': calendar_name}

        market_open = schedule.iloc[0].market_open
        market_close = schedule.iloc[0].market_close
        
        # Define pre-market and post-market hours
        pre_market_start = market_open - timedelta(hours=5)
        post_market_end = market_close + timedelta(hours=4)
        
        # Determine the current session based on the time
        session = 'closed'
        if pre_market_start <= now < market_open:
            session = 'pre'
        elif market_open <= now < market_close:
            session = 'open'
        elif market_close <= now < post_market_end:
            session = 'post'

        return {
            'status': session,
            'is_open': session == 'open',
            'holiday': None,
            'calendar': calendar_name
        }
    # Catch specific, expected errors from the calendar library.
    except (ValueError, AttributeError) as e:
        logging.warning(f"Calendar data issue for {calendar_name}: {type(e).__name__} - {e}")
        return {'status': 'closed', 'is_open': False, 'holiday': 'Data Error', 'calendar': calendar_name}
    # Catch any other unexpected errors and log with a full stack trace.
    except Exception:
        logging.exception(f"Unexpected error getting market status for {calendar_name}")
        return {'status': 'closed', 'is_open': False, 'holiday': 'Error', 'calendar': calendar_name}

def get_historical_data(ticker: str, period: str, interval: str = "1d"):
    """
    Fetches historical market data (OHLCV) for a given ticker.

    Args:
        ticker: The stock ticker symbol.
        period: The time period for the data (e.g., "1mo", "1y").
        interval: The data interval (e.g., "1d", "1wk").

    Returns:
        A pandas DataFrame with the historical data. If an error occurs,
        it returns an empty DataFrame with an 'error' attribute set.
    """
    df = pd.DataFrame()
    df.attrs['symbol'] = ticker.upper() # Add symbol to attrs for all return paths
    try:
        ticker_obj = yf.Ticker(ticker)
        # Pre-validate ticker to provide better error feedback.
        if not ticker_obj.info or ticker_obj.info.get('currency') is None:
            logging.warning(f"Historical data check: Ticker '{ticker}' appears invalid.")
            df.attrs['error'] = 'Invalid Ticker'
            return df

        data = ticker_obj.history(period=period, interval=interval)
        if not data.empty:
            data.attrs['symbol'] = ticker.upper()
        return data
    # Catch network-related errors specifically.
    except RequestException as e:
        logging.warning(f"Network error fetching historical data for {ticker}: {type(e).__name__}")
        df.attrs['error'] = 'Network Error'
        return df
    # Catch unexpected errors and log with a full stack trace.
    except Exception:
        logging.exception(f"Unexpected error fetching historical data for {ticker}")
        df.attrs['error'] = 'Data Error'
        return df

def get_news_data(ticker: str) -> list[dict] | None:
    """
    Fetches and processes news articles for a single ticker symbol, with caching.

    Exceptions are intended to be caught by the calling worker.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        A list of dictionaries, each representing a news article. Returns None
        if the ticker symbol is invalid. Returns an empty list if there's no news.
    """
    if not ticker: return []
    normalized_ticker = ticker.upper()

    # Check cache first
    now = datetime.now()
    if normalized_ticker in _news_cache:
        timestamp, cached_data = _news_cache[normalized_ticker]
        if now - timestamp < timedelta(seconds=CACHE_DURATION_SECONDS):
            return cached_data

    ticker_obj = yf.Ticker(normalized_ticker)
    # Pre-validate ticker. If invalid, return None to signal failure.
    # Let yfinance exceptions bubble up to the worker.
    if not ticker_obj.info or ticker_obj.info.get('currency') is None:
        logging.warning(f"News data check: Ticker '{normalized_ticker}' appears invalid.")
        return None

    raw_news = ticker_obj.news
    if not raw_news:
        return []

    # Process the raw news data into a cleaner format
    processed_news = []
    for item in raw_news:
        content = item.get('content', {})
        if not content:
            continue

        title = content.get('title', 'N/A')
        summary = content.get('summary', 'N/A')
        publisher = content.get('provider', {}).get('displayName', 'N/A')
        link = content.get('canonicalUrl', {}).get('url', '#')
        
        # Format the publication timestamp
        publish_time_str = "N/A"
        pub_date_str = content.get('pubDate')
        if pub_date_str:
            try:
                utc_dt = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                local_dt = utc_dt.astimezone()
                publish_time_str = local_dt.strftime('%Y-%m-%d %H:%M %Z')
            except (ValueError, TypeError):
                publish_time_str = pub_date_str

        processed_news.append({
            'title': title,
            'summary': summary,
            'publisher': publisher,
            'link': link,
            'publish_time': publish_time_str,
        })
    
    # Update the cache
    _news_cache[normalized_ticker] = (datetime.now(), processed_news)
    return processed_news

def get_ticker_info_comparison(ticker: str) -> dict:
    """Gets both 'fast_info' and full 'info' for a ticker for debug/comparison."""
    try:
        ticker_obj = yf.Ticker(ticker)
        fast_info = ticker_obj.fast_info
        slow_info = ticker_obj.info
        
        # yfinance returns empty dicts for invalid tickers after a delay
        if not slow_info:
            return {"fast": {}, "slow": {}}
            
        return {"fast": fast_info, "slow": slow_info}
    except RequestException as e:
        logging.warning(f"Network error getting info for {ticker}: {type(e).__name__}")
        return {"fast": {}, "slow": {}}
    except Exception:
        logging.exception(f"Unexpected error getting info comparison for {ticker}")
        return {"fast": {}, "slow": {}}


def run_ticker_debug_test(tickers: list[str]) -> list[dict]:
    """ 
    Tests a list of tickers for validity and measures API response latency.

    Args:
        tickers: A list of ticker symbols to test.

    Returns:
        A list of dictionaries with debug info for each ticker, sorted by latency.
    """
    results = []
    for symbol in tickers:
        start_time = time.perf_counter()
        try:
            info = yf.Ticker(symbol).info
            is_valid = info and info.get('currency') is not None
        except RequestException as e:
            logging.warning(f"Network error testing {symbol}: {type(e).__name__}")
            info, is_valid = {}, False
        except Exception:
            logging.exception(f"Unexpected error testing {symbol}")
            info, is_valid = {}, False
        latency = time.perf_counter() - start_time
        description = info.get('longName', 'N/A') if is_valid else "Could not retrieve data. Delisted or invalid."
        results.append({"symbol": symbol, "is_valid": is_valid, "description": description, "latency": latency})
    results.sort(key=lambda x: x['latency'], reverse=True)
    return results

def run_list_debug_test(lists: dict[str, list[str]]):
    """
    Measures the time it takes to fetch data for entire lists of tickers.

    Args:
        lists: A dictionary where keys are list names and values are lists of tickers.

    Returns:
        A list of dictionaries with debug info for each list, sorted by latency.
    """
    results = []
    for list_name, tickers in lists.items():
        if not tickers:
            results.append({"list_name": list_name, "latency": 0.0, "ticker_count": 0})
            continue
        start_time = time.perf_counter()
        try:
            ticker_objects = yf.Tickers(" ".join(tickers))
            for ticker in ticker_objects.tickers:
                _ = ticker_objects.tickers[ticker].info # Access .info to trigger fetch
        except RequestException as e:
            logging.warning(f"Network error testing list '{list_name}': {type(e).__name__}")
        except Exception:
            logging.exception(f"Unexpected error testing list '{list_name}'")
        latency = time.perf_counter() - start_time
        results.append({"list_name": list_name, "latency": latency, "ticker_count": len(tickers)})
    results.sort(key=lambda x: x['latency'], reverse=True)
    return results

def run_cache_test(lists: dict[str, list[str]]) -> list[dict]:
    """
    Tests the performance of reading pre-cached data for lists of tickers.

    Args:
        lists: A dictionary where keys are list names and values are lists of tickers.

    Returns:
        A list of dictionaries with cache performance info, sorted by latency.
    """
    results = []
    # Ensure all tickers are in the cache before running the test
    all_tickers = list(set(ticker for L in lists.values() for ticker in L))
    if all_tickers:
        get_market_price_data(all_tickers)

    for list_name, tickers in lists.items():
        start_time = time.perf_counter()
        # Retrieve data from cache
        _ = [data for ticker in tickers if (entry := _price_cache.get(ticker.upper())) and (data := entry[1])]
        latency = time.perf_counter() - start_time
        results.append({"list_name": list_name, "latency": latency, "ticker_count": len(tickers)})
    
    results.sort(key=lambda x: x['latency'], reverse=True)
    return results