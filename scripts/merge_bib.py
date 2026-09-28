#!/usr/bin/env python3
"""
Merge two BibTeX files into one, keyed on the citation key.

latexdiff keeps deleted text (including deleted \\cite{...} calls) visible
in the diff, struck through, so bibtex/biber still needs entries for
references that the *new* version removed. This script takes the union of
both bibliographies; where the same key exists in both, the entry from
`new_bib` wins (in case the entry itself was corrected/updated).

Usage:
    merge_bib.py OLD_BIB NEW_BIB OUTPUT_BIB
"""
import re
import sys

ENTRY_RE = re.compile(r"^@(\w+)\{([^,]+),", re.MULTILINE)


def parse_entries(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    chunks = re.split(r"(?=^@)", text, flags=re.MULTILINE)
    entries: dict[str, str] = {}
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk.startswith("@"):
            continue
        m = re.match(r"@\w+\{([^,]+),", chunk)
        if m:
            entries[m.group(1).strip()] = chunk
    return entries


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(f"usage: {sys.argv[0]} OLD_BIB NEW_BIB OUTPUT_BIB")
    old_bib, new_bib, out_bib = sys.argv[1], sys.argv[2], sys.argv[3]

    old_entries = parse_entries(old_bib)
    new_entries = parse_entries(new_bib)

    merged = dict(old_entries)
    merged.update(new_entries)  # new_bib wins on key collisions

    with open(out_bib, "w", encoding="utf-8") as f:
        for entry in merged.values():
            f.write(entry)
            f.write("\n\n")

    added_from_old = set(old_entries) - set(new_entries)
    print(
        f"[merge_bib] {len(new_entries)} entries from new, "
        f"{len(added_from_old)} kept from old (removed-but-still-cited), "
        f"{len(merged)} total -> {out_bib}"
    )


if __name__ == "__main__":
    main()
