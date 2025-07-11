# Change Log

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.0-beta.1] - 2025-07-11

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

### Docs

-   `docs(readme)`: Revised README for clarity, adding PyPI installation instructions and specific OS requirements.

### Build

-   `build(packaging)`: Configured the project for PyPI distribution with a `pyproject.toml` and restructured the source layout.

## [0.1.0-beta.0] - 2025-07-08

-   Initial pre-release.
-   Many foundational changes; changelog entries begin from `0.1.0-beta.1`.