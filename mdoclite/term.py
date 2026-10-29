"""Terminal output: filling words into lines with bold and underline."""

from .roff import B, I


def encode(chars):
    """Render (char, font) pairs with overstriking: bold is c BS c and
    underline is _ BS c."""
    out = []
    for ch, font in chars:
        if ch == "\xa0":
            ch = " "
        if font == B and ch != " ":
            out.append(ch + "\b" + ch)
        elif font == I and ch != " ":
            out.append("_\b" + ch)
        else:
            out.append(ch)
    return "".join(out)


class Terminal:
    def __init__(self, width=78, indent=5):
        self.width = width
        self.indent = indent
        self.lines = []
        self.offset = 0
        self.words = []          # [(chars, space_before)]
        self.nospace = False     # next word attaches to the previous one
        self.nofill = False
        self.first_offset = None  # offset for the first line of the next paragraph
        self.pending_blank = False

    # -- words ---------------------------------------------------------------
    def word(self, chars, space=True):
        if not chars:
            return
        if self.nospace:
            space = False
            self.nospace = False
        self.words.append((list(chars), space))

    def text(self, chars):
        """Add a run of characters, split at spaces."""
        cur = []
        for c in chars:
            if c[0] == " ":
                if cur:
                    self.word(cur)
                    cur = []
            else:
                cur.append(c)
        if cur:
            self.word(cur)

    def end_sentence(self):
        """Two spaces after a sentence that ends an input line."""
        if self.words:
            chars, space = self.words[-1]
            stripped = [c for c, _ in chars if c not in "\"')]"]
            if stripped and stripped[-1] in ".!?":
                self.words[-1] = (chars + [("\x01", "R")], space)

    # -- lines ---------------------------------------------------------------
    def emit(self, text):
        if self.pending_blank:
            if self.lines and self.lines[-1] != "":
                self.lines.append("")
            self.pending_blank = False
        self.lines.append(text.rstrip(" ") if text.strip(" ") else "")

    def blank(self):
        self.flush()
        self.pending_blank = True

    def flush(self):
        """Fill the collected words into lines."""
        if not self.words:
            return
        words, self.words = self.words, []
        offset = self.offset if self.first_offset is None else self.first_offset
        self.first_offset = None
        right = self.width
        line, col = [], offset
        for chars, space in words:
            w = len(chars)
            sep = 0
            if line and space:
                sep = 1
                prev = line[-1]
                if prev and prev[-1][0] == "\x01":
                    line[-1] = prev[:-1]
                    sep = 2
            elif line and line[-1] and line[-1][-1][0] == "\x01":
                line[-1] = line[-1][:-1]
            if line and space and col + sep + w > right:
                self._out(line, offset)
                line, col, offset = [], self.offset, self.offset
                sep = 0
            if sep:
                line.append([(" ", "R")] * sep)
                col += sep
            line.append(chars)
            col += w
        if line and line[-1] and line[-1][-1][0] == "\x01":
            line[-1] = line[-1][:-1]
        self._out(line, offset)

    def _out(self, parts, offset):
        chars = [c for p in parts for c in p]
        self.emit(" " * offset + encode(chars))

    def literal(self, chars):
        self.emit(" " * self.offset + encode(chars))

    def tag(self, tag_chars, width):
        """Start a -tag list item: the tag at the offset, the body after it."""
        self.flush()
        n = len(tag_chars)
        if n + 1 > width:
            self.emit(" " * self.offset + encode(tag_chars))
            self.offset += width
        else:
            self.words = [(list(tag_chars) + [(" ", "R")] * (width - n), False)]
            self.first_offset = self.offset
            self.offset += width
            self.nospace = True

    # -- page frame ----------------------------------------------------------
    def three(self, left, center, right):
        """A header or footer line: left, centered, right."""
        width = self.width
        col = (width - len(center) + 1) // 2
        line = left + " " * max(1, col - len(left)) + center
        pad = width - len(line) - len(right)
        return line + " " * max(1, pad) + right
