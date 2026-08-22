# Probate Guardians Estate Portal (Phase 1)

A focused MVP so executors, heirs, and probate attorneys can stay aligned during the sale of an inherited home in Middle Tennessee.

Live intent: `portal.probateguardians.com` (or `app.probateguardians.com`).

## What Phase 1 includes

- Email + password login with role-based access
- Admin-created invite links (executor, heir, attorney)
- Estate dashboard with status and last update
- Estate workspace: timeline, activity feed, comments, document vault
- Admin: create estates, edit status, invite people

**Not in Phase 1:** notifications, vendor marketplace, CRM sync, payments.

## Roles

| Role | Access |
|------|--------|
| **Executor / Administrator** | Full estate view, post updates, upload documents |
| **Heir / family** | View-only + comments on updates |
| **Attorney / paralegal** | All invited estates, post notes, view documents |
| **Probate Guardians admin** | Create estates, invite users, manage everything |

## Local setup

Requires Node 20+.

```bash
cd estate-portal
cp .env.example .env
npm install
npx prisma generate
npm run db:reset
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Demo logins (password `demo1234`)

| Role | Email |
|------|--------|
| Admin | `admin@probateguardians.com` |
| Executor | `executor@example.com` |
| Heir | `heir@example.com` |
| Attorney | `attorney@example.com` |

The seed creates the **Whitfield family home** at 4521 Main St, Lebanon (Wilson County) with two updates and a family comment.

## Create a real estate (admin)

1. Sign in as admin.
2. **Admin → Create estate**.
3. Open the estate → **Invite someone** → copy the invite link and send it (email delivery comes later).
4. They set a password at `/invite/[token]` and land on the dashboard.

## Environment

```
DATABASE_URL="file:./dev.db"
AUTH_SECRET="long-random-string-at-least-16-chars"
AUTH_URL="http://localhost:3000"
```

For production Postgres, change `DATABASE_URL` to a Postgres URL and set `provider = "postgresql"` in `prisma/schema.prisma`, then `npx prisma db push`.

## Deploy (Vercel)

1. Create a Vercel project with **Root Directory** `estate-portal`.
2. Set `AUTH_SECRET`, `AUTH_URL` (`https://portal.probateguardians.com`), and `DATABASE_URL`.
3. For SQLite on Vercel, use Postgres (Neon/Supabase) instead — serverless filesystems are ephemeral.
4. Add a persistent disk or S3 later for `uploads/`. Phase 1 stores files on local disk.
5. Point the subdomain in DNS (CNAME to Vercel) and add it in Vercel → Domains.

Build command: `npm run build`  
Install: `npm install`  
Output: Next.js default.

## Security notes

- Sessions are httpOnly JWTs (30 days).
- Documents and update attachments are only served after membership checks.
- Heirs cannot post official updates or upload vault files.
- Invite links expire in 14 days.

## Stack

Next.js 15 (App Router) · Tailwind CSS · Prisma · SQLite (dev) · jose + bcryptjs
