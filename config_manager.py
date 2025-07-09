import json
from pathlib import Path
import logging
import os
import time

class ConfigManager:
    """
    Manages loading and saving of application configuration files.
    Handles the fallback logic from default configs to user configs.
    """
    def __init__(self, app_root: Path):
        """Initializes the ConfigManager, setting up paths and loading all configs."""
        # The root directory of the application, used to find default configs
        self.app_root = app_root
        # The directory where user-specific configuration files are stored
        self.user_dir = Path.home() / ".config" / "stockstui"
        # The directory containing default configuration files
        self.default_dir = app_root / "default_configs"
        # Ensure the user config directory exists
        self.user_dir.mkdir(parents=True, exist_ok=True)

        # Load configurations into memory
        self.settings: dict = self._load_or_create('settings.json')
        self.lists: dict = self._load_or_create('lists.json')
        self.themes: dict = self._load_or_create('themes.json')
        self.descriptions: dict = self._load_or_create('descriptions.json')

    def _load_or_create(self, filename: str) -> dict:
        """
        Loads a JSON config file from the user's config directory.

        - If the user file doesn't exist, it's created by copying the default.
        - If the user file is empty or corrupted (invalid JSON), it's deleted and
          restored from the default.
        - If a default file is missing, a critical error is logged.
        - 'descriptions.json' is special-cased to not have a default and can be empty.
        """
        user_path = self.user_dir / filename
        default_path = self.default_dir / filename

        # Special handling for descriptions.json which has no default and can be empty.
        if filename == 'descriptions.json':
            if not user_path.exists():
                return {}
            try:
                with open(user_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {} # Return empty on corruption

        # Loop to handle automatic restoration of corrupted/empty files.
        while True:
            # If user config exists, try to load it.
            if user_path.exists():
                try:
                    with open(user_path, 'r') as f:
                        data = json.load(f)
                    # If the file is just an empty dictionary/list, it's not useful.
                    # Treat it as corrupt so it gets restored from default.
                    if not data:
                        raise json.JSONDecodeError("File is empty", "", 0)
                    return data
                except (json.JSONDecodeError, IOError):
                    logging.warning(f"Corrupted or empty config '{filename}'. Deleting and restoring from default.")
                    try:
                        os.remove(user_path)
                    except OSError as e:
                        logging.error(f"Failed to remove corrupted config '{filename}': {e}")
                        return {} # Return empty if we can't delete the corrupt file.
                    # Fall through to the creation logic below.

            # If user config does not exist (or was just deleted).
            if not default_path.exists():
                logging.critical(f"Default config '{filename}' is missing!")
                return {} # Critical failure, return empty.
            
            try:
                # Read the default config
                with open(default_path, 'r') as f_default:
                    default_data = json.load(f_default)
                # Write it to the user's config directory
                with open(user_path, 'w') as f_user:
                    json.dump(default_data, f_user, indent=4)
                logging.info(f"Created user config '{filename}' from default.")
                return default_data
            except (IOError, json.JSONDecodeError) as e:
                logging.error(f"Failed to create user config '{filename}' from default: {e}")
                return {} # Failed to create from default, return empty.

    def get_setting(self, key: str, default=None):
        """Retrieves a specific setting by key from the loaded settings."""
        return self.settings.get(key, default)

    def save_settings(self):
        """Saves the current settings to the user's 'settings.json' file."""
        try:
            with open(self.user_dir / 'settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            logging.error(f"Could not save settings: {e}")

    def save_lists(self):
        """Saves the current symbol lists to the user's 'lists.json' file."""
        try:
            with open(self.user_dir / 'lists.json', 'w') as f:
                json.dump(self.lists, f, indent=4)
        except IOError as e:
            logging.error(f"Could not save lists: {e}")

    def save_descriptions(self):
        """Saves the current descriptions cache to the user's 'descriptions.json' file."""
        try:
            with open(self.user_dir / 'descriptions.json', 'w') as f:
                json.dump(self.descriptions, f, indent=4)
        except IOError as e:
            logging.error(f"Could not save descriptions: {e}")

    def get_description(self, ticker: str) -> str | None:
        """
        Gets a company description (longName) from the cache.

        Returns the name if it exists and is less than 7 days old, otherwise None.
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
        """Updates the description cache with new data, adding a fresh timestamp."""
        for ticker, long_name in new_data.items():
            self.descriptions[ticker] = {
                "longName": long_name,
                "timestamp": time.time()
            }
        self.save_descriptions()