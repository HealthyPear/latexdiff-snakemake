"""
latexdiff-pipeline
==================
Reproducible "old vs new" manuscript diff, from two Overleaf-exported
source trees down to a compiled PDF with tracked changes.

    conda env create -f environment.yml
    conda activate latexdiff-pipeline
    snakemake --cores 1

See README.md for the full story on why each step exists, and
config.yaml for the tunable (and documented) knobs.
"""

configfile: "config.yaml"

OLD_DIR = config["old_dir"]
NEW_DIR = config["new_dir"]
MAIN_TEX = config["main_tex"]
NAME = config["output_name"]
ENGINE = config["engine"]

BUILD = f"results/build"
DIFF_TEX = f"{BUILD}/{NAME}.tex"


rule all:
    input:
        f"results/{NAME}.pdf",
        "results/figure_table_change_report.txt",

rule clean:
    shell:
        "rm -rf results"

# ---------------------------------------------------------------------------
# 1. Neutralise adjacent "$$" in both sources before anything else touches
#    them (see scripts/fix_math_dollars.py / config.yaml for why).
# ---------------------------------------------------------------------------
rule fix_math_old:
    input:
        f"{OLD_DIR}/{MAIN_TEX}",
    output:
        "results/old_fixed.tex",
    conda:
        "environment.yml"
    shell:
        r"""
        python scripts/fix_math_dollars.py {input} {output}.tmp
        python scripts/strip_comment_envs.py {output}.tmp {output}
        rm {output}.tmp
        """


rule fix_math_new:
    input:
        f"{NEW_DIR}/{MAIN_TEX}",
    output:
        "results/new_fixed.tex",
    conda:
        "environment.yml"
    shell:
        r"""
        python scripts/fix_math_dollars.py {input} {output}.tmp
        python scripts/strip_comment_envs.py {output}.tmp {output}
        rm {output}.tmp
        """


# ---------------------------------------------------------------------------
# 2. Run latexdiff with the safe-mode flags documented in config.yaml.
# ---------------------------------------------------------------------------
rule latexdiff:
    input:
        old="results/old_fixed.tex",
        new="results/new_fixed.tex",
    output:
        DIFF_TEX,
    params:
        math_markup=config["latexdiff"]["math_markup"],
        graphics_markup=config["latexdiff"]["graphics_markup"],
        picture_regex=(
            r"(?:picture[\w\d*@]*|tikzpicture[\w\d*@]*|DIFnomarkup|"
            + "|".join(config["latexdiff"]["picture_env_extra"])
            + ")"
        ),
        verbatim_regex=r"(?:verbatim\*?|comment)",
    conda:
        "environment.yml"
    shell:
        r"""
        mkdir -p {BUILD}
        latexdiff \
            --math-markup={params.math_markup} \
            --graphics-markup={params.graphics_markup} \
            --config="PICTUREENV={params.picture_regex}" \
            --config="VERBATIMENV={params.verbatim_regex}" \
            {input.old} {input.new} > {output}.raw

        python scripts/disable_risky_url_links.py {output}.raw {output}
        rm {output}.raw
        """


# ---------------------------------------------------------------------------
# 3. Assemble everything the build needs in one directory: the diff .tex,
#    a merged bibliography, and the union of both versions' figures /
#    class / style files (new_dir wins on filename collisions).
# ---------------------------------------------------------------------------
rule merge_bib:
    input:
        old=f"{OLD_DIR}/bib.bib",
        new=f"{NEW_DIR}/bib.bib",
    output:
        f"{BUILD}/bib.bib",
    conda:
        "environment.yml"
    shell:
        "mkdir -p {BUILD} && python scripts/merge_bib.py {input.old} {input.new} {output}"


rule merge_assets:
    input:
        old=OLD_DIR,
        new=NEW_DIR,
    output:
        touch(f"{BUILD}/.assets_merged"),
    conda:
        "environment.yml"
    shell:
        r"""
        mkdir -p {BUILD}
        # Union of figures, class and style files: copy old dir first,
        # then new dir on top so the new version wins on collisions.
        # (Deleted figures still referenced -- but commented out -- by
        # latexdiff don't strictly need to be present, but we copy them
        # anyway for robustness against future edge cases.)
        rsync -a --exclude '{MAIN_TEX}' --exclude 'bib.bib' {input.old}/ {BUILD}/
        rsync -a --exclude '{MAIN_TEX}' --exclude 'bib.bib' {input.new}/ {BUILD}/
        """


rule figure_table_change_report:
    input:
        old=f"{OLD_DIR}/{MAIN_TEX}",
        new=f"{NEW_DIR}/{MAIN_TEX}",
    output:
        "results/figure_table_change_report.txt",
    conda:
        "environment.yml"
    shell:
        "python scripts/figure_table_change_report.py {input.old} {input.new} {output}"


# ---------------------------------------------------------------------------
# 4. Compile. Exactly one "compile" rule is defined, chosen at parse time
#    by config["engine"], so there is never an ambiguous-rule situation.
# ---------------------------------------------------------------------------
if ENGINE == "tectonic":

    rule compile:
        input:
            tex=DIFF_TEX,
            bib=f"{BUILD}/bib.bib",
            assets=f"{BUILD}/.assets_merged",
        output:
            f"results/{NAME}.pdf",
        log:
            "results/logs/tectonic.log",
        conda:
            "environment.yml"
        shell:
            r"""
            mkdir -p results/logs
            cd {BUILD}
            tectonic -X compile --keep-logs {NAME}.tex >> ../logs/tectonic.log 2>&1 || true
            cp {NAME}.pdf ../{NAME}.pdf
            """

elif ENGINE == "pdflatex":

    rule compile:
        input:
            tex=DIFF_TEX,
            bib=f"{BUILD}/bib.bib",
            assets=f"{BUILD}/.assets_merged",
        output:
            f"results/{NAME}.pdf",
        log:
            "results/logs/pdflatex.log",
        shell:
            r"""
            mkdir -p results/logs
            cd {BUILD}
            # See the tectonic rule for why each pass tolerates its own
            # non-zero exit: warnings routinely make (pdf)latex exit 1
            # even on a fully successful run. The final `cp` is the real
            # success/failure gate.
            pdflatex -interaction=nonstopmode {NAME}.tex >> ../logs/pdflatex.log 2>&1 || true
            bibtex {NAME} >> ../logs/pdflatex.log 2>&1 || true
            pdflatex -interaction=nonstopmode {NAME}.tex >> ../logs/pdflatex.log 2>&1 || true
            pdflatex -interaction=nonstopmode {NAME}.tex >> ../logs/pdflatex.log 2>&1 || true
            cp {NAME}.pdf ../{NAME}.pdf
            """

else:
    raise ValueError(f"config['engine'] must be 'tectonic' or 'pdflatex', got {ENGINE!r}")
