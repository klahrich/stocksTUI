# stocksTUI

A Terminal User Interface for monitoring stock prices, news, and historical data, built with [Textual](https://github.com/textualize/textual). Information is fetched using the [yfinance](https://github.com/ranaroussi/yfinance) API.

![stocksTUI Screenshot](https://raw.githubusercontent.com/andriy-git/stocksTUI/main/assets/screenshot.png)

## Features

-   📈 **Real-Time(ish) Price Data** – Because latency is still better than CNBC ads.
-   🧮 **Custom Watchlists** – Sort your tech bros from your energy overlords.
-   📊 **Historical Charts** – Plots your portfolio’s regrets with style.
-   📰 **Ticker News** – Stay smarter than the talking heads.
-   🎨 **Theming** – Dark mode? Light mode? You've got taste, and now you’ve got options.
-   ⚙️ **Configurable Everything** – Refresh rate, default views, and more are all tweakable from the config screen.

**Note:** All ticker symbols must be in the format used by [Yahoo Finance](https://finance.yahoo.com/) (e.g., `AAPL` for Apple, `^GSPC` for S&P 500, `BTC-USD` for Bitcoin).

## Requirements

-   **Python:** 3.9 or newer.
-   **Operating System:**
    -   **Linux / macOS:** Fully supported.
    -   **Windows:** Requires **Windows Terminal** with PowerShell, or **WSL2**. The application will *not* work correctly in the legacy `cmd.exe` console due to its reliance on advanced terminal features.

## Installation

The recommended way to install stocksTUI is with `pipx`. This installs the application and its dependencies in an isolated environment, ensuring that it does not conflict with any other Python packages on your system.

#### 1. Install `pipx`

If you don't have `pipx` installed, you can install it with your system's package manager or with `pip`.

```bash
# On Debian/Ubuntu
sudo apt install pipx

# On Arch Linux
sudo pacman -S python-pipx

# On macOS
brew install pipx

# Or, using pip (ensure ~/.local/bin is in your PATH)
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

#### 2. Install stocksTUI

Once `pipx` is installed, you can install stocksTUI with a single command:

```bash
pipx install stocksTUI
```

## Usage

To run the application, simply execute the following command in your terminal:

```bash
stockstui
```

## Keybindings

| Key             | Action                        | Context      |
| --------------- | ----------------------------- | ------------ |
| `q`             | Quit the application          | Global       |
| `r`             | Refresh current view          | Global       |
| `R` (`Shift+R`) | Refresh all lists in background | Global       |
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

## For Developers: Installing from Source

If you want to run the latest code or contribute to development, you can install from the source repository.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/andriy-git/stocksTUI.git
    cd stocksTUI
    ```

2.  **Run the installation script:**
    This script will create a virtual environment, install all dependencies in editable mode, and create a symlink for the `stockstui` command.
    ```bash
    ./install.sh
    ```

3.  **Run the application:**
    You can now run the application from anywhere.
    ```bash
    stockstui
    ```

## License

This project is licensed under the GNU General Public License v3.0. See the `LICENSE` file for details.
