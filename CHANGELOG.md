# Change Log

## [unreleased] 

### Added
-   `feat(cache)`: Added intelligent cache expiration based on market status (open/closed) to optimize API usage and data freshness.
-   `feat(cache)`: Implemented a persistent cache for ticker metadata (exchange, name) to reduce redundant API calls.
-   `feat(logs)`: Implemented in-app notifications for `WARNING` and `ERROR` log messages, providing users with real-time feedback on application issues.
-   `feat(cli)`: Implemented command-line argument parsing, allowing the app to be launched into specific views (e.g., `stockstui --history AAPL`).
-   `feat(cli)`: Added a `--session-list` argument to create temporary, single-session watchlists from the command line.
-   `feat(cache)`: Implemented a persistent SQLite cache (`app_cache.db`) for price data to significantly improve application startup times.
-   `feat(cache)`: Added automatic, age-based pruning of the persistent cache to maintain performance and control file size.

### Changed
-   `refactor(cli)`: Dynamically load app version from package metadata instead of hard-coding it.
-   `refactor(cache)`: Converted all caching logic to use timezone-aware UTC datetimes for improved accuracy and reliability.

### Fixed
-   `fix(config)`: Use `os.replace` for atomic writes to ensure cross-platform compatibility (especially Windows).
-   `fix(debug)`: Re-enable test buttons correctly when the "Compare Info" modal is cancelled.
-   `fix(news)`: Hardened the link-parsing regex to prevent errors with special characters in news titles.
-   `fix(provider)`: Refactored the data fetching pipeline to resolve a critical bug that caused silent failures and no data to be displayed.
-   `fix(provider)`: Ensured the force refresh option correctly bypasses the market-aware cache logic.
-   `fix(provider)`: Fixed a bug preventing price data from being processed and displayed after a fresh info fetch.
-   `fix(logs)`: Corrected the `TextualHandler` to reliably post notifications from any thread without errors.
-   `fix(cache)`: Reduced the in-memory cache duration to ensure data is properly refreshed when switching tabs.
-   `fix(db)`: Corrected SQLite transaction management to prevent connection state errors and ensure the cache saves reliably on application exit.
-   `fix(db)`: Resolved a `sqlite3.OperationalError` by setting `isolation_level=None` to allow for explicit transaction control.
-   `fix(logs)`: Made the `TextualHandler` thread-safe, preventing a `RuntimeError` when logging errors from the main application thread.
-   `fix(ux)`: Corrected the "Last Refresh" timestamp to update properly after a data fetch.
-   `fix(ux)`: Ensured data is always refreshed (from API or cache) when switching tabs.

## [0.1.0-b2] - 2025-07-11

### Added
-   `feat(ux)`: Added background color flash (green for up, red for down) on 'Change' and '% Change' cells to highlight price updates
-   `feat(ux)`: Improved refresh UX by keeping stale data visible until new data arrives, eliminating loading screen on subsequent refreshes
-   `feat(ux)`: Enhanced readability with inverted text color during price change flashes
-   `feat(ux)`: Refined price comparison to round values, avoiding flashes on minor floating-point fluctuations

### Docs

-   `docs(readme, cli)`: Updated `README.md` to recommend `pipx` installation with setup instructions
-   `docs(readme, cli)`: Added disclaimer in `README.md` and help command requiring tickers in Yahoo Finance format

## [0.1.0-b1] - 2025-07-11

### Added

-   `feat(ui)`: Show specific feedback for invalid tickers and data fetching failures in the history and news views.
-   `feat(news)`: Notify the user when attempting to open an external link.
  
### Fixed

-   `fix(config)`: Use atomic writes for config files to prevent data loss.
-   `fix(config)`: Eliminate risk of infinite loops during config loading.
-   `fix(config)`: Backup corrupted config files as `.bak` to allow manual recovery.
-   `fix(news)`: Show clear error messages in the Markdown widget for invalid tickers or network issues.
-   `fix(news)`: Provide actionable feedback if no web browser is configured when opening external links.
-   `fix(debug)`: Prevent race conditions by disabling test buttons on start and restoring them on modal cancel.
-   `fix(provider)`: Improve resilience of batch requests by handling individual ticker failures gracefully.
-   `fix(imports)`: Corrected all internal imports to be absolute for package compatibility.

### Changed

-   `refactor(provider)`: Replace broad `except Exception` with targeted exception handling for network, data, and validation errors.
-   `refactor(cli)`: Modernize command-line help display to use `subprocess` for better robustness.

### Docs

-   `docs(readme)`: Revised README for clarity, adding PyPI installation instructions and specific OS requirements.
-   `docs(help)`: Overhaul help text for improved clarity, structure, and readability.

### Build

-   `build(packaging)`: Configured the project for PyPI distribution with a `pyproject.toml` and restructured the source layout.
-   `build(install)`: Reworked `install.sh` to use `pip install -e .` for a standard, editable development setup.

## [0.1.0-beta.0] - 2025-07-08

-   Initial pre-release.
-   Many foundational changes; changelog entries begin from `0.1.0-beta.1`.