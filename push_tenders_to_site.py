"""
push_tenders_to_site.py  —  sends scraped tenders to the TenderRadarPK website.

HOW YOUR SCRAPER USES IT (inside your existing scraper, after it collects tenders):
    from push_tenders_to_site import push
    push([ {...tender dict...}, {...}, ... ])

Two secrets are needed (NEVER paste them into index.html):
    RADAR_SUPABASE_URL          e.g. https://abcdxyz.supabase.co
    RADAR_SERVICE_KEY           the "service_role" key (Supabase -> Project Settings -> API)
In GitHub: your repo -> Settings -> Secrets and variables -> Actions -> New repository secret.
"""
import os, json, re, urllib.request
from datetime import date, datetime

URL = os.environ["RADAR_SUPABASE_URL"].rstrip("/")
KEY = os.environ["RADAR_SERVICE_KEY"]

PROVINCE_FIX = {"kpk":"Khyber Pakhtunkhwa","khyber pakhtunkhwa":"Khyber Pakhtunkhwa","kp":"Khyber Pakhtunkhwa",
                "sindh":"Sindh","punjab":"Punjab","balochistan":"Balochistan","federal":"Federal","islamabad":"Islamabad"}

def to_date(v):
    """Accepts date, datetime or text like 2026-11-20 / 20/11/2026 / 20-Nov-2026 / Nov 30, 2026 02:15 PM."""
    if isinstance(v, datetime): return v.date().isoformat()
    if isinstance(v, date): return v.isoformat()
    s = re.sub(r"\s+", " ", str(v or "").strip())
    if not s: return None
    fmts = ("%Y-%m-%d","%Y-%m-%dT%H:%M:%S","%Y-%m-%d %H:%M:%S","%d/%m/%Y","%d-%m-%Y","%d-%b-%Y","%d %b %Y","%d %B %Y","%d.%m.%Y",
            "%b %d, %Y","%B %d, %Y","%b %d, %Y %I:%M %p","%B %d, %Y %I:%M %p","%d-%b-%Y %I:%M %p","%d/%m/%Y %I:%M %p","%d-%m-%Y %I:%M %p",
            "%d/%m/%Y %H:%M","%d-%b-%Y %H:%M","%Y-%m-%d %H:%M")
    for f in fmts:
        try: return datetime.strptime(s, f).date().isoformat()
        except ValueError: pass
    # last resort: find a date-looking piece inside the text
    for rx, f in ((r"[A-Za-z]{3,9} \d{1,2}, \d{4}", None), (r"\d{1,2}[-/ ][A-Za-z]{3,9}[-/ ]\d{4}", None), (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"), (r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", None)):
        m = re.search(rx, s)
        if m and m.group(0) != s:
            return to_date(m.group(0))
    return None

def clean(t):
    """Maps YOUR scraper's field names to the website's. Edit the right-hand names if yours differ."""
    closing = to_date(t.get("closing") or t.get("closing_date"))
    if not t.get("title") or not closing:
        return None                                   # skip rows without title or closing date
    prov = PROVINCE_FIX.get(str(t.get("province","")).strip().lower(), "Federal")
    src = t.get("source","")
    key = t.get("ref") or re.sub(r"\W+","", t["title"])[:40]
    return {
        "id": t.get("id") or f"{src}-{key}"[:80],
        "title": str(t["title"]).strip()[:300],
        "org": t.get("org") or t.get("department",""),
        "category": t.get("category") or "General",
        "province": prov,
        "city": t.get("city",""),
        "type": t.get("type") or "Goods",
        "source": src,
        "sector": t.get("sector") or "GOVERNMENT",
        "ref": t.get("ref",""),
        "published": to_date(t.get("published") or t.get("publish_date") or t.get("opening")),
        "closing": closing,
        "value": t.get("value",""),
        "fee": str(t.get("fee","")),
        "eligibility": t.get("eligibility",""),
        "docs": t.get("docs") or [],
        "source_url": t.get("source_url") or t.get("pdf_url") or t.get("link",""),
        "updated_at": datetime.utcnow().isoformat(),
    }

HDRS_BASE = {"Content-Type":"application/json", "Prefer":"resolution=merge-duplicates,return=minimal"}
hdrs = dict(HDRS_BASE, apikey=KEY)
if not KEY.startswith("sb_"):                 # old-style JWT keys also need the Authorization header
    hdrs["Authorization"] = f"Bearer {KEY}"

def push(tenders):
    rows = list({r["id"]: r for r in (clean(t) for t in tenders) if r}.values())   # one row per id (avoids database errors)
    sent = 0
    for i in range(0, len(rows), 200):                # send in batches of 200
        batch = rows[i:i+200]
        req = urllib.request.Request(
            f"{URL}/rest/v1/radar_tenders?on_conflict=id", data=json.dumps(batch).encode(), method="POST",
            headers=hdrs)
        urllib.request.urlopen(req, timeout=60).read()
        sent += len(batch)
    print(f"Pushed {sent} tenders to TenderRadarPK ({len(tenders)-len(rows)} skipped: missing title/closing date)")
    return sent

if __name__ == "__main__":      # quick self-test:  python push_tenders_to_site.py
    push([{"title":"Test tender from script","org":"Test Dept","province":"KPK","closing":"30-Dec-2026","source":"TEST","ref":"X1"}])
