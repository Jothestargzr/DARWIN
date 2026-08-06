#!/bin/bash
set -e

# remote_build.sh
# Runs on the remote AWS Mac instance to fetch and compile DARWIN OS.

# 1. Install Dependencies
echo "Installing Xcode Command Line Tools (requires manual confirmation if not automated)..."
xcode-select --install || true

echo "Installing Homebrew and Python..."
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || true
eval "$(/opt/homebrew/bin/brew shellenv)" || true
brew install python node || true

# 2. Clone DARWIN OS Repo
echo "Cloning DARWIN repository..."
cd ~
if [ ! -d "DARWIN" ]; then
    git clone https://github.com/Jothestargzr/DARWIN.git
fi
cd DARWIN

# 3. Setup bos_build system
echo "Installing build system..."
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install typer pyyaml requests click rich pydantic httpx
cd BrowserOS/packages/browseros
python3 -m pip install -e .

# 4. Fetch Chromium
echo "Fetching Chromium Source (Shallow)..."
cd ~
python3 -m bos_build source ensure --root /tmp/chromium

# 5. Compile DARWIN OS Binary
echo "Starting DARWIN OS Compilation..."
cd ~/DARWIN/BrowserOS/packages/browseros
python3 -m bos_build build --preset release --skip download_resources,sign_macos,sparkle_sign,upload --chromium-src /tmp/chromium/src

echo "✅ Compilation Complete! Artifacts are in /tmp/chromium/**/*.dmg"
