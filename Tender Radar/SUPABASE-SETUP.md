# Turn on real accounts, shared data and payment approvals (about 15 minutes, free)

Until you do this, the site runs in browser-only demo mode. Nothing here costs money on Supabase's free plan.

## Part 1 — Create the database
1. Go to **https://supabase.com** → **Start your project** → sign in (GitHub or email).
2. Press **New project**. Name: `tenderradarpk`. Set a database password (save it somewhere). Region: pick the closest to you (e.g. Singapore). Press **Create new project** and wait ~2 minutes.
3. In the left menu click **SQL Editor** → **New query**.
4. Open the file **supabase-schema.sql** from your folder in Notepad, press Ctrl+A, Ctrl+C, then paste into the Supabase query box (Ctrl+V).
5. Press **Run**. You should see "Success. No rows returned".

## Part 2 — Sign-up emails (important)
By default Supabase makes people confirm their email, and the free plan only sends a few emails per hour.
1. Left menu → **Authentication** → **Sign In / Providers** (or **Providers**) → **Email**.
2. For your first pilot you can switch **Confirm email** OFF so people can sign in immediately. Turn it back ON, with a proper email sender (SMTP), before a big launch.

## Part 3 — Copy your two keys into the site
1. Left menu → **Project Settings** (gear icon) → **API** (or **Data API**).
2. Copy **Project URL** and the **anon public** key (NOT the "service_role" key. Never share that one).
3. Open **index.html** in Notepad, press Ctrl+F and search for `TRP_SUPA`. You will see:
   `const TRP_SUPA = { url: '', anonKey: '' };`
   Paste your values between the quotes, for example:
   `const TRP_SUPA = { url: 'https://abcdxyz.supabase.co', anonKey: 'eyJhbGci...' };`
4. A few lines below, change `SHOW_DEMO_ACCOUNTS = true` to `false` (hides the demo accounts for real visitors).
5. Search for `DEMO_MODE` and change `true` to `false`.
6. Save the file.

## Part 4 — Re-upload and make yourself admin
1. Re-upload the folder to Netlify (drag it onto your site's **Deploys** page) or upload index.html to GitHub.
2. Open your live site, press **Create a free account**, and sign up with your own email.
3. Back in Supabase → **SQL Editor** → New query, paste this with YOUR email, and Run:
   `update public.profiles set is_admin = true where email = 'your-email@example.com';`
4. Sign out and sign in again. You now see the **Payment requests** panel in **Plans & billing**, and can Approve or Reject.

## How a sale works now
Customer signs up → picks Pro → pays by JazzCash/Easypaisa/bank → enters the transaction ID → you check your phone/bank → press **Approve** → their account switches to Pro on every device.

## Test checklist
- Sign up with a second email → it should show "Free plan" with locked tender details.
- Submit a payment request → approve it from your admin account → the second account becomes Pro after it signs in again.
- Track a tender on one device and open the site on another: the pipeline follows you.

## Still not live (be honest with customers)
- **Tenders are still the sample set.** Real tenders need your scraper to write into a Supabase `tenders` table; the next step is connecting your existing scraper project to this site.
- Vendor directory entries, RFQs and documents are still browser-only.
- Add Terms, Privacy and Refund pages before charging real money.
