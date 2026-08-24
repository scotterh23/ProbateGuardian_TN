# Probate Guardians Estate Portal (Phase 1)

A focused MVP so executors, heirs, and probate attorneys can stay aligned during the sale of an inherited home in Middle Tennessee.

Live intent: `portal.probateguardians.com`.

**Database:** PostgreSQL (Neon in production). Prisma reads `DATABASE_URL` and `DIRECT_URL`.

## What Phase 1 includes

- Email + password login with role-based access
- Admin-created invite links (executor, heir, attorney)
- Estate dashboard with status and last update
- Estate workspace: house timeline, overall probate progress, glossary, activity, document vault
- Heirs send private questions to the Probate Guardians team (not visible to other heirs)
- Admin: create/delete estates, invite users, edit status
- Admin/executor: delete documents from the vault
- Invite emails via Resend (`portal@probateguardians.com`)
- Curated recommended vendors on each estate (admin-managed)

**Not in Phase 1:** notifications, vendor marketplace, CRM sync, payments.

## Roles

| Role | Access |
|------|--------|
| **Executor / Administrator** | Full estate view, post updates, upload and delete documents |
| **Heir** | View updates and documents; send questions to Probate Guardians only |
| **Attorney / paralegal** | Invited estates, post notes, view and upload documents |
| **Probate Guardians admin** | Create/delete estates, invite users, manage everything, see heir questions |

## Environment

```
DATABASE_URL="postgresql://USER:PASSWORD@HOST/dbname?sslmode=require"
DIRECT_URL="postgresql://USER:PASSWORD@HOST/dbname?sslmode=require"
AUTH_SECRET="long-random-string-at-least-16-chars"
AUTH_URL="http://localhost:3000"
```

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | App queries. On Neon, use the **pooled** connection (`-pooler` host). |
| `DIRECT_URL` | Migrations. On Neon, use the **unpooled** / direct connection. If you only have one URL, set both to the same **direct** string. |
| `AUTH_SECRET` | JWT cookie signing |
| `AUTH_URL` | Public site origin (invite links). Use `https://portal.probateguardians.com` in production, not `/login`. |
| `BLOB_STORE_ID` | Set automatically when a Vercel Blob store is connected to the project |
| `BLOB_READ_WRITE_TOKEN` | Optional static blob token (needed off Vercel; OIDC is used on Vercel) |
| `RESEND_API_KEY` | Sends invite emails via Resend |
| `INVITE_FROM_EMAIL` | Optional. Defaults to `Probate Guardians <portal@probateguardians.com>` |

SQLite is no longer used. Local `.env` must be a Postgres URL (Neon branch or local Postgres).

## Local setup

Requires Node 20+ and a Postgres database (Neon is fine for local too).

```bash
cd estate-portal
cp .env.example .env
# Put your Neon URLs in .env (pooled → DATABASE_URL, direct → DIRECT_URL)
npm install
npx prisma generate
npx prisma migrate deploy
npm run db:seed
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Demo logins (password `demo1234`)

Only after `npm run db:seed` (wipes data — never run on production without intending to).

| Role | Email |
|------|--------|
| Admin | `admin@probateguardians.com` |
| Executor | `executor@example.com` |
| Heir | `heir@example.com` |
| Attorney | `attorney@example.com` |

## Database commands

```bash
npx prisma migrate deploy    # apply migrations (production + first local setup)
npx prisma migrate dev       # create a new migration while developing
npx prisma db push           # push schema without migration files (prototyping only)
npm run db:seed              # load demo users/estate (destructive)
```

`npm run build` already runs `prisma generate` and `prisma migrate deploy`.

## First production admin (safe, one-time)

Do **not** run `db:seed` against production — it wipes all tables.

From your laptop, with Neon **direct** URLs in the command (not committed to git):

```bash
cd estate-portal
npx prisma generate

DIRECT_URL="postgresql://…unpooled…?sslmode=require" \
DATABASE_URL="postgresql://…unpooled…?sslmode=require" \
ADMIN_EMAIL="you@probateguardians.com" \
ADMIN_PASSWORD="choose-a-long-password" \
ADMIN_NAME="Scott Hardesty" \
npm run db:create-admin
```

That script only inserts an admin. If an admin already exists, it exits unless you set `FORCE_ADMIN=true`.

## Create a real estate (admin)

1. Sign in as admin.
2. **Admin → Create estate**.
3. Open the estate → **Invite someone** → copy the invite link.
4. They set a password at `/invite/[token]` and land directly on that estate.

## Vercel + Neon

See the deploy checklist in the project notes after this change. In short:

1. Root Directory: `estate-portal`
2. Env: `DATABASE_URL`, `DIRECT_URL`, `AUTH_SECRET`, `AUTH_URL`
3. Redeploy so `prisma migrate deploy` runs during build
4. Do **not** seed production unless you want the demo accounts

Invite email uses **Resend**. Add `RESEND_API_KEY` in Vercel, and verify `probateguardians.com` in the Resend dashboard so `portal@probateguardians.com` can send.

Uploads use **Vercel Blob** in production (private store). Locally they still write to `uploads/` unless a blob token is present.

Create a **Private** Blob store in the Vercel dashboard, connect it to this project (Production and Preview). That sets `BLOB_STORE_ID` and OIDC so the app can store wills, letters, and photos off the serverless filesystem.

## Security notes

- Sessions are httpOnly JWTs (30 days).
- Documents are only served after membership checks.
- Heirs cannot post official updates, public comments, or upload vault files.
- Heir questions are visible only to the Probate Guardians team (and the heir who asked).
- Invite links expire in 14 days.
- Seed refuses to run unless `ALLOW_SEED=true`.

## Stack

Next.js 15 (App Router) · Tailwind CSS · Prisma · PostgreSQL (Neon) · jose + bcryptjs
