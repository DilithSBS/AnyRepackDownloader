<div align="center">

# 🚀 AnyRepackDownloader

### Universal Multi-Threaded Batch Downloader with Timer Scheduling & Archive Verifier

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-modular-green.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

<p align="center">
  A high-performance command-line downloader built for multi-part archives (e.g., FitGirl, DODI repacks), ISOs, and bulk files.<br>
  Features <b>live multi-slot progress bars</b>, <b>HTTP Range byte-level resuming</b>, <b>timer scheduling (off-peak hours)</b>, <b>browser link extraction for Cloudflare hosts</b>, and <b>archive completeness verification</b>.
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
* [Resolving Protected Links (Link Extractor)](#-resolving-protected-links-link-extractor)
* [Usage Modes](#-usage-modes)
  * [1. Interactive Wizard](#1-interactive-wizard-easiest)
  * [2. Command-Line Interface (CLI)](#2-command-line-interface-cli)
  * [3. Scheduled Downloads (Timer / Off-Peak)](#3-scheduled-downloads-timer--off-peak)
  * [4. Generate Browser Extractor Script](#4-generate-browser-extractor-script)
  * [5. Archive Verification Only](#5-archive-verification-only)
* [End-to-End Workflow (FitGirl / Repacks)](#-end-to-end-workflow-fitgirl--repacks)
* [Repository Structure](#-repository-structure)
* [Configuration & Network Tuning](#-configuration--network-tuning)
* [Troubleshooting & FAQ](#-troubleshooting--faq)
* [Contributing](#-contributing)
* [License](#-license)

---

## ✨ Features

* **Universal Multi-Part Support**: Handles any number of parts (from 1 file to hundreds of `.rar`, `.zip`, `.7z`, or `.001` slices).
* **🔗 Integrated Link Extractor**: Resolves Cloudflare-protected landing page links (e.g. `fuckingfast.co/<id>`) into direct CDN download links (`dl.fuckingfast.co`).
* **⏰ Timer & Start Scheduler**: Schedule downloads to start automatically at a specific clock time (e.g., `02:00` AM, `23:30`) or after a duration (e.g., `2h`, `45m`) for off-peak unlimited internet quotas.
* **Standby Mode with Live Countdown**: Displays real-time countdown clock, animated timer progress bar, and lets you press <kbd>Enter</kbd> to skip the wait immediately.
* **Rich Multi-Bar Terminal UI**: Powered by `rich` with zero screen flickering:
  * **Overall Progress Bar**: Real-time completed parts count, percentage, and total ETA.
  * **Dedicated Parallel Slots**: Every active thread has its own bar showing current file, transfer speed (`MB/s`), and buffer progress.
* **Smart HTTP Range Resuming**: Paused or interrupted downloads resume from their exact byte offset. Already completed files are verified and skipped.
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
git clone https://github.com/your-username/AnyRepackDownloader.git
cd AnyRepackDownloader

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

*(Optional)* Install locally as a system command:
```bash
pip install -e .
# Now you can run it anywhere in your terminal:
anydownloader --help
```

---

## 🔗 Resolving Protected Links (Link Extractor)

File hosts like **FuckingFast** and **Datanodes** protect their landing pages (`https://fuckingfast.co/<id>`) with **Cloudflare Turnstile** anti-bot challenges. If you try to download directly from these URLs in Python/curl, you receive an `HTTP 403 Forbidden` error.

To download them, they must first be resolved into **direct CDN URLs** (`https://dl.fuckingfast.co/...`). AnyRepackDownloader provides **3 convenient ways** to do this:

### 1. Automatic Detection & Prompt (Easiest)
If you provide landing page URLs to `main.py`, AnyRepackDownloader automatically detects them and asks:
```text
⚠ Landing Page Links Detected!
Would you like AnyRepackDownloader to generate 'extract_links.js' for you?
  [1] Auto-generate browser extractor script (extract_links.js) [Recommended]
  [2] Continue anyway
```
Selecting `[1]` instantly writes `extract_links.js`. You then paste it once in your browser console, it downloads `direct_links.txt`, and AnyRepackDownloader immediately continues downloading!

### 2. Generate Extractor via CLI
If you have a file with share links (e.g., `game_links.txt`):
```bash
python main.py --make-extractor "game_links.txt"
```
This generates `extract_links.js` pre-loaded with all your URLs.

### 3. Universal Browser Extractor (`extractors/browser_extractor.js`)
If you want to extract links directly while browsing:
1. Open [extractors/browser_extractor.js](extractors/browser_extractor.js) and copy all code.
2. Go to `https://fuckingfast.co` in your browser.
3. Open DevTools (<kbd>F12</kbd> -> **Console**), paste the script, and press <kbd>Enter</kbd>.
4. A floating dark-themed panel appears where you can paste any links, click **Extract Direct Links**, and it will download `direct_links.txt`!

---

## 💻 Usage Modes

### 1. Interactive Wizard (Easiest)
```bash
python main.py
```
The wizard guides you step-by-step:
1. **Link Source**: Auto-detects existing `.txt` files in the directory or lets you paste links.
2. **Download Directory**: Defaults to `./downloads` or your custom path.
3. **Parallel Concurrency**: Choose how many files to download simultaneously (default `4`).
4. **Schedule Start**:
   * `[1] Start immediately`
   * `[2] Start at a specific time` (e.g. `02:00`, `23:30`, `01:30 AM`)
   * `[3] Start after a delay` (e.g. `30m`, `2h`, `1h30m`)

---

### 2. Command-Line Interface (CLI)

For headless setups, servers, or batch automation:

```bash
# Standard batch download
python main.py -i "direct_links.txt" -d "D:\Games\MyGame\Downloads" -p 4

# High-speed connection (6 threads)
python main.py -i "direct_links.txt" -d "./downloads" -p 6

# Conservative mode (2 threads) for unstable connections
python main.py -i "direct_links.txt" -d "./downloads" -p 2
```

#### CLI Flags:
| Flag | Alternative | Description | Default |
| :--- | :--- | :--- | :--- |
| `-i` | `--input` | Path to text file containing links | `None` (prompts wizard) |
| `-d` | `--dir` | Destination download directory | `./downloads` |
| `-p` | `-c`, `--parallel` | Number of simultaneous downloads | `4` |
| `--start-at` | | Schedule start time (`"02:00"`, `"23:30"`, `"11:45 PM"`) | `None` (Immediate) |
| `--delay` | | Schedule start after delay (`"45m"`, `"2h"`, `"1h30m"`) | `None` (Immediate) |
| `--make-extractor` | | Generates `extract_links.js` from links file | `None` |
| `--verify-only` | | Audits an existing folder without downloading | `False` |

---

### 3. Scheduled Downloads (Timer / Off-Peak)

Take advantage of off-peak or free nighttime internet bandwidth by scheduling your download to trigger while you sleep:

#### Start at a Specific Clock Time:
```bash
# Schedule to start at 2:00 AM tonight (or next occurrence)
python main.py -i "direct_links.txt" -d "./downloads" --start-at "02:00"

# Schedule with 12-hour AM/PM format
python main.py -i "direct_links.txt" --start-at "11:30 PM"

# Schedule for a specific date and time
python main.py -i "direct_links.txt" --start-at "2026-11-14 02:30"
```

#### Start After a Relative Delay:
```bash
# Start in 2 hours
python main.py -i "direct_links.txt" --delay "2h"

# Start in 1 hour and 30 minutes
python main.py -i "direct_links.txt" --delay "1h30m"

# Start in 45 minutes with 4 threads
python main.py -i "direct_links.txt" --delay "45m" -p 4
```

#### Standby Mode & Controls:
When scheduled, AnyRepackDownloader displays an animated dashboard:
```text
┌─────────────────── ⏰ Scheduled Download - Standby Mode ────────────────────┐
│                                                                             │
│  🕒 Current Time:                       21:55:10                            │
│  🎯 Start Time  :                       02:00:00 (Tomorrow)                 │
│  ⏳ Time Left   :                       04h 04m 50s                         │
│                                                                             │
│  Timer Progress ━━━━━━━━━━━━━━━━━━━━━━                      45%             │
│                                                                             │
│  Controls: Press <Enter> or <Space> to start immediately • <Ctrl+C> to      │
│  cancel                                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

* **Start Immediately**: Press <kbd>Enter</kbd> or <kbd>Space</kbd> at any time to skip the timer and begin downloading right away.
* **Cancel**: Press <kbd>Ctrl</kbd> + <kbd>C</kbd> to exit cleanly.

---

### 4. Generate Browser Extractor Script

To convert a text file of host links into an executable browser script:
```bash
python main.py --make-extractor "my_game_links.txt"
```
Outputs `extract_links.js` ready to copy into Chrome/Edge/Firefox DevTools.

---

### 5. Archive Verification Only
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

## 🎮 End-to-End Workflow (FitGirl / Repacks)

1. **Get Direct Links**:
   * If you have share links (e.g. `fuckingfast.co/xyz#part001.rar`), run:
     ```bash
     python main.py --make-extractor "links.txt"
     ```
   * Open the first link in your browser, open DevTools (<kbd>F12</kbd> -> **Console**), paste `extract_links.js`, and hit <kbd>Enter</kbd>.
   * It will automatically download `direct_links.txt`.
2. **Run Downloader with Timer**:
   ```bash
   python main.py -i "direct_links.txt" -d "E:\Games\Downloads" --start-at "02:00" -p 4
   ```
3. **Extract Archive**:
   When verification succeeds, right-click **`part001.rar`** (or `.001`) and select **Extract Here** using **7-Zip** or **WinRAR**.
4. **Install**: Run `setup.exe`.

---

## 📂 Repository Structure

```text
AnyRepackDownloader/
├── .github/
│   ├── workflows/ci.yml           # Cross-platform GitHub Actions CI
│   └── ISSUE_TEMPLATE/            # Bug report & feature request templates
├── core/
│   ├── __init__.py
│   ├── engine.py                  # Thread-pool manager, HTTP Range resume logic
│   ├── scheduler.py               # Time parser, delay calculator, countdown dashboard
│   ├── url_parser.py              # Header parser, filename sanitizer, part extractor, landing detector
│   └── verifier.py                # Archive auditor & missing part detector
├── extractors/
│   ├── __init__.py
│   ├── browser_extractor.js       # Universal browser console script with floating UI
│   └── generator.py               # CLI generator creating customized extract_links.js
├── ui/
│   ├── __init__.py
│   └── display.py                 # Rich progress panels, speedometers, tables
├── examples/
│   └── links.sample.txt           # Sample link input formats
├── .gitignore                     # Production Git ignore rules
├── config.py                      # Global settings, timeouts & formats
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

* **HTTP 403 Forbidden**: Links may have expired (some CDN links expire after 24h). Generate fresh links and run again — AnyRepackDownloader will resume right where it stopped.
* **HTTP 429 Too Many Requests**: Host is rate-limiting concurrent streams. Lower parallel connections to `-p 2` or `-p 3`.
* **Pausing**: Hit <kbd>Ctrl</kbd> + <kbd>C</kbd> safely at any point. No files will be corrupted.
* **Timer Standby**: The countdown runs in low-power standby mode consuming minimal CPU.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and development process.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
