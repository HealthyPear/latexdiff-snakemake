#!/usr/bin/env python3
"""
Neutralize a hyperref/url.sty interaction bug in the *diff build only*.

\\url{...} arguments containing a literal '#' (written doubled, e.g. "##",
per url.sty's own escaping convention) crash hyperref's XeTeX PDF-string
builder with "Illegal parameter number in definition of \\Hy@gtemp"
(reproducible even compiling sources/new/ms.tex standalone with tectonic --
this is a latent bug in the manuscript, not a latexdiff artifact).

We deliberately do NOT patch sources/old or sources/new: the actual
manuscript keeps its clickable link untouched. Instead, this script
rewrites \\url{...#...} -> \\nolinkurl{...#...} in the already-generated
diff .tex, right before compilation. \\nolinkurl still goes through
url.sty's parser (formatting/escaping unaffected) but skips hyperref's
link/PDF-string generation -- the part that crashes. All other \\url{}
calls (without '#') are left as live links in the diff PDF too.

Usage:
    disable_risky_url_links.py DIFF.tex OUTPUT.tex
"""
import re
import sys

# \url{...} whose argument contains a literal '#'. URL arguments aren't
# expected to contain braces, so a non-brace character class is safe here.
PATTERN = re.compile(r"\\url\{([^{}]*#[^{}]*)\}")


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(f"usage: {sys.argv[0]} DIFF.tex OUTPUT.tex")
    in_path, out_path = sys.argv[1], sys.argv[2]

    with open(in_path, encoding="utf-8") as f:
        text = f.read()

    fixed, count = PATTERN.subn(r"\\nolinkurl{\1}", text)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(fixed)

    print(
        f"[disable_risky_url_links] {count} \\url{{...#...}} occurrence(s) "
        "-> \\nolinkurl (diff build only, sources untouched)"
    )


if __name__ == "__main__":
    main()