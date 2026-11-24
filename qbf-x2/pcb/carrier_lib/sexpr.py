"""Minimal s-expression reader for KiCad netlists / boards (strings unescaped, atoms kept as str)."""


def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in "()":
            yield c
            i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while s[j] != '"':
                if s[j] == "\\":
                    j += 1
                    buf.append({"n": "\n", "t": "\t"}.get(s[j], s[j]))
                else:
                    buf.append(s[j])
                j += 1
            yield ("str", "".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()"':
                j += 1
            yield ("atom", s[i:j])
            i = j


def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == "(":
            stack.append([])
        elif t == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(t[1])
    return stack[0][0]


def find(tree, key):
    return [x for x in tree if isinstance(x, list) and x and x[0] == key]
