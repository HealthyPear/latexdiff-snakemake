#!/usr/bin/env python3
"""
The pipeline's latexdiff settings deliberately treat `tabular*`/`figure*`
environments as atomic blocks (see config.yaml), which means genuine
changes inside them compile safely but are NOT visually flagged in the
diff PDF. This script produces a plain-text early-warning report so
nothing gets missed: it does a line-level diff of the two raw source
files, restricted to lines that mention graphics or tabular/multicolumn
constructs, and lists what was added/removed.

This is a coarse, deliberately dumb signal -- read the report, then go
look at the relevant figure/table by hand in both PDFs (or in the
manuscript text) if anything shows up.

Usage:
    figure_table_change_report.py OLD.tex NEW.tex OUTPUT.txt
"""
import difflib
import re
import sys

PATTERN = re.compile(
    r"\\(includegraphics|resizebox|scalebox|begin\{table\*?\}|"
    r"begin\{tabular\*?\}|multicolumn)"
)


def relevant_lines(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if PATTERN.search(line)]


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(f"usage: {sys.argv[0]} OLD.tex NEW.tex OUTPUT.txt")
    old_path, new_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    old_lines = relevant_lines(old_path)
    new_lines = relevant_lines(new_path)

    diff = list(
        difflib.unified_diff(
            old_lines, new_lines, fromfile=old_path, tofile=new_path, lineterm=""
        )
    )

    with open(out_path, "w", encoding="utf-8") as f:
        if not diff:
            f.write(
                "No differences found among \\includegraphics / \\resizebox / "
                "\\scalebox / table* / tabular* / \\multicolumn lines.\n"
                "(This does NOT guarantee nothing changed -- e.g. a caption-only "
                "edit inside a figure* block wouldn't show up here. When in "
                "doubt, eyeball the figures/tables in both PDFs.)\n"
            )
        else:
            f.write(
                "Lines involving figures/tables that differ between old and "
                "new (these are the ones the diff PDF will NOT visually "
                "flag, per the picture_env_extra safe-mode setting):\n\n"
            )
            f.write("\n".join(diff))
            f.write("\n")

    print(f"[figure_table_change_report] {len(diff)} diff line(s) -> {out_path}")


if __name__ == "__main__":
    main()
