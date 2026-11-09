"""
scraper.py  —  collects tenders from Pakistani procurement portals and saves them
straight into the TenderRadarPK website table (radar_tenders).

Runs on GitHub Actions (see scrape-tenders.yml). Needs only two secrets:
  RADAR_SUPABASE_URL   https://lkyyektvfhvmjmvunewf.supabase.co
  RADAR_SERVICE_KEY    your Supabase *Secret* key (sb_secret_...)

HOW IT WORKS: for each portal in SOURCES it downloads the page, finds the biggest table of
tenders, recognises the columns by their headings (Title, Closing Date, Department...),
and sends every row to the website. The log tells you exactly what it found on each portal.
A portal that fails never stops the others.
"""
import re, sys, time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ---- Portals to read. Add more by copying a line. -----------------------------------------
SOURCES = [
  {"name":"PPRA Punjab", "url":"https://eproc.punjab.gov.pk/ActiveTenders.aspx", "province":"Punjab"},
  {"name":"PPRA Federal","url":"https://epms.ppra.gov.pk/public/tenders/active-tenders", "province":"Federal", "pages":10},
  {"name":"SPPRA Sindh", "url":"https://portalsindh.eprocure.gov.pk/",           "province":"Sindh", "insecure":True},
  {"name":"BPPRA Balochistan","url":"http://bpptwo.vdc.services:5451/Tenders",    "province":"Balochistan"},
]
HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
           "Accept-Language":"en-US,en;q=0.9"}

# ---- Column recognition (by heading text) -------------------------------------------------
COLS = {
  "closing":   r"clos|deadline|due|last date|submission|bid.*(date|open)|end date",
  "published": r"publish|posted|start|advert|issue|opening date|date of",
  "ref":       r"tender (no|number|id)|ref|reference|\bno\b|\bid\b|number",
  "org":       r"department|agency|authority|organi[sz]ation|procuring|office|entity|client",
  "fee":       r"fee|cost of (tender|document)",
  "value":     r"estimated|value|amount",
  "city":      r"city|district|location|place",
  "title":     r"title|description|name|subject|tender|work|item|procurement",   # keep LAST: most generic
}

# ---- Category / type guessing (so the Match Score works) ----------------------------------
CATEGORY_WORDS = [
  ("IT & Software",            r"\b(?:software|computer|laptop|server|network|website|erp|cctv|printer|digital|hardware|licen[cs]e)s?\b"),
  ("Construction",             r"\b(?:construction|road|bridge|building|rehabilitation|repair|renovation|civil|pavement|drain|sewerage|water supply|boundary wall|carpeting)s?\b"),
  ("Engineering",              r"\b(?:engineering|mechanical|plant|machinery|boiler|tube ?well|pump|survey|design|consultan)s?\b"),
  ("Medical & Healthcare",     r"\b(?:medical|medicine|hospital|surgical|health|pharma|drug|laborator|diagnostic|ambulance|vaccine|dental)s?\b"),
  ("Food & Catering",          r"\b(?:food|catering|ration|meal|dietary|kitchen|grocery|cooking)s?\b"),
  ("Security Services",        r"\b(?:security guard|security service|security|surveillance|guards)s?\b"),
  ("Electrical",               r"\b(?:electric|solar|transformer|cable|generator|inverter|lighting|led|ups|power)s?\b"),
  ("Logistics & Transportation",r"\b(?:transport|vehicle|car|bus|truck|fuel|petrol|diesel|lubricant|logistic|courier|tyre|tire)s?\b"),
  ("Cleaning & Janitorial",    r"\b(?:janitorial|cleaning|sweeping|sanitation|waste|garbage|hygiene|housekeeping)s?\b"),
  ("Office Supplies",          r"\b(?:stationery|furniture|office|paper|printing|toner|cartridge|book|uniform)s?\b"),
]
def guess_category(text):
    t = " " + text.lower() + " "
    for cat, rx in CATEGORY_WORDS:
        if re.search(rx, t): return cat
    return "General"
def guess_type(text):
    t = text.lower()
    if re.search(r"construction|road|bridge|rehabilitation|renovation|repair|civil|building|sewerage|pavement", t): return "Works"
    if re.search(r"consultan|design|survey|feasibility|audit", t): return "Consultancy"
    if re.search(r"service|janitorial|cleaning|security|catering|hiring|maintenance|transport", t): return "Services"
    return "Goods"

def text_of(el): return re.sub(r"\s+", " ", el.get_text(" ", strip=True))

def best_table(soup):
    """Pick the table that looks most like a list of tenders."""
    best, best_score = None, 0
    for tb in soup.find_all("table"):
        rows = tb.find_all("tr")
        if len(rows) < 3: continue
        head = " ".join(text_of(c) for c in rows[0].find_all(["th","td"])).lower()
        score = len(rows) + 25*len(re.findall(r"title|closing|tender|department|agency|date|description|deadline", head))
        if score > best_score: best, best_score = tb, score
    return best

def map_columns(header_cells):
    mapping, used = {}, set()
    for field, rx in COLS.items():
        for i, h in enumerate(header_cells):
            if i in used: continue
            if re.match(r"^\s*(s\.?\s?no\.?|sr\.?( no\.?)?|serial.*|#)\s*$", h.lower()): continue   # skip row-number columns
            if re.search(rx, h.lower()):
                mapping[field] = i; used.add(i); break
    return mapping

def fetch(src, url):
    """Downloads a page. 'insecure' sources use relaxed SSL (some Pakistani portals have old SSL settings)."""
    if src.get("insecure"):
        import ssl, urllib3
        from requests.adapters import HTTPAdapter
        urllib3.disable_warnings()
        class Relaxed(HTTPAdapter):
            def init_poolmanager(self, *a, **k):
                ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
                try: ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
                except Exception: pass
                try: ctx.options |= 0x4   # allow legacy renegotiation
                except Exception: pass
                k["ssl_context"] = ctx; return super().init_poolmanager(*a, **k)
        sess = requests.Session(); sess.mount("https://", Relaxed())
        return sess.get(url, headers=HEADERS, timeout=(15, 40), verify=False)
    return requests.get(url, headers=HEADERS, timeout=(15, 40))

def scrape_source(src):
    out, seen_first = [], None
    for page in range(1, int(src.get("pages", 1)) + 1):
        url = src["url"] if page == 1 else f"{src['url']}{'&' if '?' in src['url'] else '?'}page={page}"
        rows = scrape_page(src, url)
        if not rows: break
        if rows[0]["title"] == seen_first: break          # same page again (portal ignores ?page=): stop
        seen_first = rows[0]["title"]
        out += rows
    return out

def scrape_page(src, url):
    r = fetch(src, url)
    print(f"  {url}  ->  HTTP {r.status_code}, {len(r.text)//1024} KB")
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    tb = best_table(soup)
    if tb is None:
        print("  !! No table found. This portal probably builds its list with JavaScript (needs a browser-based scraper).")
        return []
    rows = tb.find_all("tr")
    header = [text_of(c) for c in rows[0].find_all(["th","td"])]
    print("  Table headings:", " | ".join(header))
    m = map_columns(header)
    print("  Column mapping:", {k: header[i] for k, i in m.items()})
    if "title" not in m or "closing" not in m:
        print("  !! Could not find a Title and a Closing-date column. Send this log to your helper to adjust.")
        return []
    out = []
    for tr in rows[1:]:
        cells = tr.find_all(["td","th"])
        if len(cells) < len(header) - 1: continue
        get = lambda f: text_of(cells[m[f]]) if f in m and m[f] < len(cells) else ""
        title = get("title")
        if len(title) < 5: continue
        a = tr.find("a", href=True)
        link = urljoin(src["url"], a["href"]) if a else src["url"]
        out.append({
          "title": title, "org": get("org"), "city": get("city"), "province": src["province"],
          "source": src["name"], "ref": get("ref"), "published": get("published"), "closing": get("closing"),
          "fee": get("fee"), "value": get("value") or "Not disclosed", "source_url": link,
          "category": guess_category(title + " " + get("org")), "type": guess_type(title), "sector": "GOVERNMENT",
        })
    print(f"  Parsed {len(out)} tender rows" + (f". Example: {out[0]['title'][:70]!r} closing {out[0]['closing']!r}" if out else ""))
    return out

if __name__ == "__main__":
    from push_tenders_to_site import push
    everything = []
    for src in SOURCES:
        print(f"\n=== {src['name']}  {src['url']}")
        try:
            everything += scrape_source(src)
        except Exception as e:
            print(f"  !! FAILED: {type(e).__name__}: {e}")
        time.sleep(2)
    print(f"\nTotal collected from all portals: {len(everything)}")
    if not everything:
        print("Nothing collected. See the messages above for each portal."); sys.exit(1)
    push(everything)
