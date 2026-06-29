#!/usr/bin/env python3
"""Generate Core 30 static pages — run once when structure changes."""
from pathlib import Path

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
      <a href="/roadmap/" class="btn btn-secondary">Free Guardian Kit Roadmap</a>
      {extra}
    </div>"""


def internal_links() -> str:
    return f"""
    <p class="internal-links">Also explore: <a href="/roadmap/">Guardian Kit &amp; Family Roadmap</a> · <a href="/services/">All Services</a> · <a href="/counties/">Counties We Serve</a> · <a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>"""


SERVICES = [
    ("probate-specialist", "🛡️", "Probate Real Estate Specialist",
     "Court-aware probate property guidance for Middle Tennessee heirs.",
     ["Compassionate first call — no pressure, no pitch", "Coordinate with your probate attorney on authority to sell", "Free CMA & Net Sheet for every heir", "Guardian Kit with real options and vendor network"]),
    ("inherited-home-sales", "🏠", "Inherited Home Sales",
     "Sell an inherited house with clarity — as-is cash, funded repairs, or full MLS.",
     ["Compare list vs. cash on one Net Sheet", "Out-of-state heir coordination", "Sibling buyout feasibility math", "Subject to court approval on all paths"]),
    ("muniment-title", "📜", "Muniment of Title Assistance",
     "Tennessee's faster transfer path when the estate may qualify.",
     ["Education — never legal advice", "Attorney referral from vetted rolodex", "Property valuation for retain-or-sell decisions", "Timeline alignment with muniment filings"]),
    ("cash-offers-probate", "⚡", "Cash Offers for Probate Properties",
     "Multiple competing cash buyers — as-is, no showings, fast certainty.",
     ["Express Offers network through eXp Realty", "48–72 hour competing bids typical", "Ideal for overwhelmed or out-of-state heirs", "Subject to court approval"]),
    ("estate-coordination", "🧭", "Full-Service Estate Coordination",
     "One Project Coordinator — we handle the heavy lifting so you focus on family.",
     ["Vendor dispatch: attorneys, insurance, estate sales", "Weekly status — you always know what's happening", "Attorney loop-ins at every milestone", "Four paths presented with real numbers"]),
    ("cleanout", "📦", "House Clean-Out Coordination",
     "Contents, junk, attic, garage — dispatched and tracked for you.",
     ["Estate sale + haul-off vendors from our rolodex", "Sentimental item shipping for out-of-state heirs", "Dumpster and bulk removal coordination", "$0 upfront options where available"]),
    ("repair-staging", "🔨", "Repair & Staging Coordination",
     "Funded repairs at closing — list at peak value without heir arguments.",
     ["Roof, HVAC, paint, flooring — repaid at settlement", "Light staging for MLS when ARV upside warrants it", "Contractor bids managed by your coordinator", "Compare repair path vs. cash on Net Sheet"]),
    ("senior-move", "💙", "Senior Move Assistance",
     "Care transitions and estate moves with compassion — before and during probate.",
     ["Hospice & skilled-nursing referral support", "Pre-death house burden planning", "Movers and packing for heir relocations", "Medicaid planning introductions — attorney-led"]),
    ("buying-selling", "🔄", "Property Buying & Sales",
     "Buy, sell, or hold inherited property — neutral guidance for the whole family.",
     ["Retention analysis vs. sale proceeds", "Rental / property management referrals", "Traditional listing for maximum net", "Cash backup if listing timeline slips"]),
    ("investing", "📈", "Real Estate Investing",
     "Investor network for estates that need speed, certainty, or as-is exit.",
     ["Multiple vetted cash buyers — never one lowball", "Middle TN investor desk backup bids", "Wholesale-friendly timelines aligned with court", "Transparent comparison on your Net Sheet"]),
    ("sellers-agent", "📋", "Seller's Agent Services",
     "Full MLS representation with probate-aware marketing and disclosure.",
     ["Probate-specific showing and disclosure strategy", "Funded repairs available at closing", "Professional photography and MLS launch", "Commission structure explained on Net Sheet"]),
    ("probate-specialist-field", "🤝", "Probate Real Estate Specialist — Field Team",
     "Branton Walker walks with families in the field — Scott coordinates the system.",
     ["Same-day compassionate callbacks", "Property walk-throughs at your pace", "Guardian Kit delivery at kitchen table", "Mobile-friendly support across Middle TN"]),
]

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
    details = []
    for sid, icon, name, lead, bullets in SERVICES:
        cards.append(f"""
        <a class="core-card" href="#{sid}">
          <span class="core-card-icon" aria-hidden="true">{icon}</span>
          <h2>{name}</h2>
          <p>{lead}</p>
          <span class="core-card-arrow">Learn more →</span>
        </a>""")
        bl = "".join(f"<li>{b}</li>" for b in bullets)
        details.append(f"""
    <article class="service-detail" id="{sid}">
      <div class="container narrow">
        <p class="eyebrow">{icon} Service</p>
        <h2>{name}</h2>
        <p class="service-detail-lead">{lead}</p>
        <ul>{bl}</ul>
        {cta_block()}
        {internal_links()}
      </div>
    </article>""")
    body = f"""
    <section class="page-hero">
      <div class="container">
        <p class="eyebrow">Probate Guardians TN · Core Services</p>
        <h1>Services for Middle Tennessee Probate Families</h1>
        <p class="page-hero-lead">One support system — the same compassionate tone as your <a href="/roadmap/">Guardian Kit</a>. Tap a service below or call <a href="tel:{PHONE_TEL}">{PHONE_LINK}</a>.</p>
        <p class="phone-line"><a href="tel:{PHONE_TEL}">{PHONE_LINK}</a></p>
      </div>
    </section>
    <section class="section">
      <div class="container">
        <div class="core-card-grid">{"".join(cards)}</div>
        <div class="cta-phone-strip">
          <p>One call. Everything handled. We remove the house burden so you can focus on family.</p>
          <a href="tel:{PHONE_TEL}" class="btn btn-light">{PHONE_LINK}</a>
        </div>
      </div>
    </section>
    <section class="section section-warm">{"".join(details)}
    </section>"""
    return shell(
        "Probate Services Middle Tennessee | Probate Guardians TN",
        "12 probate real estate services for Middle TN heirs — inherited home sales, muniment, cash offers, clean-out, repairs, senior moves, and full estate coordination. Call (615) 669-7075.",
        "https://probateguardians.com/services/",
        "../", "../",
        {"svc": True},
        body,
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
    (root / "counties" / "index.html").write_text(build_counties(), encoding="utf-8")
    (root / "about" / "index.html").write_text(build_about(), encoding="utf-8")
    print("Built services/, counties/, about/")


if __name__ == "__main__":
    main()