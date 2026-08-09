# Translation Workflow

Python docstrings, API identifiers, package Documentation, and the Handbook's
editorial source are canonical in English. Package Documentation remains
English-only for the first public release. Existing Chinese Documentation
catalogs are historical scaffolding, not a completeness or CI gate.

Do not update or publish Chinese package-Documentation catalogs during the rc1
cycle. A later localization cycle can regenerate them with:

```bash
cd docs
make update-zh
make html-zh
```

The companion Handbook is different: English and Chinese are both rc1
publication targets. Regenerate its Chinese catalogs whenever the English
source changes:

```bash
cd book
make update-zh
## Translate and review every new/fuzzy catalog message before continuing.
make localize-zh-math
make normalize-zh PO_REVISION_DATE="YYYY-MM-DD HH:MM+ZZZZ"
make check-zh
make html-zh
```

The normalization step removes placeholder translator identities and the
generic gettext claim that catalogs inherit one package license. It records a
reviewed revision date without inventing a personal email address; translation
credit remains traceable in repository history. The Handbook component license
must be approved explicitly before public distribution.

The math-label step localizes only reviewed human-readable `\\text{...}`
phrases inside equations. It preserves the algebraic skeleton and fails when
an English label has no explicit Chinese decision; code, symbols, and computed
values remain unchanged.

`make check-zh` rebuilds gettext templates from the latest canonical English
source and compares every active message with its maintained Chinese catalog.
This source-synchronization gate prevents Sphinx from silently falling back to
English when a paragraph changes but a stale PO file still appears complete.

The 30 reader-source catalogs are accompanied by
`book/locale/zh_CN/LC_MESSAGES/sphinx.po`, a deliberately small catalog for
theme controls such as the sidebar and color-mode labels. It is part of the
same completeness gate but not another Handbook source. The Chinese Sphinx
configuration also keeps its browser search stemmer aligned with the bundled
JavaScript implementation; a strict build should therefore be followed by a
real Chinese search smoke, not only an inspection of `searchindex.js`.

Translation pull requests must preserve code, mathematics, cross-reference
labels, API names, citations, and generated values. They must follow
`specs/CHINESE_TRANSLATION_GUIDE.md` and pass the translation-completeness and
strict bilingual Sphinx gates. Chinese prose is edited for idiomatic scholarly
usage rather than translated word by word.
