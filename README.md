# latexdiff Snakemake pipeline

[![Snakemake](https://img.shields.io/badge/Snakemake-%E2%89%A59.27.0-2c8ebb.svg?style=flat-square&logo=snakemake)](https://snakemake.readthedocs.io/)
[![Pixi](https://img.shields.io/badge/Pixi-%E2%89%A50.81.0-4b9.svg?style=flat-square)](https://pixi.sh/)
[![Tectonic](https://img.shields.io/badge/Tectonic-0.17.0-2c3e50.svg?style=flat-square)](https://tectonic-typesetting.github.io/)

This was tested on an A&A manuscript, so other use cases might prove easier or not.

## Requirements

The only requirements is [Snakemake](https://snakemake.readthedocs.io/en/stable/).

It is recommended to install it using [pixi](https://pixi.prefix.dev/latest/).

> [!TIP]
> If you use [VSCode](https://code.visualstudio.com/) you only need [Docker](https://docs.docker.com/get-started/get-docker/): open the cloned repo with VSCode and agree to re-open the workflow in the devcontainer shipped with it when prompted

## Quick start

Place the source trees under ``source/new`` and ``sources/old``, then run

```shell
snakemake --cores 1 --use-conda
```

The expected outoput is stored under ``results``.

## Expected input layout

Paths, filenames and the output name are all set in `config.yaml`, which is
the configuration for the Snakemake workflow.

## What each step does

Assuming the main document is called ``ms.tex``:

1. **`fix_math_old` / `fix_math_new`** — preprocesses both `ms.tex`
   files identically, turning any adjacent inline-math delimiters
   written as `...$$...` (two touching `$...$` groups, e.g.
   `$\sim1.2\times10^6$$M_{\odot}$`) into `$` + `{}` + `$`: an invisible
   empty group. Without this, LaTeX/latexdiff can misread `$$` as a
   legacy display-math delimiter, which corrupted a diff mid-sentence
   and crashed the build.

2. **`latexdiff`** — runs latexdiff with three settings, each fixing a
   specific crash found while diffing this paper (see `config.yaml` for
   the full rationale on each):
   - `--math-markup=0` — diff formulas atomically.
   - `--graphics-markup=none` — latexdiff's own `--help` text recommends
     this as a workaround for table-related "Misplaced \noalign"
     errors; it can also fix "Division by 0" crashes when using `\resizebox{w}{!}{...}` 
   - `PICTUREENV` extended to also match `tabular*` and `figure*` —
     treats those environments as atomic (whole-old-block,
     whole-new-block) instead of diffing inside them word-by-word.
     This is what actually stops pdflatex from crashing on tables with
     rewritten `\multicolumn` cells, or figures where the image file
     changed inside a `\resizebox`.

3. **`merge_bib`** — unions `old/bib.bib` and `new/bib.bib` (new wins on
   key collisions). Needed because latexdiff shows deleted `\cite{}`
   calls struck through rather than removing them, so bibtex still
   needs entries for references the new version dropped.

4. **`merge_assets`** — copies the union of both trees' figures,
   `.cls`/`.bst`/etc. into the build directory (new wins on filename
   collisions).

5. **`figure_table_change_report`** — a coarse plain-text safety net for
   the trade-off in step 2: changes inside `tabular*`/`figure*` blocks
   compile correctly but aren't visually flagged in the PDF anymore.
   This report line-diffs just the `\includegraphics` / `\resizebox` /
   `\multicolumn` / `table*` / `tabular*` lines from the two raw
   sources, so a changed figure or table doesn't silently go unflagged.
   Read it, then eyeball the relevant figure/table by hand if anything
   shows up.

6. **`compile`** — builds the final PDF. Engine is chosen by
   `config["engine"]`:
   - `tectonic` (default) — `tectonic -X compile`, then `bibtex`, then
     two more tectonic passes
   - `pdflatex` — classic `pdflatex → bibtex → pdflatex → pdflatex` in
     case you already have an installation and/or you do not like to use tectonic.

   Either way, each LaTeX/tectonic pass is allowed to exit non-zero on
   its own — a routine warning (e.g. an unresolved `\ref` on the first
   pass) makes these tools exit 1 even on an otherwise-successful run,
   and Snakemake's shell blocks run under `set -euo pipefail` which
   would otherwise abort the whole recipe on the very first pass. The
   final `cp` of the PDF is the real success/failure gate.

## Caveats

- The `PICTUREENV` extension (step 2) trades away word-level diff
  markup inside `tabular*`/`figure*` blocks for a build that reliably
  compiles. If a future revision needs finer-grained diffing there,
  the two documented options in `config.yaml`'s comments
  (`graphics_markup`, `picture_env_extra`) are the knobs to revisit —
  and the error signatures to watch for ("Misplaced \omit" /
  "Division by 0" in `results/logs/*.log`) are exactly what led to the
  current settings.
