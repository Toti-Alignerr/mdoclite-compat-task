"""mdoclite: format mdoc(7) manual pages for the terminal, like mandoc(1)."""

import io
import sys

from . import cli

__all__ = ["run"]


def run(argv, stdout=None, stderr=None, stdin=b""):
    """Run mandoc with the arguments argv (without the program name).

    stdout and stderr are binary streams (default: the process's own);
    stdin holds the bytes read when no input file is named.  Returns the
    exit status."""
    out, err = io.StringIO(), io.StringIO()
    status = cli.main(list(argv), stdin, out, err)
    stdout = stdout if stdout is not None else sys.stdout.buffer
    stderr = stderr if stderr is not None else sys.stderr.buffer
    stdout.write(out.getvalue().encode("utf-8"))
    stderr.write(err.getvalue().encode("utf-8"))
    return status
