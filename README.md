# stocksTUI

A Terminal User Interface for monitoring stock prices, news, and historical data, built with [Textual](https://github.com/textualize/textual). Information is fetched using [yfinance](https://github.com/ranaroussi/yfinance) API.

![stocksTUI Screenshot](https://raw.githubusercontent.com/andriy-git/stocksTUI/main/assets/screenshot.png)

## Overview

stocksTUI is designed for anyone who prefers to keep an eye on the stock market from the comfort of their terminal. It provides a quick overview of your favorite stocks, indices, and cryptocurrencies, along with detailed historical data and the latest news.

## Features

-   **Real-time* Price Data:** Monitor stock prices, daily change, and ranges. (* Fetched via API, may have delays)
-   **Customizable Watchlists:** Organize your symbols into different lists (e.g., tech stocks, crypto, indices).
-   **Historical Data:** View historical performance with charts and data tables.
-   **Ticker News:** Stay updated with the latest news for any symbol.
-   **Theming:** Customize the look and feel with multiple built-in themes.
-   **Configurable:** Adjust refresh rates, default tabs, and more.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/andriy-git/stocksTUI.git
    cd stocksTUI
    ```

2.  **Run the installation script:**
    This will create a virtual environment, install dependencies, and create a `stockstui` command for you.
    ```bash
    ./install.sh
    ```

3.  **Run the application:**
    You can now run the application from anywhere using the `stockstui` command. The symlink located ~/.local/bin, so make sure it's in your path.
    ```bash
    stockstui
    ```
    To see the help text, use the `-h` flag:
    ```bash
    stockstui -h
    ```

## Keybindings

| Key             | Action                        | Context      |
| --------------- | ----------------------------- | ------------ |
| `q`             | Quit the application          | Global       |
| `r`             | Refresh current view          | Global       |
| `R` (`Shift+r`) | Refresh all lists in background | Global       |
| `s`             | Enter Sort Mode               | Price/History |
| `?`             | Toggle Help Screen            | Global       |
| `/`             | Search in current table       | Tables       |
| `1-0`           | Switch to corresponding tab   | Global       |
| `h, j, k, l`    | Navigate / Scroll             | All          |
| `Up, Down`      | Navigate / Scroll             | All          |
| `Left, Right`   | Navigate                      | All          |
| `Tab, Shift+Tab`| Focus next/previous widget    | Global       |
| `Enter`         | Select / Action               | All          |
| `Esc`           | Close dialog/search, exit sort mode, or focus tabs | Global |

In Sort Mode (after pressing `s`):

| Key | Action               | Context       |
| --- | -------------------- | ------------- |
| `d` | Sort by Description/Date | Price/History |
| `p` | Sort by Price        | Price         |
| `c` | Sort by Change/Close | Price/History |
| `e` | Sort by % Change     | Price         |
| `t` | Sort by Ticker       | Price         |
| `u` | Undo Sort            | Price         |
| `H` | Sort by High         | History       |
| `L` | Sort by Low          | History       |
| `v` | Sort by Volume       | History       |

## Configuration

User-specific configuration files are stored in `~/.config/stockstui/`. You can edit `lists.json` to manage your watchlists or `settings.json` for application settings. The application must be restarted for changes to `lists.json` to take effect.

## Dependencies
Dependencies will automatically be installed with the install script.
-   [textual](https://github.com/textualize/textual)
-   [yfinance](https://github.com/ranaroussi/yfinance)
-   [pandas-market-calendars](https://github.com/rsheftel/pandas_market_calendars)
-   [plotext](https://github.com/pplcc/plotext)
-   [textual-plotext](https://github.com/Textualize/textual-plotext)

## License

This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for details.
