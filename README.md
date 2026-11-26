# PANGEA 1.0 — One Language for People, Machines, and Minds

Pangea is a small programming language that reads like English and is built
for a world where humans, AI models, and computers all talk to each other.
A Pangea program is a conversation: agents — a person, an AI, or a machine —
linked in one room, sending and receiving messages.

```pangea
link Ahmad as human
link Alya as ai
link Server as computer

speak as Ahmad
send "What is the temperature in Lahore?" to Alya

speak as Alya
let question = receive from Ahmad
send "Checking the weather station..." to Ahmad
```

## What's in this package

| File | What it is |
|------|-----------|
| `pangea.py` | The reference interpreter (Python 3, standard library only) |
| `PANGEA.md` | The full language specification |
| `examples/` | Five working programs, including the human–AI–computer conversation |
| `Install.bat` | Double-click to install on Windows |
| `windows/` | The installer, uninstaller, and the `pangea` launcher |

## Install on Windows

1. Unzip this package anywhere (for example, your Downloads folder).
2. Double-click **`Install.bat`**.
3. The installer checks for Python 3. If it is missing, it opens the Python
   download page — install Python 3 (tick **"Add python.exe to PATH"**),
   then run `Install.bat` again.
4. It installs Pangea to `%LOCALAPPDATA%\Pangea`, adds it to your PATH,
   creates Start Menu and Desktop shortcuts, and links `.pangea` files to
   the interpreter.

To remove it later, run `windows\Uninstall-Pangea.ps1` (right-click →
Run with PowerShell).

## Use it

In any Command Prompt or PowerShell window (open a new one after installing):

```
pangea examples\hello.pangaea        run a program
pangea examples\conversation.pangaea run the human–AI–computer demo
pangea                               open the interactive REPL
pangea --check myprogram.pangaea     check a program without running it
```

Double-clicking any `.pangaea` file runs it.

## Examples

- `hello.pangaea` — first steps: say, let, arithmetic
- `conversation.pangaea` — a human, an AI, and a computer talking in one room
- `fizzbuzz.pangaea` — loops and decisions
- `todo.pangaea` — lists, functions, and saving to a file
- `guess.pangaea` — an interactive guessing game (`ask` + `while`)

## Honest notes

- Pangea 1.0 is a **reference implementation**, not a replacement for
  Python, C, or JavaScript. It is the shared tongue between people, AIs,
  and computers — the language of the conversation about the work.
- The interpreter is one readable Python file, so anyone can check how it
  works. It runs on Windows, Mac, and Linux anywhere Python 3 is installed.
- The Windows installer is a PowerShell script, not a compiled `.exe` —
  this machine has no Windows compiler. It does the same job: install
  folder, PATH, shortcuts, and file association.
