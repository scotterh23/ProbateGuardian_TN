# Probate CRM Pro (Round 2)

Next.js CRM for Shelly’s calling workflow. Talks to the live Supabase project used by [probate-crm-pro.vercel.app](https://probate-crm-pro.vercel.app).

This folder is the shippable app. The original `probate-crm-pro` source is not in the `ProbateGuardian_TN` repo. Deploy this directory to the Vercel project **probate-crm-pro** (Root Directory = `probate-crm`).

## Round 2 fixes

1. **Back arrow** on a lead returns to the leads list (saved URL + filters).
2. **Scroll position** is saved on `window` and the main pane, then restored when she comes back. The last opened card is scrolled into view if needed.
3. **Sidebar Leads** keeps the active filter/sort URL instead of resetting to `/leads`.
4. **Last called sort** label: “Never called first, then oldest last-called,” with helper text.
5. **Stacked filters** — status, last-called, mailer, follow-up, and search combine. They do not replace each other.
6. **Multi-signal outreach** — call / email / mailer counts and last dates sit next to status. Status is not reused for mailer or email.
7. **Safe batch only** — “Move N New leads with a logged call to Contacted.” Requires `status = new` **and** at least one `lead_activities` row typed `call`. It will not touch Warm, Hot, Follow-up, DNC, or Needs Mailer. The live production button that said “New leads with contact” (phone on file) is **parked** as unsafe.

## Parked (do not dump on Branton)

- Send-from-CRM email compose, drip enrollment, paste import, case create, partner/agent admin, and org settings from the current production app.
- Unsafe mass “New → Contacted” for leads that only have a phone number and no logged call. Shelly can flip those one-by-one, or use the safe button when a call is already logged.

## Local

```bash
cd probate-crm
cp env.example .env.local
npm install
npm run dev
```

## Vercel production

Project: `probate-crm-pro`  
Root Directory: `probate-crm`  
Env: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (same values already used by the live app)

Do not point the estate-portal Vercel project at this folder.

## How Shelly should verify

1. Open a filtered list (e.g. New + Never called first). Scroll halfway. Open a lead. Tap the **back arrow**. Land on the same filtered list, same scroll.
2. From that lead, click left-menu **Leads**. Filters stay. List does not jump to “all / default.”
3. Combine **Needs Mailer** with **Never called first, then oldest last-called**. Both stay applied.
4. On a lead card, confirm call / email / mailer show as three lines, not one status.
5. Optional: the batch button only appears with a count of New leads that already have a logged call. Cancel unless she wants those moved.
