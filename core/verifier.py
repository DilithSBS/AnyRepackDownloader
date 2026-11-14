"""
Archive & Multi-Part Integrity Verifier
Detects missing parts, verifies completeness, and calculates archive sizes.
Supports multi-part archives, single files, and arbitrary subset downloads.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from core.url_parser import extract_part_number, format_bytes

def verify_directory(
    target_dir: Path,
    expected_count: Optional[int] = None,
    expected_files: Optional[List[Path]] = None
) -> Dict[str, Any]:
    """
    Scans target directory and verifies download completeness and integrity.
    
    Supports:
    1. Multi-part archives (e.g. part001 to part136).
    2. Single files or arbitrary subsets (e.g. part6 only, setup.exe).
    3. Standalone directory verification (--verify-only mode).
    """
    target_dir = Path(target_dir)
    found_parts: Dict[int, Path] = {}
    verified_files: List[Path] = []
    missing_items: List[str] = []
    incomplete_files: List[str] = []
    total_size = 0

    if not target_dir.exists():
        return {
            'total_found': 0,
            'total_expected': expected_count or (len(expected_files) if expected_files else 0),
            'missing_parts': [f.name for f in expected_files] if expected_files else [],
            'total_size_bytes': 0,
            'incomplete_files': [],
            'is_complete': False,
            'is_multipart': False
        }

    # Case 1: We have explicit expected_files from the download engine
    if expected_files:
        expected_total = len(expected_files)
        # Check if the expected files appear to be a numbered multi-part archive
        file_part_map = {}
        for f in expected_files:
            p_num = extract_part_number(f.name)
            if p_num is not None:
                file_part_map[f.name] = p_num

        is_multipart_batch = len(file_part_map) == len(expected_files) and len(expected_files) > 1

        for expected_path in expected_files:
            # File may be located directly in target_dir or subfolder
            actual_path = target_dir / expected_path.name if not expected_path.is_file() else expected_path
            part_file = actual_path.with_name(f"{actual_path.name}.part")

            if part_file.exists():
                incomplete_files.append(part_file.name)

            if actual_path.exists() and actual_path.stat().st_size > 0:
                verified_files.append(actual_path)
                total_size += actual_path.stat().st_size
                p_num = extract_part_number(actual_path.name)
                if p_num is not None:
                    found_parts[p_num] = actual_path
            else:
                missing_items.append(expected_path.name)

        is_complete = (len(missing_items) == 0 and len(incomplete_files) == 0 and len(verified_files) == expected_total)

        return {
            'total_found': len(verified_files),
            'total_expected': expected_total,
            'missing_parts': missing_items,
            'total_size_bytes': total_size,
            'incomplete_files': incomplete_files,
            'is_complete': is_complete,
            'is_multipart': is_multipart_batch
        }

    # Case 2: Standalone folder scan (--verify-only or no explicit expected_files list)
    all_files = [f for f in target_dir.iterdir() if f.is_file()]
    for f in all_files:
        if f.name.endswith('.part') or f.name.endswith('.crdownload'):
            incomplete_files.append(f.name)
            continue

        p_num = extract_part_number(f.name)
        if p_num is not None:
            found_parts[p_num] = f
        verified_files.append(f)
        total_size += f.stat().st_size

    # Analyze if files form a sequential multi-part series starting at part 1
    if found_parts:
        min_p = min(found_parts.keys())
        max_p = max(found_parts.keys())

        if (len(found_parts) > 1 and min_p == 1) or (expected_count and expected_count > 1 and min_p == 1):
            expected_total = expected_count if expected_count is not None else max_p
            missing_parts_nums = [i for i in range(1, expected_total + 1) if i not in found_parts]
            missing_items = [f"Part {i}" for i in missing_parts_nums]
            is_complete = (len(missing_items) == 0 and len(incomplete_files) == 0 and len(found_parts) == expected_total)
            return {
                'total_found': len(found_parts),
                'total_expected': expected_total,
                'missing_parts': missing_items,
                'total_size_bytes': total_size,
                'incomplete_files': incomplete_files,
                'is_complete': is_complete,
                'is_multipart': True
            }

    # Non-multipart or individual files in folder
    expected_total = expected_count if expected_count is not None else len(verified_files)
    if expected_count is not None and len(verified_files) < expected_count:
        missing_items = [f"{expected_count - len(verified_files)} file(s) missing"]

    is_complete = (len(missing_items) == 0 and len(incomplete_files) == 0 and len(verified_files) >= expected_total and expected_total > 0)

    return {
        'total_found': len(verified_files),
        'total_expected': expected_total,
        'missing_parts': missing_items,
        'total_size_bytes': total_size,
        'incomplete_files': incomplete_files,
        'is_complete': is_complete,
        'is_multipart': False
    }
