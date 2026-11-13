"""
Archive & Multi-Part Integrity Verifier
Detects missing parts, verifies completeness, and calculates archive sizes.
"""

from pathlib import Path
from typing import Dict, List, Any
from core.url_parser import extract_part_number, format_bytes

def verify_directory(target_dir: Path, expected_count: int = None) -> Dict[str, Any]:
    """
    Scans target directory for multi-part archives and verifies completeness.
    """
    found_parts: Dict[int, Path] = {}
    incomplete_parts: List[Path] = []
    total_size = 0

    if not target_dir.exists():
        return {
            'total_found': 0,
            'total_expected': expected_count or 0,
            'missing_parts': list(range(1, (expected_count or 0) + 1)),
            'total_size_bytes': 0,
            'incomplete_files': [],
            'is_complete': False
        }

    for f in target_dir.iterdir():
        if f.is_file():
            # Check for leftover partial files
            if f.name.endswith('.part') or f.name.endswith('.crdownload'):
                incomplete_parts.append(f)
                continue

            part_no = extract_part_number(f.name)
            if part_no is not None:
                found_parts[part_no] = f
                total_size += f.stat().st_size
            else:
                # Regular non-numbered file
                total_size += f.stat().st_size

    if expected_count is not None:
        expected_total = expected_count
    elif found_parts:
        expected_total = max(found_parts.keys())
    else:
        expected_total = 0

    missing = []
    if expected_total > 0:
        for i in range(1, expected_total + 1):
            if i not in found_parts:
                missing.append(i)

    is_complete = (len(missing) == 0 and len(incomplete_parts) == 0 and len(found_parts) == expected_total) if expected_total > 0 else True

    return {
        'total_found': len(found_parts),
        'total_expected': expected_total,
        'missing_parts': missing,
        'total_size_bytes': total_size,
        'incomplete_files': [f.name for f in incomplete_parts],
        'is_complete': is_complete
    }

