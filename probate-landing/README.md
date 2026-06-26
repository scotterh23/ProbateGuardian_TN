# Probate Guardians TN — Public Landing Page

Mobile-first marketing site for **probateguardians.com**. No CRM or internal tools.

## Preview locally

```bash
cd probate-landing
python3 -m http.server 8080
```

Open **http://localhost:8080** on your phone (same Wi‑Fi) or desktop.

Alternative:

```bash
cd probate-landing
npx --yes serve -l 8080
```

## Deploy to probateguardians.com

### Option A — Netlify (recommended, free SSL + custom domain)

1. Push this repo to GitHub (or drag-drop the `probate-landing` folder at [app.netlify.com/drop](https://app.netlify.com/drop)).
2. In Netlify: **Add new site → Import from Git** → select repo.
3. Build settings:
   - **Base directory:** `probate-landing`
   - **Build command:** *(leave empty)*
   - **Publish directory:** `.` (or `probate-landing` if deploying from repo root without base dir)
4. **Domain settings → Add custom domain** → `probateguardians.com` and `www.probateguardians.com`.
5. At your domain registrar, point DNS to Netlify (A record `75.2.60.5` or CNAME to your Netlify subdomain).

CLI deploy (one-time `netlify login`):

```bash
cd probate-landing
npx netlify-cli deploy --prod --dir=.
```

### Option B — Cloudflare Pages

1. Cloudflare Dashboard → **Workers & Pages → Create → Pages → Connect Git**.
2. **Build command:** empty · **Build output directory:** `probate-landing`
3. Add custom domain `probateguardians.com` in Pages settings.

### Option C — Vercel

```bash
cd probate-landing
npx vercel --prod
```

Then add `probateguardians.com` in Vercel project → Domains.

### Option D — GitHub Pages (subpath or root)

If the whole repo publishes from `/docs` or a `gh-pages` branch, copy `probate-landing/*` to the publish root or set GitHub Pages source to the `probate-landing` folder via Actions.

## Google Business Profile

- Use business name: **Probate Guardians TN**
- Primary category: Real Estate Agent (or Real Estate Consultant)
- Services: match the six cards on the site + Muniment of Title guidance
- Service areas: Sumner, Wilson, Davidson, Rutherford, Williamson, Robertson, Cheatham, Dickson, Maury counties
- Website URL: `https://probateguardians.com`
- Phone: `615-XXX-XXXX` (Branton's Google Voice) or `615-953-0758`

## Files

| File | Purpose |
|------|---------|
| `index.html` | Single-page site + JSON-LD schema |
| `styles.css` | Mobile-first styles |
| `script.js` | Form UX + footer year |
| `robots.txt` | Crawler rules |
| `sitemap.xml` | SEO sitemap |

Replace hero photo placeholder with a real team photo at `/og-image.jpg` when ready.