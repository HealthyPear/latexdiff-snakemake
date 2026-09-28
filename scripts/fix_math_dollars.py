#!/usr/bin/env python3
"""
Disambiguate adjacent inline-math delimiters written as "...$$..." (two
separate "$...$" groups touching, with nothing between them) so that they
cannot be misread as legacy "$$ ... $$" display-math delimiters.

Every unescaped "$$" becomes "$" + "{}" + "$": an empty group, invisible
in the typeset output, that gives the parser a token to land on between
the two delimiters. Escaped dollar signs ("\$", e.g. in currency amounts)
are left untouched.

Usage:
    fix_math_dollars.py INPUT.tex OUTPUT.tex
"""
import sys


def fix(text: str) -> tuple[str, int]:
    out = []
    i = 0
    n = len(text)
    count = 0
    while i < n:
        c = text[i]
        if c == "\\" and i + 1 < n and text[i + 1] == "$":
            out.append("\\$")
            i += 2
            continue
        if c == "$" and i + 1 < n and text[i + 1] == "$":
            out.append("${}$")
            i += 2
            count += 1
            continue
        out.append(c)
        i += 1
    return "".join(out), count


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(f"usage: {sys.argv[0]} INPUT.tex OUTPUT.tex")
    in_path, out_path = sys.argv[1], sys.argv[2]

    with open(in_path, encoding="utf-8") as f:
        text = f.read()

    fixed, count = fix(text)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(fixed)

    print(f"[fix_math_dollars] {in_path} -> {out_path}: fixed {count} adjacent-$$ occurrence(s)")


if __name__ == "__main__":
    main()
