"""
Rich-based Visual Terminal UI
Renders interactive banners, multi-bar progress layouts, and summary tables.
"""

from typing import Optional
from datetime import datetime
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TaskProgressColumn
)
from core.url_parser import format_bytes

console = Console()

def print_banner(
    source_name: str,
    target_dir: str,
    total_files: int,
    concurrency: int,
    scheduled_time: Optional[datetime] = None
):
    """Prints the application startup banner."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_row(f"[bold cyan]📁 Target Folder:[/] [white]{target_dir}[/]")
    grid.add_row(f"[bold cyan]🔗 Links Source :[/] [white]{source_name}[/]")
    grid.add_row(f"[bold cyan]📦 Total Files  :[/] [bold yellow]{total_files}[/]")
    grid.add_row(f"[bold cyan]⚡ Parallel Conns:[/] [bold green]{concurrency} simultaneous downloads[/]")

    if scheduled_time:
        grid.add_row(f"[bold cyan]⏰ Scheduled For:[/] [bold magenta]{scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}[/]")
    else:
        grid.add_row(f"[bold cyan]⏰ Start Time   :[/] [bold green]Immediate[/]")

    panel = Panel(
        grid,
        title="[bold green]🚀 AnyRepackDownloader - Universal Multi-Part Downloader[/]",
        subtitle="[dim]HTTP Range Resuming • Multi-Threaded • Timer Scheduling • Auto-Verification[/]",
        border_style="bright_blue"
    )
    console.print(panel)
    console.print()

def create_progress_bars(concurrency: int):
    """
    Creates the dual progress system:
    1. Overall progress across all parts
    2. Active worker slot progress bars
    """
    overall_progress = Progress(
        TextColumn("[bold green]{task.description:<24}"),
        BarColumn(bar_width=36, style="grey30", complete_style="green", finished_style="bright_green"),
        TaskProgressColumn(),
        TextColumn("[bold yellow]{task.completed}/{task.total} parts"),
        TimeRemainingColumn(),
        console=console
    )

    file_progress = Progress(
        TextColumn("{task.description:<34}"),
        BarColumn(bar_width=24, style="grey30", complete_style="cyan", finished_style="bright_cyan"),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console
    )

    overall_task_id = overall_progress.add_task("📦 Overall Progress", total=100)
    slot_task_ids = [
        file_progress.add_task(f"[cyan]Slot {i+1}[/]: [dim]Waiting...[/]", total=100)
        for i in range(concurrency)
    ]

    display_group = Group(
        Panel(
            Group(overall_progress, file_progress),
            title=f"[bold cyan]Active Downloads ({concurrency} Parallel Slots)[/]",
            border_style="cyan"
        )
    )

    return overall_progress, file_progress, overall_task_id, slot_task_ids, display_group

def print_summary(report: dict, elapsed_seconds: float, target_dir: str):
    """Renders a beautiful summary table upon completion."""
    table = Table(title="[bold green]🎉 Download & Verification Report[/]", border_style="bright_blue")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Details", style="white")

    is_multi = report.get('is_multipart', False)
    label = "Parts" if is_multi else "Files"

    if report['is_complete']:
        status_text = f"[bold green]Complete (All {label} Verified)[/]"
    else:
        status_text = f"[bold red]Incomplete (Missing {label})[/]"

    table.add_row("Status", status_text)
    table.add_row(f"{label} Verified", f"{report['total_found']} / {report['total_expected']}")
    table.add_row("Total Size", f"{format_bytes(report['total_size_bytes'])}")
    table.add_row("Time Elapsed", f"{elapsed_seconds / 60:.1f} minutes ({elapsed_seconds:.0f} seconds)")
    
    if elapsed_seconds > 0 and report['total_size_bytes'] > 0:
        avg_speed = report['total_size_bytes'] / elapsed_seconds
        table.add_row("Average Speed", f"{format_bytes(avg_speed)}/s")

    table.add_row("Destination", f"{target_dir}")

    if report['incomplete_files']:
        table.add_row("Incomplete Files (.part)", f"[yellow]{', '.join(report['incomplete_files'])}[/]")

    if report['missing_parts']:
        table.add_row(f"Missing {label}", f"[bold red]{', '.join(str(m) for m in report['missing_parts'])}[/]")

    console.print()
    console.print(table)

    if report['is_complete']:
        if is_multi:
            console.print(Panel(
                "[bold white]All archive parts are present and ready for extraction![/]\n"
                "Right-click [bold yellow]part001.rar[/] (or .001) and choose [bold green]Extract Here[/] using 7-Zip or WinRAR.",
                border_style="green",
                title="[bold green]Ready for Extraction[/]"
            ))
        else:
            console.print(Panel(
                "[bold green]✔ All downloaded files verified intact and ready to use![/]",
                border_style="green",
                title="[bold green]Download Successful[/]"
            ))
    else:
        console.print(Panel(
            f"[bold yellow]Some {label.lower()} are missing or incomplete.[/]\n"
            "Simply re-run the program pointing to the same folder to resume the missing files automatically.",
            border_style="yellow",
            title="[bold yellow]Action Required[/]"
        ))

