"""Refine and extend the Japanese Danbooru tag index.

Usage from the repository root::

    python scripts/refine_index.py \
        --additions data/appearance_tag_additions.csv \
        --output index.csv

The input index is refined first.  Reviewed additions are then appended with
contiguous indices.  The script writes UTF-8 with BOM and CRLF to match the
existing CSV consumed by the tagger UI.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
from pathlib import Path
from typing import Iterable, Mapping

try:
    from .tag_classification import (
        MIXED_APPEARANCE_CATEGORY,
        classify_category,
        is_usable_api_tag,
    )
except ImportError:  # pragma: no cover - supports direct script execution
    from tag_classification import (
        MIXED_APPEARANCE_CATEGORY,
        classify_category,
        is_usable_api_tag,
    )

FIELDS = ["index", "tag", "db_category_filled", "tag_jp", "category_jp"]
CORRECTION_FIELDS = [
    "index",
    "tag",
    "old_tag_jp",
    "new_tag_jp",
    "old_category_jp",
    "new_category_jp",
    "reason",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"{path} must have columns {FIELDS}, got {reader.fieldnames}")
        return [
            {field: (row.get(field) or "").strip() for field in FIELDS}
            for row in reader
        ]


def refine_rows(rows: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    """Apply the prompt-oriented category rules without changing tag text."""

    refined: list[dict[str, str]] = []
    for source in rows:
        row = {field: str(source.get(field) or "").strip() for field in FIELDS}
        if not row["tag"]:
            raise ValueError("tag must not be empty")
        row["category_jp"] = classify_category(row["tag"], row["category_jp"])
        refined.append(row)
    return refined


def merge_additions(
    existing: Iterable[Mapping[str, str]],
    additions: Iterable[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Append reviewed additions and assign the next contiguous indices."""

    merged = [
        {field: str(row.get(field) or "").strip() for field in FIELDS}
        for row in existing
    ]
    tags = {row["tag"] for row in merged}
    initial_rows_by_tag = {row["tag"]: row for row in merged}
    if "" in tags:
        raise ValueError("existing rows contain an empty tag")
    if len(tags) != len(merged):
        raise ValueError("existing rows contain duplicate tags")

    try:
        next_index = max((int(row["index"]) for row in merged), default=-1) + 1
    except (TypeError, ValueError) as exc:
        raise ValueError("existing indices must be integers") from exc

    for source in additions:
        tag = str(source.get("tag") or "").strip()
        if not is_usable_api_tag(tag):
            raise ValueError(f"addition is not a usable canonical tag: {tag!r}")
        row = {field: str(source.get(field) or "").strip() for field in FIELDS}
        row["category_jp"] = classify_category(tag, row["category_jp"])

        if tag in initial_rows_by_tag:
            existing_row = initial_rows_by_tag[tag]
            if all(existing_row[field] == row[field] for field in FIELDS if field != "index"):
                continue
            raise ValueError(f"addition conflicts with an existing tag: {tag}")
        if tag in tags:
            raise ValueError(f"addition duplicates an earlier addition: {tag}")

        row["index"] = str(next_index)
        merged.append(row)
        tags.add(tag)
        next_index += 1
    return merged


def apply_manual_corrections(
    rows: Iterable[Mapping[str, str]],
    corrections: Iterable[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Apply reviewed row corrections without silently overwriting changes."""

    corrected = [
        {field: str(row.get(field) or "").strip() for field in FIELDS}
        for row in rows
    ]
    rows_by_key = {(row["index"], row["tag"]): row for row in corrected}
    seen: set[tuple[str, str]] = set()

    for source in corrections:
        correction = {
            field: str(source.get(field) or "").strip()
            for field in CORRECTION_FIELDS
        }
        key = (correction["index"], correction["tag"])
        if key in seen:
            raise ValueError(f"manual correction is duplicated: {key}")
        seen.add(key)

        row = rows_by_key.get(key)
        if row is None:
            raise ValueError(f"manual correction target was not found: {key}")
        old_values = (correction["old_tag_jp"], correction["old_category_jp"])
        new_values = (correction["new_tag_jp"], correction["new_category_jp"])
        current_values = (row["tag_jp"], row["category_jp"])
        if not all(new_values):
            raise ValueError(f"manual correction has an empty replacement: {key}")
        if current_values == new_values:
            continue
        if any(
            current not in {old, new}
            for current, old, new in zip(current_values, old_values, new_values)
        ):
            raise ValueError(
                f"manual correction old values do not match for {key}: "
                f"expected {old_values}, got {current_values}"
            )
        row["tag_jp"], row["category_jp"] = new_values

    return corrected


def write_rows(path: Path, rows: Iterable[Mapping[str, str]]) -> None:
    """Write the index atomically in the repository's original CSV format."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=FIELDS,
                lineterminator="\r\n",
                quoting=csv.QUOTE_ALL,
            )
            writer.writeheader()
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in FIELDS})
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def build_index(
    input_path: Path,
    output_path: Path,
    additions_path: Path | None = None,
    corrections_path: Path | None = None,
) -> dict[str, int]:
    original = read_rows(input_path)
    refined = refine_rows(original)
    additions: list[dict[str, str]] = []
    if additions_path is not None:
        additions = read_additions(additions_path)
    merged = merge_additions(refined, additions)
    corrections: list[dict[str, str]] = []
    if corrections_path is not None:
        corrections = read_corrections(corrections_path)
    corrected = apply_manual_corrections(merged, corrections)
    write_rows(output_path, corrected)
    return {
        "original_rows": len(original),
        "refined_rows": len(refined),
        "added_rows": len(additions),
        "manual_correction_rows": len(corrections),
        "output_rows": len(corrected),
        "mixed_category_rows": sum(
            row["category_jp"] == MIXED_APPEARANCE_CATEGORY for row in corrected
        ),
    }


def read_additions(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"tag", "db_category_filled", "tag_jp", "category_jp"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing addition columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def read_corrections(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(CORRECTION_FIELDS).difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} is missing correction columns: {sorted(missing)}")
        return [dict(row) for row in reader]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("index.csv"))
    parser.add_argument("--output", type=Path, default=Path("index.csv"))
    parser.add_argument("--additions", type=Path)
    parser.add_argument("--corrections", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_index(args.input, args.output, args.additions, args.corrections)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
