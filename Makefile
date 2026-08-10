PYTHON ?= python
SPHINXBUILD ?= sphinx-build
normalize-command = $(if $(findstring /,$(1)),$(abspath $(1)),$(1))

.PHONY: test documentation docs documentation-examples benchmark-smoke benchmark-release clean

test:
	@MPLBACKEND=Agg MPL_IGNORE_SYSTEM_FONTS=1 \
		MPLCONFIGDIR=/tmp/deapack-matplotlib-pytest \
		$(call normalize-command,$(PYTHON)) -m pytest

documentation: docs

docs:
	@$(MAKE) -C docs html \
		SPHINXBUILD="$(call normalize-command,$(SPHINXBUILD))"

documentation-examples:
	@MPLBACKEND=Agg MPL_IGNORE_SYSTEM_FONTS=1 \
		MPLCONFIGDIR=/tmp/deapack-matplotlib-doc-examples \
		$(call normalize-command,$(PYTHON)) \
		scripts/run_documentation_examples.py \
		--include-visualization

benchmark-smoke:
	@$(call normalize-command,$(PYTHON)) scripts/run_benchmarks.py \
		--tier smoke --output-dir benchmark-results

benchmark-release:
	@$(call normalize-command,$(PYTHON)) scripts/run_benchmarks.py \
		--tier release --output-dir benchmark-results

clean:
	@$(MAKE) -C docs clean \
		SPHINXBUILD="$(call normalize-command,$(SPHINXBUILD))"
