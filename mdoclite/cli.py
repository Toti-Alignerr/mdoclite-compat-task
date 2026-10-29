"""Command line handling: options, input and exit status."""

from .mdoc import Formatter


class UsageError(Exception):
    pass


def parse_args(argv):
    """mandoc-style options; returns (options, file names)."""
    opts = {"output": "ascii", "width": 78, "indent": 5, "os": None, "warn": []}
    files = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--":
            files.extend(argv[i + 1:])
            break
        if not a.startswith("-") or a == "-":
            files.append(a)
            i += 1
            continue
        flag, val = a[:2], a[2:]
        if flag not in ("-T", "-W", "-O", "-I"):
            raise UsageError("unknown option %s" % a)
        if not val:
            i += 1
            if i >= len(argv):
                raise UsageError("option %s needs a value" % flag)
            val = argv[i]
        if flag == "-T":
            opts["output"] = val
        elif flag == "-W":
            opts["warn"] = val.split(",")
        elif flag == "-O":
            for o in val.split(","):
                k, _, v = o.partition("=")
                if k in ("width", "indent") and v.isdigit():
                    opts[k] = int(v)
        elif flag == "-I":
            if val.startswith("os="):
                opts["os"] = val[3:]
        i += 1
    return opts, files


def main(argv, stdin, stdout, stderr):
    try:
        opts, files = parse_args(argv)
    except UsageError as e:
        stderr.write("mandoc: %s\n" % e)
        return 5
    if files:
        try:
            with open(files[0], "rb") as f:
                data = f.read()
        except OSError as e:
            stderr.write("mandoc: %s: %s\n" % (files[0], e.strerror))
            return 5
    else:
        data = stdin
    text = data.decode("utf-8", "replace")
    stdout.write(Formatter(opts).run(text))
    return 0
