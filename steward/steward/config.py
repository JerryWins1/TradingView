"""Load the rules file."""

from __future__ import annotations

import tomllib
from pathlib import Path

DEFAULT_RULES = Path(__file__).resolve().parent.parent / "rules.toml"


def load_rules(path: str | Path | None = None) -> dict:
    with open(path or DEFAULT_RULES, "rb") as f:
        rules = tomllib.load(f)
    if rules["account"].get("mode") != "paper":
        raise ValueError("Steward only runs in paper mode for now.")
    return rules
