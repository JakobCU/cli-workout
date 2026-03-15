"""WebSocket terminal: spawn a real CLI session for web demo."""

import asyncio
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

# Max concurrent demo sessions
MAX_SESSIONS = 5
_active_sessions = 0

# Demo state pre-seeded data
_DEMO_STATE = {
    "completed_sessions": 47,
    "current_workout_index": 0,
    "xp": 1850,
    "level": 5,
    "level_title": "Warrior",
    "current_streak": 4,
    "longest_streak": 12,
    "exercise_progress": {"Push-Ups": 10, "Squats": 15, "Plank": 5},
    "achievements": [
        {"id": "first_session", "name": "First Step", "desc": "Complete your first session"},
        {"id": "streak_3", "name": "Streak 3", "desc": "3-day streak"},
        {"id": "streak_7", "name": "Week Warrior", "desc": "7-day streak"},
        {"id": "sessions_10", "name": "Dedicated", "desc": "Complete 10 sessions"},
        {"id": "sessions_25", "name": "Committed", "desc": "Complete 25 sessions"},
    ],
    "history": [
        {"date": "2026-03-15 08:30:00", "workout": "Workout A", "duration_min": 18, "notes": "felt strong"},
        {"date": "2026-03-14 07:45:00", "workout": "Workout B", "duration_min": 16},
        {"date": "2026-03-13 08:00:00", "workout": "Workout C", "duration_min": 20, "notes": "pushed hard"},
        {"date": "2026-03-12 07:30:00", "workout": "Workout A", "duration_min": 17},
        {"date": "2026-03-10 08:15:00", "workout": "Workout B", "duration_min": 15},
    ],
    "stars": [],
}

_DEMO_CONFIG = {
    "profile": {"name": "Demo User", "target_sessions_per_week": 3},
    "settings": {
        "countdown_seconds": 3,
        "rest_between_exercises": 15,
        "rest_between_rounds": 30,
        "progression_every_completed_sessions": 3,
        "progression_seconds_step": 5,
        "enable_clear_screen": True,
        "webhook_url": None,
        "anthropic_api_key": None,
        "openai_api_key": None,
        "ai_provider": "anthropic",
    },
    "workouts": [
        {
            "name": "Workout A",
            "rounds": 3,
            "exercises": [
                {"name": "Push-Ups", "mode": "time", "value": 30},
                {"name": "Squats", "mode": "time", "value": 40},
                {"name": "Plank", "mode": "time", "value": 25},
                {"name": "Reverse Lunges", "mode": "time", "value": 35},
                {"name": "Superman", "mode": "time", "value": 25},
            ],
        },
        {
            "name": "Workout B",
            "rounds": 3,
            "exercises": [
                {"name": "Push-Ups", "mode": "time", "value": 30},
                {"name": "Squats", "mode": "time", "value": 45},
                {"name": "Side Plank Left", "mode": "time", "value": 20},
                {"name": "Side Plank Right", "mode": "time", "value": 20},
                {"name": "Glute Bridge", "mode": "time", "value": 35},
            ],
        },
    ],
}

_DEMO_USER = {
    "id": "demo-web-user",
    "username": "demo",
    "name": "Demo User",
    "bio": "Trying out GitFit!",
    "joined": "2026-01-15",
    "auth_token": None,
    "cli_token": None,
    "linked_username": None,
    "public_profile": True,
    "share_activity": True,
}


def _setup_demo_dir() -> str:
    """Create a temp directory with demo data for a session."""
    demo_dir = tempfile.mkdtemp(prefix="gitfit_demo_")
    state_path = Path(demo_dir) / "state.json"
    config_path = Path(demo_dir) / "config.json"
    user_path = Path(demo_dir) / "user.json"

    state_path.write_text(json.dumps(_DEMO_STATE, indent=2), encoding="utf-8")
    config_path.write_text(json.dumps(_DEMO_CONFIG, indent=2), encoding="utf-8")
    user_path.write_text(json.dumps(_DEMO_USER, indent=2), encoding="utf-8")

    return demo_dir


def _can_use_pty() -> bool:
    """Check if PTY is available (Linux/Mac only)."""
    try:
        import pty  # noqa: F401
        import fcntl  # noqa: F401
        import termios  # noqa: F401
        return True
    except ImportError:
        return False


async def _run_with_pty(ws: WebSocket, python: str, project_root: str, env: dict):
    """Run CLI with full PTY support (Linux/Mac)."""
    import pty as pty_module
    import fcntl
    import struct
    import termios
    import tty

    master_fd, slave_fd = pty_module.openpty()

    # Set terminal size to match xterm.js (80x30)
    winsize = struct.pack("HHHH", 30, 80, 0, 0)
    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)

    # Disable PTY echo -- client handles display
    attrs = termios.tcgetattr(slave_fd)
    attrs[3] = attrs[3] & ~termios.ECHO
    termios.tcsetattr(slave_fd, termios.TCSANOW, attrs)

    process = await asyncio.create_subprocess_exec(
        python, "app.py",
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        cwd=project_root, env=env,
    )
    os.close(slave_fd)

    loop = asyncio.get_event_loop()

    async def read_pty():
        while True:
            try:
                data = await loop.run_in_executor(None, os.read, master_fd, 4096)
                if not data:
                    break
                await ws.send_text(data.decode("utf-8", errors="replace"))
            except (OSError, WebSocketDisconnect):
                break

    async def write_pty():
        try:
            while True:
                data = await asyncio.wait_for(ws.receive_text(), timeout=300)
                os.write(master_fd, data.encode("utf-8"))
        except (WebSocketDisconnect, asyncio.TimeoutError, OSError):
            pass

    try:
        await asyncio.gather(read_pty(), write_pty(), return_exceptions=True)
    finally:
        try:
            os.close(master_fd)
        except OSError:
            pass
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except asyncio.TimeoutError:
                process.kill()


async def _run_with_pipes(ws: WebSocket, python: str, project_root: str, env: dict):
    """Run CLI with subprocess pipes (Windows-compatible, uses threads)."""
    import subprocess
    import threading
    import queue

    send_queue: queue.Queue = queue.Queue()
    done = threading.Event()

    process = subprocess.Popen(
        [python, "-u", "app.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=project_root,
        env=env,
        bufsize=0,
    )

    def _reader_thread():
        """Read stdout one byte at a time, push chunks to queue."""
        try:
            while not done.is_set():
                byte = process.stdout.read(1)
                if not byte:
                    break
                send_queue.put(byte)
        except (OSError, ValueError):
            pass
        finally:
            send_queue.put(None)  # sentinel

    reader = threading.Thread(target=_reader_thread, daemon=True)
    reader.start()

    async def _send_loop():
        """Drain queue and send batched data to WebSocket."""
        loop = asyncio.get_event_loop()
        try:
            while not done.is_set():
                # Wait for first byte
                first = await loop.run_in_executor(None, lambda: send_queue.get(timeout=1))
                if first is None:
                    break
                buf = first
                # Drain everything else currently in the queue
                while not send_queue.empty():
                    item = send_queue.get_nowait()
                    if item is None:
                        break
                    buf += item
                await ws.send_text(buf.decode("utf-8", errors="replace"))
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception:
            pass

    async def _recv_loop():
        """Read from WebSocket, write to process stdin."""
        try:
            while not done.is_set():
                data = await asyncio.wait_for(ws.receive_text(), timeout=300)
                if process.poll() is not None:
                    break
                process.stdin.write(data.encode("utf-8"))
                process.stdin.flush()
        except (WebSocketDisconnect, asyncio.TimeoutError, OSError, BrokenPipeError):
            pass

    try:
        await asyncio.gather(_send_loop(), _recv_loop(), return_exceptions=True)
    finally:
        done.set()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        reader.join(timeout=2)


async def websocket_terminal(ws: WebSocket):
    """Handle a WebSocket terminal session."""
    global _active_sessions

    if _active_sessions >= MAX_SESSIONS:
        await ws.close(code=1013, reason="Too many active sessions")
        return

    await ws.accept()
    _active_sessions += 1

    demo_dir = _setup_demo_dir()

    try:
        python = sys.executable
        project_root = str(Path(__file__).resolve().parent.parent)

        env = os.environ.copy()
        env["GITFIT_HOME"] = demo_dir
        env["TERM"] = "xterm-256color"
        env["COLUMNS"] = "80"
        env["LINES"] = "30"
        env["FORCE_COLOR"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        # No AI keys in demo
        env.pop("ANTHROPIC_API_KEY", None)
        env.pop("OPENAI_API_KEY", None)

        if _can_use_pty():
            await _run_with_pty(ws, python, project_root, env)
        else:
            await _run_with_pipes(ws, python, project_root, env)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[terminal] Session error: {tb}")
        try:
            await ws.send_text(f"\r\n\x1b[31mSession error: {type(e).__name__}: {e}\x1b[0m\r\n")
            await ws.send_text(f"\x1b[90m{tb}\x1b[0m\r\n")
        except Exception:
            pass
    finally:
        _active_sessions -= 1
        try:
            shutil.rmtree(demo_dir, ignore_errors=True)
        except Exception:
            pass
