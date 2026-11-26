# PANGEA 1.2 — One Language for People, Machines, and Minds

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

**Python is bundled with Pangea (version 1.2). Nothing else needs to be
installed — not even Python itself.** Both 32-bit and 64-bit Windows are
supported; Pangea picks the right one for your PC.

## Get Pangea

**Windows, ready to run:** download the [Pangea 1.2 Windows package](https://drive.google.com/file/d/1hYWahvJA5Nf4VjxVVY0XFZLvYFCP9mjs/view) (21 MB, Python bundled in). Unzip it and double-click `Run-Pangea.bat` — no install needed.

**From source:** clone this repo and run it with Python 3 — no install, no dependencies beyond the standard library:

```
git clone https://github.com/megaartaiking-cmd/pangea.git
cd pangea
python pangea.py examples/conversation.pangaea
```

(The Windows runtimes in `python32/` and `python64/` are only in the
packaged zip, not in this repo — they are 41 MB of binaries. The language
itself is one Python file.)

## Admin access — no room for error

When you ask an agent to do a real task, give it admin access and switch
on strict mode. Only a human can grant admin — an AI can never grant it
to itself.

```pangea
link Ahmad as human
link Alya as ai

grant admin to Alya        # one agent
grant admin to all ai      # every AI agent at once

no room                    # strict mode: checks enforced, commands retried

speak as Alya
let answer = run "echo hello from the computer"
check answer is "hello from the computer"
```

A `check` states what must be true — if it is not, the program stops at
once and says exactly what failed. A failed command is retried up to 3
times. When the program finishes cleanly, it prints its own report:
`No-room report: 17 statements ran, 3 checks passed, 1 commands ran,
0 retries, 0 errors.` See `examples/admin.pangaea` and section 6 of
`PANGEA.md`.

## What's in this package

| File | What it is |
|------|-----------|
| `pangea.py` | The reference interpreter (Python 3, standard library only) |
| `PANGEA.md` | The full language specification |
| `examples/` | Five working programs, including the human–AI–computer conversation |
| `python32/`, `python64/` | Portable Python 3.12, bundled — no install needed |
| `Run-Pangea.bat` | Double-click to run Pangea right now, no install at all |
| `Install.bat` | Double-click to install Pangea properly on Windows |
| `windows/` | The installer, uninstaller, and the `pangea` launcher |

## Run it (no install)

1. Unzip this package anywhere (for example, your Downloads folder).
2. Double-click **`Run-Pangea.bat`**. Pangea opens straight away.

## Install it (optional, but nicer)

1. Unzip this package anywhere.
2. Double-click **`Install.bat`**.
3. It installs Pangea to `%LOCALAPPDATA%\Pangea`, adds it to your PATH,
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

Double-clicking any `.pangea` file runs it.

## Examples

- `hello.pangaea` — first steps: say, let, arithmetic
- `conversation.pangaea` — a human, an AI, and a computer talking in one room
- `admin.pangaea` — admin access and no room for error: a human grants an AI full power, every step is checked
- `fizzbuzz.pangaea` — loops and decisions
- `todo.pangaea` — lists, functions, and saving to a file
- `guess.pangaea` — an interactive guessing game (`ask` + `while`)

## If it still does not work

- Make sure you **unzipped the whole package first** — running files from
  inside the zip does not work.
- If Windows shows a blue "Windows protected your PC" screen, click
  **More info**, then **Run anyway**. Pangea is safe; it is just new.
- If a black window opens and closes at once, open a Command Prompt in the
  folder and run `Run-Pangea.bat` there, so you can read the message.

## Honest notes

- Pangea 1.2 is a **reference implementation**, not a replacement for
  Python, C, or JavaScript. It is the shared tongue between people, AIs,
  and computers — the language of the conversation about the work.
- The interpreter is one readable Python file, so anyone can check how it
  works. It runs on Windows, Mac, and Linux anywhere Python 3 is installed.
- The Windows installer is a PowerShell script, not a compiled `.exe` —
  this machine has no Windows compiler. It does the same job: install
  folder, PATH, shortcuts, and file association.
