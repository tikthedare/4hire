# ForHire India MVP

Django 5 + DRF API and React (Vite) SPA for hiring soccer coaches in India. Business rules and validation mirror the [4hire-local](https://github.com) reference (Supabase/Next.js); this stack uses JWT auth and DRF permissions instead of RLS.

## Repository layout

- `api/` — Django project (`accounts`, `catalog`, `listings`, `hire_requests`, `reviews`, `chat`, `payments`)
- `web/` — Vite + React + Tailwind SPA (dev port **3847**)
- `docker-compose.yml` — PostgreSQL 16

## Prerequisites

- Docker (for Postgres)
- Python 3.12+ recommended (3.14 works locally with current `psycopg`)
- Node.js 20+ for the SPA

## Local setup

1. Copy environment file:

   ```bash
   cp .env.example .env
   ```

2. Start Postgres:

   ```bash
   docker compose up -d db
   ```

3. API:

   ```bash
   cd api
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   # source .venv/bin/activate     # macOS/Linux
   pip install -r requirements.txt
   set DJANGO_SETTINGS_MODULE=config.settings.local   # Windows
   python manage.py migrate
   python manage.py runserver
   ```

   API: http://localhost:8000 — OpenAPI: http://localhost:8000/api/docs/

4. Web:

   ```bash
   cd web
   npm install
   npm run dev
   ```

   SPA: http://localhost:3847

## Tests

```bash
cd api
pytest
```

CI runs `pytest` against Postgres and `npm run build` for `web/`.

## Auth / security notes (MVP)

- **Access JWT** is held in memory; **refresh** token is in `sessionStorage` (documented trade-off: XSS exposure vs simplicity). Prefer same-origin deployment in production.
- Contact fields (email, mobile, WhatsApp) are only returned when a hire request is **accepted** and the viewer is a party on that request.
- Profile **role** is immutable after signup (model guard + DB constraints).

## Razorpay test keys

1. Create a Razorpay account and switch the dashboard to **Test Mode**.
2. Generate a test API key. Put `rzp_test_...` in `RAZORPAY_KEY_ID` and the secret in `RAZORPAY_KEY_SECRET` in the repo-root `.env` (see `.env.example`). The API loads that file on startup when those variables are not already set in the process environment. The SPA never sees the secret; `POST /api/v1/hire-requests/{id}/payments/order/` returns the key id.
3. Add a webhook to `https://<your-api-host>/api/v1/payments/webhook/` with a secret in `RAZORPAY_WEBHOOK_SECRET`. Subscribe to `payment.captured` and `payment.failed`.
4. Restart the API after changing `.env`. For local webhooks, tunnel `localhost:8000` (Cloudflare Tunnel or similar) and point the dashboard webhook at that URL.
5. Checkout also posts `razorpay_order_id`, `razorpay_payment_id`, and `razorpay_signature` to `POST /api/v1/hire-requests/{id}/payments/verify/`. The API checks that signature with the key secret before marking the payment captured. A browser “success” callback alone does not capture a payment. Replaying the same webhook does not create a second payout.
6. In test mode, Razorpay documents card `4111 1111 1111 1111` (any future expiry and CVV) and UPI VPA `success@razorpay`. Use live keys only after a real ₹1 UPI payment succeeds in test mode.

Amounts are stored in **paise**. The platform Razorpay account collects the full charge. A payout row records what is owed to the coach; staff mark it paid in Django admin with a UTR. This step does not use Razorpay Route.

## Hosting (one India VM)

Run the API and Postgres on a single small VM in **Mumbai or Bengaluru**. Oracle Cloud Always Free in Mumbai if the account qualifies; otherwise a DigitalOcean Bangalore droplet (about $6/month). Do not add Redis, Django Channels, or a second admin app.

- **API:** `DJANGO_SETTINGS_MODULE=config.settings.production`, gunicorn behind nginx. Set `SECRET_KEY`, `DATABASE_URL` (Postgres on the same machine), `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and the Razorpay variables above.
- **SPA:** Cloudflare Pages (free), with `VITE_API_BASE_URL` pointing at the API. Cloudflare also proxies the API hostname.
- **Email:** Brevo free tier (about 300 emails/day) for payment receipts. In production, set `BREVO_SMTP_USER`, `BREVO_SMTP_KEY`, and `DEFAULT_FROM_EMAIL`. SMTP host defaults to `smtp-relay.brevo.com:587`.
- **Backups:** nightly `pg_dump` to Cloudflare R2 (free tier, 10 GB).
- **Admin:** Django admin at `/admin/` for users, listings, requests, payments, reviews, and threads. Add operators to the **Staff** group. Mark due payouts paid from the payout action; a UTR is required. Reviews can be hidden or restored. Messages are read-only. `Profile.role` stays immutable.

Spend more only when chat polling, manual payouts, or single-machine backups become the bottleneck. GST invoices and Razorpay Route are out of scope until volume justifies them.

## Manual QA (short)

- Coach: register → create listing → appears on `/coaches` with filters and a rating line
- Hirer: register → request on coach detail → coach accepts → hirer sees WhatsApp on `/requests`
- Accepted request: hirer uses Pay with UPI; after capture the row shows Paid and a review form. Coach page shows the public average.
- Pending or accepted request: Messages polls about every 8 seconds while the panel is open and the tab is visible
- Decline/withdraw: contact stays hidden and the thread panel is hidden
