"""NCSS Kellogg Soil Survey Laboratory characterization database.

The only federal path to MEASURED soil organic carbon on identified pedons over
decades -- as opposed to RaCA, which is one national snapshot with no second
visit, and SSURGO, whose values are mapped and modelled rather than sampled.
Lal's lens identified this as the binding gap in the soil-carbon argument.

It is not scrubbed and never was. It is simply behind an ASP.NET WebForms
postback: the download "links" are __doPostBack calls, so a crawler that follows
hrefs finds nothing and the database never appears in any mirror. Reaching it
means replaying the form with its __VIEWSTATE, which is what this does.
"""
import re, sys, time
sys.path.insert(0, "scripts")
from fetchlib import session, record, utcstamp, today, sha256_file, append_manifest, RAW

BASE = "https://ncsslabdatamart.sc.egov.usda.gov/database_download.aspx"
AGENCY, DATASET = "usda-nrcs", "ncss-lab-characterization"

def hidden_fields(html):
    """ASP.NET carries form state in hidden inputs; the postback is invalid without them."""
    out = {}
    for m in re.finditer(r'<input[^>]*type="hidden"[^>]*>', html, re.I):
        tag = m.group(0)
        n = re.search(r'name="([^"]+)"', tag)
        v = re.search(r'value="([^"]*)"', tag)
        if n:
            out[n.group(1)] = v.group(1) if v else ""
    return out

def download(target, filename, notes):
    s = session()
    r = s.get(BASE, timeout=180)
    if r.status_code != 200:
        print(f"  [FAIL] landing page HTTP {r.status_code}"); return
    form = hidden_fields(r.text)
    form["__EVENTTARGET"] = target
    form["__EVENTARGUMENT"] = ""
    print(f"  posting {target} with {len(form)} form fields "
          f"(viewstate {len(form.get('__VIEWSTATE',''))} bytes)")

    dest_dir = RAW / AGENCY / DATASET / today(); dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  [cached] {dest.name}"); return

    with s.post(BASE, data=form, stream=True, timeout=3600,
                headers={"Referer": BASE, "Content-Type": "application/x-www-form-urlencoded"}) as resp:
        ctype = resp.headers.get("content-type", "")
        if resp.status_code != 200 or "text/html" in ctype:
            print(f"  [FAIL] HTTP {resp.status_code} type={ctype[:40]} — postback rejected")
            return
        tmp = dest.with_suffix(dest.suffix + ".part")
        n = 0
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_content(1 << 20):
                if chunk:
                    fh.write(chunk); n += len(chunk)
                    if n % (100 << 20) < (1 << 20):
                        print(f"    {n/1e6:,.0f} MB", flush=True)
        tmp.replace(dest)
    sha = sha256_file(dest)
    record({"url": f"{BASE}#{target}", "retrieved_at": utcstamp(), "sha256": sha,
            "bytes": dest.stat().st_size, "agency": AGENCY, "dataset": DATASET,
            "filename": filename, "content_type": ctype, "http_status": 200,
            "license": "US Government Work (17 USC 105)", "notes": notes})
    append_manifest(DATASET, sha, dest)
    print(f"  [ok] {dest.stat().st_size:,} bytes  {filename}")

if __name__ == "__main__":
    download("btnDownloadSQLiteFile", "ncss_characterization.sqlite",
             "Entire NCSS Characterization Database (Kellogg Soil Survey Laboratory) -- "
             "measured pedon data: organic carbon, bulk density, CEC, texture, pH. "
             "Retrieved by replaying the ASP.NET postback; no direct URL exists.")
