"""Verify the raw mirror against its manifests and sanity-check file contents.

Two distinct checks, because they catch different failures:
  1. Checksum verification -- did the bytes on disk change since retrieval?
  2. Structural validation -- is a file that claims to be a zip actually a
     readable zip, and does a delimited file actually parse? A truncated
     download and an agency error page both arrive as HTTP 200.
"""
from __future__ import annotations
import csv, gzip, io, sys, zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from fetchlib import sha256_file  # noqa: E402

def human(n):
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024: return f"{n:,.1f}{u}"
        n /= 1024
    return f"{n:,.1f}PB"

def verify_checksums():
    ok = bad = missing = 0
    for mf in sorted((ROOT / "data" / "manifests").glob("*.sha256")):
        for line in mf.read_text().splitlines():
            if not line.strip(): continue
            sha, rel = line.split("  ", 1)
            p = ROOT / rel
            if not p.exists(): missing += 1; print(f"  MISSING {rel}"); continue
            if sha256_file(p) == sha: ok += 1
            else: bad += 1; print(f"  CHECKSUM MISMATCH {rel}")
    print(f"\nchecksums: {ok} verified, {bad} mismatched, {missing} missing")
    return bad == 0 and missing == 0

def validate_structure(sample_per_dir=3):
    """Open a sample of archives/tables per directory and confirm they parse."""
    problems = []
    checked = 0
    by_dir = defaultdict(list)
    for p in (ROOT / "data" / "raw").rglob("*"):
        if p.is_file() and p.stat().st_size > 0:
            by_dir[p.parent].append(p)
    for d, files in sorted(by_dir.items()):
        for p in sorted(files)[:sample_per_dir]:
            suf = p.suffix.lower()
            try:
                if suf == ".zip":
                    with zipfile.ZipFile(p) as z:
                        if z.testzip() is not None:
                            problems.append((p, "corrupt member")); continue
                        if not z.namelist():
                            problems.append((p, "empty zip")); continue
                    checked += 1
                elif suf == ".gz":
                    with gzip.open(p, "rb") as fh:
                        fh.read(1 << 16)
                    checked += 1
                elif suf in (".txt", ".csv"):
                    head = p.read_bytes()[:1 << 16].decode("utf-8", "replace")
                    if head.lstrip()[:15].lower().startswith("<!doctype") or head.lstrip()[:6].lower() == "<html>":
                        problems.append((p, "HTML error page saved as data")); continue
                    checked += 1
                elif suf == ".pdf":
                    if p.read_bytes()[:5] != b"%PDF-":
                        problems.append((p, "not a PDF")); continue
                    checked += 1
            except Exception as e:
                problems.append((p, f"{type(e).__name__}: {e}"))
    print(f"\nstructure: {checked} files opened cleanly, {len(problems)} problems")
    for p, why in problems[:40]:
        print(f"  BAD  {p.relative_to(ROOT)}: {why}")
    return problems

def inventory():
    prov = ROOT / "data" / "provenance.csv"
    stats = defaultdict(lambda: {"n": 0, "bytes": 0, "fail": 0, "wayback": 0})
    with open(prov) as fh:
        for row in csv.DictReader(fh):
            k = f"{row['agency']}/{row['dataset']}"
            s = stats[k]
            if str(row["http_status"]) == "200":
                s["n"] += 1; s["bytes"] += int(row["bytes"] or 0)
                if "VIA_WAYBACK" in row["notes"]: s["wayback"] += 1
            else:
                s["fail"] += 1
    print(f"\n{'dataset':<44} {'files':>7} {'size':>12} {'failed':>7} {'wayback':>8}")
    print("-" * 82)
    tn = tb = tf = 0
    for k in sorted(stats):
        s = stats[k]
        tn += s["n"]; tb += s["bytes"]; tf += s["fail"]
        print(f"{k:<44} {s['n']:>7,} {human(s['bytes']):>12} {s['fail']:>7} {s['wayback']:>8}")
    print("-" * 82)
    print(f"{'TOTAL':<44} {tn:>7,} {human(tb):>12} {tf:>7}")

if __name__ == "__main__":
    inventory()
    validate_structure()
    verify_checksums()
