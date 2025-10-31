# PyNixShell

A cross-platform, Python-powered terminal/shell that blends Unix-style ergonomics with handy utilities, a pluggable command system, and a few fun extras (hello, ASCII donut 🍩).

> **Highlights**
> - Works on Windows, macOS, and Linux
> - Built-in commands for files, processes, networking, archives, and more
> - Persistent aliases and hot-reloadable external commands
> - Two editors: a rich **nano** clone and a LAN-collab **pynano**
> - Simple LAN chat + file share (`ssh host/join`)
> - ZIP/TAR tooling using native OS where possible

---

## Table of Contents
- [Quick Start](#quick-start)
- [Requirements](#requirements)
- [Features](#features)
- [Core Commands](#core-commands)
- [Editors](#editors)
- [External Commands](#external-commands)
- [Aliases](#aliases)
- [Archives](#archives)
- [Networking](#networking)
- [System Actions](#system-actions)
- [Directory Tools](#directory-tools)
- [Automation & History](#automation--history)
- [Config Files & Layout](#config-files--layout)
- [Security Notes](#security-notes)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Quick Start

```bash
# 1) Clone your repo and cd into it, then:
python pynixshell.py
You’ll see a prompt like:

mathematica
Copy code
PynixShell C:\Users\you\projects>
Type help to see documentation sourced from commands.json, or commands to list live/registered commands.

Requirements
Python: 3.9+ recommended

Standard library: tkinter, curses (Unix), zipfile, tarfile, etc.

Pip packages:

psutil (process + system info)

pyperclip (clipboard in editors)

Windows only: windows-curses (enables curses UI)

Windows: PowerShell available (used by zip)

Install deps:

bash
Copy code
# All platforms
pip install psutil pyperclip

# Windows only (for curses-based UIs)
pip install windows-curses
Features
Unix-like commands (ls, cd, rm, mkdir, du, df, cat, head, tail, tree, etc.)

Process tools (ps, kill)

Search & sync (find, grep, rsync)

Archiving (zip, tar, unzip, dtar)

Launchers (programs, launch)

Editors:

nano — multi-file, tabs, line numbers, save/close/top/bottom, paste from clipboard

pynano — optional LAN collaboration

LAN utility: ssh host/join — simple chat + file sharing

System info: neofetch w/ custom PyNixShell ASCII

System actions: shutdown, restart, sleep (with GUI confirm for power actions)

Networking: ip (local/public), opendrop (Windows runner)

Extensibility: hot-load external commands from /commands (and /commands/added)

Aliases: persistent aliases stored beside the main script

Fun: donut — smooth ASCII torus animation

Core Commands
Run help <name> for full details (pulled from commands.json).
Run commands to see what is currently registered in memory.

Command	What it does
ls, view	List files; view -z <zip>/-t <tar> peeks inside archives
cd, goto <path>, goback, back	Navigate; goback toggles between last two dirs
touch, mkdir [-p], rm	Create and remove files/folders
move <src> <dst>	Move/rename file or folder
cat, head [-n N], tail [-n N]	Read files
df [-h], du [-s]/-f <file>	Disk info and usage
tree [-L N] [path]	Draws a tree view, depth-limited
programs, `launch <n	name>`
echo ...	Print text
find <name>	System-wide filename search (multi-threaded, skips big system dirs)
grep [-i] <pattern> <file>	Search inside files
ps [-p] [-s <name>], kill <pid>	Process list and terminate
help [name], commands	Docs and live registry
date [-i]	Show current date/time
`option <file	dir>`
watch -n <sec> [-t <count>] <command>	Re-run a command on an interval
neofetch	Pretty system summary with logo
donut	ASCII donut (press Esc to stop)

Editors
nano
A terminal editor with:

Tabs bar with open files

Keybinds:

Ctrl+S save

Ctrl+Q quit

Ctrl+W close tab

Ctrl+T new file

Ctrl+O open

Tab next tab

Ctrl+G top, Ctrl+J bottom

Ctrl+V paste (via clipboard)

Line numbers and status messages

bash
Copy code
nano                # start with untitled buffer
nano README.md      # open a file
pynano [--collab] <file>
Adds optional LAN collaboration channel:

Host: starts a small TCP server for live line updates

Join: connect to a host’s IP

Propagates edits as “UPDATE” or full “SYNC”

External Commands
Put Python files in /commands or /commands/added. They’ll be loaded at startup.

Hot-reload tools:

csync — rescan, unload stale, reload everything

lsc — list active external commands with source paths
lsc -c — scan files for @register_command("...")

rfpt — re-executes the shell script in-place (full refresh)

Helper to add one quickly:

bash
Copy code
add my_command.py
Template inside your external file:

python
Copy code
def register_command(name):
    from __main__ import registered_commands
    def wrapper(func):
        registered_commands[name] = func
        return func
    return wrapper

@register_command("hello")
def hello(args):
    print("Hello from plugin!")
Aliases
Create persistent shortcuts that behave like commands. Saved to pynix_aliases.json beside the main script.

bash
Copy code
alias ll='ls'
alias proj='goto ~/projects'
unalias ll
unalias -a
Archives
Create ZIP (native where possible):

bash
Copy code
zip <source_folder> <dest.zip>
Create TAR:

bash
Copy code
tar <source_folder> <dest.tar>
Extract:

bash
Copy code
unzip <file.zip>
dtar <file.tar|file.tar.gz>
Networking
IP info

bash
Copy code
ip          # hostname, local, public IP
ip -s       # list active IPv4s per interface
LAN chat & share

bash
Copy code
ssh host    # start a host; auto-connect self
ssh join    # discover hosts and join (or enter IP)
Client commands inside the session:

php-template
Copy code
help | listfiles | push <file> | pull <file> | rmv <name> | exit
File “rsync”

bash
Copy code
rsync path/to/source.ext            # find same-named files across system and offer to overwrite
rsync path/to/source.ext -t <dest>  # sync to a specific file or folder (renames allowed)
OpenDrop shim

bash
Copy code
opendrop   # runs opendropUnix.py on Windows (if present)
System Actions
shutdown, restart, sleep — each confirms (or uses platform-appropriate call).

sudo <windows_command> — Windows only: elevation via ShellExecute → PowerShell.

⚠️ Some actions may require admin privileges. On macOS/Linux, power actions use standard system tools (osascript, systemctl, pmset).

Directory Tools
tree [-L N] [path] — depth-limited view

du [-s] [path] or du -f <file> — human-readable sizing

df [-h] — mounted filesystem usage

view — pretty folder listing; -z/-t lists inside archives without extracting

Automation & History
queue <command> — append to autoexec.json (runs automatically on next startup)

history — show; history -n 20 — last N; history -c — clear

mod -t <seconds> <command> — delay execution

watch -n <sec> [-t N] <command> — rerun on a timer

Config Files & Layout
These are created next to the main script unless otherwise noted:

bash
Copy code
/pynixshell.py
/commands.json            # help content rendered by `help` and categories
/pynix_aliases.json       # persistent aliases
/autoexec.json            # queued commands (executed at startup)
/commands/                # external commands (auto-loaded)
   /added/                # optional, also auto-loaded
/shared/                  # used by LAN tools and collab editors
Security Notes
rsync performs system-wide scans for same-named files; it prompts before overwriting. Still, be careful: you can overwrite app data if names collide.

sudo (Windows only) triggers elevated PowerShell. Only run commands you trust.

ssh host/join is LAN-scoped and unauthenticated. Use on trusted networks only.

Troubleshooting
Windows “curses” errors: pip install windows-curses

tkinter errors: install a Python build that includes Tk (most official installers do).

ZIP/TAR failures on Windows: ensure PowerShell is available; the tool falls back to Python if native tools aren’t found on Unix.

Editor paste doesn’t work: install pyperclip.

Public IP shows “unavailable”: outbound HTTP may be blocked.