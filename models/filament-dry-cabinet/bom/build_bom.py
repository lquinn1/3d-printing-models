#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build BOM.csv and BOM.md from bom_source.csv (one cabinet, as built).

bom_source.csv is the single place to edit. Run:  python3 bom/build_bom.py
--sheet-json prints the rows for the Sheets artifact (formulas included).
"""
import csv, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "bom_source.csv"
FIRST_ROW = 7  # sheet row of the first item

def load():
    with open(SRC, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def num(s):
    return float(s) if s not in ("", None) else None

def packs(r):
    return math.ceil(round(num(r["Qty"]) / num(r["Pack size"]), 6))

def ext(r):
    p = num(r["Price per pack"])
    return None if p is None else round(packs(r) * p, 2)

COLS = ["Category", "Item", "Description", "Qty needed", "Unit", "Pack size",
        "Packs to buy", "Price / pack (USD)", "Ext price (USD)", "Supplier", "Link",
        "Alt supplier", "Alt link", "Part #", "Used in", "Status", "Actual cost (USD)",
        "Test result / notes"]

def write_csv(rows):
    with open(HERE.parent / "BOM.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([r["Category"], r["Item"], r["Description"], r["Qty"], r["Unit"],
                        r["Pack size"], packs(r), r["Price per pack"],
                        "" if ext(r) is None else f"{ext(r):.2f}", r["Supplier"], r["Link"],
                        r["Alt supplier"], r["Alt link"], r["Part #"], r["Used in"], r["Status"], "", r["Notes"]])

def write_md(rows):
    total = sum(ext(r) or 0 for r in rows)
    out = ["# Filament dry cabinet: as-built bill of materials",
           "",
           "One cabinet, spec v0.22. This is the parts list for the first (test) build: "
           "it records what is bought, what fits and what changed.",
           "",
           f"**Estimated total: ${total:,.2f}** (USD, prices checked 2026-11-24, before tax and shipping). "
           "Prices marked *estimate* in the notes are not confirmed. Every line has a second source; "
           "where no product page was confirmed, the link is a search for that exact part on the supplier's site. "
           "No auction-site links.",
           "",
           "The live copy, with status, actual cost and test columns to fill in, is the Sheets artifact. "
           "This file is generated from [`bom/bom_source.csv`](bom/bom_source.csv) by "
           "`python3 bom/build_bom.py`; edit the source, not this file.",
           "",
           "**FIT items** (measure the part when it arrives, then update `cad/params.py`): "
           "PTC heater (HEATER 80 × 52 × 30, and its surface temperature with the fan off), IEC inlet (IEC_CUT 47.5 × 27.5, 1.6 mm panel), "
           "PN5180 board (NFC_BOARD 65 × 40), display stack (TFT_STACK 4.5).",
           ""]
    cat = None
    for r in rows:
        if r["Category"] != cat:
            cat = r["Category"]
            out += ["", f"## {cat}", "",
                    "| Item | Description | Qty | Buy | $/pack | Ext $ | Supplier | Alt source | Part # | Used in | Status | Notes |",
                    "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        sup = f"[{r['Supplier']}]({r['Link']})" if r["Link"] else r["Supplier"]
        alt = f"[{r['Alt supplier']}]({r['Alt link']})" if r["Alt link"] else r["Alt supplier"]
        p = r["Price per pack"]
        e = ext(r)
        buy = f"{packs(r)} × {r['Pack size']}" if r["Pack size"] != "1" else str(packs(r))
        cells = [r["Item"], r["Description"], f"{r['Qty']} {r['Unit']}", buy,
                 p or "–", "–" if e is None else f"{e:.2f}", sup, alt, r["Part #"],
                 r["Used in"], r["Status"], r["Notes"]]
        out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    out.append("")
    (HERE.parent / "BOM.md").write_text("\n".join(out), encoding="utf-8")
    return total

def sheet_rows(rows):
    res = []
    for i, r in enumerate(rows):
        n = FIRST_ROW + i
        price = num(r["Price per pack"])
        res.append([r["Category"], r["Item"], r["Description"], num(r["Qty"]), r["Unit"],
                    num(r["Pack size"]), f"=ROUNDUP(D{n}/F{n},0)",
                    price, f'=IF(H{n}="","",G{n}*H{n})', r["Supplier"],
                    r["Link"] or None, r["Alt supplier"] or None, r["Alt link"] or None,
                    r["Part #"] or None, r["Used in"], r["Status"], None, r["Notes"] or None])
    return res

if __name__ == "__main__":
    rows = load()
    if "--sheet-json" in sys.argv:
        print(json.dumps(sheet_rows(rows), ensure_ascii=False))
    else:
        write_csv(rows)
        print(f"{len(rows)} lines, estimated total ${write_md(rows):,.2f}")
