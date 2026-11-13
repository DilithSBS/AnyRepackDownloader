<div align="center">

# 🚀 AnyDownloader

### Universal Multi-Threaded Batch & Multi-Part Archive Downloader

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-modular-green.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<p align="center">
  A high-performance command-line downloader built for multi-part archives (e.g., FitGirl, DODI repacks), ISOs, and bulk files.<br>
  Features <b>live multi-slot progress bars</b>, <b>HTTP Range byte-level resuming</b>, and <b>archive completeness verification</b>.
</p>

```text
╭────────────────── Active Downloads (4 Parallel Slots) ──────────────────╮
│ 📦 Overall Progress        ━━━━━━━━━━━━━━━━━━━━ 25.0% 34/136 parts 00:24:15 │
│ Slot 1: Part 035           ━━━━━━━━━            45.2% 237/524 MB  18.4 MB/s │
│ Slot 2: Part 036           ━━━━━━━━━━━━━━       70.1% 367/524 MB  21.1 MB/s │
│ Slot 3: Part 037           ━━━━                 20.5% 107/524 MB  15.2 MB/s │
│ Slot 4: Part 038           ━━━━━━━━━━━          55.0% 288/524 MB  19.0 MB/s │
╰─────────────────────────────────────────────────────────────────────────╯
```

</div>

---

## 📋 Table of Contents
* [Features](#-features)
* [Quick Start](#-quick-start)
* [Installation](#-installation)
* [Usage Modes](#-usage-modes)
  * [1. Interactive Wizard](#1-interactive-wizard-easiest)
  * [2. Command-Line Interface (CLI)](#2-command-line-interface-cli)
  * [3. Paste URLs Directly](#3-paste-urls-directly)
  * [4. Archive Verification Only](#4-archive-verification-only)
* [End-to-End Workflow (e.g. FitGirl / Multi-Part Repacks)](#-end-to-end-workflow-eg-fitgirl--multi-part-repacks)
* [Repository Structure](#-repository-structure)
* [Configuration & Network Tuning](#-configuration--network-tuning)
* [Troubleshooting & FAQ](#-troubleshooting--faq)
* [Contributing](#-contributing)
* [License](#-license)

---

## ✨ Features

* **Universal Multi-Part Support**: Handles any number of parts (from 1 file to hundreds of `.rar`, `.zip`, `.7z`, or `.001` slices).
* **Rich Multi-Bar Terminal UI**: Powered by `rich` with no screen flickering:
  * **Overall Progress Bar**: Real-time completed parts count, percentage, and total ETA.
  * **Dedicated Parallel Slots**: Every active thread has its own bar showing current file, transfer speed (`MB/s`), and buffer progress.
* **Smart HTTP Range Resuming**: Paused or interrupted downloads resume from their exact byte offset. Already completed files are skipped.
* **Automatic Filename Resolution**: Discovers filenames via `Content-Disposition`, URL fragments (`#name.rar`), query parameters, or paths.
* **Built-in Archive Verifier**: Audits downloaded archives after completion to ensure no parts are missing (`part001` through `partN`).
* **Configurable Concurrency**: Tune simultaneous connection threads (`-p 2`, `-p 4`, `-p 8`) to saturate your network safely.

---

## ⚡ Quick Start

### Windows (1-Click)
Double-click **`run.bat`** to start the interactive wizard!

### Linux / macOS / Terminal
```bash
# Clone the repository
git clone https://github.com/your-username/AnyDownloader.git
cd AnyDownloader

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

---

## 📦 Installation

Ensure you have **Python 3.8+** installed:

```bash
python --version
```

Install requirements:
```bash
pip install -r requirements.txt
```

*(Optional)* Install locally as a CLI command:
```bash
pip install -e .
# Now you can run it anywhere in your terminal:
anydownloader --help
```

---

## 💻 Usage Modes

### 1. Interactive Wizard (Easiest)
```bash
python main.py
```
The wizard guides you through 3 simple prompts:
1. **Link Source**: Auto-detects existing `.txt` files in the directory or lets you paste links.
2. **Download Directory**: Defaults to `./downloads` or your custom path.
3. **Parallel Concurrency**: Choose how many files to download simultaneously (default `4`).

---

### 2. Command-Line Interface (CLI)

For headless setups, servers, or batch automation:

```bash
# Standard batch download
python main.py -i "links.txt" -d "D:\Games\MyGame\Downloads" -p 4

# High-speed connection (6 threads)
python main.py -i "links.txt" -d "./downloads" -p 6

# Conservative mode (2 threads) for unstable connections
python main.py -i "links.txt" -d "./downloads" -p 2
```

#### CLI Flags:
| Flag | Alternative | Description | Default |
| :--- | :--- | :--- | :--- |
| `-i` | `--input` | Path to text file containing links | `None` (prompts wizard) |
| `-d` | `--dir` | Destination download directory | `./downloads` |
| `-p` | `-c`, `--parallel` | Number of simultaneous downloads | `4` |
| `--verify-only` | | Audits an existing folder without downloading | `False` |

---

### 3. Paste URLs Directly
1. Run `python main.py`.
2. Choose `P` when prompted for links.
3. Paste your links into the terminal and press <kbd>Enter</kbd> on a blank line (or type `done`).

---

### 4. Archive Verification Only
Verify that an existing folder contains all consecutive parts before extracting:

```bash
python main.py --verify-only -d "E:\Games\RDR2\Downloads"
```

Output Report:
* **Parts Verified**: `136 / 136`
* **Total Size**: `68.2 GB`
* **Missing Parts**: Lists missing part indices if any are absent.
* **Incomplete Files**: Highlights any unfinished `.part` files.

---

## 🎮 End-to-End Workflow (e.g. FitGirl / Multi-Part Repacks)

1. **Extract Direct Links**:
   If downloading from Cloudflare-protected hosts (like `fuckingfast.co`), open the first link in your browser, press <kbd>F12</kbd> -> Console, and run the link extractor snippet to save `direct_links.txt`.
2. **Run AnyDownloader**:
   ```bash
   python main.py -i "direct_links.txt" -d "E:\Games\Downloads" -p 4
   ```
3. **Extract Archive**:
   When verification succeeds, right-click **`part001.rar`** (or `.001`) and select **Extract Here** using **7-Zip** or **WinRAR**.
4. **Install**: Run `setup.exe`.

---

## 📂 Repository Structure

```text
AnyDownloader/
├── .github/
│   ├── workflows/ci.yml           # Cross-platform GitHub Actions CI
│   └── ISSUE_TEMPLATE/            # Bug report & feature request templates
├── core/
│   ├── __init__.py
│   ├── engine.py                  # Thread-pool manager, HTTP Range resume logic
│   ├── url_parser.py              # Header parser, filename sanitizer, part extractor
│   └── verifier.py                # Archive auditor & missing part detector
├── ui/
│   ├── __init__.py
│   └── display.py                 # Rich progress panels, speedometers, tables
├── examples/
│   └── links.sample.txt           # Sample link input formats
├── .gitignore                     # Production Git ignore rules
├── config.py                      # Global settings & timeouts
├── CONTRIBUTING.md                # Contribution guidelines
├── LICENSE                        # MIT License
├── main.py                        # Application entrypoint
├── pyproject.toml                 # Package metadata & CLI script mapping
├── README.md                      # Documentation
├── requirements.txt               # Dependencies
└── run.bat                        # Windows 1-click launcher
```

---

## ⚙️ Configuration & Network Tuning

Edit [config.py](config.py) to customize default settings:

```python
DEFAULT_CONCURRENCY = 4        # Simultaneous connections
CHUNK_SIZE = 512 * 1024        # Buffer chunk size (512 KB)
MAX_RETRIES = 5                # Reconnection attempts on drops
REQUEST_TIMEOUT = 25           # Timeout in seconds
USER_AGENT = "..."             # Custom User-Agent string
```

---

## ❓ Troubleshooting & FAQ

* **HTTP 403 Forbidden**: Links may have expired (some CDN links expire after 24h). Generate fresh links and run again — AnyDownloader will resume right where it stopped.
* **HTTP 429 Too Many Requests**: Host is rate-limiting concurrent streams. Lower parallel connections to `-p 2` or `-p 3`.
* **Pausing**: Hit <kbd>Ctrl</kbd> + <kbd>C</kbd> safely at any point. No files will be corrupted.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development process.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
