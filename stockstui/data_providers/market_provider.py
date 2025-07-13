import yfinance as yf
import logging
from datetime import datetime, timedelta, timezone
import time
import pandas as pd
from requests.exceptions import RequestException

# In-memory cache for storing fetched market data to reduce API calls.
# This acts as the single source of truth during the application's runtime.
# It is populated from a persistent DB cache on startup and saved on exit.
_price_cache = {}
_news_cache = {}
_info_cache = {} # Cache for semi-static data like exchange and company name.

# Duration for which cached data is considered fresh if a market is OPEN.
CACHE_OPEN_MARKET_SECONDS = 300  # 5 minutes

# Duration for which cached data is considered fresh if a market is CLOSED.
CACHE_CLOSED_MARKET_SECONDS = 86400  # 24 hours

# Duration after which stale cache entries are removed entirely.
CACHE_EXPIRY_SECONDS = 86400 * 2 # Cache clean is 2 days

try:
    # pandas_market_calendars is an optional dependency for market status checks.
    import pandas_market_calendars as mcal
except ImportError:
    mcal = None

def populate_price_cache(initial_data: dict):
    """Populates the in-memory price cache from a dictionary."""
    global _price_cache
    _price_cache.update(initial_data)
    logging.info(f"In-memory price cache populated with {len(initial_data)} items.")

def populate_info_cache(initial_data: dict):
    """Populates the in-memory info cache from a dictionary."""
    global _info_cache
    _info_cache.update(initial_data)
    logging.info(f"In-memory info cache populated with {len(initial_data)} items.")

def get_price_cache_state() -> dict:
    """Returns the current state of the in-memory price cache."""
    return _price_cache

def get_info_cache_state() -> dict:
    """Returns the current state of the in-memory info cache."""
    return _info_cache

def get_market_price_data(tickers: list[str], force_refresh: bool = False) -> list[dict]:
    """
    Acts as a gatekeeper for data fetching. It determines which tickers need
    a refresh based on market status and cache freshness, then delegates the
    actual API calls to `get_market_price_data_uncached`.
    """
    seen = set()
    valid_tickers = [t.upper() for t in tickers if t and t.upper() not in seen and not seen.add(t.upper())]
    if not valid_tickers: return []

    to_fetch = []
    now = datetime.now(timezone.utc)

    if force_refresh:
        to_fetch = valid_tickers
    else:
        for ticker in valid_tickers:
            info = _info_cache.get(ticker)
            
            # If we don't know the exchange, assume market is open to be safe.
            # This makes it likely to be fetched, at which point we'll get the info.
            is_open = True
            if info and info.get("exchange"):
                is_open = get_market_status(info["exchange"]).get('is_open', True)

            duration = CACHE_OPEN_MARKET_SECONDS if is_open else CACHE_CLOSED_MARKET_SECONDS

            if ticker in _price_cache:
                timestamp, _ = _price_cache[ticker]
                if (now - timestamp).total_seconds() < duration:
                    continue  # Price data is fresh enough, skip.
            
            to_fetch.append(ticker)

    if to_fetch:
        fetched_data = get_market_price_data_uncached(to_fetch)
        now_ts = datetime.now(timezone.utc)
        for item in fetched_data:
            _price_cache[item['symbol']] = (now_ts, item)
    
    return [price for ticker in valid_tickers if (entry := _price_cache.get(ticker)) and (price := entry[1])]

def get_market_price_data_uncached(tickers: list[str]) -> list[dict]:
    """
    The single worker function for fetching price data. For a given list of tickers,
    it fetches the full `.info` object and uses it to populate BOTH the info cache
    (exchange, name) and the returned price data list.
    """
    data = []
    if not tickers: return []
    
    # yf.Tickers is a container for yf.Ticker objects. Accessing .info on each
    # one is how yfinance triggers the download for that specific ticker.
    ticker_objects = yf.Tickers(" ".join(tickers))
    for ticker_symbol in tickers: # Iterate over our original list to maintain order
        try:
            info = ticker_objects.tickers[ticker_symbol].info

            if info and info.get('currency'):
                # Successfully fetched data, update info cache and prepare price data.
                _info_cache[ticker_symbol] = {"exchange": info.get("exchange"), "shortName": info.get("shortName"), "longName": info.get("longName")}
                data.append({
                    "symbol": ticker_symbol, "description": info.get('longName', ticker_symbol),
                    "price": info.get('currentPrice', info.get('regularMarketPrice')),
                    "previous_close": info.get('previousClose'), "day_low": info.get('dayLow'), "day_high": info.get('dayHigh'),
                    "fifty_two_week_low": info.get('fiftyTwoWeekLow'), "fifty_two_week_high": info.get('fiftyTwoWeekHigh'),
                })
            else:
                # API returned no data, likely an invalid ticker.
                _info_cache[ticker_symbol] = {}  # Cache failure to prevent re-fetches.
                data.append({"symbol": ticker_symbol, "description": "Invalid Ticker", "price": None, "previous_close": None, "day_low": None, "day_high": None, "fifty_two_week_low": None, "fifty_two_week_high": None})
        except Exception as e:
            logging.warning(f"Data retrieval failed for ticker {ticker_symbol}: {type(e).__name__}")
            _info_cache[ticker_symbol] = {} # Cache failure
            data.append({"symbol": ticker_symbol, "description": "Data Unavailable", "price": None, "previous_close": None, "day_low": None, "day_high": None, "fifty_two_week_low": None, "fifty_two_week_high": None})
    return data

def get_ticker_info(ticker: str) -> dict | None:
    """
    Retrieves semi-static information for a ticker (exchange, name).
    Checks in-memory cache first, then falls back to an API call.
    """
    if ticker in _info_cache:
        return _info_cache[ticker]
    
    try:
        info = yf.Ticker(ticker).info
        if not info or info.get('currency') is None:
            _info_cache[ticker] = {} # Cache failure
            return None
        _info_cache[ticker] = {"exchange": info.get("exchange"), "shortName": info.get("shortName"), "longName": info.get("longName")}
        return _info_cache[ticker]
    except Exception:
        _info_cache[ticker] = {}
        return None

def get_market_status(calendar_name='NYSE') -> dict:
    """Gets the current status of a stock market exchange."""
    if calendar_name == 'GDAX': calendar_name = 'CME_Crypto'
    if mcal is None: return {'status': 'closed', 'is_open': False}
    try:
        cal = mcal.get_calendar(calendar_name)
        now = pd.Timestamp.now(tz=cal.tz)
        schedule = cal.schedule(start_date=now.date(), end_date=now.date())
        if schedule.empty:
            return {'status': 'closed', 'is_open': False, 'calendar': calendar_name}
        market_open, market_close = schedule.iloc[0].market_open, schedule.iloc[0].market_close
        session = 'closed'
        if market_open <= now < market_close: session = 'open'
        return {'status': session, 'is_open': session == 'open', 'calendar': calendar_name}
    except Exception:
        return {'status': 'unknown', 'is_open': True, 'calendar': calendar_name or 'Unknown'}

def get_historical_data(ticker: str, period: str, interval: str = "1d"):
    """Fetches historical market data (OHLCV) for a given ticker."""
    df = pd.DataFrame()
    df.attrs['symbol'] = ticker.upper()
    try:
        info = get_ticker_info(ticker)
        if not info:
            df.attrs['error'] = 'Invalid Ticker'
            return df
        data = yf.Ticker(ticker).history(period=period, interval=interval)
        if not data.empty:
            data.attrs['symbol'] = ticker.upper()
        return data
    except Exception:
        df.attrs['error'] = 'Data Error'
        return df

def get_news_data(ticker: str) -> list[dict] | None:
    """Fetches and processes news articles for a single ticker symbol, with caching."""
    if not ticker: return []
    normalized_ticker = ticker.upper()
    now = datetime.now(timezone.utc)
    if normalized_ticker in _news_cache:
        timestamp, cached_data = _news_cache[normalized_ticker]
        if (now - timestamp).total_seconds() < CACHE_CLOSED_MARKET_SECONDS:
            return cached_data
    info = get_ticker_info(ticker)
    if not info: return None
    raw_news = yf.Ticker(normalized_ticker).news
    if not raw_news: return []
    processed_news = []
    for item in raw_news:
        content = item.get('content', {})
        if not content: continue
        title = content.get('title', 'N/A')
        summary = content.get('summary', 'N/A')
        publisher = content.get('provider', {}).get('displayName', 'N/A')
        link = content.get('canonicalUrl', {}).get('url', '#')
        publish_time_str = "N/A"
        if pub_date_str := content.get('pubDate'):
            try:
                utc_dt = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                publish_time_str = utc_dt.astimezone().strftime('%Y-%m-%d %H:%M %Z')
            except (ValueError, TypeError): publish_time_str = pub_date_str
        processed_news.append({'title': title, 'summary': summary, 'publisher': publisher, 'link': link, 'publish_time': publish_time_str})
    _news_cache[normalized_ticker] = (datetime.now(timezone.utc), processed_news)
    return processed_news

def get_ticker_info_comparison(ticker: str) -> dict:
    """Gets both 'fast_info' and full 'info' for a ticker for debug/comparison."""
    try:
        ticker_obj = yf.Ticker(ticker)
        fast_info = ticker_obj.fast_info
        slow_info = ticker_obj.info
        if not slow_info: return {"fast": {}, "slow": {}}
        return {"fast": fast_info, "slow": slow_info}
    except Exception:
        return {"fast": {}, "slow": {}}

def run_ticker_debug_test(tickers: list[str]) -> list[dict]:
    """Tests a list of tickers for validity and measures API response latency."""
    results = []
    for symbol in tickers:
        start_time = time.perf_counter()
        try:
            info = yf.Ticker(symbol).info
            is_valid = info and info.get('currency') is not None
        except Exception: info, is_valid = {}, False
        latency = time.perf_counter() - start_time
        description = info.get('longName', 'N/A') if is_valid else "Could not retrieve data."
        results.append({"symbol": symbol, "is_valid": is_valid, "description": description, "latency": latency})
    results.sort(key=lambda x: x['latency'], reverse=True)
    return results

def run_list_debug_test(lists: dict[str, list[str]]):
    """Measures the time it takes to fetch data for entire lists of tickers."""
    results = []
    for list_name, tickers in lists.items():
        if not tickers:
            results.append({"list_name": list_name, "latency": 0.0, "ticker_count": 0})
            continue
        start_time = time.perf_counter()
        try:
            _ = yf.Tickers(" ".join(tickers)).info
        except Exception: pass
        latency = time.perf_counter() - start_time
        results.append({"list_name": list_name, "latency": latency, "ticker_count": len(tickers)})
    results.sort(key=lambda x: x['latency'], reverse=True)
    return results

def run_cache_test(lists: dict[str, list[str]]) -> list[dict]:
    """Tests the performance of reading pre-cached data for lists of tickers."""
    results = []
    all_tickers = list(set(ticker for L in lists.values() for ticker in L))
    if all_tickers:
        get_market_price_data(all_tickers)
    for list_name, tickers in lists.items():
        start_time = time.perf_counter()
        _ = [data for ticker in tickers if (entry := _price_cache.get(ticker.upper())) and (data := entry[1])]
        latency = time.perf_counter() - start_time
        results.append({"list_name": list_name, "latency": latency, "ticker_count": len(tickers)})
    results.sort(key=lambda x: x['latency'], reverse=True)
    return results

def is_cached(ticker: str) -> bool:
    """Checks if a ticker's price data exists in the cache."""
    return ticker.upper() in _price_cache

def get_cached_price(ticker: str) -> dict | None:
    """Retrieves price data for a ticker from the cache."""
    entry = _price_cache.get(ticker.upper())
    return entry[1] if entry else None