#!/usr/bin/env python3
# /// script
# dependencies = ["websockets", "httpx", "pynput"]
# ///
"""
Test client for Twistt WebSocket API.
Press 1 or 2 to toggle recording with a pipeline.
Press same key again to stop.
"""

import asyncio
import json
import sys
import termios
import threading
import tty

import httpx
import websockets
from pynput import keyboard

BASE_URL = "http://localhost:7777"
WS_URL = "ws://localhost:7777/api/ws"

# Map keys to pipeline names
PIPELINES = {
    "1": "brainstorm",
    "2": "translate",
}

# Track state
current_state = "unknown"
current_pipeline: str | None = None
is_recording = False


def clear_line():
    """Clear current line and move cursor to beginning."""
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def print_status():
    """Print current status on a single line."""
    # Color code the state
    if current_state == "recording":
        color = "\033[91m"  # Red
        symbol = "●"
    elif current_state == "processing":
        color = "\033[93m"  # Yellow
        symbol = "◐"
    else:
        color = "\033[92m"  # Green
        symbol = "○"

    pipeline_display = current_pipeline or "-"
    clear_line()
    sys.stdout.write(f"{color}{symbol}\033[0m [{current_state:10}] Pipeline: {pipeline_display}")
    sys.stdout.flush()


def log_message(msg: str):
    """Print a log message above the status line."""
    clear_line()
    print(msg)
    print_status()


def on_press(key):
    """Handle key press - toggle recording."""
    global is_recording
    try:
        # Stop key
        if key.char == "0":
            if is_recording:
                try:
                    response = httpx.post(f"{BASE_URL}/api/stop")
                    if response.status_code != 200:
                        log_message(f"[API] Stop error: {response.text}")
                except Exception as e:
                    log_message(f"[API] Stop error: {e}")
                print_status()
        # Pipeline keys
        elif key.char in PIPELINES:
            pipeline_name = PIPELINES[key.char]
            if is_recording:
                # Stop then start with new pipeline
                try:
                    httpx.post(f"{BASE_URL}/api/stop")
                    response = httpx.post(f"{BASE_URL}/api/start", json={"pipeline": pipeline_name})
                    if response.status_code == 404:
                        log_message(f"[API] Pipeline '{pipeline_name}' not found")
                    elif response.status_code != 200:
                        log_message(f"[API] Start error: {response.text}")
                except Exception as e:
                    log_message(f"[API] Error: {e}")
            else:
                # Start recording with pipeline
                try:
                    response = httpx.post(f"{BASE_URL}/api/start", json={"pipeline": pipeline_name})
                    if response.status_code == 404:
                        log_message(f"[API] Pipeline '{pipeline_name}' not found")
                    elif response.status_code != 200:
                        log_message(f"[API] Start error: {response.text}")
                except Exception as e:
                    log_message(f"[API] Start error: {e}")
            print_status()
    except AttributeError:
        pass


def on_release(key):
    """Handle key release."""
    # Stop on Escape
    if key == keyboard.Key.esc:
        return False


async def listen_websocket():
    """Listen to WebSocket messages."""
    global current_state, current_pipeline, is_recording
    while True:
        try:
            async with websockets.connect(WS_URL) as ws:
                log_message(f"[WS] Connected to {WS_URL}")
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    new_state = data.get("state", "unknown")
                    new_pipeline = data.get("pipeline")
                    if new_state != current_state or new_pipeline != current_pipeline:
                        current_state = new_state
                        current_pipeline = new_pipeline
                        is_recording = new_state == "recording"
                        print_status()
        except websockets.exceptions.ConnectionClosed:
            log_message("[WS] Connection closed, reconnecting...")
            await asyncio.sleep(1)
        except Exception as e:
            log_message(f"[WS] Error: {e}, reconnecting...")
            await asyncio.sleep(1)


def run_keyboard_listener():
    """Run keyboard listener in a thread."""
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


async def main():
    # Fetch available pipelines
    try:
        response = httpx.get(f"{BASE_URL}/api/pipelines")
        available = response.json() if response.status_code == 200 else []
    except Exception:
        available = []

    print("=" * 50)
    print("Twistt WebSocket Test Client")
    print("=" * 50)
    print("Key mappings:")
    for key, name in PIPELINES.items():
        status = "available" if name in available else "not found"
        print(f"  {key} -> {name} ({status})")
    print(f"  0 -> stop")
    print()
    print("Press 1/2 to start (switches pipeline if recording)")
    print("Press 0 to stop, ESC to quit")
    print("=" * 50)
    print()

    # Start keyboard listener in a thread
    kb_thread = threading.Thread(target=run_keyboard_listener, daemon=True)
    kb_thread.start()

    # Show initial status
    print_status()

    # Run WebSocket listener
    await listen_websocket()


if __name__ == "__main__":
    # Save terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        # Disable terminal echo
        tty.setcbreak(fd)
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        # Restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("\nBye!")
