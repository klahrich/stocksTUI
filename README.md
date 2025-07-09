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

### Linux

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

### Windows

For Windows 10/11, for the poor souls who have not switched. I strongly recommend using the **Windows Subsystem for Linux (WSL 2)**. This will provide you with the knowledge to switch to Linux later, the best performance and a seamless experience.

1.  **Install WSL 2 (One-Time Setup):**
    If you don't have WSL installed, open **PowerShell as an Administrator** and run:
    ```powershell
    wsl --install
    ```
    This will install the necessary Windows features and the default Ubuntu Linux distribution. You may need to restart your computer. For more details, see the [official Microsoft documentation](https://docs.microsoft.com/en-us/windows/wsl/install).

2.  **Open Your Linux Terminal:**
    Once installed, open "Ubuntu" (or your chosen distro) from the Windows Start Menu. All the following commands should be run inside this Linux terminal.

3.  **Follow the Linux Installation Steps:**
    Now that you are inside your Linux environment, follow the exact same steps as the Linux installation above:
    ```bash
    # Clone the repository inside a directory of your choice
    git clone https://github.com/andriy-git/stocksTUI.git
    cd stocksTUI

    # Run the installation script
    ./install.sh
    ```

4.  **Run the application:**
    From your Linux terminal, you can now run the app:
    ```bash
    stockstui
    ```

### macOS

For macOS, I recommend a manual installation using Python's built-in tools.

1.  **Prerequisite: Install Python 3.**
    If you don't have a modern version of Python installed, I recommend installing it via [Homebrew](https://brew.sh/):
    ```bash
    brew install python3
    ```

2.  **Clone the repository:**
    ```bash
    git clone https://github.com/andriy-git/stocksTUI.git
    cd stocksTUI
    ```

3.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *(You will need to run `source venv/bin/activate` in every new terminal session before running the app).*

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the application:**
    ```bash
    python3 main.py
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
