"""Newspaper Scraper tab — fully isolated; no changes to other CRM tabs."""
import re
import sys

import streamlit as st


class _LazyCRM:
    _mod = None

    def __getattr__(self, name: str):
        if self._mod is None:
            self._mod = sys.modules.get("__main__")
        return getattr(self._mod, name)


crm = _LazyCRM()

SCRAPER_CSS = """
<style>
    .ns-links {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 0.75rem 0.85rem;
        margin-bottom: 0.85rem;
        font-size: 0.88rem;
        line-height: 1.65;
    }
    .ns-links a { color: #58a6ff; font-weight: 600; text-decoration: none; }
    .ns-paste-zone {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1rem 1.05rem;
        margin-bottom: 0.75rem;
    }
    .ns-paste-label {
        font-size: 0.95rem;
        font-weight: 700;
        color: #e6edf3;
        margin-bottom: 0.45rem;
    }
    .ns-btn-green-marker { display: none; }
    .ns-btn-green-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0d2818 0%, #238636 45%, #2ea043 100%) !important;
        border: 2px solid #3fb950 !important;
        color: #fff !important;
        font-weight: 800 !important;
        min-height: 3.25rem !important;
    }
</style>
"""

SCRAPER_LINKS = {
    "tnpublicnotice.com": "https://www.tnpublicnotice.com/",
    "Gallatin News": "https://www.gallatinnews.com/",
    "Sumner County Assessor": "https://sumnertn.geopowered.com/propertysearch/",
}

PROBATE_KEYWORDS = ("deceased", "estate of", "notice to creditors", "died on", "in re:", "probate")
ADDRESS_KEYWORDS = (
    "pike", "road", "rd", "drive", "dr", "lane", "ln", "avenue", "ave",
    "street", "st", "court", "ct", "way", "blvd", "gallatin", "hendersonville",
    "portland", "white house",
)
QUEUE_NOTE = "Newspaper Scrape • High Potential Asset"


def _init_session() -> None:
    st.session_state.setdefault("newspaper_scraper_raw", "")
    st.session_state.setdefault("newspaper_scraper_results", [])


def _extract_decedent(line: str) -> str:
    m = re.search(r"estate of\s+(.+?)(?:,|\.|$)", line, re.I)
    if m:
        return m.group(1).strip()[:90]
    m2 = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][\.'-]?[a-z]+)+)", line)
    if m2:
        return m2.group(1).strip()[:90]
    return line[:90]


def _phone_search_string(line: str) -> str:
    words = [w for w in re.sub(r"[^A-Za-z\s]", " ", line).split() if len(w) > 2]
    if len(words) >= 2:
        return f"{words[0]} {words[-1]} · Sumner County, TN"
    return line[:50]


def _score_line(line: str) -> str:
    lower = line.lower()
    if any(word in lower for word in ADDRESS_KEYWORDS):
        return "High"
    if any(kw in lower for kw in PROBATE_KEYWORDS):
        return "Medium"
    return "Low"


def analyze_scraper_text(raw: str) -> list:
    results = []
    for line in [ln.strip() for ln in raw.split("\n") if ln.strip()]:
        if not any(kw in line.lower() for kw in PROBATE_KEYWORDS):
            continue
        score = _score_line(line)
        results.append({
            "decedent": _extract_decedent(line),
            "real_estate_score": score,
            "phone_search_string": _phone_search_string(line),
            "status": "Analyzed",
            "raw": line,
            "county": "Sumner County",
        })
    order = {"High": 3, "Medium": 2, "Low": 1}
    results.sort(key=lambda x: order.get(x["real_estate_score"], 0), reverse=True)
    return results


def push_selected_high_to_queue(results: list, selected_rows: list) -> int:
    pushed = 0
    for row in selected_rows:
        if row.get("real_estate_score") != "High":
            continue
        if row.get("status") == "Queued":
            continue
        decedent = (row.get("decedent") or "").strip()
        if not decedent:
            continue
        notes = QUEUE_NOTE
        if row.get("phone_search_string"):
            notes += f" · {row['phone_search_string']}"
        lead = crm.add_confirmed_hot_lead(
            decedent=decedent,
            address="Address TBD",
            poc_field="Contact TBD",
            notes=notes,
            county=row.get("county", "Sumner County"),
        )
        lead["source"] = "newspaper_scraper"
        row["status"] = "Queued"
        row["lead_id"] = lead.get("id", "")
        pushed += 1
    if pushed:
        crm.commit_leads_and_reload()
        st.session_state.branton_queue_flash = (
            f"🔥 **{pushed}** newspaper leads added to {crm.PARTNER_NAME}'s Call Queue"
        )
    return pushed


def render_newspaper_scraper_tab(leads: list) -> None:
    """Self-contained Newspaper Scraper tab only."""
    run_serial = st.session_state.get("_run_serial", 0)
    if st.session_state.get("_newspaper_done_serial") == run_serial:
        return

    _init_session()
    st.markdown(SCRAPER_CSS, unsafe_allow_html=True)

    link_bits = " | ".join(
        f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in SCRAPER_LINKS.items()
    )
    st.markdown(f'<div class="ns-links">Quick links: {link_bits}</div>', unsafe_allow_html=True)

    st.markdown('<div class="ns-paste-zone">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ns-paste-label">Paste raw obituaries, Notice to Creditors, '
        'or court text here</div>',
        unsafe_allow_html=True,
    )
    raw = st.text_area(
        "Newspaper scraper paste",
        value=st.session_state.get("newspaper_scraper_raw", ""),
        height=320,
        key="newspaper_scraper_paste",
        label_visibility="collapsed",
        placeholder="Paste from tnpublicnotice.com, Gallatin News, obituaries, or court notices…",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="ns-btn-green-marker"></div>', unsafe_allow_html=True)
    if st.button("Analyze & Score Leads", use_container_width=True, type="primary", key="ns_analyze"):
        if not raw.strip():
            st.error("Paste some text first.")
        else:
            st.session_state.newspaper_scraper_raw = raw
            st.session_state.newspaper_scraper_results = analyze_scraper_text(raw)
            if st.session_state.newspaper_scraper_results:
                st.success(f"✅ **{len(st.session_state.newspaper_scraper_results)}** leads analyzed")
            else:
                st.warning("No probate-related lines detected.")
            st.rerun()

    results = st.session_state.get("newspaper_scraper_results", [])
    if results:
        editor_rows = [
            {
                "Select": False,
                "Decedent": row.get("decedent", ""),
                "Real Estate Score": row.get("real_estate_score", "Low"),
                "Phone Search String": row.get("phone_search_string", ""),
                "Status": row.get("status", "Analyzed"),
            }
            for row in results
        ]

        edited = st.data_editor(
            editor_rows,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Check High-score leads to add to Call Queue",
                    default=False,
                ),
                "Decedent": st.column_config.TextColumn("Decedent", disabled=True),
                "Real Estate Score": st.column_config.TextColumn("Real Estate Score", disabled=True),
                "Phone Search String": st.column_config.TextColumn("Phone Search String", disabled=True),
                "Status": st.column_config.TextColumn("Status", disabled=True),
            },
            disabled=["Decedent", "Real Estate Score", "Phone Search String", "Status"],
            hide_index=True,
            use_container_width=True,
            key="newspaper_scraper_table",
        )

        high_selected = []
        for r in edited:
            if not r.get("Select") or r.get("Real Estate Score") != "High":
                continue
            for orig in results:
                if (
                    orig.get("decedent") == r.get("Decedent")
                    and orig.get("phone_search_string") == r.get("Phone Search String")
                ):
                    high_selected.append(orig)
                    break

        if st.button(
            "✅ Add Selected High-Score Leads to Call Queue",
            use_container_width=True,
            type="primary",
            key="ns_push_selected",
        ):
            if not high_selected:
                st.warning("Select at least one **High**-score row in the table.")
            else:
                n = push_selected_high_to_queue(results, high_selected)
                st.session_state.newspaper_scraper_results = results
                if n:
                    st.success(f"🔥 **{n}** leads added to Call Queue")
                    st.rerun()
                else:
                    st.info("No new leads added (may already be queued).")

        st.caption("Only **High**-score rows can be pushed. Status updates to *Queued* after add.")

    st.session_state["_newspaper_done_serial"] = run_serial