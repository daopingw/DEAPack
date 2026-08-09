SPHINXBUILD ?= sphinx-build
SPHINXINTL ?= sphinx-intl
SOURCEDIR = .
BUILDDIR = _build
export LC_ALL := C
export LANG := C

.PHONY: help html html-zh gettext update-zh clean

help:
	@$(SPHINXBUILD) --help

html:
	@$(SPHINXBUILD) -E -a -W --keep-going -b html \
		"$(SOURCEDIR)" "$(BUILDDIR)/html"

gettext:
	@$(SPHINXBUILD) -W --keep-going -b gettext "$(SOURCEDIR)" "$(BUILDDIR)/gettext"

update-zh: gettext
	@$(SPHINXINTL) update -p "$(BUILDDIR)/gettext" -l zh_CN

html-zh:
	@$(SPHINXBUILD) -E -a -W --keep-going -b html -D language=zh_CN \
		"$(SOURCEDIR)" "$(BUILDDIR)/html-zh"

clean:
	@$(RM) -r "$(BUILDDIR)"
