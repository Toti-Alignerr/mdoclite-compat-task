import io
import os
import unittest

import mdoclite

HERE = os.path.dirname(os.path.abspath(__file__))
LS = os.path.join(HERE, "..", "examples", "ls.1")
HEAD = ".Dd May 7, 2021\n.Dt TEST 1\n.Os\n.Sh NAME\n.Nm test\n.Nd a test page\n"


def run(argv, stdin=b""):
    out, err = io.BytesIO(), io.BytesIO()
    status = mdoclite.run(argv, out, err, stdin)
    return status, out.getvalue().decode(), err.getvalue().decode()


def plain(text):
    """Drop the overstriking used for bold and underline."""
    out = []
    for ch in text:
        if ch == "\b":
            out.pop()
            continue
        out.append(ch)
    return "".join(out).replace("_", "")


class Frame(unittest.TestCase):
    def test_header_and_footer(self):
        status, out, err = run(["-T", "ascii"], HEAD.encode())
        lines = out.split("\n")
        self.assertEqual(status, 0)
        self.assertEqual(err, "")
        self.assertEqual(lines[0], "TEST(1)" + " " * 21 + "General Commands Manual" + " " * 20 + "TEST(1)")
        self.assertEqual(lines[-2], "macOS 26.6" + " " * 24 + "May 7, 2021" + " " * 23 + "macOS 26.6")

    def test_os_argument(self):
        out = run(["-T", "ascii"], HEAD.replace(".Os", ".Os FreeBSD 14.0").encode())[1]
        self.assertTrue(out.split("\n")[-2].startswith("FreeBSD 14.0 "))

    def test_name_section(self):
        out = run(["-T", "ascii"], HEAD.encode())[1]
        self.assertIn("\nN\bNA\bAM\bME\bE\n     t\bte\bes\bst\bt - a test page\n", out)


class Text(unittest.TestCase):
    def test_fill_and_sentence_space(self):
        doc = HEAD + ".Sh DESCRIPTION\nOne sentence.\nAnother one\nhere.\n"
        out = plain(run(["-T", "ascii"], doc.encode())[1])
        self.assertIn("\n     One sentence.  Another one here.\n", out)

    def test_wrap_at_width(self):
        doc = HEAD + ".Sh DESCRIPTION\n" + "word " * 30 + "\n"
        out = plain(run(["-T", "ascii", "-O", "width=40"], doc.encode())[1])
        body = [l for l in out.split("\n") if l.startswith("     word")]
        self.assertTrue(all(len(l) <= 40 for l in body))
        self.assertEqual(sum(l.count("word") for l in body), 30)

    def test_fonts(self):
        doc = HEAD + ".Sh DESCRIPTION\n\\fBb\\fR \\fIi\\fP\n"
        out = run(["-T", "ascii"], doc.encode())[1]
        self.assertIn("     b\bb _\bi\n", out)


class Macros(unittest.TestCase):
    def test_example_page(self):
        status, out, err = run(["-T", "ascii", LS])
        self.assertEqual((status, err), (0, ""))
        text = plain(out)
        self.assertIn("     ls [-la] [file ...]\n", text)
        self.assertIn("     -l      Long format.\n", text)
        self.assertIn("           ls -la /tmp\n", text)
        self.assertIn("     find(1)\n", text)

    def test_literal_display(self):
        doc = HEAD + ".Sh DESCRIPTION\n.Bd -literal\n  keep   spacing\nas is\n.Ed\n"
        out = plain(run(["-T", "ascii"], doc.encode())[1])
        self.assertIn("\n       keep   spacing\n     as is\n", out)

    def test_utf8_quotes(self):
        doc = HEAD + ".Sh DESCRIPTION\n.Dq quoted\n"
        self.assertIn("“quoted”", run(["-T", "utf8"], doc.encode())[1])


if __name__ == "__main__":
    unittest.main()
