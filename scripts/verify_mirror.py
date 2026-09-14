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
    """PDFs are checked exhaustively; other formats are sampled per directory."""
    """Open a sample of archives/tables per directory and confirm they parse."""
    problems = []
    checked = 0
    by_dir = defaultdict(list)
    for p in (ROOT / "data" / "raw").rglob("*"):
        if p.is_file() and p.stat().st_size > 0:
            by_dir[p.parent].append(p)
    for d, files in sorted(by_dir.items()):
        sample = sorted(files)[:sample_per_dir]
        # Always include every PDF -- see the truncation note below.
        sample += [f for f in sorted(files) if f.suffix.lower() == ".pdf" and f not in sample]
        for p in sample:
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
                    b = p.read_bytes()
                    if b[:5] != b"%PDF-":
                        problems.append((p, "not a PDF")); continue
                    # A header-only check passes truncated PDFs. Two NRI files
                    # arrived cut at exactly 5 MiB -- the Wayback captures are
                    # themselves incomplete -- and looked fine until the missing
                    # trailing %%EOF was checked. Size alone is not a signal
                    # either; check the terminator.
                    if b"%%EOF" not in b[-4096:]:
                        problems.append((p, f"truncated PDF: no trailing %%EOF ({len(b):,} bytes)"))
                        continue
                    checked += 1
            except Exception as e:
                problems.append((p, f"{type(e).__name__}: {e}"))
    print(f"\nstructure: {checked} files opened cleanly, {len(problems)} problems")
    for p, why in problems[:40]:
        print(f"  BAD  {p.relative_to(ROOT)}: {why}")
    return problems

def inventory():
    """Summarise the mirror from the provenance ledger.

    The ledger is append-only and may carry rows from more than one machine, so
    counting rows over-reports: a file retrieved on two machines appears twice.
    Identity here is the CONTENT (sha256), not the row.

    Failures are likewise reported net. A file that failed on one route and
    later succeeded on another -- NRCS via the archive, then direct via wget --
    is not a gap, and counting it as one hides the real gaps behind noise.
    """
    prov = ROOT / "data" / "provenance.csv"
    ok_sha = defaultdict(dict)       # dataset -> sha -> bytes
    ok_names = defaultdict(set)      # dataset -> filenames that ever succeeded
    fail_names = defaultdict(set)    # dataset -> filenames that ever failed
    wayback = defaultdict(set)       # dataset -> sha retrieved via the archive

    with open(prov) as fh:
        for row in csv.DictReader(fh):
            key = f"{row['agency']}/{row['dataset']}"
            name = row.get("filename", "")
            if str(row["http_status"]) == "200" and row.get("sha256"):
                ok_sha[key][row["sha256"]] = int(row["bytes"] or 0)
                ok_names[key].add(name)
                if "VIA_WAYBACK" in row.get("notes", ""):
                    wayback[key].add(row["sha256"])
            else:
                fail_names[key].add(name)

    print(f"\n{'dataset':<44} {'files':>7} {'size':>12} {'unmet':>7} {'archive':>8}")
    print("-" * 82)
    tn = tb = tf = 0
    for key in sorted(set(ok_sha) | set(fail_names)):
        n = len(ok_sha[key])
        b = sum(ok_sha[key].values())
        # Only count a failure if that filename never succeeded by any route.
        unmet = len(fail_names[key] - ok_names[key])
        tn += n; tb += b; tf += unmet
        print(f"{key:<44} {n:>7,} {human(b):>12} {unmet:>7} {len(wayback[key]):>8}")
    print("-" * 82)
    print(f"{'TOTAL':<44} {tn:>7,} {human(tb):>12} {tf:>7}")
    print("\n(files/size are distinct by sha256; 'unmet' counts only filenames "
          "that never succeeded by any route; 'archive' = retrieved via Internet Archive)")


if __name__ == "__main__":
    inventory()
    validate_structure()
    verify_checksums()
