"""
sync_from_scraper.py  —  copies the tenders your EXISTING scraper already collected
into the TenderRadarPK website (table: radar_tenders).

Put this file in the SAME GitHub repo as your scraper (repo: tender-portal),
next to push_tenders_to_site.py. The workflow file sync-to-site.yml runs it for you.

Secrets needed (GitHub repo -> Settings -> Secrets and variables -> Actions):
  SOURCE_SUPABASE_URL   Project URL of the Supabase project where your scraper SAVES tenders
  SOURCE_KEY            a key that can READ that table (the Secret key is fine; it stays in GitHub)
  RADAR_SUPABASE_URL    Project URL of tenderradarpk  (same as above if it is the same project)
  RADAR_SERVICE_KEY     Secret key (sb_secret_...) of tenderradarpk
Optional setting (Variables or just edit below): SOURCE_TABLE  (default: tenders)
"""
import os, json, re, urllib.request, urllib.parse
from datetime import date

SRC_URL   = os.environ["SOURCE_SUPABASE_URL"].rstrip("/")
SRC_KEY   = os.environ["SOURCE_KEY"]
SRC_TABLE = (os.environ.get("SOURCE_TABLE") or "tenders").strip()

# For each website field, the column names your scraper table might use (first one found is used).
# If a column in YOUR table has another name, just add it to the right list.
CANDIDATES = {
  "title":    ["title","tender_title","name","subject","description"],
  "org":      ["department","organization","organisation","org","procuring_agency","agency","authority"],
  "city":     ["city","location","district"],
  "province": ["province","region","state"],
  "source":   ["source","portal","newspaper","site","origin"],
  "ref":      ["ref","reference","reference_no","tender_no","tender_number","ref_no","number"],
  "published":["opening_date","published","publish_date","published_date","date_published","posted_date","created_at"],
  "closing":  ["closing_date","closing","deadline","due_date","end_date","submission_date","bid_closing"],
  "fee":      ["fee","tender_fee","document_fee","bid_fee"],
  "value":    ["value","estimated_value","estimated_cost","amount","cost"],
  "source_url":["pdf_url","pdf_link","file_url","link","url","document_url","image_url","source_url"],
  "type":     ["type","procurement_type","category_type"],
  "category": ["category","sector","tender_category"],
}

# Keyword -> website category (so the Match Score works). Add your own words as needed.
CATEGORY_WORDS = [
  ("IT & Software",            r"\b(?:software|computer|laptop|server|network|website|erp|cctv|printer|digital|hardware|licen[cs]e)s?\b"),
  ("Construction",             r"\b(?:construction|road|bridge|building|rehabilitation|repair|renovation|civil|pavement|drain|sewerage|water supply|boundary wall|carpeting)s?\b"),
  ("Engineering",              r"\b(?:engineering|mechanical|plant|machinery|boiler|tube ?well|pump|survey|design|consultan)s?\b"),
  ("Medical & Healthcare",     r"\b(?:medical|medicine|hospital|surgical|health|pharma|drug|laborator|diagnostic|ambulance|vaccine|dental)s?\b"),
  ("Food & Catering",          r"\b(?:food|catering|ration|meal|dietary|kitchen|grocery|cooking)s?\b"),
  ("Security Services",        r"\b(?:security guard|security service|security|surveillance|guards)s?\b"),
  ("Electrical",               r"\b(?:electric|solar|transformer|cable|generator|inverter|lighting|led|ups|power)s?\b"),
  ("Logistics & Transportation",r"\b(?:transport|vehicle|vehicles|car|bus|truck|fuel|petrol|diesel|lubricant|logistic|courier|tyre|tire)s?\b"),
  ("Cleaning & Janitorial",    r"\b(?:janitorial|cleaning|sweeping|sanitation|waste|garbage|hygiene|housekeeping)s?\b"),
  ("Office Supplies",          r"\b(?:stationery|furniture|office|paper|printing|toner|cartridge|book|uniform)s?\b"),
]
def guess_category(text):
    t = " " + text.lower() + " "
    for cat, rx in CATEGORY_WORDS:
        if re.search(rx, t): return cat
    return "General"

def guess_type(text, given):
    if given and given.strip().title() in ("Goods","Services","Works","Consultancy"): return given.strip().title()
    t = text.lower()
    if re.search(r"construction|road|bridge|rehabilitation|renovation|repair|civil|building|sewerage|pavement", t): return "Works"
    if re.search(r"consultan|design|survey|feasibility|audit", t): return "Consultancy"
    if re.search(r"service|janitorial|cleaning|security|catering|hiring|maintenance|transport", t): return "Services"
    return "Goods"

def pick(row, field):
    for c in CANDIDATES[field]:
        if c in row and row[c] not in (None, "", []):
            return row[c]
    return ""

def list_tables(hdrs):
    """Asks Supabase which tables exist, so we can tell you the right name."""
    try:
        req = urllib.request.Request(f"{SRC_URL}/rest/v1/", headers=hdrs)
        spec = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return sorted((spec.get("definitions") or {}).keys())
    except Exception as e:
        return [f"(could not list tables: {e})"]

def fetch_all():
    rows, start, page = [], 0, 1000
    hdrs = {"apikey": SRC_KEY}
    if not SRC_KEY.startswith("sb_"): hdrs["Authorization"] = f"Bearer {SRC_KEY}"
    while start < 20000:
        req = urllib.request.Request(f"{SRC_URL}/rest/v1/{urllib.parse.quote(SRC_TABLE)}?select=*",
              headers=dict(hdrs, Range=f"{start}-{start+page-1}", **{"Range-Unit":"items"}))
        try:
            chunk = json.loads(urllib.request.urlopen(req, timeout=60).read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:300]
            print(f"\n*** Supabase answered HTTP {e.code} when reading table '{SRC_TABLE}' at {SRC_URL}")
            print("*** Details:", body)
            print("*** Tables that exist in that project:", ", ".join(list_tables(hdrs)))
            print("*** FIX: set the secret/variable SOURCE_TABLE to one of those names (or fix SOURCE_SUPABASE_URL).\n")
            raise SystemExit(1)
        rows += chunk
        if len(chunk) < page: break
        start += page
    return rows

def convert(row):
    title = str(pick(row,"title")).strip()
    text = title + " " + str(pick(row,"org"))
    srcname = str(pick(row,"source")) or "Scraper"
    ref = str(pick(row,"ref"))
    slug = re.sub(r"\W+", "", title)[:20]
    return {
        "id": f"{srcname}-{ref or row.get('id','')}-{slug}"[:80],
        "title": title, "org": str(pick(row,"org")), "city": str(pick(row,"city")),
        "province": str(pick(row,"province")) or "Federal",
        "source": srcname, "ref": ref,
        "published": pick(row,"published"), "closing": pick(row,"closing"),
        "fee": pick(row,"fee"), "value": pick(row,"value") or "Not disclosed",
        "source_url": pick(row,"source_url"),
        "category": pick(row,"category") if str(pick(row,"category")) in [c for c,_ in CATEGORY_WORDS] else guess_category(text),
        "type": guess_type(text, str(pick(row,"type"))),
        "sector": "GOVERNMENT",
    }

if __name__ == "__main__":
    from push_tenders_to_site import push
    rows = fetch_all()
    print(f"Read {len(rows)} rows from table '{SRC_TABLE}'.")
    if rows: print("Columns found in your table:", ", ".join(rows[0].keys()))
    converted = [convert(r) for r in rows]
    push(converted)
