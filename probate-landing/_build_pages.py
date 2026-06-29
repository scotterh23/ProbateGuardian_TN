#!/usr/bin/env python3
"""Generate Core 30 static pages — run once when structure changes."""
from pathlib import Path

from _services_data import SERVICES, SERVICE_COUNTIES
from _service_meta import SERVICE_META

SITE = "https://probateguardians.com"

PHONE = "(615) 669-7075"
PHONE_TEL = "6156697075"
PHONE_LINK = f'Call or text <strong>{PHONE}</strong>'

NAV = """      <nav class="header-nav" aria-label="Main">
        <a href="/"{home_current}>Home</a>
        <a href="/roadmap/"{road_current}>Family Roadmap</a>
        <a href="/services/"{svc_current}>Services</a>
        <a href="/counties/"{cty_current}>Counties</a>
        <a href="/about/"{abt_current}>About</a>
        <a href="{contact_href}"{con_current}>Contact</a>
      </nav>"""

FOOTER_NAV = """        <a href="/">Home</a>
        <a href="/roadmap/">Family Roadmap</a>
        <a href="/services/">Services</a>
        <a href="/counties/">Counties</a>
        <a href="/about/">About</a>
        <a href="/#contact">Contact</a>"""


def shell(
    title: str,
    description: str,
    canonical: str,
    css_prefix: str,
    script_prefix: str,
    nav_active: dict,
    body: str,
) -> str:
    nav = NAV.format(
        home_current=' aria-current="page"' if nav_active.get("home") else "",
        road_current=' aria-current="page"' if nav_active.get("road") else "",
        svc_current=' aria-current="page"' if nav_active.get("svc") else "",
        cty_current=' aria-current="page"' if nav_active.get("cty") else "",
        abt_current=' aria-current="page"' if nav_active.get("abt") else "",
        con_current=' aria-current="page"' if nav_active.get("con") else "",
        contact_href=nav_active.get("contact_href", "/#contact"),
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="{description}" />
  <meta name="robots" content="index, follow" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:url" content="{canonical}" />
  <title>{title}</title>
  <link rel="canonical" href="{canonical}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{css_prefix}styles.css" />
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="container header-inner">
      <a href="/" class="logo" aria-label="Probate Guardians TN home">
        <span class="logo-mark" aria-hidden="true">🛡️</span>
        Probate Guardians <span class="logo-accent">TN</span>
      </a>
{nav}
      <a href="tel:{PHONE_TEL}" class="header-phone">
        <span class="header-phone-num">{PHONE_LINK}</span>
      </a>
    </div>
  </header>
  <main id="main">
{body}
  </main>
  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-brand">
        <strong>Probate Guardians TN</strong>
        <p>Compassion · Clarity · Closings</p>
      </div>
      <nav class="footer-nav" aria-label="Footer">
{FOOTER_NAV}
      </nav>
      <p class="footer-disclaimer">
        Scott Hardesty &amp; Branton Walker • Probate Guardians TN • Serving all of Middle Tennessee • Call or text {PHONE_LINK}<br />
        Not legal advice. Probate Guardians TN provides real estate coordination only. All property sales subject to court approval where required. © <span id="year"></span> Scott Hardesty &amp; Branton Walker.
      </p>
    </div>
  </footer>
  <a href="tel:{PHONE_TEL}" class="mobile-call-fab" aria-label="Call or text {PHONE}">📞</a>
  <script src="{script_prefix}script.js"></script>
</body>
</html>
"""


def cta_block(extra: str = "") -> str:
    return f"""
    <div class="detail-cta-row">
      <a href="tel:{PHONE_TEL}" class="btn btn-primary">{PHONE_LINK}</a>
      <a href="/roadmap/" class="btn btn-secondary">Get your free Guardian Kit</a>
      {extra}
    </div>"""


def service_cta_block() -> str:
    return f"""
    <div class="detail-cta-row service-cta-row">
      <a href="tel:{PHONE_TEL}" class="btn btn-primary btn-cta-phone">{PHONE_LINK}</a>
      <a href="/roadmap/" class="btn btn-secondary">Get your free Guardian Kit</a>
    </div>"""


def enriched_services() -> list:
    out = []
    for svc in SERVICES:
        meta = SERVICE_META[svc["id"]]
        out.append({**svc, **meta})
    return out


def service_href(svc: dict) -> str:
    return f"/services/{svc['slug']}/"


def service_by_id() -> dict:
    return {svc["id"]: svc for svc in enriched_services()}


def linkify(text: str) -> str:
    lookup = service_by_id()
    for sid, svc in lookup.items():
        text = text.replace(f'href="#{sid}"', f'href="{service_href(svc)}"')
    return text


def breadcrumbs(items: list, light: bool = False) -> str:
    cls = "breadcrumbs breadcrumbs-light" if light else "breadcrumbs"
    lis = []
    for label, href, current in items:
        if current:
            lis.append(f'<li aria-current="page">{label}</li>')
        else:
            lis.append(f'<li><a href="{href}">{label}</a></li>')
    return f"""
    <nav class="{cls}" aria-label="Breadcrumb">
      <ol>{"".join(lis)}</ol>
    </nav>"""


def internal_links() -> str:
    return f"""
    <p class="internal-links">Also explore: <a href="/">Home</a> · <a href="/roadmap/">Guardian Kit &amp; Family Roadmap</a> · <a href="/services/">All Services</a> · <a href="/counties/">Counties We Serve</a> · <a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>"""


def render_related_links(svc: dict) -> str:
    lookup = service_by_id()
    parts = []
    for label, ref in svc["related"]:
        if ref.startswith("#"):
            target = lookup.get(ref[1:])
            if target:
                parts.append(f'<a href="{service_href(target)}">{label}</a>')
        else:
            parts.append(f'<a href="{ref}">{label}</a>')
    parts.extend([
        '<a href="/roadmap/">Family Roadmap</a>',
        '<a href="/counties/">Counties We Serve</a>',
        '<a href="/">Home</a>',
    ])
    return f"""
    <div class="related-services-block">
      <h3 class="related-services-title">Related services</h3>
      <p class="service-related">{" · ".join(parts)}</p>
    </div>"""


def render_service_page_body(svc: dict) -> str:
    paragraphs = "".join(f"<p>{linkify(p)}</p>" for p in svc["paragraphs"])
    examples = "".join(
        f'<aside class="local-example"><p>{linkify(ex)}</p></aside>' for ex in svc["local_examples"]
    )
    bullets = "".join(f"<li>{linkify(b)}</li>" for b in svc["bullets"])
    crumbs = breadcrumbs([
        ("Home", "/", False),
        ("Services", "/services/", False),
        (svc["name"], service_href(svc), True),
    ])
    return f"""
    <section class="page-hero page-hero-service">
      <div class="container service-detail-inner">
        {crumbs}
        <p class="eyebrow">{svc['icon']} Probate Guardians TN Service</p>
        <h1>{svc['name']}</h1>
        <p class="service-benefit-headline">{svc['benefit_headline']}</p>
        <p class="page-hero-lead">{svc['lead']}</p>
        <p class="phone-line"><a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
      </div>
    </section>
    <section class="section section-warm">
      <div class="container service-detail-inner">
        <div class="service-detail-body">
          {paragraphs}
        </div>
        <h2 class="section-title section-title-sm">How we help families in Middle Tennessee</h2>
        <ul class="service-detail-bullets">{bullets}</ul>
        <h2 class="section-title section-title-sm">Local examples</h2>
        <div class="local-examples-grid">{examples}</div>
        {render_related_links(svc)}
        <p class="back-to-services"><a href="/services/">← Back to All Services</a></p>
        {internal_links()}
      </div>
    </section>
    <section class="section section-green service-page-cta">
      <div class="container narrow">
        <h2 class="section-title section-title-light">You do not have to figure this out alone</h2>
        <p class="section-lead section-lead-light">Whether you are in Wilson County, Sumner County, the Nashville area, Brentwood, Mt. Juliet, or anywhere in Middle Tennessee — one call connects you to compassion, clarity, and a free Guardian Kit. No pressure. Your timeline.</p>
        <div class="detail-cta-row service-cta-row">
          <a href="tel:{PHONE_TEL}" class="btn btn-primary btn-cta-phone">{PHONE_LINK}</a>
          <a href="/roadmap/" class="btn btn-secondary btn-on-green">Get Your Free Guardian Kit</a>
        </div>
        <p class="back-to-services back-to-services-light"><a href="/services/">← Back to All Services</a></p>
      </div>
    </section>"""


def render_service_counties_block() -> str:
    cards = []
    for c in SERVICE_COUNTIES:
        bl = "".join(f"<li>{b}</li>" for b in c["bullets"])
        county_href = f"/counties/#{c['id']}" if c["id"] != "middle-tn" else "/counties/#middle-tn"
        cards.append(f"""
        <article class="county-service-card" id="county-{c['id']}">
          <p class="eyebrow">📍 {c['name']}</p>
          <h3><a href="{county_href}">{c['name']}</a></h3>
          <p class="county-service-cities">{c['cities']}</p>
          <p class="county-service-benefit">{c['benefit']}</p>
          <ul>{bl}</ul>
          <div class="county-service-cta">
            <a href="tel:{PHONE_TEL}" class="btn btn-primary btn-sm">{PHONE_LINK}</a>
            <a href="/roadmap/" class="btn btn-secondary btn-sm">Get your free Guardian Kit</a>
          </div>
        </article>""")
    return f"""
    <section class="section section-green" id="counties-we-serve">
      <div class="container">
        <p class="eyebrow eyebrow-light">Local expertise</p>
        <h2 class="section-title section-title-light">Counties We Serve</h2>
        <p class="section-lead section-lead-light">Probate property support from Nashville to every corner of Middle Tennessee — same Guardian Kit, same compassionate team. Explore our full <a href="/counties/">county guides</a> or call now.</p>
        <div class="county-service-grid">{"".join(cards)}</div>
        <div class="cta-phone-strip">
          <p>Inherited a house in Davidson, Sumner, Wilson, Rutherford, or Williamson? One call starts everything.</p>
          <a href="tel:{PHONE_TEL}" class="btn btn-light">{PHONE_LINK}</a>
          <a href="/roadmap/" class="btn btn-secondary btn-on-green">Get your free Guardian Kit</a>
        </div>
      </div>
    </section>"""

COUNTIES = [
    ("davidson", "Davidson County", "Nashville, Hermitage, Madison, Antioch, Bellevue",
     "Davidson County Probate Court moves fast — we coordinate property timelines with your attorney while you grieve."),
    ("sumner", "Sumner County", "Gallatin, Hendersonville, Portland, Westmoreland",
     "Sumner heirs trust us for Lebanon-adjacent expertise and Gallatin-area probate property support."),
    ("wilson", "Wilson County", "Lebanon, Mt. Juliet, Watertown, Wilson County lake communities",
     "Wilson County is home base — deep court knowledge and local vendor rolodex."),
    ("rutherford", "Rutherford County", "Murfreesboro, Smyrna, La Vergne, Eagleville",
     "Rutherford estates often involve multiple heirs — we run neutral Net Sheets everyone trusts."),
    ("williamson", "Williamson County", "Franklin, Brentwood, Spring Hill, Thompson's Station",
     "Williamson properties deserve funded-repair analysis — we present real ARV upside with compassion."),
    ("robertson", "Robertson County", "Springfield, White House, Greenbrier, Coopertown",
     "Robertson County families get the same Guardian Kit and vendor network as Nashville."),
    ("cheatham", "Cheatham County", "Ashland City, Kingston Springs, Pegram",
     "Cheatham heirs receive vacant-home insurance guidance and lawn/security coordination."),
    ("dickson", "Dickson County", "Dickson, White Bluff, Charlotte",
     "Dickson County probate properties — cash, list, or muniment paths explained plainly."),
    ("maury", "Maury County", "Columbia, Spring Hill (Maury side), Mt. Pleasant",
     "Maury County estates benefit from Columbia-market CMAs and Columbia-court awareness."),
    ("montgomery", "Montgomery County", "Clarksville, St. Bethlehem, Sango",
     "Montgomery heirs — including military families — get out-of-state heir shipping and cash options."),
    ("middle-tn", "All of Middle Tennessee", "Every county we can reach with compassion",
     "Not sure which county? One call to Probate Guardians TN — we route you to the right court, vendors, and plan."),
]


def build_services() -> str:
    cards = []
    for svc in enriched_services():
        cards.append(f"""
        <a class="core-card" href="{service_href(svc)}">
          <span class="core-card-icon" aria-hidden="true">{svc['icon']}</span>
          <h2>{svc['name']}</h2>
          <p>{svc['lead']}</p>
          <span class="core-card-arrow">Learn more →</span>
        </a>""")
    crumbs = breadcrumbs([
        ("Home", "/", False),
        ("Services", "/services/", True),
    ])
    body = f"""
    <section class="page-hero">
      <div class="container">
        {crumbs}
        <p class="eyebrow">Probate Guardians TN · Core Services</p>
        <h1>Services for Middle Tennessee Probate Families</h1>
        <p class="page-hero-lead">One support system — the same compassionate tone as your <a href="/roadmap/">Guardian Kit</a>. Twelve dedicated service pages, six core counties, one number: <a href="tel:{PHONE_TEL}">{PHONE_LINK}</a>.</p>
        <p class="phone-line"><a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
        <div class="core-hub-links">
          <a href="/roadmap/" class="btn btn-secondary">Get your free Guardian Kit</a>
          <a href="#counties-we-serve" class="btn btn-secondary">Counties We Serve</a>
          <a href="/counties/" class="btn btn-secondary">Full County Guides</a>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="container">
        <div class="core-card-grid">{"".join(cards)}</div>
        <div class="cta-phone-strip">
          <p>One call. Everything handled. We remove the house burden so you can focus on family.</p>
          <a href="tel:{PHONE_TEL}" class="btn btn-light">{PHONE_LINK}</a>
          <a href="/roadmap/" class="btn btn-secondary btn-on-strip">Get your free Guardian Kit</a>
        </div>
      </div>
    </section>
    {render_service_counties_block()}"""
    return shell(
        "Probate Services Middle Tennessee | Probate Guardians TN",
        "12 probate real estate services for Middle TN heirs — inherited home sales, muniment, cash offers, clean-out, repairs, senior moves, and full estate coordination in Davidson, Sumner, Wilson, Rutherford & Williamson. Call (615) 669-7075.",
        f"{SITE}/services/",
        "../", "../",
        {"svc": True},
        body,
    )


def build_service_page(svc: dict) -> str:
    title = f"{svc['name']} | Probate Guardians TN"
    return shell(
        title,
        svc["meta_description"],
        f"{SITE}/services/{svc['slug']}/",
        "../../", "../../",
        {"svc": True},
        render_service_page_body(svc),
    )


def build_counties() -> str:
    cards = []
    details = []
    for cid, name, cities, note in COUNTIES:
        cards.append(f"""
        <a class="core-card" href="#{cid}">
          <span class="core-card-icon" aria-hidden="true">📍</span>
          <h2>{name}</h2>
          <p>{cities}</p>
          <span class="core-card-arrow">County guide →</span>
        </a>""")
        details.append(f"""
    <article class="county-detail" id="{cid}">
      <div class="container narrow">
        <p class="eyebrow">Counties We Serve</p>
        <h2>{name}</h2>
        <p class="county-cities">{cities}</p>
        <p class="county-detail-lead">{note}</p>
        <ul>
          <li>Free Guardian Kit &amp; <a href="/roadmap/">7-step Family Roadmap</a></li>
          <li>Probate-aware CMA &amp; Net Sheet — complimentary</li>
          <li>Cash offers, funded repairs, or full listing — your choice</li>
          <li>Always <em>subject to court approval</em></li>
        </ul>
        {cta_block('<a href="/services/" class="btn btn-secondary">View All Services</a>')}
        {internal_links()}
      </div>
    </article>""")
    body = f"""
    <section class="page-hero">
      <div class="container">
        <p class="eyebrow">Nashville-based · County-by-county</p>
        <h1>Counties We Serve in Middle Tennessee</h1>
        <p class="page-hero-lead">Probate court knowledge in every county below. Your <a href="/roadmap/">Guardian Kit</a> travels with you — questions? <a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
      </div>
    </section>
    <section class="section">
      <div class="container">
        <div class="core-card-grid">{"".join(cards)}</div>
      </div>
    </section>
    <section class="section section-green">
      <div class="container">
        <div class="cta-phone-strip">
          <p>Inherited a house in Middle TN? One call starts everything.</p>
          <a href="tel:{PHONE_TEL}" class="btn btn-light">{PHONE_LINK}</a>
        </div>
      </div>
    </section>
    <section class="section section-warm">{"".join(details)}
    </section>"""
    return shell(
        "Counties We Serve | Probate Real Estate Middle Tennessee",
        "Probate Guardians TN serves Davidson, Sumner, Wilson, Rutherford, Williamson, Robertson, Cheatham, Dickson, Maury, Montgomery & all of Middle Tennessee. (615) 669-7075.",
        "https://probateguardians.com/counties/",
        "../", "../",
        {"cty": True},
        body,
    )


def build_about() -> str:
    body = f"""
    <section class="page-hero">
      <div class="container">
        <p class="eyebrow">About Probate Guardians TN</p>
        <h1>Scott Hardesty &amp; Branton Walker — Your Probate Support System</h1>
        <p class="page-hero-lead">We built Probate Guardians TN together so Middle Tennessee families never have to figure out inherited property alone. Same compassionate tone as the <a href="/roadmap/">Guardian Kit</a> — one dedicated line: <a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
      </div>
    </section>
    <section class="section section-warm">
      <div class="container">
        <div class="bio-grid">
          <article class="bio-card">
            <div class="bio-photo" aria-hidden="true">SH</div>
            <h2>Scott Hardesty</h2>
            <p class="bio-role">Probate Guardian · Nashville, TN</p>
            <p>Scott coordinates the full system — Guardian Kits, vendor rolodex, Net Sheets, Express Offers, and attorney loop-ins. He is your family's Project Coordinator, not just a Realtor.</p>
          </article>
          <article class="bio-card">
            <div class="bio-photo" aria-hidden="true">BW</div>
            <h2>Branton Walker</h2>
            <p class="bio-role">Probate Guardian · Field Partner</p>
            <p>Branton walks with families in the field — compassionate calls, property visits, and warm handoffs. He delivers the human side of the support system Scott built.</p>
          </article>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="container narrow">
        <h2 class="section-title">Our Promise</h2>
        <p class="section-lead">You should not have to be the project manager of your own grief.</p>
        <ul class="county-list" style="margin-top:1rem;">
          <li><strong>Zero pressure</strong> — your timeline, not ours</li>
          <li><strong>Real numbers</strong> — Net Sheets, not Zillow guesses</li>
          <li><strong>Court-aware</strong> — subject to court approval, always</li>
          <li><strong>One call</strong> — vendors, buyers, clean-out, insurance, signage</li>
        </ul>
        <div class="cta-phone-strip" style="margin-top:2rem;">
          <p>Ready when you are — no answers required today.</p>
          <a href="tel:{PHONE_TEL}" class="btn btn-light">{PHONE_LINK}</a>
          <br /><br />
          <a href="/roadmap/" class="btn btn-secondary" style="background:transparent;border-color:#fff;color:#fff;">Free Family Roadmap</a>
        </div>
        <p class="internal-links" style="margin-top:2rem;">Explore <a href="/services/">all services</a> · <a href="/counties/">counties we serve</a> · <a href="/#contact">contact</a></p>
      </div>
    </section>"""
    return shell(
        "About Us | Scott Hardesty & Branton Walker — Probate Guardians TN",
        "Meet Scott Hardesty and Branton Walker — the Probate Guardians TN support system for inherited property in Middle Tennessee. Call or text (615) 669-7075.",
        "https://probateguardians.com/about/",
        "../", "../",
        {"abt": True},
        body,
    )


def main():
    root = Path(__file__).parent
    (root / "services").mkdir(exist_ok=True)
    (root / "counties").mkdir(exist_ok=True)
    (root / "about").mkdir(exist_ok=True)
    (root / "services" / "index.html").write_text(build_services(), encoding="utf-8")
    built = ["services/index.html"]
    for svc in enriched_services():
        svc_dir = root / "services" / svc["slug"]
        svc_dir.mkdir(exist_ok=True)
        (svc_dir / "index.html").write_text(build_service_page(svc), encoding="utf-8")
        built.append(f"services/{svc['slug']}/index.html")
    (root / "counties" / "index.html").write_text(build_counties(), encoding="utf-8")
    (root / "about" / "index.html").write_text(build_about(), encoding="utf-8")
    print(f"Built {len(built)} service pages + counties/, about/")
    for path in built:
        print(f"  · {path}")


if __name__ == "__main__":
    main()