# 🌿 DARWIN OS: Sovereign Capability Engine

> **A 4D Spatiotemporal Knowledge Architecture & Standalone Agent Browser Engine**

---

## 🏛️ Architecture Overview

DARWIN OS is a sovereign capability platform that integrates high-performance native C++ execution, 4D spatiotemporal graph persistence based on the **Akan Ontological Schema**, and an adapted standalone browser agent environment powered by **BrowserOS**.

```
                           ┌─────────────────────────────────────────────────────────┐
                           │      macOS Native Meta-OCR Menu Bar Controller          │
                           │   [Status: Active | Mode: Full Desktop | Rate: 1m]      │
                           └────────────────────────────┬────────────────────────────┘
                                                        │
┌──────────────────────────────────────┐     ┌──────────▼──────────┐     ┌──────────────────────────────────────┐
│        C++ Sovereign Engine          │     │  Akan Metaphysical  │     │   DARWIN Standalone Browser Engine   │
│       (Core/CPP/darwin_router)       ├────►│   Ontology Schema   │◄────┤  (BrowserOS App UI + Server 9105)   │
│   Entropy Routing on Port 8000       │     │(Okra/Kyinna/Ahodin) │     │      Agent Tab Execution Layer       │
└──────────────────────────────────────┘     └──────────┬──────────┘     └──────────────────────────────────────┘
                                                        │
                                             ┌──────────▼──────────┐
                                             │ TerminusDB 4D Graph │
                                             │(http://localhost:6363)│
                                             └─────────────────────┘
```

---

## ⚡ Key Systems & Features

### 1. 🌌 The Akan Ontological Schema
Data is represented according to the Akan metaphysical framework:

- **`Okra` (Intent Anchor)**: Root origin nodes representing planned goals, directives, and persistent targets.
- **`Sunsum` (Executive Spirit)**: Active executive dynamic measuring structural entropy and guiding transitions.
- **`Kyinna` (Physical Action)**: Execution event nodes recording terminal commands, CDP browser events, and keystrokes.
- **`Nnyini` (Growth & Capability)**: Cognitive friction and active skill acquisition tracking.
- **`Ahodin` (Verified Mastery)**: Proof-of-output nodes for completed builds and verified deliverables.

### 2. ⏳ 4D Spatiotemporal Knowledge Graph (TerminusDB)
- Stores reality state transitions inside TerminusDB (`http://localhost:6363`).
- Constructs 4D hypergraph objects: `PhaseState` (4D coordinates + metric energy tracking), `CapabilityAnchor` (intent hashes), and `PropagationEdge` (cause-and-effect vectors).

### 3. 🚀 C++ Sovereign Intelligence Core (`Core/CPP/`)
- **`darwin_router`**: C++ AI Router running on port `8000` performing low-latency structural entropy routing.
- **`darwin_telemetry`**: C++ macOS telemetry daemon tracking native process execution and memory state.
- **`darwin_mcp`**: Native C++ Model Context Protocol bridge.

### 4. 🌐 DARWIN Standalone Browser Engine (`BrowserOS/`)
- Adapted from the open-source BrowserOS platform.
- Provides a dedicated AI-agent browser interface with multi-tab isolation, CDP protocol hooks, and MCP integration (`http://localhost:3001`).

### 5. 🌿 Native macOS Meta-OCR Menu Bar Controller (`Core/darwin_menubar.py`)
- Ambient top menu bar controller (`🌿 DARWIN`) with built-in OPSEC privacy gates (filtering 1Password, AWS keys, and system credentials).
- Automatically categorizes cross-application activity (BrowserOS, Terminal, Xcode, Cursor) into the Akan Ontology.

---

## 🚀 Quick Start

### Boot the Engine
To start all 5 core DARWIN services with a single command:

```bash
./boot_darwin.sh
```

This automatically initializes:
1. **TerminusDB Graph Database** (`port 6363`)
2. **C++ Telemetry Daemon**
3. **C++ AI Router** (`port 8000`)
4. **macOS Meta-OCR Menu Bar Controller** (`🌿 DARWIN`)
5. **DARWIN Standalone App Server & UI** (`http://localhost:3001`)

---

## 📂 Repository Layout

```
DARWIN/
├── Core/
│   ├── CPP/                     # C++ Sovereign Engine (darwin_router, darwin_telemetry, darwin_mcp)
│   ├── darwin_menubar.py        # Native macOS Menu Bar Meta-OCR Controller
│   ├── darwin_ocr_logger.py    # Screen OCR & Akan Ontology GLM-5.1 Classifier
│   └── darwin_logger.py        # Terminal & Process Capability Logger
├── BrowserOS/                   # Standalone Browser Engine & Agent Server
│   ├── packages/browseros      # bos_build Chromium builder & patches
│   └── packages/browseros-agent# Bun server (apps/server) & App UI (apps/app)
├── aws_build/                   # Remote build and cloud deployment scripts
├── DOCX_Documentation/          # System architecture specs and security assessments
├── boot_darwin.sh               # Master engine startup script
└── README.md                    # Project documentation
```

---

## 🛠️ Building Releases

To build a standalone macOS installer bundle (`DARWIN_OS_v1.0_macOS.dmg`):

```bash
PYTHONPATH=BrowserOS/packages/browseros python3 -m bos_build build --preset release --skip download_resources,sign_macos,sparkle_sign,upload
```

Automated cloud builds are managed via GitHub Actions in [.github/workflows/build-darwin-os.yml](.github/workflows/build-darwin-os.yml).

---

## 📜 License & Acknowledgments
Built with **BrowserOS**, **TerminusDB**, **GLM-5.1**, and the **Akan Metaphysical Framework**.
