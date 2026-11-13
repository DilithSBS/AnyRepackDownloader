#!/usr/bin/env python3
"""
AnyDownloader - Universal Multi-Part Batch Downloader
Entrypoint script supporting both CLI commands and an Interactive Wizard.
"""

import sys
import argparse
from pathlib import Path

# Add current directory to sys.path so modules resolve cleanly
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import DEFAULT_DOWNLOAD_DIR, DEFAULT_CONCURRENCY, AUTO_VERIFY
from core.engine import DownloadEngine
from core.verifier import verify_directory
from ui.display import print_banner, print_summary, console

def load_links_from_file(file_path: Path) -> list:
    """Reads non-empty, non-comment lines from a file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def interactive_wizard() -> tuple:
    """Interactive wizard to guide the user when no CLI arguments are supplied."""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/]")
    console.print("[bold green]  🚀 Welcome to AnyDownloader - Setup Wizard[/]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/]\n")

    # 1. Discover potential link files
    potential_files = []
    search_dirs = [CURRENT_DIR, CURRENT_DIR.parent, Path.home() / "Downloads"]
    for d in search_dirs:
        if d.exists():
            for f in d.glob("*.txt"):
                if "link" in f.name.lower() or "url" in f.name.lower() or "out_" in f.name.lower():
                    if f not in potential_files and f.stat().st_size > 0:
                        potential_files.append(f)

    urls = []
    source_name = ""

    if potential_files:
        console.print("[bold yellow]Found links file(s) on your computer:[/]")
        for idx, f in enumerate(potential_files[:5]):
            console.print(f"  [bold cyan][{idx + 1}][/] {f.name} [dim]({f.parent})[/]")
        console.print("  [bold cyan][C][/] Enter custom file path or drag-and-drop a file")
        console.print("  [bold cyan][P][/] Paste URLs directly into terminal\n")

        choice = console.input("[bold white]Choose an option [Default: 1]: [/]").strip()
        if not choice:
            choice = "1"

        if choice.isdigit() and 1 <= int(choice) <= len(potential_files):
            chosen_file = potential_files[int(choice) - 1]
            urls = load_links_from_file(chosen_file)
            source_name = chosen_file.name
        elif choice.lower() == "p":
            console.print("\n[bold yellow]Paste your URLs below (press Enter twice or type 'done' to finish):[/]")
            while True:
                line = input().strip()
                if not line or line.lower() == "done":
                    break
                urls.append(line)
            source_name = f"Pasted ({len(urls)} links)"
        else:
            custom_path = console.input("\n[bold yellow]👉 Enter or drag-and-drop the links .txt file: [/]").strip(' "\'')
            file_obj = Path(custom_path)
            if file_obj.is_file():
                urls = load_links_from_file(file_obj)
                source_name = file_obj.name
            else:
                console.print(f"[bold red]File not found: {custom_path}[/]")
                sys.exit(1)
    else:
        custom_path = console.input("[bold yellow]👉 Enter or drag-and-drop links .txt file (or type 'paste'): [/]").strip(' "\'')
        if custom_path.lower() == 'paste':
            console.print("\n[bold yellow]Paste your URLs below (press Enter twice to finish):[/]")
            while True:
                line = input().strip()
                if not line:
                    break
                urls.append(line)
            source_name = f"Pasted ({len(urls)} links)"
        else:
            file_obj = Path(custom_path)
            if file_obj.is_file():
                urls = load_links_from_file(file_obj)
                source_name = file_obj.name
            else:
                console.print(f"[bold red]File not found: {custom_path}[/]")
                sys.exit(1)

    if not urls:
        console.print("[bold red]No valid URLs found. Exiting.[/]")
        sys.exit(1)

    # 2. Target Directory
    console.print(f"\n[bold yellow]Download Folder:[/] [dim]Default: {DEFAULT_DOWNLOAD_DIR}[/]")
    target_input = console.input("[bold white]Press Enter to use default or type custom folder path: [/]").strip(' "\'')
    target_dir = Path(target_input) if target_input else DEFAULT_DOWNLOAD_DIR

    # 3. Parallel Count
    console.print(f"\n[bold yellow]Simultaneous Parallel Downloads:[/] [dim]Default: {DEFAULT_CONCURRENCY}[/]")
    par_input = console.input(f"[bold white]Enter number of parallel downloads (1-16) [Default: {DEFAULT_CONCURRENCY}]: [/]").strip()
    concurrency = int(par_input) if par_input.isdigit() and 1 <= int(par_input) <= 32 else DEFAULT_CONCURRENCY

    console.print("\n")
    return urls, source_name, target_dir, concurrency

def main():
    parser = argparse.ArgumentParser(description="AnyDownloader - Universal Multi-Part Batch Downloader")
    parser.add_argument("-i", "--input", help="Path to links text file", default=None)
    parser.add_argument("-d", "--dir", help="Destination download directory", default=None)
    parser.add_argument("-p", "--parallel", "-c", "--concurrency", help="Number of simultaneous parallel downloads", type=int, default=None)
    parser.add_argument("--verify-only", help="Verify completeness of an existing download folder without downloading", action="store_true")
    args = parser.parse_args()

    # Verify only mode
    if args.verify_only:
        folder = Path(args.dir or DEFAULT_DOWNLOAD_DIR)
        console.print(f"[bold cyan]🔍 Verifying folder:[/] {folder}")
        report = verify_directory(folder)
        print_summary(report, elapsed_seconds=0, target_dir=str(folder))
        return

    # Check CLI vs Interactive Wizard
    if args.input:
        links_file = Path(args.input)
        if not links_file.is_file():
            console.print(f"[bold red]File not found: {args.input}[/]")
            sys.exit(1)
        urls = load_links_from_file(links_file)
        source_name = links_file.name
        target_dir = Path(args.dir or DEFAULT_DOWNLOAD_DIR)
        concurrency = args.parallel or DEFAULT_CONCURRENCY
    else:
        urls, source_name, target_dir, concurrency = interactive_wizard()

    print_banner(
        source_name=source_name,
        target_dir=str(target_dir),
        total_files=len(urls),
        concurrency=concurrency
    )

    engine = DownloadEngine(
        urls=urls,
        target_dir=target_dir,
        concurrency=concurrency
    )

    result = engine.start()

    if not result.get('interrupted', False) and AUTO_VERIFY:
        report = verify_directory(target_dir, expected_count=len(urls))
        print_summary(report, elapsed_seconds=result['elapsed'], target_dir=str(target_dir))

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Program closed.[/]")

