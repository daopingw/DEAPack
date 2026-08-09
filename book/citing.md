# Citing This Book and DEAPack

The book and DEAPack are related but distinct scholarly works. Cite the book
when relying on its theory, unified vocabulary, interpretation, or worked
cases. Cite the software when reporting a computation, implementation, or
numerical workflow. Cite both when both materially support the study.

## Cite the book

The current English-source Handbook and its Chinese translation form
*Bilingual Handbook Preview 1*, one development manuscript by Daoping Wang.
Until a formal edition supplies its own bibliographic record, identify the
repository snapshot and language that you consulted. A suitable citation for
the English rendering is:

> Wang, Daoping. *Data Envelopment Analysis: Efficiency, Productivity, and
> Environmental Performance with Python*. Bilingual Handbook Preview 1,
> English rendering, development manuscript, DEAPack repository, commit
> **FULL_COMMIT_HASH**, accessed **YYYY-MM-DD**.
> <https://github.com/daopingw/DEAPack>

Replace the bold placeholders with the full Git commit hash and your access
date. Do not add a publisher, publication year, edition number, or persistent
identifier that the cited snapshot does not carry.

For the Chinese rendering, retain the author and English title so that the
record remains discoverable, add “Chinese translation” in brackets, and use
the same commit and access date. The two renderings should not be assigned
separate placeholder DOI or ISBN values.

## Cite the software

The repository's current software citation metadata are recorded in
[CITATION.cff](https://github.com/daopingw/DEAPack/blob/main/CITATION.cff).
Use those metadata for the software citation and report the exact DEAPack
version used in the analysis. The installed version is available in Python:

```python
import deapack

deapack.__version__
```

For an unreleased or source-based analysis, also record the full repository
commit:

```console
git rev-parse HEAD
```

The version, commit when applicable, data snapshot, and analysis code together
identify the computation more precisely than the package name alone.
