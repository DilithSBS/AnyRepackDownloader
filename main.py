#!/usr/bin/env python3
"""
AnyRepackDownloader - Universal Multi-Part Batch Downloader
Entrypoint script supporting CLI commands, Scheduling Timers, Interactive Wizard,
and automatic Browser Link Extractor generation.
"""

import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple

# Add current directory to sys.path so modules resolve cleanly
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import DEFAULT_DOWNLOAD_DIR, DEFAULT_CONCURRENCY, AUTO_VERIFY
from core.engine import DownloadEngine
from core.verifier import verify_directory
from core.url_parser import detect_landing_page_urls
from core.scheduler import (
    parse_scheduled_time,
    parse_delay,
    wait_until_scheduled_time
)
from extractors.generator import generate_extractor_script
from ui.display import print_banner, print_summary, console

def load_links_from_file(file_path: Path) -> list:
    """Reads non-empty, non-comment lines from a file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def find_extracted_links_file() -> Optional[Path]:
    """Looks for newly downloaded or existing direct_links.txt files."""
    candidates = [
        CURRENT_DIR / "direct_links.txt",
        DEFAULT_DOWNLOAD_DIR / "direct_links.txt",
        Path.home() / "Downloads" / "direct_links.txt",
        Path.home() / "Downloads" / "Out_Direct_Links.txt"
    ]
    for c in candidates:
        if c.is_file() and c.stat().st_size > 0:
            return c
    return None

def check_and_handle_landing_pages(urls: List[str]) -> Tuple[List[str], str]:
    """
    Checks if provided URLs are host landing pages (e.g. fuckingfast.co/<id>)
    which are blocked by Cloudflare. If so, offers to generate extract_links.js.
    """
    landing = detect_landing_page_urls(urls)
    if not landing:
        return urls, ""

    console.print(f"\n[bold yellow]⚠ Landing Page Links Detected ({len(landing)} of {len(urls)})[/]")
    console.print(
        "[dim]These links (e.g. [white]https://fuckingfast.co/<id>[/]) are web landing pages protected by "
        "Cloudflare Turnstile anti-bot verification. CLI downloaders receive HTTP 403 unless direct CDN links "
        "([white]https://dl.fuckingfast.co/...[/]) are used.[/]\n"
    )

    console.print("[bold cyan]Choose an action:[/]")
    console.print("  [bold green][1] Auto-generate browser extractor script (extract_links.js)[/] [Recommended]")
    console.print("  [bold white][2] Continue anyway (if you already have direct tokens or proxy bypass)[/]")

    choice = console.input("\n[bold white]Select option [Default: 1]: [/]").strip()
    if choice != "2":
        output_js = CURRENT_DIR / "extract_links.js"
        generate_extractor_script(urls, output_js)

        first_url = urls[0] if urls else "https://fuckingfast.co"
        console.print(f"\n[bold green]✓ Generated browser script:[/] [cyan]{output_js}[/]")
        console.print("[bold white]═══════════════════════════════════════════════════════════════[/]")
        console.print("[bold cyan]👉 Follow these 3 easy steps in your browser:[/]")
        console.print(f"1. Open Chrome/Edge/Firefox and visit: [underline cyan]{first_url}[/]")
        console.print("2. Press [bold yellow]F12[/] (or Right-Click -> Inspect) and click the [bold yellow]Console[/] tab.")
        console.print(f"3. Copy all code from [yellow]{output_js.name}[/], paste it into Console, and hit [bold yellow]Enter[/].")
        console.print("   [dim]It will resolve all links and download [white]direct_links.txt[/] automatically.[/]")
        console.print("[bold white]═══════════════════════════════════════════════════════════════[/]\n")

        console.input("[bold yellow]Press <Enter> here once direct_links.txt has downloaded...[/]")

        # Search for direct_links.txt
        found = find_extracted_links_file()
        if found:
            resolved_urls = load_links_from_file(found)
            console.print(f"[bold green]✓ Loaded {len(resolved_urls)} direct CDN download links from:[/] {found.name}\n")
            return resolved_urls, found.name
        else:
            console.print("[bold red]Could not find direct_links.txt. Proceeding with original links.[/]")

    return urls, ""

def interactive_wizard() -> tuple:
    """Interactive wizard to guide the user when no CLI arguments are supplied."""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════════[/]")
    console.print("[bold green]  🚀 Welcome to AnyRepackDownloader - Setup Wizard[/]")
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

    # Check for landing pages (FuckingFast / Datanodes) and resolve if needed
    urls, new_source = check_and_handle_landing_pages(urls)
    if new_source:
        source_name = new_source

    # 2. Target Directory
    console.print(f"\n[bold yellow]Download Folder:[/] [dim]Default: {DEFAULT_DOWNLOAD_DIR}[/]")
    target_input = console.input("[bold white]Press Enter to use default or type custom folder path: [/]").strip(' "\'')
    target_dir = Path(target_input) if target_input else DEFAULT_DOWNLOAD_DIR

    # 3. Parallel Count
    console.print(f"\n[bold yellow]Simultaneous Parallel Downloads:[/] [dim]Default: {DEFAULT_CONCURRENCY}[/]")
    par_input = console.input(f"[bold white]Enter number of parallel downloads (1-16) [Default: {DEFAULT_CONCURRENCY}]: [/]").strip()
    concurrency = int(par_input) if par_input.isdigit() and 1 <= int(par_input) <= 32 else DEFAULT_CONCURRENCY

    # 4. Scheduling Options
    scheduled_time: Optional[datetime] = None
    console.print(f"\n[bold yellow]⏰ Schedule Start Time:[/] [dim]Default: Immediate[/]")
    console.print("  [bold cyan][1][/] Start immediately (Default)")
    console.print("  [bold cyan][2][/] Start at a specific time (e.g. 02:00, 23:30, 01:30 AM)")
    console.print("  [bold cyan][3][/] Start after a delay (e.g. 30m, 2h, 1h30m)")

    sched_choice = console.input("\n[bold white]Choose schedule mode [Default: 1]: [/]").strip()
    if sched_choice == "2":
        while True:
            time_input = console.input("👉 Enter target clock time (e.g. [yellow]02:00[/], [yellow]23:30[/], [yellow]01:30 AM[/]): ").strip()
            try:
                scheduled_time = parse_scheduled_time(time_input)
                console.print(f"[bold green]✓ Scheduled for:[/] [bold magenta]{scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}[/]")
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/] {e}. Please try again.")
    elif sched_choice == "3":
        while True:
            delay_input = console.input("👉 Enter delay duration (e.g. [yellow]45m[/], [yellow]2h[/], [yellow]1h30m[/]): ").strip()
            try:
                seconds = parse_delay(delay_input)
                scheduled_time = datetime.now() + timedelta(seconds=seconds)
                console.print(f"[bold green]✓ Starting in {int(seconds/60)} minutes at:[/] [bold magenta]{scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}[/]")
                break
            except Exception as e:
                console.print(f"[bold red]Error:[/] {e}. Please try again.")

    console.print("\n")
    return urls, source_name, target_dir, concurrency, scheduled_time

def main():
    parser = argparse.ArgumentParser(description="AnyRepackDownloader - Universal Multi-Part Batch Downloader with Timer Scheduler")
    parser.add_argument("-i", "--input", help="Path to links text file", default=None)
    parser.add_argument("-d", "--dir", help="Destination download directory", default=None)
    parser.add_argument("-p", "--parallel", "-c", "--concurrency", help="Number of simultaneous parallel downloads", type=int, default=None)
    parser.add_argument("--start-at", help="Schedule start at a specific time (e.g. '02:00', '23:30', '11:30 PM', '2026-11-14 02:00')", default=None)
    parser.add_argument("--delay", help="Schedule start after a delay (e.g. '45m', '2h', '1h30m', '90s')", default=None)
    parser.add_argument("--make-extractor", help="Generate an extract_links.js browser script from a links file and exit", default=None)
    parser.add_argument("--verify-only", help="Verify completeness of an existing download folder without downloading", action="store_true")
    args = parser.parse_args()

    # Make Extractor only mode
    if args.make_extractor:
        src_file = Path(args.make_extractor)
        if not src_file.is_file():
            console.print(f"[bold red]File not found: {args.make_extractor}[/]")
            sys.exit(1)
        raw_urls = load_links_from_file(src_file)
        out_js = CURRENT_DIR / "extract_links.js"
        generate_extractor_script(raw_urls, out_js)
        console.print(f"[bold green]✓ Generated browser extractor script:[/] [cyan]{out_js}[/]")
        console.print(f"Pre-loaded with [yellow]{len(raw_urls)}[/] URLs. Paste into browser DevTools Console to run.")
        return

    # Verify only mode
    if args.verify_only:
        folder = Path(args.dir or DEFAULT_DOWNLOAD_DIR)
        console.print(f"[bold cyan]🔍 Verifying folder:[/] {folder}")
        report = verify_directory(folder)
        print_summary(report, elapsed_seconds=0, target_dir=str(folder))
        return

    # Check CLI vs Interactive Wizard
    scheduled_time: Optional[datetime] = None

    if args.input:
        links_file = Path(args.input)
        if not links_file.is_file():
            console.print(f"[bold red]File not found: {args.input}[/]")
            sys.exit(1)
        urls = load_links_from_file(links_file)
        source_name = links_file.name
        target_dir = Path(args.dir or DEFAULT_DOWNLOAD_DIR)
        concurrency = args.parallel or DEFAULT_CONCURRENCY

        # Check for landing pages
        urls, new_source = check_and_handle_landing_pages(urls)
        if new_source:
            source_name = new_source

        # Check CLI scheduling flags
        if args.start_at:
            try:
                scheduled_time = parse_scheduled_time(args.start_at)
            except Exception as e:
                console.print(f"[bold red]Error in --start-at:[/] {e}")
                sys.exit(1)
        elif args.delay:
            try:
                sec = parse_delay(args.delay)
                scheduled_time = datetime.now() + timedelta(seconds=sec)
            except Exception as e:
                console.print(f"[bold red]Error in --delay:[/] {e}")
                sys.exit(1)
    else:
        urls, source_name, target_dir, concurrency, scheduled_time = interactive_wizard()

    print_banner(
        source_name=source_name,
        target_dir=str(target_dir),
        total_files=len(urls),
        concurrency=concurrency,
        scheduled_time=scheduled_time
    )

    # If scheduled in future, wait with animated dashboard
    if scheduled_time and scheduled_time > datetime.now():
        proceed = wait_until_scheduled_time(scheduled_time, console=console)
        if not proceed:
            sys.exit(0)

    engine = DownloadEngine(
        urls=urls,
        target_dir=target_dir,
        concurrency=concurrency
    )

    result = engine.start()

    if not result.get('interrupted', False) and AUTO_VERIFY:
        report = verify_directory(
            target_dir=target_dir,
            expected_count=len(urls),
            expected_files=result.get('downloaded_files')
        )
        print_summary(report, elapsed_seconds=result['elapsed'], target_dir=str(target_dir))

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Program closed.[/]")
