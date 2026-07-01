"""AI Agent Lead Harvester tab — isolated module; does not modify other CRM tabs."""
import json
import re
import sys
from datetime import datetime

import streamlit as st


class _LazyCRM:
    _mod = None

    def __getattr__(self, name: str):
        if self._mod is None:
            self._mod = sys.modules.get("__main__")
        return getattr(self._mod, name)


crm = _LazyCRM()

AGENT_CSS = """
<style>
    .agent-links {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 0.75rem 0.85rem;
        margin-bottom: 0.85rem;
        font-size: 0.88rem;
        line-height: 1.65;
    }
    .agent-links a { color: #58a6ff; font-weight: 600; text-decoration: none; }
    .agent-paste-zone {
        background: linear-gradient(135deg, #0d1117 0%, #23863618 100%);
        border: 2px solid #3fb950;
        border-radius: 14px;
        padding: 1rem 1.05rem;
        margin-bottom: 0.75rem;
        color: #e6edf3;
    }
    .agent-paste-label {
        font-size: 0.95rem;
        font-weight: 700;
        color: #3fb950;
        margin-bottom: 0.45rem;
    }
    .agent-btn-green-marker { display: none; }
    .agent-btn-green-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0d2818 0%, #238636 45%, #2ea043 100%) !important;
        border: 2px solid #3fb950 !important;
        color: #fff !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        min-height: 3.75rem !important;
        box-shadow: 0 8px 28px rgba(46, 160, 67, 0.45) !important;
    }
    .agent-step-marker { display: none; }
    .agent-step-marker + div[data-testid="stButton"] > button {
        min-height: 2.85rem !important;
        font-weight: 700 !important;
    }
</style>
"""

AGENT_HARVEST_LINKS = {
    "tnpublicnotice.com": "https://www.tnpublicnotice.com/",
    "Gallatin News": "https://www.gallatinnews.com/",
    "Sumner County Assessor": "https://sumnertn.geopowered.com/propertysearch/",
    "Hendersonville Standard": "https://www.hendersonvillestandard.com/",
}
AGENT_QUEUE_NOTE = "Newspaper Scrape • High Potential Asset"
AGENT_SUMNER_CITIES = (
    "Hendersonville", "Gallatin", "Portland", "White House", "Cottontown",
    "Westmoreland", "Mitchellville", "Bethpage",
)
AGENT_NOTICE_SPLIT_RE = re.compile(
    r"\n\s*\n+|\n(?=(?:NOTICE|Notice|Estate of|IN RE|In Re|Published|Probate|"
    r"Application|Letters Testamentary|Obituary)\b)",
    re.I,
)
AGENT_OBIT_NAME_RE = re.compile(
    r"^([A-Z][a-z]+(?:\s+[A-Z][\.'-]?[a-z]+)+),?\s*(?:age\s*)?(\d{1,3})?,?\s*"
    r"(?:of\s+([\w\s]+?))?(?:\s+passed|\s+died|\s+went|\s*[,.]|\s*$)",
    re.M,
)
AGENT_SURVIVED_RE = re.compile(
    r"survived by\s+(.+?)(?:\.|;|\n|He was|She was|A\s+(?:memorial|service))",
    re.I | re.S,
)
AGENT_PR_ROLE_RE = re.compile(
    r"(?:personal representative|petitioner|executor|executrix|administrator|"
    r"administratrix|applicant)[:\s]+([A-Z][^\n.;]{2,60})",
    re.I,
)
AGENT_DATE_HINT_RE = re.compile(
    r"(?:published|filed|died|passed|deceased)\s+(?:on\s+)?"
    r"([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})",
    re.I,
)


def _init_agent_session_state() -> None:
    st.session_state.setdefault("agent_harvest_results", [])
    st.session_state.setdefault("agent_harvest_raw", "")
    st.session_state.setdefault("agent_harvest_json", "")


def agent_city_hint(address: str, county: str, block: str = "") -> str:
    if address and address != "Address TBD":
        m = re.search(r",\s*([^,]+)\s*,\s*TN\b", address, re.I)
        if m:
            return m.group(1).strip()
    blob = (block or "").lower()
    for city in AGENT_SUMNER_CITIES:
        if city.lower() in blob:
            return city
    if "sumner" in (county or "").lower():
        return "Gallatin"
    return "Middle TN"


def agent_re_score_label(re_score: int, likely_re: bool, address_clue: str) -> str:
    addr_ok = bool(address_clue and address_clue != "Address TBD")
    if (addr_ok and re_score >= 45) or re_score >= 65:
        return "High"
    if re_score >= 30 or likely_re:
        return "Med"
    return "Low"


def agent_generate_bv_search_string(contact: str, address: str, county: str, block: str = "") -> str:
    contact_clean = (contact or "").split("(")[0].strip()
    if contact_clean in ("", "Contact TBD", "POC TBD", "Unknown"):
        return "— need PR/heir name —"
    fn, ln = crm._parse_name_parts(contact_clean)
    city = agent_city_hint(address, county, block)
    if fn and ln:
        return f"{fn} {ln} · {city}, TN"
    return f"{contact_clean} · {city}, TN"


def agent_split_notice_blocks(raw: str) -> list:
    text = (raw or "").strip()
    if not text:
        return []
    blocks = [b.strip() for b in AGENT_NOTICE_SPLIT_RE.split(text) if b.strip()]
    if len(blocks) <= 1 and len(text) > 40:
        return [text]
    return [b for b in blocks if len(b) >= 25]


def agent_parse_notice_block(block: str, default_county: str = "Sumner County") -> dict:
    parsed = crm.parse_court_row_block(block, default_county=default_county)
    obit_m = AGENT_OBIT_NAME_RE.search(block)
    if obit_m and parsed.get("decedent") in ("Unknown Decedent", ""):
        name = crm._clean_person_name(obit_m.group(1))
        if crm._is_valid_decedent(name):
            parsed["decedent"] = name
    pr_heir = parsed.get("contact_name") or parsed.get("heirs") or ""
    if not pr_heir or pr_heir == "Contact TBD":
        pr_m = AGENT_PR_ROLE_RE.search(block)
        if pr_m:
            pr_heir = crm._clean_person_name(pr_m.group(1))
        else:
            surv = AGENT_SURVIVED_RE.search(block)
            if surv:
                pr_heir = surv.group(1).strip()[:80]
    date_hint = parsed.get("filing_date", "")
    if not date_hint:
        dm = AGENT_DATE_HINT_RE.search(block)
        if dm:
            date_hint = dm.group(1).strip()
        elif crm.DATE_RE.search(block):
            date_hint = crm.DATE_RE.search(block).group(0)
    address = parsed.get("address", "Address TBD")
    if address == "Address TBD":
        city_m = re.search(r"\bof\s+([\w\s]+?)(?:\s+passed|\s+died|,|\.)", block, re.I)
        if city_m:
            city = city_m.group(1).strip()
            if city and len(city) < 40:
                address = f"{city}, TN"
    county = parsed.get("county", default_county)
    if "sumner" not in county.lower() and re.search(
        r"\b(Hendersonville|Gallatin|Sumner County|Portland|White House)\b", block, re.I
    ):
        county = "Sumner County"
    return {
        "decedent": parsed.get("decedent", "Unknown Decedent"),
        "date": date_hint or "—",
        "pr_heir": pr_heir or "Contact TBD",
        "address_clue": address,
        "county": county,
        "case_number": parsed.get("case_number", ""),
        "raw": block,
        "re_score": 0,
        "re_score_label": "Low",
        "phone_search_string": "",
        "status": "Parsed",
        "lead_id": "",
        "likely_re": False,
        "is_recent_30": parsed.get("is_recent_30", False),
        "recency_days": parsed.get("recency_days"),
    }


def agent_parse_extract(raw: str, county: str = "Sumner County") -> list:
    blocks = agent_split_notice_blocks(raw)
    if not blocks:
        blocks = crm.split_court_export(raw, default_county=county)
        results = []
        for block in blocks:
            if not block.strip():
                continue
            parsed = crm.parse_court_row_block(block, county)
            results.append({
                "decedent": parsed.get("decedent", "Unknown Decedent"),
                "date": parsed.get("filing_date", "—") or "—",
                "pr_heir": parsed.get("contact_name") or parsed.get("heirs") or "Contact TBD",
                "address_clue": parsed.get("address", "Address TBD"),
                "county": parsed.get("county", county),
                "case_number": parsed.get("case_number", ""),
                "raw": block,
                "re_score": 0,
                "re_score_label": "Low",
                "phone_search_string": "",
                "status": "Parsed",
                "lead_id": "",
                "likely_re": False,
                "is_recent_30": parsed.get("is_recent_30", False),
                "recency_days": parsed.get("recency_days"),
            })
        return results
    return [agent_parse_notice_block(b, default_county=county) for b in blocks]


def agent_detect_re_likelihood(results: list) -> list:
    for row in results:
        assess = crm.assess_re_likelihood({
            "address": row.get("address_clue", ""),
            "raw": row.get("raw", ""),
            "county": row.get("county", ""),
            "has_real_estate": row.get("address_clue", "") not in ("", "Address TBD"),
            "is_recent_30": row.get("is_recent_30", False),
            "recency_days": row.get("recency_days"),
        })
        row["re_score"] = assess["re_score"]
        row["likely_re"] = assess["likely_re"]
        row["re_signals"] = assess.get("re_signals", [])
        row["re_score_label"] = agent_re_score_label(
            assess["re_score"], assess["likely_re"], row.get("address_clue", "")
        )
        row["status"] = "RE Scored"
    results.sort(
        key=lambda x: (
            {"High": 3, "Med": 2, "Low": 1}.get(x.get("re_score_label", "Low"), 0),
            x.get("re_score", 0),
        ),
        reverse=True,
    )
    return results


def agent_generate_bv_strings(results: list) -> list:
    for row in results:
        row["phone_search_string"] = agent_generate_bv_search_string(
            row.get("pr_heir", ""),
            row.get("address_clue", ""),
            row.get("county", "Sumner County"),
            row.get("raw", ""),
        )
        lookups = crm.lookup_urls(
            row.get("pr_heir", ""),
            row.get("address_clue", ""),
            row.get("county", ""),
        )
        row["beenverified_url"] = lookups.get("beenverified", "")
        if row.get("status") != "Queued":
            row["status"] = "BV Ready"
    return results


def agent_push_row_to_branton(row: dict) -> bool:
    if row.get("re_score_label") != "High":
        return False
    if row.get("status") == "Queued" and row.get("lead_id"):
        return False
    decedent = (row.get("decedent") or "").strip()
    if not decedent or decedent == "Unknown Decedent":
        return False
    notes = AGENT_QUEUE_NOTE
    if row.get("phone_search_string") and "need PR" not in row["phone_search_string"]:
        notes += f" · BV: {row['phone_search_string']}"
    lead = crm.add_confirmed_hot_lead(
        decedent=decedent,
        case_number=row.get("case_number", ""),
        filing_date=row.get("date", "") if row.get("date") != "—" else "",
        poc_field=row.get("pr_heir", ""),
        address=row.get("address_clue", "Address TBD"),
        notes=notes,
        county=row.get("county", "Sumner County"),
    )
    lead["source"] = "ai_agent_harvester"
    row["status"] = "Queued"
    row["lead_id"] = lead.get("id", "")
    return True


def agent_push_all_high_score(results: list) -> int:
    pushed = 0
    for row in results:
        if agent_push_row_to_branton(row):
            pushed += 1
    if pushed:
        crm.commit_leads_and_reload()
        st.session_state.branton_queue_flash = (
            f"🔥 **{pushed}** high-score leads pushed to {crm.PARTNER_NAME}'s HOT queue"
        )
    return pushed


def agent_run_full_pipeline(raw: str, county: str = "Sumner County") -> list:
    results = agent_parse_extract(raw, county=county)
    results = agent_detect_re_likelihood(results)
    results = agent_generate_bv_strings(results)
    agent_push_all_high_score(results)
    return results


def agent_results_for_export(results: list) -> list:
    export = []
    for row in results:
        export.append({
            "decedent": row.get("decedent", ""),
            "date": row.get("date", ""),
            "pr_heir": row.get("pr_heir", ""),
            "address_clue": row.get("address_clue", ""),
            "real_estate_score": row.get("re_score_label", "Low"),
            "re_score_numeric": row.get("re_score", 0),
            "phone_search_string": row.get("phone_search_string", ""),
            "beenverified_url": row.get("beenverified_url", ""),
            "status": row.get("status", ""),
            "county": row.get("county", ""),
            "case_number": row.get("case_number", ""),
            "lead_id": row.get("lead_id", ""),
            "source_note": AGENT_QUEUE_NOTE,
        })
    return export


def render_ai_agent_lead_harvester(leads: list) -> None:
    """Self-contained AI Agent tab — no side effects on other tabs."""
    run_serial = st.session_state.get("_run_serial", 0)
    if st.session_state.get("_agent_done_serial") == run_serial:
        return

    _init_agent_session_state()
    st.markdown(AGENT_CSS, unsafe_allow_html=True)

    link_bits = " | ".join(
        f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in AGENT_HARVEST_LINKS.items()
    )
    st.markdown(f'<div class="agent-links">Quick links: {link_bits}</div>', unsafe_allow_html=True)

    st.markdown('<div class="agent-paste-zone">', unsafe_allow_html=True)
    st.markdown(
        '<div class="agent-paste-label">Paste raw obituaries, Notice to Creditors, '
        'or court text here</div>',
        unsafe_allow_html=True,
    )
    raw = st.text_area(
        "Agent harvest paste",
        value=st.session_state.get("agent_harvest_raw", ""),
        height=260,
        key="agent_harvest_paste",
        label_visibility="collapsed",
        placeholder="Paste tnpublicnotice.com clips, Gallatin News obits, Notice to Creditors, court exports…",
    )
    county = st.selectbox(
        "Default county",
        list(crm.MIDDLE_TN_COUNTY_LINKS.keys()),
        index=list(crm.MIDDLE_TN_COUNTY_LINKS.keys()).index("Sumner County"),
        key="agent_harvest_county",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="agent-btn-green-marker"></div>', unsafe_allow_html=True)
    if st.button("🚀 Run Full Agent Pipeline", use_container_width=True, type="primary", key="agent_full_pipeline"):
        if not raw.strip():
            st.warning("Paste raw text first.")
        else:
            st.session_state.agent_harvest_raw = raw
            st.session_state.agent_harvest_results = agent_run_full_pipeline(raw, county=county)
            st.session_state.agent_harvest_json = json.dumps(
                agent_results_for_export(st.session_state.agent_harvest_results), indent=2
            )
            high_n = sum(1 for r in st.session_state.agent_harvest_results if r.get("re_score_label") == "High")
            queued_n = sum(1 for r in st.session_state.agent_harvest_results if r.get("status") == "Queued")
            st.success(
                f"✅ **{len(st.session_state.agent_harvest_results)}** records · "
                f"**{high_n}** High · **{queued_n}** queued"
            )
            st.rerun()

    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown('<div class="agent-step-marker"></div>', unsafe_allow_html=True)
        if st.button("Parse & Extract", use_container_width=True, key="agent_step_parse"):
            if not raw.strip():
                st.warning("Paste raw text first.")
            else:
                st.session_state.agent_harvest_raw = raw
                st.session_state.agent_harvest_results = agent_parse_extract(raw, county=county)
                st.session_state.agent_harvest_json = json.dumps(
                    agent_results_for_export(st.session_state.agent_harvest_results), indent=2
                )
                st.success(f"✅ **{len(st.session_state.agent_harvest_results)}** extracted")
                st.rerun()
    with s2:
        st.markdown('<div class="agent-step-marker"></div>', unsafe_allow_html=True)
        if st.button("Detect Real Estate", use_container_width=True, key="agent_step_re"):
            results = st.session_state.get("agent_harvest_results", [])
            if not results:
                st.warning("Run **Parse & Extract** first.")
            else:
                st.session_state.agent_harvest_results = agent_detect_re_likelihood(results)
                st.session_state.agent_harvest_json = json.dumps(
                    agent_results_for_export(st.session_state.agent_harvest_results), indent=2
                )
                st.success("✅ Real estate scored")
                st.rerun()
    with s3:
        st.markdown('<div class="agent-step-marker"></div>', unsafe_allow_html=True)
        if st.button("Generate Phone Searches", use_container_width=True, key="agent_step_bv"):
            results = st.session_state.get("agent_harvest_results", [])
            if not results:
                st.warning("Run **Parse & Extract** first.")
            else:
                if results[0].get("re_score", 0) == 0 and results[0].get("status") == "Parsed":
                    results = agent_detect_re_likelihood(results)
                st.session_state.agent_harvest_results = agent_generate_bv_strings(results)
                st.session_state.agent_harvest_json = json.dumps(
                    agent_results_for_export(st.session_state.agent_harvest_results), indent=2
                )
                st.success("✅ Phone searches ready")
                st.rerun()
    with s4:
        st.markdown('<div class="agent-step-marker"></div>', unsafe_allow_html=True)
        if st.button("Push to Branton 🔥", use_container_width=True, key="agent_step_push"):
            results = st.session_state.get("agent_harvest_results", [])
            if not results:
                st.warning("Complete earlier steps first.")
            else:
                if not results[0].get("phone_search_string"):
                    results = agent_detect_re_likelihood(results)
                    results = agent_generate_bv_strings(results)
                n = agent_push_all_high_score(results)
                st.session_state.agent_harvest_results = results
                st.session_state.agent_harvest_json = json.dumps(
                    agent_results_for_export(results), indent=2
                )
                if n:
                    st.success(f"🔥 **{n}** pushed to Branton queue")
                else:
                    st.info("No new High-score leads to push.")
                st.rerun()

    results = st.session_state.get("agent_harvest_results", [])
    if results:
        table_rows = [
            {
                "Decedent": row.get("decedent", ""),
                "Date": row.get("date", ""),
                "PR/Heir": row.get("pr_heir", ""),
                "Address Clue": row.get("address_clue", ""),
                "Real Estate Score": row.get("re_score_label", "Low"),
                "Phone Search String": row.get("phone_search_string", ""),
                "Status": row.get("status", ""),
            }
            for row in results
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        j1, j2 = st.columns(2)
        with j1:
            if st.button("📋 Copy JSON for Hermes/Open Claw", use_container_width=True, key="agent_copy_json"):
                st.session_state.agent_harvest_json = json.dumps(
                    agent_results_for_export(results), indent=2
                )
        with j2:
            if st.button("✅ Add High-Score Leads to Branton Queue", use_container_width=True, key="agent_push_all_high"):
                n = agent_push_all_high_score(results)
                st.session_state.agent_harvest_results = results
                st.session_state.agent_harvest_json = json.dumps(
                    agent_results_for_export(results), indent=2
                )
                if n:
                    st.success(f"🔥 **{n}** added to Branton queue")
                    st.rerun()
                else:
                    st.info("No new High-score leads to add.")

        if st.session_state.get("agent_harvest_json"):
            st.text_area(
                "JSON for Hermes / Open Claw (select all → copy)",
                value=st.session_state.agent_harvest_json,
                height=200,
                key="agent_json_display",
                label_visibility="collapsed",
            )

    st.session_state["_agent_done_serial"] = run_serial