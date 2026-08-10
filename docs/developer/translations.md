# Documentation Localization

Python docstrings, API identifiers, and package Documentation are maintained
in English. The current public Read the Docs site is English-only; historical
localization catalogs are not a completeness gate for the stable package
Documentation.

If package-Documentation localization is resumed, regenerate catalogs from the
current English source before translating:

```bash
cd docs
make update-zh
```

Translate and review every new or fuzzy message, then run:

```bash
make html-zh
```

Localization changes must preserve code, mathematics, cross-reference labels,
API names, citations, and generated values. Translated prose should be edited
for idiomatic scholarly usage rather than translated word by word. A localized
site should not be advertised until its complete source set passes the same
strict warning policy and navigation checks as the English site.
