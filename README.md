# mdoclite

A pure-Python formatter for mdoc(7) manual pages with the same command line
as `mandoc(1)`. It writes the page for a terminal (`-T ascii` or `-T utf8`)
and needs only the Python standard library (3.14).

```sh
python3 -m mdoclite -T ascii examples/ls.1
python3 -m mdoclite -T utf8 -O width=60 examples/ls.1
python3 -m unittest discover -s tests
```

## Options

| Option | What it does |
| --- | --- |
| `-T ascii` / `-T utf8` | output format (default `ascii`) |
| `-O width=N` | line width (default 78) |
| `-O indent=N` | indentation of section bodies (default 5) |
| `-I os=NAME` | operating system name for the footer when `.Os` has none |
| `-W LEVEL` | accepted; diagnostics are not implemented yet |

Without a file name the page is read from standard input. The exit status
is 0.

## How it works

* `mdoclite/roff.py` splits macro arguments (with double quotes) and turns
  escape sequences (`\fB`, `\fI`, `\fR`, `\fP`, `\(xx`, `\[name]`, `\*q`,
  `\e`, `\&`, `\-`, `\~` ...) into characters with their font.
* `mdoclite/mdoc.py` reads the page line by line and formats each macro as
  it comes: the prologue (`Dd`, `Dt`, `Os`), sections, paragraphs,
  displays, lists (`-tag`, `-bullet`, `-dash`, `-enum`, `-item`) and the
  common inline macros (`Fl`, `Ar`, `Nm`, `Xr`, `Op`, `Dq` ...).
* `mdoclite/term.py` fills words into lines, puts two spaces after a
  sentence that ends an input line, and writes bold as `c BS c` and
  underline as `_ BS c`, like mandoc does on a terminal.
* `mdoclite/cli.py` handles the options and the input file.

## Library

```python
import mdoclite
status = mdoclite.run(["-T", "ascii", "page.1"])
```

`mdoclite.run(argv, stdout=None, stderr=None, stdin=b"")` takes the
arguments without the program name, writes to the given binary streams and
returns the exit status.
