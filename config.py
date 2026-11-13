"""
AnyRepackDownloader - Configuration
Centralized settings for modular file downloading.
"""

from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = BASE_DIR / "downloads"

# Network & Download Engine
DEFAULT_CONCURRENCY = 4        # Number of simultaneous parallel downloads
CHUNK_SIZE = 512 * 1024        # 512 KB per buffer chunk for smooth progress
MAX_RETRIES = 5                # Retry attempts per file on network drop
REQUEST_TIMEOUT = 25           # Connection/Read timeout in seconds

# User-Agent Header
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0.0.0 Safari/537.36"
)

# UI Settings
REFRESH_RATE = 8               # Progress bar refresh rate per second
AUTO_VERIFY = True             # Auto-check multi-part archive completeness upon finish

# Scheduler Settings
DEFAULT_SCHEDULE_FORMAT = "%H:%M"   # Default display format for time
