"""Low-level roff handling: input lines, macro arguments and escape sequences."""

# fonts of a character run
R, B, I = "R", "B", "I"

# \(xx and \[name] glyphs: (ASCII rendering, UTF-8 rendering)
GLYPHS = {
    "em": ("--", "—"),
    "en": ("-", "–"),
    "hy": ("-", "‐"),
    "mi": ("-", "−"),
    "lq": ('"', "“"),
    "rq": ('"', "”"),
    "oq": ("`", "‘"),
    "cq": ("'", "’"),
    "aq": ("'", "'"),
    "dq": ('"', '"'),
    "bu": ("o", "•"),
    "co": ("(C)", "©"),
    "rg": ("(R)", "®"),
    "tm": ("tm", "™"),
    ">=": (">=", "≥"),
    "<=": ("<=", "≤"),
    "!=": ("!=", "≠"),
    "->": ("->", "→"),
    "<-": ("<-", "←"),
    "mu": ("x", "×"),
    "di": ("/", "÷"),
    "pl": ("+", "+"),
    "eq": ("=", "="),
    "ba": ("|", "|"),
    "rs": ("\\", "\\"),
    "de": ("<degree>", "°"),
    "sc": ("<section>", "§"),
    "Fo": ("<<", "«"),
    "Fc": (">>", "»"),
}

# \*q, \*(xx and \*[name] predefined strings
STRINGS = {
    "q": ('"', '"'),
    "Lq": ('"', "“"),
    "Rq": ('"', "”"),
    "lq": ('"', "“"),
    "rq": ('"', "”"),
    "Ge": (">=", "≥"),
    "Le": ("<=", "≤"),
    "Ne": ("!=", "≠"),
    "Pi": ("pi", "π"),
    "If": ("infinity", "∞"),
    "Tm": ("tm", "™"),
    "Gt": (">", ">"),
    "Lt": ("<", "<"),
}


def strip_comment(line):
    """Remove a \\" comment from the end of an input line."""
    i = 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line):
            if line[i + 1] == '"':
                return line[:i].rstrip(" ")
            i += 2
            continue
        i += 1
    return line


def split_args(text):
    """Split the arguments of a macro line; double quotes group words."""
    args = []
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i] == " ":
            i += 1
        if i >= n:
            break
        if text[i] == '"':
            i += 1
            word = []
            while i < n:
                if text[i] == '"':
                    if i + 1 < n and text[i + 1] == '"':
                        word.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                word.append(text[i])
                i += 1
            args.append("".join(word))
        else:
            start = i
            while i < n and text[i] != " ":
                if text[i] == "\\" and i + 1 < n:
                    i += 1
                i += 1
            args.append(text[start:i])
    return args


def expand(text, utf8, font=R):
    """Turn a string with escape sequences into a list of (char, font) pairs.

    A non-breaking space is returned as the character "\\xa0".  The second
    value is the font in effect at the end, so \\fB can carry across words.
    """
    out = []
    prev = font
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch != "\\" or i + 1 >= n:
            out.append((ch, font))
            i += 1
            continue
        nxt = text[i + 1]
        i += 2
        if nxt == "f":
            name = ""
            if i < n and text[i] == "(":
                name, i = text[i + 1:i + 3], i + 3
            elif i < n and text[i] == "[":
                j = text.find("]", i)
                j = n if j < 0 else j
                name, i = text[i + 1:j], j + 1
            elif i < n:
                name, i = text[i], i + 1
            if name in ("B", "I", "R"):
                prev, font = font, name
            elif name == "BI":
                prev, font = font, B
            elif name == "P":
                prev, font = font, prev
        elif nxt in "([":
            if nxt == "(":
                name, i = text[i:i + 2], i + 2
            else:
                j = text.find("]", i)
                j = n if j < 0 else j
                name, i = text[i:j], j + 1
            glyph = GLYPHS.get(name)
            if glyph:
                for c in glyph[1 if utf8 else 0]:
                    out.append((c, font))
        elif nxt == "*":
            name = ""
            if i < n and text[i] == "(":
                name, i = text[i + 1:i + 3], i + 3
            elif i < n and text[i] == "[":
                j = text.find("]", i)
                j = n if j < 0 else j
                name, i = text[i + 1:j], j + 1
            elif i < n:
                name, i = text[i], i + 1
            s = STRINGS.get(name)
            if s:
                for c in s[1 if utf8 else 0]:
                    out.append((c, font))
        elif nxt == "e":
            out.append(("\\", font))
        elif nxt == "-":
            out.append(("-", font))
        elif nxt in "~ ":
            out.append(("\xa0", font))
        elif nxt in ".'`_":
            out.append((nxt, font))
        elif nxt in "&|^%:c)":
            pass
        else:
            out.append((nxt, font))
    return out, font
