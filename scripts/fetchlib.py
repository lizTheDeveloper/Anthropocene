"""
Provenance-preserving fetcher for federal data acquisition.

Design premise (see docs/PROVENANCE.md): every artifact we may later cite must
exist in our own custody with (a) the originating URL, (b) a retrieval
timestamp, and (c) a SHA-256 of the exact bytes the agency served. Agencies
have removed, altered, and silently re-scoped these datasets; our copy is the
one that survives.

Bytes are never transformed on the way in. Unzipping, parsing, and cleaning all
happen downstream of the raw mirror, so the checksum always refers to the
file as served.
"""
from __future__ import annotations

import csv
import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFESTS = ROOT / "data" / "manifests"
PROVENANCE = ROOT / "data" / "provenance.csv"

PROV_FIELDS = [
    "url", "retrieved_at", "sha256", "bytes", "agency", "dataset",
    "filename", "content_type", "http_status", "license", "notes",
]

# Several agency WAFs (FDA/Akamai, USGS) reject requests that carry only a
# User-Agent. A complete browser header set gets through where a partial one
# does not, so we send one by default.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Chromium";v="125", "Not.A/Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


def utcstamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update(BROWSER_HEADERS)
    return s


def _filename_for(url: str, resp: requests.Response | None) -> str:
    disp = (resp.headers.get("content-disposition") or "") if resp else ""
    if "filename=" in disp:
        name = disp.split("filename=")[-1].strip().strip('";\' ')
        if name:
            return unquote(name)
    name = unquote(os.path.basename(urlparse(url).path))
    return name or "index.html"


def record(row: dict) -> None:
    """Append one row to the global provenance ledger."""
    new = not PROVENANCE.exists() or PROVENANCE.stat().st_size == 0
    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROVENANCE, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=PROV_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in PROV_FIELDS})


def append_manifest(dataset: str, sha: str, path: Path) -> None:
    """Write a sha256sum-compatible line so `sha256sum -c` can verify the mirror."""
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    rel = path.relative_to(ROOT)
    line = f"{sha}  {rel}\n"
    mf = MANIFESTS / f"{dataset}.sha256"
    if mf.exists() and line in mf.read_text():
        return
    with open(mf, "a") as fh:
        fh.write(line)


def fetch(
    url: str,
    agency: str,
    dataset: str,
    *,
    filename: str | None = None,
    subdir: str = "",
    license: str = "US Government Work (17 USC 105), public domain unless noted",
    notes: str = "",
    retries: int = 4,
    timeout: int = 180,
    sess: requests.Session | None = None,
    force: bool = False,
    params: dict | None = None,
) -> dict:
    """Download one URL into the raw mirror and record its provenance.

    Returns a dict with status/path/sha256. Never raises on HTTP failure; a
    failed acquisition is recorded in the ledger too, because "we tried and
    the agency refused" is itself evidence worth keeping.
    """
    sess = sess or session()
    dest_dir = RAW / agency / dataset / today() / subdir if subdir else RAW / agency / dataset / today()
    dest_dir.mkdir(parents=True, exist_ok=True)

    last_err = ""
    for attempt in range(retries + 1):
        try:
            with sess.get(url, stream=True, timeout=timeout, allow_redirects=True, params=params) as r:
                if r.status_code in RETRY_STATUS and attempt < retries:
                    last_err = f"HTTP {r.status_code}"
                    time.sleep(2 ** (attempt + 1))
                    continue
                name = filename or _filename_for(r.url, r)
                dest = dest_dir / name
                if r.status_code != 200:
                    record({
                        "url": url, "retrieved_at": utcstamp(), "sha256": "",
                        "bytes": 0, "agency": agency, "dataset": dataset,
                        "filename": name, "content_type": r.headers.get("content-type", ""),
                        "http_status": r.status_code, "license": license,
                        "notes": f"FAILED: {notes}".strip(),
                    })
                    return {"ok": False, "status": r.status_code, "url": url, "path": None}

                if dest.exists() and not force:
                    sha = sha256_file(dest)
                    return {"ok": True, "status": 200, "url": url, "path": dest,
                            "sha256": sha, "bytes": dest.stat().st_size, "cached": True}

                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        if chunk:
                            fh.write(chunk)
                tmp.replace(dest)

                sha = sha256_file(dest)
                size = dest.stat().st_size
                record({
                    "url": url, "retrieved_at": utcstamp(), "sha256": sha,
                    "bytes": size, "agency": agency, "dataset": dataset,
                    "filename": name, "content_type": r.headers.get("content-type", ""),
                    "http_status": 200, "license": license, "notes": notes,
                })
                append_manifest(dataset, sha, dest)
                return {"ok": True, "status": 200, "url": url, "path": dest,
                        "sha256": sha, "bytes": size, "cached": False}
        except Exception as e:  # network flake, TLS reset, truncated transfer
            last_err = f"{type(e).__name__}: {e}"
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue

    record({
        "url": url, "retrieved_at": utcstamp(), "sha256": "", "bytes": 0,
        "agency": agency, "dataset": dataset, "filename": filename or "",
        "content_type": "", "http_status": "ERR", "license": license,
        "notes": f"FAILED after {retries} retries: {last_err}",
    })
    return {"ok": False, "status": "ERR", "url": url, "path": None, "error": last_err}


def fetch_all(items, agency, dataset, *, pause=0.7, **kw):
    """Fetch a list of (url) or (url, filename) items, politely paced."""
    sess = kw.pop("sess", None) or session()
    out = []
    for it in items:
        url, fname = (it, None) if isinstance(it, str) else (it[0], it[1])
        res = fetch(url, agency, dataset, filename=fname, sess=sess, **kw)
        flag = "ok " if res["ok"] else "FAIL"
        size = res.get("bytes", 0)
        print(f"  [{flag}] {size:>12,}  {url.split('/')[-1][:70]}", flush=True)
        out.append(res)
        time.sleep(pause)
    return out


# ---------------------------------------------------------------------------
# Archive fallbacks
#
# FDA's edge (Akamai) returns 401 to this network for every /media/ download,
# so those bytes cannot be pulled from the agency directly. The Internet
# Archive's "id_" modifier replays the ORIGINAL unmodified response body, so
# the artifact is byte-identical to what FDA served at capture time.
#
# The provenance implication has to be stated, not glossed: the checksum then
# attests to an archived copy captured at a known timestamp by a third party,
# not to a live agency fetch by us. For a contested citation that is arguably
# the stronger record -- an independent custodian with its own timestamp -- but
# it is a different claim, so every such row is tagged VIA_WAYBACK with the
# capture timestamp.
# ---------------------------------------------------------------------------

CDX = "https://web.archive.org/cdx/search/cdx"


class CDXLookupFailed(Exception):
    """The capture index could not be consulted -- distinct from 'no captures exist'.

    Conflating the two is how a transient rate-limit gets written into the
    provenance ledger as a permanent 'NO_SNAPSHOT', which reads as 'the archive
    does not have this file' and is simply false. The distinction has to survive
    all the way to the ledger.
    """


def wayback_snapshots(url: str, sess: requests.Session | None = None,
                      limit: int = 40, retries: int = 5) -> list[dict]:
    """Return successful captures of `url`, newest first.

    Returns [] only when the index was successfully consulted and genuinely has
    no 200-status captures. Raises CDXLookupFailed if the index could not be
    reached -- archive.org rate-limits aggressively under parallel load and
    answers with 4xx/5xx or a dropped connection.
    """
    sess = sess or session()
    last = ""
    for attempt in range(retries):
        try:
            r = sess.get(CDX, params={
                "url": url, "output": "json", "limit": limit,
                "filter": "statuscode:200", "collapse": "digest",
            }, timeout=180)
            if r.status_code != 200:
                last = f"HTTP {r.status_code}"
                time.sleep(4 * (attempt + 1))
                continue
            body = r.text.strip()
            if not body:
                return []          # consulted successfully; nothing indexed
            rows = r.json()
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(4 * (attempt + 1))
            continue
        if not rows or len(rows) < 2:
            return []
        cols = rows[0]
        snaps = [dict(zip(cols, row)) for row in rows[1:]]
        snaps.sort(key=lambda d: d.get("timestamp", ""), reverse=True)
        return snaps
    raise CDXLookupFailed(f"CDX unreachable after {retries} attempts: {last}")


def fetch_via_wayback(url: str, agency: str, dataset: str, *,
                      filename: str | None = None, subdir: str = "",
                      notes: str = "", sess: requests.Session | None = None,
                      timeout: int = 900, pause: float = 3.0, **kw) -> dict:
    """Fetch original bytes for `url` from the Internet Archive."""
    sess = sess or session()
    try:
        snaps = wayback_snapshots(url, sess=sess)
    except CDXLookupFailed as e:
        # Report the lookup failure as itself, never as "no capture exists".
        record({
            "url": url, "retrieved_at": utcstamp(), "sha256": "", "bytes": 0,
            "agency": agency, "dataset": dataset, "filename": filename or "",
            "content_type": "", "http_status": "CDX_LOOKUP_FAILED",
            "license": "US Government Work (17 USC 105)",
            "notes": f"RETRYABLE: capture index unreachable ({e}). {notes}".strip(),
        })
        return {"ok": False, "status": "CDX_LOOKUP_FAILED", "url": url, "path": None}
    if not snaps:
        record({
            "url": url, "retrieved_at": utcstamp(), "sha256": "", "bytes": 0,
            "agency": agency, "dataset": dataset, "filename": filename or "",
            "content_type": "", "http_status": "NO_SNAPSHOT",
            "license": "US Government Work (17 USC 105)",
            "notes": f"FAILED: no Wayback capture found. {notes}".strip(),
        })
        return {"ok": False, "status": "NO_SNAPSHOT", "url": url, "path": None}

    for snap in snaps[:4]:
        ts = snap["timestamp"]
        wb = f"https://web.archive.org/web/{ts}id_/{url}"
        res = fetch(wb, agency, dataset, filename=filename, subdir=subdir,
                    sess=sess, timeout=timeout, retries=2,
                    notes=(f"VIA_WAYBACK capture={ts} original_url={url} "
                           f"(agency edge returns 401 to this network). {notes}").strip(),
                    **kw)
        if res["ok"] and res.get("bytes", 0) > 0:
            res["capture"] = ts
            return res
        time.sleep(pause)
    return {"ok": False, "status": "ALL_SNAPSHOTS_FAILED", "url": url, "path": None}


# ---------------------------------------------------------------------------
# wget transport
#
# NRCS (www.nrcs.usda.gov) accepts wget but not curl or python-requests from
# the same host and IP: curl's TLS handshake completes and the HTTP/2 stream
# opens, then the connection dies, and requests times out reading the response.
# Chrome succeeds too, so the discriminator is the TLS/ALPN fingerprint rather
# than the address. wget presents a different one and is served normally.
#
# Worth having as a first-class transport rather than a one-off: it turns a set
# of files we could otherwise only get as third-party archive copies into
# direct-from-agency retrievals, which is a strictly stronger provenance claim.
# ---------------------------------------------------------------------------

import shutil
import subprocess


def fetch_via_wget(url: str, agency: str, dataset: str, *,
                   filename: str | None = None, subdir: str = "",
                   notes: str = "", timeout: int = 900, tries: int = 4,
                   license: str = "US Government Work (17 USC 105), public domain unless noted",
                   force: bool = False) -> dict:
    """Download one URL with wget and record its provenance."""
    if not shutil.which("wget"):
        return {"ok": False, "status": "NO_WGET", "url": url, "path": None}

    dest_dir = RAW / agency / dataset / today() / subdir if subdir else RAW / agency / dataset / today()
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = filename or _filename_for(url, None)
    dest = dest_dir / name

    if dest.exists() and not force:
        sha = sha256_file(dest)
        return {"ok": True, "status": 200, "url": url, "path": dest,
                "sha256": sha, "bytes": dest.stat().st_size, "cached": True}

    tmp = dest.with_suffix(dest.suffix + ".part")
    proc = subprocess.run(
        ["wget", "-q", f"--timeout={timeout}", f"--tries={tries}", "-O", str(tmp), url],
        capture_output=True, text=True,
    )
    if proc.returncode != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        record({
            "url": url, "retrieved_at": utcstamp(), "sha256": "", "bytes": 0,
            "agency": agency, "dataset": dataset, "filename": name,
            "content_type": "", "http_status": f"WGET_{proc.returncode}",
            "license": license,
            "notes": f"FAILED (wget): {proc.stderr.strip()[:200]} {notes}".strip(),
        })
        return {"ok": False, "status": f"WGET_{proc.returncode}", "url": url, "path": None}

    tmp.replace(dest)
    sha = sha256_file(dest)
    size = dest.stat().st_size
    record({
        "url": url, "retrieved_at": utcstamp(), "sha256": sha, "bytes": size,
        "agency": agency, "dataset": dataset, "filename": name,
        "content_type": "", "http_status": 200, "license": license,
        "notes": f"direct from agency via wget. {notes}".strip(),
    })
    append_manifest(dataset, sha, dest)
    return {"ok": True, "status": 200, "url": url, "path": dest,
            "sha256": sha, "bytes": size, "cached": False}
