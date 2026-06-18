# Email subscriptions — setup

Market Prompt collects signups and emails the day's issue to subscribers, with a
button back to the website. The code is all here; you just connect **Resend**.

## How it works

1. **Signup** — the hero form posts to `/api/subscribe` (a Vercel serverless
   function, `api/subscribe.js`), which adds the email to a Resend *Audience*.
   No database; emails never live in this repo.
2. **Daily send** — after the 7am workflow generates and deploys the issue,
   `send_email.py` builds a short teaser email (headline + bullets) with a
   **"Read today's full brief →"** button linking back to that day's page, and
   sends it to the whole audience via Resend *Broadcasts*.

## One-time setup (≈10 min)

1. **Create a Resend account** → https://resend.com
2. **Verify a sending domain** (Resend → Domains → add e.g. `mail.yourdomain.com`,
   then add the DNS records it shows). This is required or emails go to spam.
3. **Create an Audience** (Resend → Audiences). Copy its **Audience ID**.
4. **Create an API key** (Resend → API Keys). Copy it.
5. **Add the secrets / env vars:**

   **GitHub** (repo → Settings → Secrets and variables → Actions → *Secrets*):
   - `RESEND_API_KEY` — the API key
   - `RESEND_AUDIENCE_ID` — the audience ID
   - `MP_FROM` — e.g. `Market Prompt <brief@mail.yourdomain.com>` (must be on the
     verified domain)

   Optional **variable** (same screen → *Variables*):
   - `SITE_URL` — public site base for email links (defaults to the GitHub Pages
     URL if unset; set to your Vercel/custom domain if you prefer).

   **Vercel** (project → Settings → Environment Variables) — for the signup form:
   - `RESEND_API_KEY`
   - `RESEND_AUDIENCE_ID`

That's it. Until these are set, signup shows a friendly "not switched on yet"
message and the daily email step skips itself — nothing breaks.

## Notes

- The signup **backend only runs on Vercel** (GitHub Pages can't run functions),
  so use the Vercel deployment as the public site for working signups. The form
  POSTs with CORS allowed, so the Pages mirror's form will also reach it.
- Every email includes a one-click **unsubscribe** link (Resend handles it).
- Test the daily email any time without waiting for 7am:
  `RESEND_API_KEY=... RESEND_AUDIENCE_ID=... MP_FROM="..." python3 send_email.py 2026-06-18`
