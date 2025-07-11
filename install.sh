#!/bin/bash

set -e # Exit immediately if a command exits with a non-zero status.

# Get the absolute path of the project directory (where install.sh is located)
PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

VENV_DIR="$PROJECT_DIR/venv"
RUNNER_SCRIPT="$PROJECT_DIR/run.sh"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
SYMLINK_TARGET_DIR="$HOME/.local/bin"
SYMLINK_NAME="stockstui"
SYMLINK_PATH="$SYMLINK_TARGET_DIR/$SYMLINK_NAME"

echo "Starting installation for StocksTUI..."

# 1. Set up Python virtual environment
if [ -d "$VENV_DIR" ]; then
  echo "Virtual environment already exists. Skipping creation."
else
  echo "Creating Python virtual environment at $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

# 2. Install dependencies
echo "Installing dependencies from $REQUIREMENTS_FILE..."
"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"

# 3. Create the runner script (run.sh)
echo "Creating runner script at $RUNNER_SCRIPT..."
cat <<'EOF' >"$RUNNER_SCRIPT"
#!/bin/bash

# Resolve the true directory of the script, following symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

# Define paths relative to the script's location
VENV_PATH="$SCRIPT_DIR/venv"
MAIN_PY_PATH="$SCRIPT_DIR/stockstui/main.py"
HELP_TXT_PATH="$SCRIPT_DIR/stockstui/documents/help.txt"

# Help flag logic
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    # Use 'less' if available, otherwise 'cat'
    if command -v less &> /dev/null; then
        less "$HELP_TXT_PATH"
    else
        cat "$HELP_TXT_PATH"
    fi
    exit 0
fi

# Activate venv and run the main python script
source "$VENV_PATH/bin/activate"
python3 "$MAIN_PY_PATH" "$@" # Pass all arguments to the python script
EOF

# 4. Make the runner script executable
echo "Making runner script executable..."
chmod +x "$RUNNER_SCRIPT"

# 5. Create the symbolic link
# Ensure the target directory exists
mkdir -p "$SYMLINK_TARGET_DIR"

echo "Creating symbolic link at $SYMLINK_PATH..."
# Remove existing symlink to avoid errors
rm -f "$SYMLINK_PATH"
ln -s "$RUNNER_SCRIPT" "$SYMLINK_PATH"

echo ""
echo "Installation complete!"
echo "You can now run the application by typing: stockstui"
echo "Or display help with: stockstui -h"
