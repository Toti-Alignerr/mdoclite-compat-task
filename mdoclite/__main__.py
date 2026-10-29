import sys

from . import cli, run


def main():
    try:
        files = cli.parse_args(sys.argv[1:])[1]
    except cli.UsageError:
        files = []
    data = b"" if files else sys.stdin.buffer.read()
    sys.exit(run(sys.argv[1:], sys.stdout.buffer, sys.stderr.buffer, data))


if __name__ == "__main__":
    main()
