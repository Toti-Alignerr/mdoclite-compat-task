"""mdoc(7) macros, formatted straight to the terminal as the lines are read."""

from .roff import B, I, R, expand, split_args, strip_comment
from .term import Terminal

VOLUMES = {
    "1": "General Commands Manual",
    "2": "System Calls Manual",
    "3": "Library Functions Manual",
    "4": "Device Drivers Manual",
    "5": "File Formats Manual",
    "6": "Games Manual",
    "7": "Miscellaneous Information Manual",
    "8": "System Manager's Manual",
    "9": "Kernel Developer's Manual",
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# punctuation that attaches to the word before it, and to the word after it
CLOSE = {".", ",", ";", ":", "?", "!", ")", "]"}
OPEN = {"(", "["}

# inline macros: font of their arguments
FONTS = {
    "Fl": B, "Cm": B, "Ic": B, "Sy": B, "Nm": B, "Fd": B, "Cd": B, "Ms": B,
    "Ar": I, "Pa": I, "Em": I, "Va": I, "Ev": R, "Dv": R, "Er": R, "Li": R,
    "Ad": I, "Ft": I, "Fa": I, "Vt": I, "Tn": R, "Ux": R, "Mt": I,
}
# enclosures: (open, close) in ASCII and UTF-8
ENCLOSE = {
    "Dq": (('"', '"'), ("“", "”")),
    "Sq": (("`", "'"), ("‘", "’")),
    "Ql": (("`", "'"), ("‘", "’")),
    "Pq": (("(", ")"), ("(", ")")),
    "Bq": (("[", "]"), ("[", "]")),
    "Brq": (("{", "}"), ("{", "}")),
    "Aq": (("<", ">"), ("⟨", "⟩")),
    "Op": (("[", "]"), ("[", "]")),
    "Qq": (('"', '"'), ('"', '"')),
}
CALLABLE = set(FONTS) | set(ENCLOSE) | {"Xr", "Ns", "No", "Fn", "Oo", "Oc", "Pf", "Lk", "Sx", "Ta"}


def parse_date(s):
    """'Month D, YYYY' or '$Mdocdate: Month D YYYY $'; anything else verbatim."""
    t = s.replace(",", " ").split()
    if t and t[0] == "$Mdocdate:":
        t = t[1:4]
    if len(t) == 3 and t[0] in MONTHS and t[1].isdigit() and t[2].isdigit():
        return "%s %d, %s" % (t[0], int(t[1]), t[2])
    return s


class Formatter:
    def __init__(self, opts):
        self.utf8 = opts.get("output") == "utf8"
        self.t = Terminal(opts.get("width", 78), opts.get("indent", 5))
        self.os_name = opts.get("os")
        self.date = ""
        self.title = ""
        self.section = ""
        self.os = ""
        self.name = ""
        self.cur_sec = None
        self.lists = []      # stack of (type, width, offset, counter)
        self.displays = []   # stack of (offset, nofill)
        self.font = R

    # -- helpers -------------------------------------------------------------
    def chars(self, s, font=None):
        c, _ = expand(s, self.utf8, font or R)
        return c

    def put(self, s, font=None, space=True):
        chars = self.chars(s, font)
        if chars:
            self.t.word(chars, space)

    def args_inline(self, args):
        """Format macro arguments that may contain callable macros."""
        i = 0
        font = R
        while i < len(args):
            a = args[i]
            if a in CALLABLE and i > 0 or (i == 0 and a in CALLABLE):
                i = self.call(a, args, i + 1)
                font = R
                continue
            if a in CLOSE:
                self.put(a, R, space=False)
            elif a in OPEN:
                self.put(a, R)
                self.t.nospace = True
            else:
                self.put(a, font)
            i += 1

    def call(self, name, args, i):
        """Run inline macro `name` on args[i:]; return the index after it."""
        j = i
        while j < len(args) and args[j] not in CALLABLE:
            j += 1
        own = args[i:j]
        rest_start = j
        words = [a for a in own if a not in CLOSE]
        trailing = own[len(words):] if words == own[:len(words)] else []
        if trailing:
            own = own[:len(words)]
        if name in FONTS:
            font = FONTS[name]
            if name == "Nm" and not own:
                own = [self.name] if self.name else []
            if name == "Fl":
                if not own:
                    self.put("\\-", B)
                for a in own:
                    if a in CLOSE:
                        self.put(a, R, space=False)
                    else:
                        self.put("\\-" + a, B)
            else:
                for a in own:
                    if a in CLOSE:
                        self.put(a, R, space=False)
                    else:
                        self.put(a, font)
                if name == "Ar" and not own:
                    self.put("file ...", I)
        elif name in ENCLOSE:
            o, c = ENCLOSE[name][1 if self.utf8 else 0]
            self.put(o, R)
            self.t.nospace = True
            inner = args[i:]
            if inner:
                self.args_inline(inner)
            self.put(c, R, space=False)
            return len(args)
        elif name == "Xr":
            if own:
                self.put(own[0], R)
                if len(own) > 1:
                    self.put("(" + own[1] + ")", R, space=False)
            for a in own[2:]:
                self.put(a, R, space=False if a in CLOSE else True)
        elif name == "Fn":
            if own:
                self.put(own[0], B)
                self.put("(", R, space=False)
                for k, a in enumerate(own[1:]):
                    self.put(a + ("," if k < len(own) - 2 else ""), I, space=k > 0)
                self.put(")", R, space=False)
        elif name == "Ns":
            self.t.nospace = True
            for a in own:
                self.put(a)
        elif name in ("No", "Sx", "Lk", "Ta"):
            for a in own:
                self.put(a, R, space=a not in CLOSE)
        elif name == "Oo":
            self.put("[", R)
            self.t.nospace = True
            for a in own:
                self.put(a)
        elif name == "Oc":
            self.put("]", R, space=False)
        elif name == "Pf":
            if own:
                self.put(own[0])
                self.t.nospace = True
            for a in own[1:]:
                self.put(a)
        for a in trailing:
            self.put(a, R, space=False)
        return rest_start

    # -- block macros --------------------------------------------------------
    def macro(self, name, args):
        t = self.t
        if name == "Dd":
            self.date = parse_date(" ".join(args))
        elif name == "Dt":
            self.title = args[0] if args else "UNTITLED"
            self.section = args[1] if len(args) > 1 else ""
        elif name == "Os":
            self.os = " ".join(args) if args else (self.os_name or "macOS 26.6")
            self.header()
        elif name == "Sh":
            t.flush()
            t.offset = 0
            self.lists, self.displays = [], []
            self.cur_sec = " ".join(args)
            t.pending_blank = True
            t.text(self.chars(" ".join(args), B))
            t.flush()
            t.offset = t.indent
        elif name == "Ss":
            t.blank()
            t.offset = 3
            t.text(self.chars(" ".join(args), B))
            t.flush()
            t.offset = t.indent
        elif name in ("Pp", "Lp"):
            t.blank()
        elif name == "br":
            t.flush()
        elif name == "sp":
            t.blank()
        elif name == "Nm":
            if args and not self.name:
                self.name = args[0]
            if self.cur_sec == "SYNOPSIS":
                t.flush()
            self.call("Nm", args, 0)
        elif name == "Nd":
            self.put("\\-")
            self.args_inline(args)
        elif name == "Bl":
            self.begin_list(args)
        elif name == "It":
            self.item(args)
        elif name == "El":
            t.flush()
            if self.lists:
                _, _, offset, _, _ = self.lists.pop()
                t.offset = offset
        elif name == "Bd":
            t.flush()
            if "-compact" not in args:
                t.blank()
            offset = t.offset
            if "-offset" in args:
                k = args.index("-offset")
                val = args[k + 1] if k + 1 < len(args) else ""
                t.offset += 6 if val in ("indent", "") else len(val)
            nofill = "-literal" in args or "-unfilled" in args
            self.displays.append((offset, nofill))
            t.nofill = nofill
        elif name == "Ed":
            t.flush()
            if self.displays:
                offset, _ = self.displays.pop()
                t.offset = offset
            t.nofill = bool(self.displays and self.displays[-1][1])
        elif name in ("D1", "Dl"):
            t.flush()
            t.offset += 6
            if name == "Dl":
                for a in args:
                    self.put(a)
            else:
                self.args_inline(args)
            t.flush()
            t.offset -= 6
        elif name == "Ex":
            n = self.name
            self.put("The")
            self.put(n, B)
            self.put("utility exits 0 on success, and >0 if an error occurs.")
        elif name == "Rv":
            self.put("The")
            self.put(args[-1] if args and args[-1] != "-std" else "function", B)
            self.put("() function returns the value 0 if successful;")
            self.put("otherwise the value -1 is returned and the global variable")
            self.put("errno", I)
            self.put("is set to indicate the error.")
        elif name in CALLABLE:
            self.args_inline([name] + args)
        # anything else is ignored

    def begin_list(self, args):
        t = self.t
        t.flush()
        kind = args[0][1:] if args and args[0].startswith("-") else "item"
        width = 8
        if "-width" in args:
            k = args.index("-width")
            val = args[k + 1] if k + 1 < len(args) else ""
            width = (6 if val == "Ds" else len(val)) + 2
        elif kind in ("bullet", "dash", "hyphen", "enum"):
            width = 4 if kind != "enum" else 4
        compact = "-compact" in args
        self.lists.append((kind, width, t.offset, compact, [0]))
        if self.lists[:-1] or not compact:
            t.blank()

    def item(self, args):
        t = self.t
        if not self.lists:
            return
        kind, width, offset, compact, counter = self.lists[-1]
        t.flush()
        t.offset = offset
        if counter[0] and not compact:
            t.blank()
        counter[0] += 1
        if kind == "tag":
            save = t.words
            t.words = []
            self.args_inline(args)
            tag = []
            for k, (chars, space) in enumerate(t.words):
                if k and space:
                    tag.append((" ", R))
                tag.extend(chars)
            t.words = save
            t.tag(tag, width)
        elif kind in ("bullet", "dash", "hyphen", "enum"):
            mark = {"bullet": "o" if not self.utf8 else "•", "dash": "-", "hyphen": "-"}.get(kind)
            if kind == "enum":
                mark = "%d." % counter[0]
            t.tag([(c, B if kind != "enum" else R) for c in mark], width)
        elif kind == "item":
            t.offset = offset + width
        else:  # -ohang, -inset, -hang, -diag, -column: the head on its own line
            if args:
                self.args_inline(args)
            t.flush()
            t.offset = offset + width

    def header(self):
        title = "%s(%s)" % (self.title, self.section) if self.section else self.title
        vol = VOLUMES.get(self.section[:1], "")
        self.t.emit(self.t.three(title, vol, title))
        self.t.pending_blank = True

    def footer(self):
        t = self.t
        t.flush()
        t.pending_blank = True
        t.emit(t.three(self.os, self.date, self.os))

    # -- input ---------------------------------------------------------------
    def run(self, text):
        t = self.t
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        for line in lines:
            if line.startswith(".") or line.startswith("'"):
                body = strip_comment(line[1:]).strip(" ")
                if not body:
                    continue
                parts = body.split(" ", 1)
                name = parts[0]
                args = split_args(parts[1]) if len(parts) > 1 else []
                self.macro(name, args)
                if t.nofill:
                    t.flush()
                elif args and args[-1] in (".", "!", "?") or (args and args[-1].endswith(".")):
                    t.end_sentence()
                continue
            line = strip_comment(line)
            if t.nofill:
                t.literal(self.chars(line.replace("\t", "        ")))
                continue
            if not line.strip():
                t.blank()
                continue
            chars, self.font = expand(line, self.utf8, self.font)
            if line.startswith(" "):
                t.flush()
            t.text(chars)
            t.end_sentence()
        self.footer()
        return "\n".join(t.lines) + "\n"
