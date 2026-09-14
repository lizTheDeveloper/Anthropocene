"""Verify the mechanism behind the empty soil-toxicity record, from primary law.

The ECOTOX audit concludes the federal record is near-empty on non-target soil
organisms not because the science is hard but because the data requirement does
not exist. 40 CFR 158.630 is the table of terrestrial and aquatic non-target
organism data requirements for pesticide registration, so the claim is directly
checkable rather than a matter of interpretation.

Note on fetching: this eCFR endpoint refuses requests that do not permit
response compression (HTTP 406). Without --compressed the body is an error
message, and a naive keyword scan over it returns zero hits for EVERY term --
which reads exactly like "no soil tests required" while actually meaning
"the document was never retrieved". Fetch failures must not be allowed to
masquerade as findings.
"""
import html, re, subprocess, sys

URL = ("https://www.ecfr.gov/api/versioner/v1/full/2026-09-09/title-40.xml?part=158")
xml = subprocess.run(["curl", "-sS", "-m", "180", "--compressed",
                      "-H", "Accept: application/xml", "-H", "User-Agent: Mozilla/5.0", URL],
                     capture_output=True, text=True).stdout
if len(xml) < 5000 or "158.630" not in xml:
    sys.exit(f"FETCH FAILED - refusing to report keyword counts. Body: {xml[:200]}")

m = re.search(r'<DIV8[^>]*N="158\.630"[^>]*>(.*?)</DIV8>', xml, re.S)
body = m.group(1)
heading = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", re.search(r"<HEAD>(.*?)</HEAD>", body, re.S).group(1)))).strip()
txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body)))

print(f"{heading}\n({len(txt):,} chars of table text)\n")
REQUIRED = ["honey bee", "avian", "fish", "aquatic invertebrate"]
ABSENT = ["earthworm", "soil microorganism", "soil invertebrate",
          "nitrogen transformation", "Collembola", "springtail", "mycorrhiz"]
print("organisms WITH a data requirement:")
for t in REQUIRED:
    print(f"   {t:<24} {len(re.findall(t, txt, re.I)):>3} mention(s)")
print("\nsoil organisms:")
soil_hits = 0
for t in ABSENT:
    n = len(re.findall(t, txt, re.I)); soil_hits += n
    print(f"   {t:<24} {n:>3} mention(s)")
print(f"\nRESULT: {soil_hits} mentions of any soil organism in the non-target data requirements table.")
print("US registration requires honey bee, avian, fish and aquatic invertebrate testing.")
print("EU Reg. 283/2013 by contrast requires OECD 222 (earthworm), 232 (Collembola), 216 (soil N transformation).")
sys.exit(0 if soil_hits == 0 else 1)
