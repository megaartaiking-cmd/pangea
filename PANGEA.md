# PANGEA — One Language for People, Machines, and Minds

**Version 1.2** · File extension: `.pangaea` · Reference implementation: `pangea.py` (Python 3, standard library only)

## 1. What Pangea is

Pangea is a small, plain-English programming language built for a world where
humans, AI models, and computers all talk to each other. A Pangea program reads
like a conversation, runs on any computer, and treats every participant —
a person, an AI, or a machine — as an **agent** that sends and receives messages.

Three ideas drive the whole design:

1. **Reads like English.** If a non-programmer cannot follow a Pangea program,
   the language is wrong, not the reader.
2. **One way to say each thing.** No hidden behaviour, no clever shortcuts.
   A statement does exactly what its words say.
3. **Everything is a message.** Code, data, and conversation are the same thing:
   agents linked in one room, speaking to each other.

Pangea does not try to replace C, Python, or JavaScript. It is an
**interchange language**: the simple, shared tongue you use when a human, an AI,
and a computer need to understand the same instructions. Think of it as the
language of the conversation *about* the work, with enough power to do real work.

## 2. Hello, world

```pangea
# The first Pangea program.
say "Hello, world!"
```

```pangea
let name = ask "What is your name?"
say "Hello, " + name + ". Welcome to Pangea."
```

## 3. Values

| Kind    | Example                    | Meaning                          |
|---------|----------------------------|----------------------------------|
| number  | `42`, `3.14`, `-7`         | Whole numbers and decimals       |
| text    | `"Hello"`                  | Words in double quotes           |
| yes/no  | `yes`, `no`                | True and false, in plain words   |
| list    | `[1, 2, 3]`, `["a", "b"]`  | An ordered group of values       |
| map     | `{"name": "Sheru"}`        | Named values, like a form        |
| nothing | `nothing`                  | No value yet                     |

Text joins with `+`. Numbers use `+ - * / %` and `^` (power).
Compare with `==`, `!=`, `<`, `<=`, `>`, `>=` — or the English forms
`is` and `is not`. Combine with `and`, `or`, `not`.

```pangea
let age = 5
let adult = age >= 18
say adult          # says: no

let score = 10 + 5 * 2
say score          # says: 20

let name = "Sheru"
say name is "Sheru"   # says: yes
```

## 4. Statements

### Variables — `let`

```pangea
let price = 100
let price = price + 50    # let also changes a value
```

### Talking to the human — `say` and `ask`

```pangea
say "The answer is 42."
let city = ask "Which city do you live in?"
```

### Decisions — `if`, `elif`, `else`, `end`

```pangea
let n = 7
if n > 10:
    say "big"
elif n > 5:
    say "medium"
else:
    say "small"
end
```

### Loops — `while` and `for`

```pangea
let count = 0
while count < 3:
    say count
    let count = count + 1
end

for fruit in ["apple", "mango", "banana"]:
    say fruit
end

for i in range(5):
    say i
end
```

### Functions — `to`, `return`

```pangea
to double(x):
    return x * 2
end

say double(21)    # says: 42

to greet(name):
    say "Hello, " + name
end

greet("Ahmad")
```

### Files — `save` and `read`

```pangea
save "Sheru is a lion." to "note.txt"
let words = read "note.txt"
say words
```

### Stopping — `stop`

```pangea
say "Done."
stop
say "This never runs."
```

## 5. The cross-linked core: agents and messages

This is what makes Pangea different from every other small language.
Humans, AIs, and computers are all **agents**, linked in one shared room.

```pangea
link Ahmad as human
link Alya as ai
link Server as computer
```

`link` introduces an agent and says what kind it is: `human`, `ai`, or
`computer`. Anyone linked can send and receive messages.

```pangea
send "Hello!" to Alya
```

`speak as` changes who is talking — like a stage direction in a play.
`receive from` picks up the oldest message sent to the current speaker.

```pangea
speak as Ahmad
send "What is the temperature in Lahore?" to Alya

speak as Alya
let question = receive from Ahmad
send "Checking the weather station..." to Ahmad
send "temperature in Lahore" to Server

speak as Server
let request = receive from Alya
send "Lahore is 28 degrees and sunny." to Alya

speak as Alya
let answer = receive from Server
send "Lahore is 28 degrees and sunny." to Ahmad

speak as Ahmad
let reply = receive from Alya
say reply
```

Output:

```
Lahore is 28 degrees and sunny.
```

`broadcast` sends one message to every linked agent except the speaker.
`inbox()` returns the list of messages waiting for the current speaker.
`receive from X` returns `nothing` when there is no message from X.

That is the whole idea: a human, an AI, and a computer, speaking one
language, in one room, in words anyone can read.

## 6. Admin access and no room for error

When a user asks an agent to do a real task, the agent needs two things:
the **power** to use every resource, and a way to make **almost no errors**.
Pangea gives both, and only a human can switch them on.

### Admin access — `grant admin`, `revoke admin`

Admin agents can use the computer's full resources: run system commands
(`run`) and manage files (`delete`). Nobody is born an admin — a human
grants it, and a human can take it away.

```pangea
link Ahmad as human
link Alya as ai

grant admin to Alya        # one agent
grant admin to all ai      # every linked AI agent
grant admin to all         # every linked agent

revoke admin from Alya
say admins()               # says: ["Alya"]
```

Only a human (or the human running the program) can grant or revoke admin.
An AI cannot grant admin to itself — if it tries, Pangea refuses in plain
words. An agent that is not admin and tries to use a powerful command gets
a clear refusal telling it what to ask the human for.

```pangea
speak as Alya
let files = list "."                     # listing files is open to everyone
let answer = run "echo hello"            # needs admin — refuses without it
delete "old.txt"                         # needs admin too
```

### No room for error — `no room`, `check`, `room`

`no room` switches on strict mode for the rest of the program:

- **`check` statements are enforced.** A `check` states what must be true.
  If it is not true, the program stops at once and says exactly what
  failed — it never carries on with a wrong result.
- **Failed commands are retried.** In strict mode a failed `run` command
  is tried up to 3 times before it is allowed to fail.
- **A report is printed at the end.** When the program finishes cleanly,
  it reports exactly what happened: how many statements ran, how many
  checks passed, how many commands ran, how many retries were needed —
  and 0 errors.

```pangea
no room

check len(files) > 0
check answer is "hello from the computer"
```

`room` switches strict mode back off. No system can promise literally zero
errors — but a program that checks every step, retries what fails, and
reports its own work is as close as a language can get.

## 7. Built-in functions

| Function        | What it does                                  |
|-----------------|-----------------------------------------------|
| `len(x)`        | Length of text, list, or map                  |
| `type(x)`       | The kind of a value: `"number"`, `"text"`…    |
| `str(x)`        | Turn a value into text                        |
| `num(x)`        | Turn text into a number                       |
| `upper(text)`   | Text in capital letters                       |
| `lower(text)`   | Text in small letters                         |
| `abs(x)`        | A number without its minus sign               |
| `round(x)`      | A number rounded to the nearest whole         |
| `range(n)`      | Numbers from 0 up to (not including) n        |
| `keys(map)`     | The names in a map, as a list                 |
| `push(list, x)` | Add a value to the end of a list              |
| `pop(list)`     | Take the last value off a list                |
| `inbox()`       | Messages waiting for the current speaker      |
| `now()`         | The current date and time, as text            |
| `read(file)`    | Read a whole text file                        |
| `list(folder)`  | The files in a folder, as a sorted list       |
| `admins()`      | The agents that have admin access, as a list  |

## 8. Grammar (informal)

```
program     := statement*
statement   := let | say | ask | if | while | for | to | return
             | link | speak | send | broadcast | save | stop | expression
let         := "let" name "=" expression
say         := "say" expression
if          := "if" expression ":" statement* ("elif" expression ":")* ("else" ":")? "end"
while       := "while" expression ":" statement* "end"
for         := "for" name "in" expression ":" statement* "end"
to          := "to" name "(" params? ")" ":" statement* "end"
link        := "link" name "as" ("human" | "ai" | "computer")
speak       := "speak" "as" name
send        := "send" expression "to" name
broadcast   := "broadcast" expression
save        := "save" expression "to" expression
expression  := or-expression
```

Blocks are closed with `end`. Indentation is for humans; the interpreter
only needs `end`. A `#` starts a comment that runs to the end of the line.

## 9. Errors, in plain words

Pangea never crashes with a stack trace. Every error says what went wrong,
where, and in plain language:

```
Line 4: I don't know the name 'prcie'. Did you mean 'price'?
Line 9: 'send' needs a linked agent. 'Bob' is not linked yet.
Line 2: You cannot divide by zero.
```

## 10. Keywords (all 36)

```
let say ask if elif else end while for in to return
link as speak send receive broadcast from save read
grant revoke admin check no room delete run list all
and or not is yes no nothing stop
```

## 11. What Pangea is not (honest notes)

- **Not a replacement for C, Python, or JavaScript.** Those languages exist
  because different jobs need different tools. Pangea is the shared tongue
  between them, not a substitute for them.
- **Not a new AI model.** Pangea is a language, not a mind. It lets minds
  talk to each other clearly; it does not think for them.
- **Version 1.2 is a reference implementation.** The interpreter is a
  single Python file, deliberately small and readable, so anyone can check
  how it works. Speed and large programs come later.

## 12. Installing on Windows

Python is bundled with Pangea (version 1.2), so nothing else needs to be
installed. Two ways to run it:

**Install it:** unzip the package and double-click `Install.bat`. It copies
Pangea to `%LOCALAPPDATA%\Pangea`, adds it to your PATH, creates Start Menu
and Desktop shortcuts, and links `.pangea` files to the interpreter, so
double-clicking a program runs it.

**Or just run it:** unzip the package and double-click `Run-Pangea.bat`.
No install at all — Pangea opens straight away from the folder.

Then, in any Command Prompt or PowerShell window:

```
pangea hello.pangaea     # run a program
pangea                   # open the interactive REPL
pangea --check file.pangaea   # check a program without running it
```

On Mac and Linux, run it with the Python 3 already on the machine:
`python3 pangea.py hello.pangaea`.
