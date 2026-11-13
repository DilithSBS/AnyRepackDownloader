# Contributing to AnyDownloader

Thank you for your interest in improving **AnyDownloader**! We welcome bug reports, feature suggestions, documentation improvements, and pull requests.

---

## 🛠 Development Setup

1. **Fork & Clone**:
   ```bash
   git clone https://github.com/your-username/AnyDownloader.git
   cd AnyDownloader
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Submitting Pull Requests

1. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/my-cool-feature
   ```
2. **Make Clean Commits**:
   Follow conventional commits format when possible:
   * `feat: add support for magnet links`
   * `fix: correct content-disposition unicode parsing`
   * `docs: update troubleshooting guide`
3. **Verify Locally**:
   Ensure all modules compile and run cleanly:
   ```bash
   python -m py_compile main.py core/*.py ui/*.py config.py
   python main.py --help
   ```
4. **Push & Open PR**:
   Push to your fork and submit a Pull Request with a clear description of the change.

---

## 🐛 Reporting Bugs

When reporting an issue, please provide:
* Your Operating System (Windows / macOS / Linux)
* Python version (`python --version`)
* Terminal/Shell used (e.g., Windows Terminal, PowerShell, CMD, Bash)
* Error logs and steps to reproduce
