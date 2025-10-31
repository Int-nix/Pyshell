#!/usr/bin/env python3
import os
import sys
import threading
import itertools
import time
from pathlib import Path

# ==============================
# Spinner with Percentage
# ==============================
class Spinner:
    def __init__(self, message="Working"):
        self.message = message
        self.running = False
        self.thread = None
        self.progress = 0
        self.total = 1
        self.lock = threading.Lock()

    def start(self, message=None):
        if message:
            self.message = message
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def _spin(self):
        for c in itertools.cycle("|/-\\"):
            if not self.running:
                break
            with self.lock:
                percent = (self.progress / self.total) * 100 if self.total > 0 else 0
            sys.stdout.write(f"\r{self.message}... {c}  [{percent:6.2f}%]")
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write("\r" + " " * 60 + "\r")

    def update(self, progress, total=None):
        with self.lock:
            self.progress = progress
            if total is not None:
                self.total = total

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()


# ==============================
# Directory Counting (Optimized)
# ==============================
def count_dirs(start_dir, spinner=None):
    """Count directories much faster using os.scandir instead of os.walk."""
    spinner.start("Counting directories")

    count = 0
    stack = [start_dir]
    start_time = time.time()

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                subdirs = [e.path for e in entries if e.is_dir(follow_symlinks=False) and not e.name.startswith('.')
                           and e.name.lower() != 'node_modules']
                count += len(subdirs)
                stack.extend(subdirs)
        except (PermissionError, FileNotFoundError):
            continue

        # Update spinner roughly every 100 directories for efficiency
        if count % 100 == 0:
            spinner.update(count, total=count + 500)

    spinner.stop()
    duration = time.time() - start_time
    print(f"📁 Counted {count} directories in {duration:.2f}s")
    return count or 1


# ==============================
# Git Repo Scanner
# ==============================
def find_git_repos(start_dir, spinner=None):
    """Find all folders containing a .git folder."""
    repos = []
    start = Path(start_dir).expanduser().resolve()

    # Fast directory count
    count_spinner = Spinner()
    total_dirs = count_dirs(str(start), count_spinner)

    # Scan for repos
    spinner.start("Scanning for Git repositories")
    current = 0

    for root, dirs, files in os.walk(start, topdown=True):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() != 'node_modules']
        git_dir = Path(root) / ".git"
        if git_dir.is_dir():
            repos.append(str(Path(root).resolve()))
            dirs[:] = []  # skip deeper
        current += 1
        if current % 100 == 0:  # update occasionally for speed
            spinner.update(current, total_dirs)

    spinner.stop()
    return repos


# ==============================
# Main Program
# ==============================
def main():
    home = Path.home()
    print(f"🔍 Searching for Git repositories in {home}...\n")

    spinner = Spinner()
    found = find_git_repos(home, spinner)

    print()  # Newline after spinner

    if found:
        print(f"✅ Found {len(found)} repositories:\n")
        for repo in found:
            print("•", repo)
    else:
        print("❌ No Git repositories found in your home directory.")


if __name__ == "__main__":
    main()