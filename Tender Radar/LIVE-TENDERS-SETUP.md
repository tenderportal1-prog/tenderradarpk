# Put REAL tenders on the site (about 20 minutes)

Do **SUPABASE-SETUP.md first** (accounts and keys). Then:

## Part 1 — Create the tenders table
1. Supabase → **SQL Editor → New query**.
2. Open **supabase-tenders.sql** in Notepad → Ctrl+A, Ctrl+C → paste into Supabase → **Run**.
3. This also adds 3 TEST tenders. Refresh your live site: you will see them in **Search tenders**, and the old sample tenders disappear. That proves the connection works.
4. When real tenders are flowing, delete the tests: SQL Editor → run
   `delete from public.radar_tenders where id like 'TEST-%';`

## Part 2 — Let your scraper send tenders to the site
Your scraper already lives on GitHub (repo `tender-portal`, runs on GitHub Actions).
1. On GitHub open your repo → **Add file → Upload files** → upload **push_tenders_to_site.py** → Commit.
2. Supabase → **Project Settings → API**: copy the **Project URL** and the **service_role** key.
   ⚠️ The service_role key is a master password. Put it ONLY in GitHub Secrets, never in index.html, never in a chat.
3. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**. Add two:
   - Name `RADAR_SUPABASE_URL` → value: your Project URL
   - Name `RADAR_SERVICE_KEY` → value: your service_role key
4. In your workflow file (`.github/workflows/....yml`), under the step that runs the scraper, add:
   ```
   env:
     RADAR_SUPABASE_URL: ${{ secrets.RADAR_SUPABASE_URL }}
     RADAR_SERVICE_KEY: ${{ secrets.RADAR_SERVICE_KEY }}
   ```
5. At the end of your scraper, add: `from push_tenders_to_site import push` and then `push(list_of_tenders)`.
   The helper accepts your fields (title, department/org, city, province, closing, ref, fee, source, pdf link…) and fixes dates and province names.
   Tenders are matched by `id`, so re-running never creates duplicates.
6. Run the workflow once (**Actions → your workflow → Run workflow**) and refresh the site.

If you paste me your scraper's output (one example tender and the file where it is built), I will write the exact lines for step 5 so you can paste them in.

## How it behaves on the site
- Everyone can see the tender list; **Pro** customers also get eligibility details, documents and the original notice link.
- The page re-checks for new tenders every 10 minutes while it is open.
- Tenders stay in the Archive tab for 60 days after closing.
- New categories from the scraper are added to the filters automatically.
- A few real notices that were already inside the app (the Sindh Integrated Emergency and Health Services ones) stay visible alongside live data.
- If the table is ever empty, the sample tenders show instead, so the site is never blank.

## Reminder
Tender notices are public, but check each source website's terms and always keep the "source" and original link on every tender.
