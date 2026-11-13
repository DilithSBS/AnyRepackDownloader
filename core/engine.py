"""
Download Engine
Multi-threaded queue-based download manager with HTTP Range resuming and retry mechanisms.
"""

import time
import queue
import threading
from pathlib import Path
from typing import List, Dict, Any, Tuple
import requests

from core.url_parser import parse_filename
from config import CHUNK_SIZE, MAX_RETRIES, REQUEST_TIMEOUT, USER_AGENT, REFRESH_RATE
from ui.display import create_progress_bars, console
from rich.live import Live

class DownloadEngine:
    def __init__(
        self,
        urls: List[str],
        target_dir: Path,
        concurrency: int = 4,
        chunk_size: int = CHUNK_SIZE,
        max_retries: int = MAX_RETRIES,
        timeout: int = REQUEST_TIMEOUT,
        user_agent: str = USER_AGENT
    ):
        self.urls = urls
        self.target_dir = Path(target_dir)
        self.concurrency = max(1, min(concurrency, 32))
        self.chunk_size = chunk_size
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agent = user_agent

        self.work_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self.completed_counter = {
            'count': 0,
            'failed': [],
            'lock': threading.Lock()
        }

    def _get_remote_size(self, session: requests.Session, url: str) -> int:
        """Attempts to obtain file size via HEAD or zero-range GET."""
        try:
            r = session.head(url, allow_redirects=True, timeout=self.timeout)
            if r.status_code == 200 and 'content-length' in r.headers:
                return int(r.headers['content-length'])
        except Exception:
            pass

        try:
            r = session.get(url, headers={'Range': 'bytes=0-0'}, allow_redirects=True, timeout=self.timeout)
            if 'content-range' in r.headers:
                total = r.headers['content-range'].split('/')[-1]
                return int(total)
            if 'content-length' in r.headers:
                return int(r.headers['content-length'])
        except Exception:
            pass
        return None

    def _worker(
        self,
        slot_id: int,
        file_progress,
        slot_task_id,
        overall_progress,
        overall_task_id
    ):
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Connection': 'keep-alive',
        })

        while not self.shutdown_event.is_set():
            try:
                item = self.work_queue.get(timeout=0.5)
            except queue.Empty:
                break

            index, url, total_items = item
            item_num = index + 1
            default_name = parse_filename(url, fallback_index=item_num)
            file_path = self.target_dir / default_name
            part_path = self.target_dir / f"{default_name}.part"

            file_progress.reset(
                slot_task_id,
                total=100,
                completed=0,
                description=f"[cyan]Slot {slot_id+1}[/]: [yellow]Part {item_num:03d}[/] Connecting..."
            )

            # Check if file exists and is complete
            if file_path.exists():
                local_size = file_path.stat().st_size
                remote_size = self._get_remote_size(session, url)
                if remote_size is not None and local_size == remote_size:
                    file_progress.update(
                        slot_task_id,
                        completed=local_size,
                        total=local_size,
                        description=f"[cyan]Slot {slot_id+1}[/]: [green]{file_path.name[:20]}[/] (Verified)"
                    )
                    with self.completed_counter['lock']:
                        self.completed_counter['count'] += 1
                        overall_progress.update(overall_task_id, completed=self.completed_counter['count'])
                    self.work_queue.task_done()
                    time.sleep(0.05)
                    continue

            # Check existing .part file for resume
            existing_bytes = 0
            if part_path.exists():
                existing_bytes = part_path.stat().st_size

            success = False
            retries = 0

            while retries < self.max_retries and not self.shutdown_event.is_set():
                try:
                    headers = {
                        'User-Agent': self.user_agent,
                        'Accept': '*/*',
                        'Connection': 'keep-alive',
                    }
                    mode = 'wb'
                    if existing_bytes > 0:
                        headers['Range'] = f'bytes={existing_bytes}-'
                        mode = 'ab'

                    with session.get(url, headers=headers, stream=True, timeout=self.timeout) as r:
                        if r.status_code not in (200, 206):
                            if r.status_code == 416:  # Range fully satisfied
                                if part_path.exists():
                                    if file_path.exists():
                                        file_path.unlink()
                                    part_path.rename(file_path)
                                success = True
                                break
                            raise Exception(f"HTTP {r.status_code}")

                        # Check real filename from Content-Disposition header
                        cd = r.headers.get('content-disposition', '')
                        real_name = parse_filename(url, cd, fallback_index=item_num)
                        if real_name != default_name:
                            default_name = real_name
                            file_path = self.target_dir / default_name
                            part_path = self.target_dir / f"{default_name}.part"

                        # Determine total size
                        total_size = None
                        if 'content-range' in r.headers:
                            try:
                                total_size = int(r.headers['content-range'].split('/')[-1])
                            except Exception:
                                pass
                        if not total_size and 'content-length' in r.headers:
                            if r.status_code == 206:
                                total_size = existing_bytes + int(r.headers['content-length'])
                            else:
                                total_size = int(r.headers['content-length'])

                        if not total_size:
                            total_size = 524288000  # Fallback estimate

                        # If server didn't support resume, restart
                        if existing_bytes > 0 and r.status_code == 200:
                            existing_bytes = 0
                            mode = 'wb'

                        file_progress.reset(
                            slot_task_id,
                            total=total_size,
                            completed=existing_bytes,
                            description=f"[cyan]Slot {slot_id+1}[/]: [bold white]{default_name[:22]}[/]"
                        )

                        downloaded = existing_bytes
                        with open(part_path, mode) as f:
                            for chunk in r.iter_content(chunk_size=self.chunk_size):
                                if self.shutdown_event.is_set():
                                    break
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    file_progress.update(slot_task_id, advance=len(chunk))

                        if self.shutdown_event.is_set():
                            break

                        # Rename .part to final filename
                        if part_path.exists():
                            if file_path.exists():
                                file_path.unlink()
                            part_path.rename(file_path)

                        file_progress.update(
                            slot_task_id,
                            completed=total_size,
                            description=f"[cyan]Slot {slot_id+1}[/]: [green]{default_name[:22]} Done[/]"
                        )
                        success = True
                        break

                except Exception as e:
                    retries += 1
                    if part_path.exists():
                        existing_bytes = part_path.stat().st_size
                    wait_sec = min(2 ** retries, 10)
                    file_progress.update(
                        slot_task_id,
                        description=f"[cyan]Slot {slot_id+1}[/]: [red]{default_name[:16]} Retry ({retries}/{self.max_retries})[/]"
                    )
                    time.sleep(wait_sec)

            if success:
                with self.completed_counter['lock']:
                    self.completed_counter['count'] += 1
                    overall_progress.update(overall_task_id, completed=self.completed_counter['count'])
            else:
                with self.completed_counter['lock']:
                    self.completed_counter['failed'].append((item_num, default_name, url))

            self.work_queue.task_done()
            time.sleep(0.05)

        file_progress.update(slot_task_id, description=f"[cyan]Slot {slot_id+1}[/]: [dim]Idle[/]", completed=0, total=100)

    def start(self) -> Dict[str, Any]:
        """Starts the multi-threaded download process with live UI."""
        self.target_dir.mkdir(parents=True, exist_ok=True)
        total_items = len(self.urls)

        for idx, url in enumerate(self.urls):
            self.work_queue.put((idx, url, total_items))

        overall_prog, file_prog, overall_id, slot_ids, group = create_progress_bars(self.concurrency)
        overall_prog.update(overall_id, total=total_items, completed=0)

        threads = []
        for i in range(self.concurrency):
            t = threading.Thread(
                target=self._worker,
                args=(i, file_prog, slot_ids[i], overall_prog, overall_id),
                daemon=True
            )
            t.start()
            threads.append(t)

        start_time = time.time()

        try:
            with Live(group, console=console, refresh_per_second=REFRESH_RATE):
                while any(t.is_alive() for t in threads):
                    time.sleep(0.2)
        except KeyboardInterrupt:
            console.print("\n[bold yellow][!] Pausing downloads... Saving progress safely.[/]")
            self.shutdown_event.set()
            for t in threads:
                t.join(timeout=2.0)
            console.print("[bold green]Progress saved! You can resume anytime by re-running.[/]")
            return {
                'completed': self.completed_counter['count'],
                'failed': self.completed_counter['failed'],
                'elapsed': time.time() - start_time,
                'interrupted': True
            }

        elapsed = time.time() - start_time
        return {
            'completed': self.completed_counter['count'],
            'failed': self.completed_counter['failed'],
            'elapsed': elapsed,
            'interrupted': False
        }

