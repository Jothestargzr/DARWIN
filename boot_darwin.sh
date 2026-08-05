#!/bin/bash
echo "🚀 Booting DARWIN Sovereign Capability Engine..."

# 1. Start TerminusDB (Ontology Layer)
echo "[1/4] Starting TerminusDB..."
docker run -d -p 6363:6363 terminusdb/terminusdb:latest > /dev/null 2>&1
echo "✅ TerminusDB initialized on port 6363"

# 2. Start C++ Telemetry Daemon
echo "[2/4] Waking C++ Telemetry Daemon (darwin_telemetry)..."
cd Core/CPP
./darwin_telemetry &
TELEMETRY_PID=$!
cd ../..

# 3. Start C++ AI Router
echo "[3/4] Waking C++ AI Router (darwin_router)..."
cd Core/CPP
./darwin_router &
ROUTER_PID=$!
cd ../..

# 4. Start BrowserOS (DARWIN UI Layer)
echo "[4/4] Launching DARWIN Standalone Desktop App..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9005 --user-data-dir=/tmp/darwin_chrome_profile > /dev/null 2>&1 &
cd BrowserOS/packages/browseros-agent
export PATH="$HOME/.bun/bin:$PATH"
bun run start:server

# Cleanup on exit
trap "kill $TELEMETRY_PID $ROUTER_PID; echo 'DARWIN Offline.'; exit" SIGINT SIGTERM
