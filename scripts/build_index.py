#!/usr/bin/env python3
"""Rebuild the model index in the root README.md.

Scans models/<name>/README.md, reads the YAML-style front matter at the top
of each file, and writes a table between the INDEX markers in README.md.

Usage:  python3 scripts/build_index.py
No third-party packages required.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
README = ROOT / "README.md"
START = "<!-- INDEX:START -->"
END = "<!-- INDEX:END -->"


def parse_front_matter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            val = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        else:
            val = val.strip("'\"")
        meta[key.strip().lower()] = val
    return meta


def first_heading(text: str) -> str | None:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else None


def esc(s: str) -> str:
    return str(s).replace("|", "\\|").strip()


def collect_models():
    models = []
    for d in sorted(p for p in MODELS_DIR.iterdir() if p.is_dir()):
        if d.name.startswith(("_", ".")):
            continue  # skip _template and hidden folders
        readme = d / "README.md"
        if not readme.exists():
            print(f"warning: {d.name} has no README.md, skipped", file=sys.stderr)
            continue
        text = readme.read_text(encoding="utf-8")
        meta = parse_front_matter(text)
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        models.append({
            "slug": d.name,
            "title": meta.get("title") or first_heading(text) or d.name,
            "category": meta.get("category", "Uncategorized"),
            "status": meta.get("status", ""),
            "material": meta.get("material", ""),
            "summary": meta.get("summary", ""),
            "tags": tags,
        })
    return models


def render(models) -> str:
    if not models:
        return "_No models yet. Copy `models/_template` to get started._"
    lines = [f"**{len(models)} model{'s' if len(models) != 1 else ''}**", ""]
    by_cat = {}
    for m in models:
        by_cat.setdefault(m["category"], []).append(m)
    for cat in sorted(by_cat, key=str.lower):
        lines += [f"### {esc(cat)}", "",
                  "| Model | Description | Material | Status | Tags |",
                  "|-------|-------------|----------|--------|------|"]
        for m in sorted(by_cat[cat], key=lambda x: x["title"].lower()):
            tags = " ".join(f"`{esc(t)}`" for t in m["tags"])
            lines.append(
                f"| [{esc(m['title'])}](models/{m['slug']}/README.md) "
                f"| {esc(m['summary'])} | {esc(m['material'])} "
                f"| {esc(m['status'])} | {tags} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def main():
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        sys.exit(f"README.md is missing {START} / {END} markers")
    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    new = f"{before}{START}\n{render(collect_models())}\n{END}{after}"
    if new != readme:
        README.write_text(new, encoding="utf-8")
        print("README.md index updated")
    else:
        print("README.md index already up to date")


if __name__ == "__main__":
    main()
