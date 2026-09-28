#!/usr/bin/env python3
"""
ESC key listener for the Django server.
Monitors stdin for ESC key and sends SIGTERM to parent process when pressed.
"""

import sys
import os
import signal
import tty
import termios

def main():
    if len(sys.argv) < 2:
        print("Usage: esc_listener.py <pid>", file=sys.stderr)
        sys.exit(1)
    
    target_pid = int(sys.argv[1])
    
    original_settings = None
    try:
        original_settings = termios.tcgetattr(sys.stdin.fileno())
        tty.setraw(sys.stdin.fileno())
        
        print("Press ESC to stop the server gracefully.", flush=True)
        
        while True:
            char = sys.stdin.read(1)
            if ord(char) == 27:
                print("\n\nESC pressed — stopping server...", flush=True)
                try:
                    os.kill(target_pid, signal.SIGTERM)
                except OSError:
                    pass
                break
    
    except KeyboardInterrupt:
        pass
    
    finally:
        if original_settings:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, original_settings)
            except (OSError, termios.error):
                pass
        print("", flush=True)

if __name__ == "__main__":
    main()
