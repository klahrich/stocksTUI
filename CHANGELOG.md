# Change Log
## [unreleased]

### Added
-   `feat(cli)`: Added a `--man` flag to display a detailed, man-page-style user guide.
-   `feat(debug)`: Debug test isolation for accurate measurements
-   `feat(ux)`: Smart refresh system (`r` vs `R` keybindings)
-   `feat(news)`: Added support for viewing a combined news feed for multiple tickers, sorted by publication time
-   `feat(cache)`: Implemented persistent SQLite cache (`app_cache.db`) for price/ticker metadata
-   `feat(cache)`: Added market-aware cache expiration to optimize API usage
-   `feat(cli)`: Implemented CLI argument parsing for launching into specific views
-   `feat(logs)`: Added in-app notifications for WARNING/ERROR log messages
-   `feat(logs)`: Added file logger (`stockstui.log`) for debug information

### Changed
-   `refactor(ux)`: Simplified price comparison data handling to update after table population
-   `refactor(ux)`: Improved price change flash by moving direction logic to formatter.py for accurate comparison
-   `refactor(provider)`: Overhauled data fetching pipeline for efficiency
-   `refactor(cli)`: Dynamically load app version from package metadata
-   `refactor(cache)`: Converted caching to timezone-aware UTC datetimes
-   `refactor(config)`: Relocated config/cache files to OS-appropriate directories
-   `refactor(cli)`: Enhanced `--news` to support multiple comma-separated tickers

### Fixed
-   `fix(ui)`: Prevented crash when switching tabs during price cell flash animation
-   `fix(ui)`: Ensured search box is dismissed when switching tabs, preventing it from lingering
-   `fix(ui)`: Fixed invalid state in "Default Tab" dropdown when the configured default tab is deleted
-   `fix(cache)`: Ensured live price updates are saved to session cache, maintaining consistent prices when switching tabs
-   `fix(formatter)`: Restored user-defined aliases in the price table, prioritizing custom names over default descriptions
-   `fix(cache)`: Standardized cache structure to prevent TypeErrors
-   `fix(provider)`: Prioritized `fast_info` for real-time data accuracy
-   `fix(core)`: Improved stability with better DB transaction handling
-   `fix(core)`: Ensured atomic config saves using `os.replace`
-   `fix(ux)`: Guaranteed data refresh on tab switch with accurate timestamps
-   `fix(ui)`: Corrected source ticker styling in multi-news view
-   `fix(news)`: Hardened link-parsing regex against special characters
-   `fix(debug)`: Fixed test button re-enabling after modal cancellation
-   `fix(history)`: Added CLI argument handling for `--chart` and `--period`
-   `fix(css)`: Fixed scrollbar in config visible tabs container
-   `fix(logs)`: Implemented thread-safe logging

### Docs
-   `docs`: README and manual overhaul

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
