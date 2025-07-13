import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

# Only load data into memory if it's less than a day old.
CACHE_LOAD_DURATION_SECONDS = 86400  # 24 hours

# Prune any data from the database file that is older than 7 days.
# This keeps the database file size manageable over time.
CACHE_PRUNE_EXPIRY_SECONDS = 604800  # 7 days


class DbManager:
    """
    Manages the persistent SQLite database for caching application data, primarily
    stock prices, to enable faster startups and reduce API calls.
    """
    def __init__(self, db_path: Path):
        """
        Initializes the DbManager and establishes a connection to the database.

        Args:
            db_path: The file path for the SQLite database.
        """
        self.db_path = db_path
        self.conn = None
        try:
            # Ensure the parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._create_tables()
            self._prune_expired_entries()  # Clean up old data on startup.
        except sqlite3.Error as e:
            logging.error(f"Database connection failed for '{self.db_path}': {e}")

    def _create_tables(self):
        """Creates the necessary tables in the database if they don't already exist."""
        if not self.conn:
            return
        try:
            cursor = self.conn.cursor()
            # Stores the price cache. data is a JSON string. timestamp is a Unix timestamp (float).
            # Using INSERT OR REPLACE requires a PRIMARY KEY.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_cache (
                    ticker TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to create database tables: {e}")

    def _prune_expired_entries(self):
        """
        Removes entries from the persistent cache that are older than the prune expiry date.
        This is a simple, age-based maintenance task to keep the DB size in check.
        """
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            # Determine the cutoff timestamp for pruning.
            prune_before_ts = datetime.now(timezone.utc).timestamp() - CACHE_PRUNE_EXPIRY_SECONDS
            
            cursor.execute("DELETE FROM price_cache WHERE timestamp < ?", (prune_before_ts,))
            
            # Log how many rows were deleted for diagnostics.
            rows_deleted = cursor.rowcount
            if rows_deleted > 0:
                logging.info(f"Pruned {rows_deleted} expired entries from the persistent cache.")
                self.conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to prune expired cache entries: {e}")

    def load_cache_from_db(self) -> dict:
        """
        Loads the price cache from the database, filtering for entries fresh enough to use.
        Converts float timestamps from DB back to datetime objects for in-memory use.
        """
        if not self.conn:
            return {}

        loaded_data = {}
        try:
            cursor = self.conn.cursor()
            # Determine the cutoff timestamp for what is considered "fresh" to load.
            load_after_ts = datetime.now(timezone.utc).timestamp() - CACHE_LOAD_DURATION_SECONDS
            
            cursor.execute("SELECT ticker, data, timestamp FROM price_cache WHERE timestamp >= ?", (load_after_ts,))
            rows = cursor.fetchall()
            
            for ticker, data_json, timestamp_float in rows:
                try:
                    # Convert float timestamp back to a timezone-aware datetime object
                    ts_dt = datetime.fromtimestamp(timestamp_float, tz=timezone.utc)
                    data = json.loads(data_json)
                    # The value is a tuple of (datetime_object, data_dict) to match the in-memory format.
                    loaded_data[ticker] = (ts_dt, data)
                except (json.JSONDecodeError, ValueError, TypeError, OSError):
                    logging.warning(f"Failed to decode or parse data for ticker '{ticker}' from DB cache.")
        except sqlite3.Error as e:
            logging.error(f"Failed to load cache from database: {e}")
            
        logging.info(f"Loaded {len(loaded_data)} fresh items from the persistent cache.")
        return loaded_data

    def save_cache_to_db(self, cache_data: dict):
        """
        Saves the current in-memory price cache to the database.
        Uses 'INSERT OR REPLACE' to efficiently update existing records or add new ones.
        """
        if not self.conn:
            return
            
        items_to_save = []
        for ticker, (timestamp_dt, data) in cache_data.items():
            try:
                data_json = json.dumps(data)
                # Convert the datetime object to a Unix timestamp (float) for storage.
                unix_timestamp = timestamp_dt.timestamp()
                items_to_save.append((ticker, data_json, unix_timestamp))
            except (TypeError, ValueError, AttributeError):
                logging.warning(f"Could not serialize data for ticker '{ticker}' to save in cache.")

        if not items_to_save:
            return

        try:
            cursor = self.conn.cursor()
            # Use a transaction for an atomic write operation.
            cursor.execute("BEGIN TRANSACTION")
            
            # 'INSERT OR REPLACE' is an efficient way to "upsert" data in SQLite.
            # It will update the row if the ticker (PRIMARY KEY) exists, or insert a new one if not.
            cursor.executemany(
                "INSERT OR REPLACE INTO price_cache (ticker, data, timestamp) VALUES (?, ?, ?)",
                items_to_save
            )
            
            self.conn.commit()
            logging.info(f"Saved/Updated {len(items_to_save)} items in the persistent cache.")
        except sqlite3.Error as e:
            logging.error(f"Failed to save cache to database: {e}")
            self.conn.rollback()  # Roll back changes on error

    def close(self):
        """Closes the database connection if it's open."""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")