#!/usr/bin/env python3
import re
import sys

PATTERN = re.compile(r"\\begin\{comment\}.*?\\end\{comment\}", re.DOTALL)

def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(f"usage: {sys.argv[0]} INPUT.tex OUTPUT.tex")
    in_path, out_path = sys.argv[1], sys.argv[2]
    with open(in_path, encoding="utf-8") as f:
        text = f.read()
    stripped, count = PATTERN.subn("", text)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(stripped)
    print(f"[strip_comment_envs] {in_path} -> {out_path}: removed {count} comment block(s)")

if __name__ == "__main__":
    main()