"""
Download Scheduler & Timer
Allows scheduling downloads at a specific clock time or after a specified delay,
complete with an interactive live countdown dashboard and early-start controls.
"""

import re
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn

def parse_delay(val: str) -> float:
    """
    Parses a delay string into total seconds.
    Examples:
      - '45m' -> 2700s
      - '2h' -> 7200s
      - '1h30m' -> 5400s
      - '90s' -> 90s
      - '30' -> 1800s (defaults to minutes)
    """
    val = val.strip().lower()
    total_seconds = 0.0

    pattern = r'(\d+(?:\.\d+)?)\s*([hms])'
    matches = re.findall(pattern, val)
    if matches:
        for amount, unit in matches:
            amt = float(amount)
            if unit == 'h':
                total_seconds += amt * 3600
            elif unit == 'm':
                total_seconds += amt * 60
            elif unit == 's':
                total_seconds += amt
        if total_seconds > 0:
            return total_seconds

    # Fallback to plain numeric string (assume minutes if <= 300, else seconds)
    cleaned = val.replace('.', '', 1)
    if cleaned.isdigit():
        num = float(val)
        return num * 60 if num <= 300 else num

    raise ValueError(
        f"Invalid delay format '{val}'. Examples: '30m', '2h', '1h30m', '45s'"
    )

def parse_scheduled_time(time_str: str) -> datetime:
    """
    Parses a target time string into a concrete future datetime.
    Supports:
      - '02:00', '2:00', '23:30' (24-hour clock)
      - '02:00:00'
      - '2:30 AM', '11:45 PM' (12-hour clock)
      - '2026-11-14 02:00' (full date-time)
      - '14/11/2026 02:00'
    If the time given is earlier than the current time today, it automatically
    schedules for the next occurrence tomorrow.
    """
    time_str = time_str.strip()
    now = datetime.now()

    formats = [
        '%H:%M',
        '%H:%M:%S',
        '%I:%M %p',
        '%I:%M%p',
        '%I %p',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y %H:%M:%S',
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            if dt.year == 1900:
                scheduled = now.replace(
                    hour=dt.hour,
                    minute=dt.minute,
                    second=dt.second,
                    microsecond=0
                )
                # If target time has already passed today, schedule for tomorrow
                if scheduled <= now:
                    scheduled += timedelta(days=1)
                return scheduled
            else:
                if dt <= now:
                    raise ValueError(f"Specified time '{time_str}' is in the past!")
                return dt
        except ValueError as e:
            if "is in the past" in str(e):
                raise
            continue

    raise ValueError(
        f"Could not parse '{time_str}'. Supported formats: '02:00', '23:30', '11:45 PM', '2026-11-14 02:00'"
    )

def format_time_delta(seconds: float) -> str:
    """Formats seconds into 'XXh YYm ZZs' or 'YYm ZZs'."""
    sec = max(0, int(seconds))
    hours, remainder = divmod(sec, 3600)
    minutes, seconds_left = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}h {minutes:02d}m {seconds_left:02d}s"
    elif minutes > 0:
        return f"{minutes:02d}m {seconds_left:02d}s"
    else:
        return f"{seconds_left:02d}s"

def check_skip_key() -> bool:
    """Non-blocking check for keyboard press to skip countdown."""
    try:
        import msvcrt
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            return True
    except ImportError:
        import select
        if select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
            return True
    return False

def wait_until_scheduled_time(target_time: datetime, console: Optional[Console] = None) -> bool:
    """
    Renders an animated countdown timer until target_time is reached.
    Allows user to press Enter or Space to start immediately, or Ctrl+C to abort.
    Returns:
      True: Proceed to download (time reached or skipped).
      False: Aborted by user.
    """
    if console is None:
        console = Console()

    now = datetime.now()
    total_wait_seconds = (target_time - now).total_seconds()
    if total_wait_seconds <= 0:
        return True

    # Setup progress bar for the waiting period
    wait_progress = Progress(
        TextColumn("[bold cyan]Timer Progress"),
        BarColumn(bar_width=40, style="grey30", complete_style="magenta", finished_style="bright_magenta"),
        TaskProgressColumn(),
        console=console
    )
    timer_task_id = wait_progress.add_task("Wait", total=total_wait_seconds, completed=0)

    start_instant = datetime.now()

    try:
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                current_now = datetime.now()
                remaining = (target_time - current_now).total_seconds()

                if remaining <= 0:
                    break

                # Check if user pressed a key to skip wait
                if check_skip_key():
                    console.print("\n[bold green]⏩ Skip requested by user! Starting download immediately...[/]")
                    return True

                elapsed = (current_now - start_instant).total_seconds()
                wait_progress.update(timer_task_id, completed=min(elapsed, total_wait_seconds))

                # Build Dashboard Table
                table = Table.grid(expand=True)
                table.add_column(justify="left", style="bold cyan", width=18)
                table.add_column(justify="left", style="bold white")

                # Day indicator
                day_indicator = ""
                if target_time.date() == current_now.date():
                    day_indicator = "(Today)"
                elif target_time.date() == (current_now.date() + timedelta(days=1)):
                    day_indicator = "(Tomorrow)"
                else:
                    day_indicator = f"({target_time.strftime('%Y-%m-%d')})"

                table.add_row("🕒 Current Time:", f"{current_now.strftime('%H:%M:%S')}")
                table.add_row("🎯 Start Time  :", f"[bold yellow]{target_time.strftime('%H:%M:%S')}[/] [dim]{day_indicator}[/]")
                table.add_row("⏳ Time Left   :", f"[bold green]{format_time_delta(remaining)}[/]")

                panel = Panel(
                    Group(
                        table,
                        "",
                        wait_progress,
                        "",
                        "[dim cyan]Controls:[/] [white]Press [bold yellow]<Enter>[/] or [bold yellow]<Space>[/] to start immediately • [bold red]<Ctrl+C>[/] to cancel[/]"
                    ),
                    title="[bold magenta]⏰ Scheduled Download - Standby Mode[/]",
                    border_style="magenta",
                    padding=(1, 2)
                )

                live.update(panel)
                time.sleep(0.25)

        console.print("\n[bold green]⏰ Scheduled time reached! Initiating download...[/]\n")
        return True

    except KeyboardInterrupt:
        console.print("\n[bold yellow][!] Scheduled download cancelled by user.[/]")
        return False

