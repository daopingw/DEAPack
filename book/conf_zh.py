"""Read the Docs entry point for the Chinese Handbook rendering."""

from __future__ import annotations

import os
from pathlib import Path

os.environ["DEAPACK_BOOK_LANGUAGE"] = "zh_CN"
source = Path(__file__).with_name("conf.py")
exec(compile(source.read_text(encoding="utf-8"), str(source), "exec"))
