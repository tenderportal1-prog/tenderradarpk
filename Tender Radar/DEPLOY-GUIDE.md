# TenderRadarPK — Deploy Guide (no coding needed, ~10 minutes, free)

You have ONE file that matters: **index.html**. It is the whole website.

## Before you start: test it on your own computer (1 minute)
1. Download the folder `TenderRadarPK` to your computer.
2. Double-click **index.html**. It opens in your browser.
3. Click "Create a free account", or use a demo account (the password for all of them is `DevPassword!1`).
4. Open **Plans & billing** to see the plans and try the payment screen. In demo mode you can switch plans with one click.

## Option A (easiest): Netlify Drop — 3 minutes, no account setup tricks
1. Go to **https://app.netlify.com/drop** and sign up free (use Google login).
2. Drag the whole **TenderRadarPK folder** onto the page.
3. Wait about 20 seconds. Netlify gives you a live link like `https://random-name.netlify.app`.
4. Click **Site configuration → Change site name** to pick something like `tenderradarpk`.
   Your link becomes `https://tenderradarpk.netlify.app`. Share it.

## Option B: GitHub Pages — free, permanent
1. Create a free account at **https://github.com**.
2. Click the **+** (top right) → **New repository**. Name it `tenderradarpk`, choose **Public**, press **Create repository**.
3. Click **uploading an existing file**, drag in **index.html**, then press **Commit changes**.
4. Go to **Settings → Pages**. Under "Branch" choose **main** and **/ (root)**, press **Save**.
5. After 1–2 minutes your site is at `https://YOUR-USERNAME.github.io/tenderradarpk/`.

## Option C: Vercel
1. Sign up free at **https://vercel.com** (use GitHub login).
2. Press **Add New → Project**, import your `tenderradarpk` GitHub repository, press **Deploy**.

## Updating the site later
Replace **index.html** (Netlify: drag the folder again; GitHub: upload the new file and Commit). The link stays the same.

## Things you MUST change before sharing publicly
Open index.html in **Notepad** (right-click → Open with → Notepad). Press **Ctrl+F** and search for `TRP_SETTINGS`. Change:
- `whatsapp` → your real WhatsApp number (format `923001234567`)
- `supportEmail` → your real email
- the `payment` lines → your real JazzCash / Easypaisa / bank details
- prices in `PLANS` (search `price:2500`)
- `DEMO_MODE = true` → `DEMO_MODE = false` (this hides the free plan-switching buttons so people must really pay)

Save the file and re-upload.

## Honest limits of the browser-only version (please read)
(After you complete **SUPABASE-SETUP.md**, accounts, plans, pipeline and payment approvals become real and shared.)
- **Data is stored inside each visitor's own browser.** Accounts, pipelines and payment requests are NOT shared between people or devices. You cannot see your customers' sign-ups yet.
- **Passwords are not secure** in this version. Do not collect real passwords until you connect Supabase (see NEXT-STEPS file).
- **The tenders are sample data**, not live. Your scraper project (TenderAlert-style) can feed real tenders later.
- Because of the above, treat this as a **public demo / pilot** to show people and get feedback, and do real selling after Step 1 of the next-steps guide.
