"""
URL Parser and Filename Detection
Extracts accurate filenames and part numbers from headers, URLs, and hash fragments.
"""

import re
import urllib.parse
from pathlib import Path

INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

def sanitize_filename(filename: str) -> str:
    """Removes invalid filesystem characters from filenames."""
    cleaned = re.sub(INVALID_CHARS, '_', filename).strip('. ')
    return cleaned or "downloaded_file.bin"

def parse_filename(url: str, content_disposition: str = None, fallback_index: int = None) -> str:
    """
    Detects the best filename using multiple fallback strategies:
    1. Content-Disposition header
    2. URL fragment (#filename.ext)
    3. URL path (/downloads/file.ext)
    4. Query parameters (?filename=...)
    5. Fallback numbered part
    """
    # 1. Content-Disposition header
    if content_disposition:
        # Check RFC 5987 / UTF-8 encoded filename
        match_utf8 = re.search(r"filename\*\s*=\s*(?:UTF-8''|utf-8'')([^;]+)", content_disposition, re.IGNORECASE)
        if match_utf8:
            candidate = urllib.parse.unquote(match_utf8.group(1).strip('"\' '))
            if candidate:
                return sanitize_filename(candidate)

        # Standard filename parameter
        match_std = re.search(r'filename\s*=\s*("([^"]+)"|([^;\s]+))', content_disposition, re.IGNORECASE)
        if match_std:
            candidate = match_std.group(2) or match_std.group(3)
            candidate = urllib.parse.unquote(candidate.strip('"\' '))
            if candidate:
                return sanitize_filename(candidate)

    parsed = urllib.parse.urlparse(url)

    # 2. URL Fragment (#...)
    if parsed.fragment:
        candidate = parsed.fragment.strip()
        if "." in candidate and len(candidate) > 3:
            return sanitize_filename(candidate)

    # 3. URL Path
    path_name = Path(parsed.path).name
    if path_name and "." in path_name and len(path_name) > 2:
        return sanitize_filename(urllib.parse.unquote(path_name))

    # 4. URL Query params (e.g. ?file=... or ?name=...)
    queries = urllib.parse.parse_qs(parsed.query)
    for key in ['file', 'filename', 'name', 'title']:
        if key in queries and queries[key]:
            candidate = queries[key][0]
            if "." in candidate:
                return sanitize_filename(candidate)

    # 5. Fallback numbered name
    if fallback_index is not None:
        return f"part_{fallback_index:03d}.bin"

    return "downloaded_file.bin"

def extract_part_number(filename: str) -> int:
    """
    Detects archive part number from filenames like:
    - game.part001.rar -> 1
    - archive.part1.rar -> 1
    - file.001 -> 1
    - file.r01 -> 1
    - part_05.zip -> 5
    Returns None if not detected.
    """
    fname = filename.lower()
    
    # Matches .part001, .part1, .part_01
    m = re.search(r'\.part[_-]?(\d+)', fname)
    if m:
        return int(m.group(1))

    # Matches standard 7-zip .001, .002
    m = re.search(r'\.(\d{3})$', fname)
    if m:
        return int(m.group(1))

    # Matches old RAR .r00, .r01
    m = re.search(r'\.r(\d{2})$', fname)
    if m:
        return int(m.group(1))

    # Matches _part01 or -part-01
    m = re.search(r'[_-]part[_-]?(\d+)', fname)
    if m:
        return int(m.group(1))

    return None

def format_bytes(bytes_num: float) -> str:
    """Formats raw bytes into human-readable units (KB, MB, GB, TB)."""
    if bytes_num is None:
        return "0.0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:3.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"

def is_landing_page_url(url: str) -> bool:
    """
    Checks if a URL is a known file host landing page protected by Cloudflare/captchas
    rather than a direct CDN download link.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()

        # FuckingFast (landing: fuckingfast.co/<id>, direct: dl.fuckingfast.co/dl/...)
        if "fuckingfast.co" in host:
            if not host.startswith("dl.") and not path.startswith("/dl/"):
                return True

        # Datanodes (landing: datanodes.to/<id>, direct has /dl/ or /direct/)
        if "datanodes.to" in host:
            if not path.startswith("/dl/") and "/direct/" not in path:
                return True

        # Pixeldrain (landing: pixeldrain.com/u/<id>, direct: /api/file/<id>)
        if "pixeldrain.com" in host and "/u/" in path:
            return True

        # Gofile (landing: gofile.io/d/<id>)
        if "gofile.io" in host and "/d/" in path:
            return True

    except Exception:
        pass

    return False

def detect_landing_page_urls(urls: list) -> list:
    """Filters and returns all URLs in the list that are landing page URLs."""
    return [u for u in urls if is_landing_page_url(u)]


