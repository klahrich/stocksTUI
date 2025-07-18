#!/bin/bash

set -e # Exit immediately if a command exits with a non-zero status.

# Get the absolute path of the project directory (where install.sh is located)
PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

VENV_DIR="$PROJECT_DIR/venv"
SYMLINK_TARGET_DIR="$HOME/.local/bin"
SYMLINK_NAME="stockstui"
SYMLINK_PATH="$SYMLINK_TARGET_DIR/$SYMLINK_NAME"

echo "Starting development installation for StocksTUI..."

# 1. Set up Python virtual environment
if [ -d "$VENV_DIR" ]; then
  echo "Virtual environment already exists. Skipping creation."
else
  echo "Creating Python virtual environment at $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

# 2. Install dependencies from pyproject.toml in editable mode
# The '-e' flag means changes to your .py files will be reflected immediately.
# The '.' tells pip to install the project in the current directory.
echo "Installing project in editable mode..."
"$VENV_DIR/bin/pip" install -e .

# 3. Create the symbolic link to the executable generated by pip
# This replaces the need for a custom run.sh script.
local_executable="$VENV_DIR/bin/$SYMLINK_NAME"

# Ensure the target directory exists
mkdir -p "$SYMLINK_TARGET_DIR"

echo "Creating symbolic link at $SYMLINK_PATH..."
# Remove existing symlink to avoid errors
rm -f "$SYMLINK_PATH"
ln -s "$local_executable" "$SYMLINK_PATH"

echo ""
echo "Installation complete!"
echo "You can now run the application by typing: stockstui"
echo "Or display help with: stockstui -h"