#!/usr/bin/env python3
"""Generate Core 30 static pages — run once when structure changes."""
from pathlib import Path

from _counties_data import CORE_COUNTIES, COUNTY_BY_SLUG, OTHER_COUNTIES
from _services_data import SERVICES, SERVICE_COUNTIES
from _service_meta import SERVICE_META

SITE = "https://probateguardians.com"

PHONE = "(615) 669-7075"
PHONE_TEL = "6156697075"
PHONE_LINK = f'Call or text <strong>{PHONE}</strong>'

# TN TREC Rule 1260-02-.12 — firm name + firm phone on every page
FOOTER_TREC = """      <div class="footer-trec" role="contentinfo" aria-label="Tennessee real estate brokerage disclosure">
        <p class="footer-trec-line">
          Scott Hardesty, <span class="firm-name">eXp Realty</span>
          <span class="footer-trec-sep" aria-hidden="true">|</span>
          Branton Walker, <span class="firm-name">The Forward Realty Group LLC</span>
        </p>
        <p class="footer-trec-phones">
          <span class="firm-name">eXp Realty</span> 888-519-5113
          <span class="footer-trec-sep" aria-hidden="true">·</span>
          <span class="firm-name">The Forward Realty Group LLC</span> (615) 554-4890
        </p>
      </div>"""

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
  <link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png" />
  <link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16.png" />
  <link rel="apple-touch-icon" href="/images/apple-touch-icon.png" />
  <link rel="icon" href="/images/pg-logo.png" type="image/png" />
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="container header-inner">
      <a href="/" class="logo" aria-label="Probate Guardians TN home">
        <img src="/images/pg-logo.png" alt="" class="logo-img" width="40" height="40" decoding="async" />
        <span class="logo-text">Probate Guardians <span class="logo-accent">TN</span></span>
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
{FOOTER_TREC}
      <p class="footer-disclaimer">
        Probate Guardians TN · Serving all of Middle Tennessee · Call or text <strong>{PHONE}</strong><br />
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


def service_href_slug(slug: str) -> str:
    return f"/services/{slug}/"


def county_href(county: dict) -> str:
    return f"/counties/{county['slug']}/"


def county_href_slug(slug: str) -> str:
    return f"/counties/{slug}/"


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


def render_core_county_cards(dark: bool = False) -> str:
    cards = []
    for c in CORE_COUNTIES:
        sc = next((x for x in SERVICE_COUNTIES if x["id"] == c["id"]), None)
        benefit = sc["benefit"] if sc else c["lead"]
        cards.append(f"""
        <a class="core-card{" core-card-dark" if dark else ""}" href="{county_href(c)}">
          <span class="core-card-icon" aria-hidden="true">📍</span>
          <h2>{c['name']}</h2>
          <p>{c['cities']}</p>
          <span class="core-card-arrow">County guide →</span>
        </a>""")
    return "".join(cards)


def render_service_counties_block() -> str:
    cards = []
    for c in CORE_COUNTIES:
        sc = next((x for x in SERVICE_COUNTIES if x["id"] == c["id"]), None)
        bl = "".join(f"<li>{b}</li>" for b in (sc["bullets"][:3] if sc else []))
        cards.append(f"""
        <article class="county-service-card" id="county-{c['id']}">
          <p class="eyebrow">📍 {c['name']}</p>
          <h3><a href="{county_href(c)}">{c['name']}</a></h3>
          <p class="county-service-cities">{c['cities']}</p>
          <p class="county-service-benefit">{c['headline']}</p>
          <ul>{bl}</ul>
          <div class="county-service-cta">
            <a href="{county_href(c)}" class="btn btn-secondary btn-sm">County guide →</a>
            <a href="tel:{PHONE_TEL}" class="btn btn-primary btn-sm">{PHONE_LINK}</a>
          </div>
        </article>""")
    middle = next(x for x in SERVICE_COUNTIES if x["id"] == "middle-tn")
    cards.append(f"""
        <article class="county-service-card" id="county-middle-tn">
          <p class="eyebrow">📍 {middle['name']}</p>
          <h3><a href="/counties/">{middle['name']}</a></h3>
          <p class="county-service-cities">{middle['cities']}</p>
          <p class="county-service-benefit">{middle['benefit']}</p>
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
        <p class="section-lead section-lead-light">Inherited a house in Davidson, Sumner, Wilson, Williamson, or Rutherford County? Each county has a dedicated guide with local probate flavor, city-by-city support, and links to every service your family may need. Same Guardian Kit, same compassionate team — explore <a href="/counties/">all county guides</a> or call now.</p>
        <div class="county-service-grid">{"".join(cards)}</div>
        <div class="cta-phone-strip">
          <p>Inherited a house in Middle Tennessee? One call starts everything.</p>
          <a href="tel:{PHONE_TEL}" class="btn btn-light">{PHONE_LINK}</a>
          <a href="/roadmap/" class="btn btn-secondary btn-on-green">Get your free Guardian Kit</a>
        </div>
      </div>
    </section>"""


def render_county_related(county: dict) -> str:
    svc_parts = [
        f'<a href="{service_href_slug(slug)}">{label}</a>'
        for label, slug in county["related_services"]
    ]
    county_parts = [
        f'<a href="{county_href_slug(slug)}">{COUNTY_BY_SLUG[slug]["name"]}</a>'
        for slug in county["related_counties"]
    ]
    return f"""
    <div class="related-services-block">
      <h3 class="related-services-title">Services for {county['name']}</h3>
      <p class="service-related">{" · ".join(svc_parts)}</p>
      <h3 class="related-services-title">Nearby counties</h3>
      <p class="service-related">{" · ".join(county_parts)} · <a href="/counties/">All Counties</a> · <a href="/roadmap/">Family Roadmap</a> · <a href="/services/">All Services</a> · <a href="/">Home</a></p>
    </div>"""


def render_county_page_body(county: dict) -> str:
    paragraphs = "".join(f"<p>{p}</p>" for p in county["paragraphs"])
    challenges = "".join(f"<li>{c}</li>" for c in county["challenges"])
    helps = "".join(f"<li>{h}</li>" for h in county["how_we_help"])
    crumbs = breadcrumbs([
        ("Home", "/", False),
        ("Counties", "/counties/", False),
        (county["name"], county_href(county), True),
    ])
    return f"""
    <section class="page-hero page-hero-service">
      <div class="container service-detail-inner">
        {crumbs}
        <p class="eyebrow">📍 Probate Guardians TN · {county['name']}</p>
        <h1>{county['headline']}</h1>
        <p class="county-cities county-cities-hero">{county['cities']}</p>
        <p class="page-hero-lead">{county['lead']}</p>
        <p class="phone-line"><a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
      </div>
    </section>
    <section class="section section-warm">
      <div class="container service-detail-inner">
        <div class="service-detail-body">
          {paragraphs}
        </div>
        <h2 class="section-title section-title-sm">Common probate challenges in {county['name']}</h2>
        <ul class="service-detail-bullets county-challenges-list">{challenges}</ul>
        <h2 class="section-title section-title-sm">How Probate Guardians TN helps {county['name']} families</h2>
        <ul class="service-detail-bullets">{helps}</ul>
        {render_county_related(county)}
        <p class="back-to-services"><a href="/counties/">← Back to All Counties</a></p>
        <p class="internal-links">Also explore: <a href="/">Home</a> · <a href="/roadmap/">Guardian Kit &amp; Family Roadmap</a> · <a href="/services/">All Services</a> · <a href="/counties/">Counties We Serve</a> · <a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
      </div>
    </section>
    <section class="section section-green service-page-cta">
      <div class="container narrow">
        <h2 class="section-title section-title-light">{county['name']} heirs — we are ready when you are</h2>
        <p class="section-lead section-lead-light">No pressure. No obligation. One call connects you to a free Guardian Kit, a complimentary Net Sheet, and a team that understands {county['name']} probate property.</p>
        <div class="detail-cta-row service-cta-row">
          <a href="tel:{PHONE_TEL}" class="btn btn-primary btn-cta-phone">{PHONE_LINK}</a>
          <a href="/roadmap/" class="btn btn-secondary btn-on-green">Get Your Free Guardian Kit</a>
        </div>
        <p class="back-to-services back-to-services-light"><a href="/counties/">← Back to All Counties</a></p>
      </div>
    </section>"""


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
    other_cards = []
    for cid, name, cities, note in OTHER_COUNTIES:
        other_cards.append(f"""
        <article class="county-other-card">
          <h3>{name}</h3>
          <p class="county-other-cities">{cities}</p>
          <p>{note}</p>
        </article>""")
    crumbs = breadcrumbs([
        ("Home", "/", False),
        ("Counties", "/counties/", True),
    ])
    body = f"""
    <section class="page-hero">
      <div class="container">
        {crumbs}
        <p class="eyebrow">Nashville-based · County-by-county</p>
        <h1>Counties We Serve in Middle Tennessee</h1>
        <p class="page-hero-lead">Probate property is local — court rhythms in Gallatin differ from Franklin, and Mt. Juliet families face different challenges than Murfreesboro heirs. Probate Guardians TN built dedicated county guides for our five core counties, plus support across all of Middle Tennessee. Your <a href="/roadmap/">Guardian Kit</a> travels with you. Questions? <a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
        <p class="phone-line"><a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
        <div class="core-hub-links">
          <a href="/roadmap/" class="btn btn-secondary">Get your free Guardian Kit</a>
          <a href="/services/" class="btn btn-secondary">All Services</a>
        </div>
      </div>
    </section>
    <section class="section section-warm" id="core-counties">
      <div class="container">
        <h2 class="section-title">Core counties we serve</h2>
        <p class="section-lead">Tap your county for localized probate property guidance — cities, common challenges, and services that fit.</p>
        <div class="core-card-grid">{render_core_county_cards()}</div>
      </div>
    </section>
    <section class="section section-green">
      <div class="container">
        <div class="cta-phone-strip">
          <p>Inherited a house in Davidson, Sumner, Wilson, Williamson, or Rutherford? One call starts everything.</p>
          <a href="tel:{PHONE_TEL}" class="btn btn-light">{PHONE_LINK}</a>
          <a href="/roadmap/" class="btn btn-secondary btn-on-green">Get your free Guardian Kit</a>
        </div>
      </div>
    </section>
    <section class="section">
      <div class="container">
        <h2 class="section-title">Also serving across Middle Tennessee</h2>
        <p class="section-lead">Robertson, Cheatham, Dickson, Maury, Montgomery, and beyond — same Guardian Kit, same vendor network, same compassionate team.</p>
        <div class="county-other-grid">{"".join(other_cards)}</div>
        <p class="internal-links" style="margin-top:1.5rem;border-top:none;padding-top:0;">Explore <a href="/services/">all services</a> · <a href="/roadmap/">Family Roadmap</a> · <a href="/">home</a></p>
      </div>
    </section>"""
    return shell(
        "Counties We Serve | Probate Real Estate Middle Tennessee",
        "Probate Guardians TN serves Davidson, Sumner, Wilson, Rutherford & Williamson counties with dedicated guides — plus all of Middle Tennessee. Inherited home help. (615) 669-7075.",
        f"{SITE}/counties/",
        "../", "../",
        {"cty": True},
        body,
    )


def build_county_page(county: dict) -> str:
    title = f"{county['name']} Probate Real Estate | Probate Guardians TN"
    return shell(
        title,
        county["meta_description"],
        f"{SITE}/counties/{county['slug']}/",
        "../../", "../../",
        {"cty": True},
        render_county_page_body(county),
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
    county_built = ["counties/index.html"]
    for county in CORE_COUNTIES:
        county_dir = root / "counties" / county["slug"]
        county_dir.mkdir(exist_ok=True)
        (county_dir / "index.html").write_text(build_county_page(county), encoding="utf-8")
        county_built.append(f"counties/{county['slug']}/index.html")
    (root / "about" / "index.html").write_text(build_about(), encoding="utf-8")
    print(f"Built {len(built)} service pages + {len(county_built)} county pages + about/")
    for path in built + county_built:
        print(f"  · {path}")


if __name__ == "__main__":
    main()