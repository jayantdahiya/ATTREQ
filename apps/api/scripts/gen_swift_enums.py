#!/usr/bin/env python
"""RI-2: generate the iOS mirror of `schemas/wardrobe_enums.py`.

`apps/ios/ATTREQ/Core/Models/WardrobeEnums.swift` must never hand-drift from
the Python vocabulary — rather than trusting a hand-copied comment to keep
them in sync (the RI-2 plan's finding #9), this script is the single source
that emits the Swift file, and `--check` mode is wired into CI (backend-ci.yml)
so a PR that changes an enum in Python without regenerating the Swift file
fails the build.

Usage:
    python scripts/gen_swift_enums.py            # (re)writes the Swift file
    python scripts/gen_swift_enums.py --check     # exits 1 if the committed
                                                   # file is stale, writes nothing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from attreq_api.schemas.wardrobe_enums import (  # noqa: E402
    Neckline,
    Silhouette,
    SleeveLength,
    StatementLevel,
    Texture,
)

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "ios"
    / "ATTREQ"
    / "Core"
    / "Models"
    / "WardrobeEnums.swift"
)

_HEADER = """// WardrobeEnums.swift
// ATTREQ
//
// GENERATED FILE — DO NOT EDIT BY HAND.
//
// Mirrors the fixed-vocabulary attribute enums in
// apps/api/src/attreq_api/schemas/wardrobe_enums.py (single source of truth).
// Regenerate with:
//     python apps/api/scripts/gen_swift_enums.py
// CI (`backend-ci.yml`) runs `--check` and fails the build if this file is
// stale relative to the Python enums (RI-2 plan finding #9 — generate, don't
// hand-mirror).

import Foundation
"""

# (Swift type name, Python enum class, doc comment)
_ENUMS = [
    ("Texture", Texture, "Fabric/material texture. `.other` is the coercion fallback."),
    ("Silhouette", Silhouette, "Garment fit/cut."),
    (
        "Neckline",
        Neckline,
        "Neckline shape. Only meaningful for tops/fullbody garments — `.nA` is a "
        "legal, expected value for bottoms/footwear.",
    ),
    (
        "SleeveLength",
        SleeveLength,
        "Sleeve length. Only meaningful for tops/outerwear/fullbody garments — "
        "`.nA` is a legal, expected value for bottoms/footwear.",
    ),
    ("StatementLevel", StatementLevel, "How much visual attention the item commands."),
]


def _swift_case_name(value: str) -> str:
    """`snake_case` value -> Swift `lowerCamelCase` case name.

    Swift case *names* are conventionally camelCase even when the raw string
    value stays snake_case (e.g. `case silkSatin = "silk_satin"`), so this
    mirrors what a human would have hand-written.
    """
    parts = value.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _render_enum(swift_name: str, enum_cls: type, doc: str) -> str:
    lines = [f"/// {doc}", f"enum {swift_name}: String, Codable, Sendable, CaseIterable {{"]
    for member in enum_cls:
        case_name = _swift_case_name(member.value)
        if case_name == member.value:
            lines.append(f"    case {case_name}")
        else:
            lines.append(f'    case {case_name} = "{member.value}"')
    lines.append("}")
    return "\n".join(lines)


def render() -> str:
    body = "\n\n".join(_render_enum(name, cls, doc) for name, cls, doc in _ENUMS)
    return _HEADER + "\n" + body + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate WardrobeEnums.swift from wardrobe_enums.py")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the committed Swift file doesn't match regenerated output; write nothing",
    )
    args = parser.parse_args()

    generated = render()

    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text() != generated:
            print(f"STALE: {OUTPUT_PATH} does not match regenerated output.")
            print("Run `python apps/api/scripts/gen_swift_enums.py` and commit the result.")
            sys.exit(1)
        print(f"OK: {OUTPUT_PATH} is up to date.")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(generated)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
