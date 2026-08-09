SPHINXBUILD ?= sphinx-build
SPHINXINTL ?= sphinx-intl
PYTHON ?= python
MAKE ?= make
SOURCEDIR = .
BUILDDIR = _build
LATEXDIR = $(BUILDDIR)/latex
LATEXDIR_ZH = $(BUILDDIR)/latex-zh
export LC_ALL := C
export LANG := C

.PHONY: help figures html latex pdf gettext update-zh localize-zh-math normalize-zh check-zh html-zh latex-zh pdf-zh clean

help:
	@$(SPHINXBUILD) --help

figures:
	@$(PYTHON) figures/generate_concept_figures.py
	@$(PYTHON) figures/generate_apz_consistency.py
	@$(PYTHON) figures/generate_ray_desli_ledger.py
	@MPL_IGNORE_SYSTEM_FONTS=1 MPLCONFIGDIR=/tmp/deapack-matplotlib \
		$(PYTHON) figures/generate_result_figures.py
	@MPL_IGNORE_SYSTEM_FONTS=1 MPLCONFIGDIR=/tmp/deapack-matplotlib \
		$(PYTHON) figures/generate_multiplicative_efficiency.py
	@MPL_IGNORE_SYSTEM_FONTS=1 MPLCONFIGDIR=/tmp/deapack-matplotlib \
		$(PYTHON) figures/generate_directional_super_efficiency.py
	@$(PYTHON) figures/localize_handbook_figures_zh.py

html: figures
	@$(SPHINXBUILD) -E -a -W --keep-going -b html \
		"$(SOURCEDIR)" "$(BUILDDIR)/html"

# The LaTeX builder keeps the manuscript text searchable.  Sphinx copies SVG
# figures verbatim, whereas pdfLaTeX requires PDF image assets, so the
# repository-owned preparation step converts only the temporary LaTeX build
# tree and rewrites its generated image references.
latex: figures
	@$(SPHINXBUILD) -E -a -W --keep-going -b latex \
		"$(SOURCEDIR)" "$(LATEXDIR)"
	@$(PYTHON) ../scripts/prepare_book_latex.py "$(LATEXDIR)"

pdf: latex
	@$(MAKE) -C "$(LATEXDIR)" all-pdf \
		LATEXOPTS="-interaction=nonstopmode -halt-on-error"
	@$(PYTHON) ../scripts/verify_book_pdf.py "$(LATEXDIR)" \
		--copy-to "$(BUILDDIR)/pdf/DEAPack-Handbook.pdf"

gettext:
	@$(SPHINXBUILD) -W --keep-going -b gettext "$(SOURCEDIR)" "$(BUILDDIR)/gettext"

update-zh: gettext
	@$(SPHINXINTL) update -p "$(BUILDDIR)/gettext" -l zh_CN

localize-zh-math:
	@$(PYTHON) ../scripts/localize_handbook_math_labels.py \
		locale/zh_CN/LC_MESSAGES

# Gettext scaffolding invents placeholder people and an umbrella package-license
# comment. Normalize those fields only when an editor supplies a reviewed date.
normalize-zh:
	@test -n "$(PO_REVISION_DATE)" || \
		(echo "PO_REVISION_DATE is required, for example 2026-08-09 03:00+0100" && exit 2)
	@$(PYTHON) ../scripts/normalize_handbook_po_headers.py \
		locale/zh_CN/LC_MESSAGES --revision-date "$(PO_REVISION_DATE)"

check-zh: figures gettext
	@$(PYTHON) ../scripts/localize_handbook_math_labels.py \
		locale/zh_CN/LC_MESSAGES --check
	@$(PYTHON) ../scripts/check_handbook_translations.py \
		locale/zh_CN/LC_MESSAGES --require-complete \
		--template-root "$(BUILDDIR)/gettext"
	@$(PYTHON) figures/localize_handbook_figures_zh.py --check

html-zh: check-zh
	@DEAPACK_BOOK_LANGUAGE=zh_CN $(SPHINXBUILD) -E -a -W --keep-going -b html \
		"$(SOURCEDIR)" "$(BUILDDIR)/html-zh"

latex-zh: check-zh
	@DEAPACK_BOOK_LANGUAGE=zh_CN $(SPHINXBUILD) -E -a -W --keep-going -b latex \
		"$(SOURCEDIR)" "$(LATEXDIR_ZH)"
	@$(PYTHON) ../scripts/prepare_book_latex.py "$(LATEXDIR_ZH)"

pdf-zh: latex-zh
	@$(MAKE) -C "$(LATEXDIR_ZH)" all-pdf \
		LATEXOPTS="-interaction=nonstopmode -halt-on-error"
	@$(PYTHON) ../scripts/verify_book_pdf.py "$(LATEXDIR_ZH)" \
		--language zh_CN \
		--copy-to "$(BUILDDIR)/pdf/DEAPack-Handbook-zh-CN.pdf"

clean:
	@$(RM) -r "$(BUILDDIR)"
