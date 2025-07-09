import json
from pathlib import Path
import logging
import os
import time

class ConfigManager:
    """
    Manages loading, saving, and accessing application configuration files.

    This class is responsible for handling all configuration data, including settings,
    symbol lists, and themes. It implements a robust fallback mechanism: if a user's
    configuration file is missing or corrupted, it is automatically created or
    restored from a default template located in the application's root directory.
    This ensures the application can always start up with a valid config.
    """
    def __init__(self, app_root: Path):
        """
        Initializes the ConfigManager.

        Args:
            app_root: The root path of the application, used to find the
                      'default_configs' directory.
        """
        # Define user-specific and default configuration directories
        self.user_dir = Path.home() / ".config" / "stockstui"
        self.default_dir = app_root / "default_configs"
        self.user_dir.mkdir(parents=True, exist_ok=True)

        # Load all primary configurations into memory upon initialization.
        # The _load_or_create method handles the logic of reading user files
        # or creating them from defaults if necessary.
        self.settings: dict = self._load_or_create('settings.json')
        self.lists: dict = self._load_or_create('lists.json')
        self.themes: dict = self._load_or_create('themes.json')
        self.descriptions: dict = self._load_or_create('descriptions.json')

    def _load_or_create(self, filename: str) -> dict:
        """
        Loads a JSON configuration file from the user's config directory.

        If the user-specific file does not exist, is empty, or is corrupted
        (i.e., not valid JSON), this method will:
        1. Load the corresponding default configuration file from the app's internal
           'default_configs' directory.
        2. Write this default configuration to the user's config path, effectively
           creating or restoring it.
        3. Return the loaded default data.

        This ensures the application always has a valid configuration to work with.

        Args:
            filename: The name of the configuration file to load (e.g., 'settings.json').

        Returns:
            A dictionary containing the loaded configuration data. Returns an empty
            dictionary if both user and default files are critically unreadable.
        """
        user_path = self.user_dir / filename
        default_path = self.default_dir / filename

        # Special case: 'descriptions.json' is a cache file. It has no default,
        # is allowed to be missing, and can be empty.
        if filename == 'descriptions.json':
            if not user_path.exists():
                return {}  # Return empty dict if it doesn't exist
            try:
                with open(user_path, 'r') as f:
                    content = f.read()
                    # An empty file is valid for the descriptions cache.
                    return json.loads(content) if content.strip() else {}
            except (json.JSONDecodeError, IOError):
                logging.warning(f"Could not read or parse descriptions file '{user_path}'. Returning empty config.")
                return {} # On error, treat as empty.

        # Standard logic for settings.json, lists.json, themes.json
        data = None
        # --- Step 1: Attempt to load the user's configuration file. ---
        if user_path.exists():
            try:
                with open(user_path, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                logging.warning(f"User config '{user_path}' is corrupted. It will be restored from default.")
                data = None  # Mark as needing restoration from default.

        # --- Step 2: If user config failed to load, create/restore it from default. ---
        if data is None:
            # First, check if the default file even exists. This is a critical error.
            if not default_path.exists():
                logging.critical(f"Default config '{default_path}' is missing! Cannot create user config.")
                return {}  # Critical failure, return empty config to prevent crash.

            try:
                # Read the default config.
                with open(default_path, 'r') as f_default:
                    default_data = json.load(f_default)
                
                # Write the default data to the user's config path. This creates a new
                # file or overwrites a corrupted one, ensuring a working baseline.
                with open(user_path, 'w') as f_user:
                    json.dump(default_data, f_user, indent=4)
                logging.info(f"Created/Restored user config '{user_path}' from default.")
                return default_data
            except (IOError, json.JSONDecodeError) as e:
                logging.error(f"Failed to create user config from '{default_path}': {e}")
                # As a last resort, try to load the default data directly into memory
                # without writing it to the user's directory.
                try:
                    with open(default_path, 'r') as f_default:
                        return json.load(f_default)
                except Exception as final_e:
                    logging.critical(f"CRITICAL: Failed to read default config '{default_path}': {final_e}")
                    return {}

        return data

    def get_setting(self, key: str, default=None):
        """
        Safely retrieves a value from the loaded settings.

        Args:
            key: The key of the setting to retrieve.
            default: The value to return if the key is not found.

        Returns:
            The setting value or the specified default.
        """
        return self.settings.get(key, default)

    def save_settings(self):
        """Saves the current in-memory settings to the user's settings.json file."""
        try:
            with open(self.user_dir / 'settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            logging.error(f"Could not save settings: {e}")

    def save_lists(self):
        """Saves the current in-memory symbol lists to the user's lists.json file."""
        try:
            with open(self.user_dir / 'lists.json', 'w') as f:
                json.dump(self.lists, f, indent=4)
        except IOError as e:
            logging.error(f"Could not save lists: {e}")

    def save_descriptions(self):
        """Saves the current in-memory descriptions cache to the user's descriptions.json file."""
        try:
            with open(self.user_dir / 'descriptions.json', 'w') as f:
                json.dump(self.descriptions, f, indent=4)
        except IOError as e:
            logging.error(f"Could not save descriptions: {e}")

    def get_description(self, ticker: str) -> str | None:
        """
        Gets a long name description for a ticker from the local cache.

        Returns the description only if it exists and is not expired (older than 7 days).
        The cache entry format is: `{"longName": "...", "timestamp": 167...}`

        Args:
            ticker: The ticker symbol to look up.

        Returns:
            The long name as a string, or None if not found or expired.
        """
        entry = self.descriptions.get(ticker)
        if not entry:
            return None
        
        timestamp = entry.get('timestamp', 0)
        # 7 days in seconds = 7 * 24 * 60 * 60 = 604800
        if time.time() - timestamp > 604800:
            return None # Expired

        return entry.get('longName')

    def update_descriptions(self, new_data: dict[str, str]):
        """
        Updates the description cache with new data and saves it to a file.

        Each new entry is timestamped to handle cache expiration.

        Args:
            new_data: A dictionary mapping ticker symbols to their long names.
        """
        for ticker, long_name in new_data.items():
            self.descriptions[ticker] = {
                "longName": long_name,
                "timestamp": time.time()
            }
        self.save_descriptions()