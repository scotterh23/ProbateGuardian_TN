import base64
import csv
import io
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

# ── Constants ────────────────────────────────────────────────────────────────
PARTNER_NAME = "Branton Walker"
ASSIGN_STATUS = f"Assigned to {PARTNER_NAME}"
LEGACY_ASSIGN_STATUSES = ("Assigned to Brantley", ASSIGN_STATUS)
PIPELINE_STAGES = ["New/Hot", "Warm", "Appt", "Contract", "Closed"]
DETAIL_PIPELINE_STAGES = [
    "🔥 Hot / New (call today)",
    "Warm / Talking",
    "Nurture / Call Back",
    "Not Interested / Keeping",
    "Appointment Set",
    "Listed / Under Contract",
    "Closed / Sold",
    "Archived",
]
NURTURE_STAGE = "Nurture / Call Back"
LEGACY_TO_DETAIL = {
    "New/Hot": "🔥 Hot / New (call today)",
    "Warm": "Warm / Talking",
    "Appt": "Appointment Set",
    "Contract": "Listed / Under Contract",
    "Closed": "Closed / Sold",
    "Cold": "Warm / Talking",
}
DETAIL_TO_ANALYTICS = {
    "🔥 Hot / New (call today)": "New/Hot",
    "Warm / Talking": "Warm",
    "Nurture / Call Back": "Warm",
    "Not Interested / Keeping": "Warm",
    "Appointment Set": "Appt",
    "Listed / Under Contract": "Contract",
    "Closed / Sold": "Closed",
    "Archived": "Closed",
}
CLOSED_DETAIL_STAGES = {"Closed / Sold", "Archived"}
HIGH_SCORE_THRESHOLD = 65
HEAT_WINDOW_DAYS = 60

STATUS_TO_PIPELINE = {
    "New/Hot": "New/Hot",
    "Warm": "Warm",
    "New": "New/Hot",
    "Qualified": "New/Hot",
    "Needs Review": "Warm",
    "Low Priority": "Warm",
    "Contacted": "Warm",
    ASSIGN_STATUS: "Warm",
    "Assigned to Brantley": "Warm",
    "Under Contract": "Contract",
    "Closed": "Closed",
    "Cold": "Warm",
}

st.set_page_config(
    page_title="ProbateGuardian Free TN",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

LEADS_FILE = (Path(__file__).resolve().parent / "leads_data.json")
GITHUB_REPO = "scotterh23/ProbateGuardian_TN"
GITHUB_LEADS_PATH = "leads_data.json"
GITHUB_BRANCH = "main"

# ── Dark theme CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(160deg, #0d1117 0%, #161b22 45%, #1a1f2e 100%);
        color: #e6edf3;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid #30363d;
    }
    h1, h2, h3, h4 { color: #f0f6fc !important; }
    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #79c0ff, #a5d6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-sub {
        color: #8b949e;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .phone-banner {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-size: 1.4rem;
        font-weight: 700;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(46, 160, 67, 0.35);
        letter-spacing: 0.5px;
    }
    .status-new { color: #58a6ff; font-weight: 600; }
    .status-assigned { color: #d29922; font-weight: 600; }
    .status-qualified { color: #3fb950; font-weight: 600; }
    .status-contacted { color: #a371f7; font-weight: 600; }
    .pipe-newhot { color: #ff7b72; font-weight: 700; }
    .pipe-warm { color: #58a6ff; font-weight: 600; }
    .pipe-cold { color: #8b949e; font-weight: 600; }
    .dash-notes-marker { display: none; }
    .dash-notes-marker + div[data-testid="stTextArea"] textarea {
        min-height: 12rem !important;
        font-size: 0.95rem !important;
        line-height: 1.55 !important;
        resize: vertical !important;
        color: #e6edf3 !important;
    }

    .pipe-appt { color: #d29922; font-weight: 600; }
    .pipe-contract { color: #a371f7; font-weight: 600; }
    .pipe-closed { color: #3fb950; font-weight: 600; }
    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #238636, #2ea043);
        color: white;
        border: none;
        font-weight: 600;
        border-radius: 8px;
        transition: transform 0.15s ease;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
    }
    .stTextArea textarea, .stTextInput input {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #30363d !important;
    }
    .crm-top-filters-start { display: none; }
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] {
        align-items: stretch !important;
        margin-bottom: 0.25rem !important;
    }
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] [data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-end !important;
    }
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] [data-testid="stVerticalBlock"] {
        width: 100% !important;
        justify-content: flex-end !important;
    }
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] [data-testid="stButton"] {
        width: 100% !important;
    }
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
        width: 100% !important;
        min-height: 2.75rem !important;
        height: 2.75rem !important;
        padding: 0.5rem 1rem !important;
        margin: 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(1) [data-testid="stButton"] > button {
        background: linear-gradient(135deg, #d29922, #f0b429) !important;
        color: #0d1117 !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(240, 180, 41, 0.45) !important;
    }
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] [data-testid="column"]:nth-child(2) [data-testid="stButton"] > button {
        background: linear-gradient(135deg, #30363d, #484f58) !important;
        color: #f0f6fc !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button:hover {
        transform: none !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
    }
    .crm-quick-stage-start { display: none; }
    .crm-quick-stage-start + div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
        min-height: 3.1rem !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        white-space: normal !important;
        line-height: 1.25 !important;
        padding: 0.55rem 0.45rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Session state init ───────────────────────────────────────────────────────
def is_assigned_status(status: str) -> bool:
    return status in LEGACY_ASSIGN_STATUSES


def normalize_lead(lead: dict) -> dict:
    if lead.get("status") == "Assigned to Brantley":
        lead["status"] = ASSIGN_STATUS
        lead["assigned_to"] = PARTNER_NAME

    if lead.get("pipeline_stage") == "Cold":
        lead["pipeline_stage"] = "Warm"

    if "pipeline_stage" not in lead:
        lead["pipeline_stage"] = STATUS_TO_PIPELINE.get(lead.get("status", "New"), "New/Hot")

    if "notes" not in lead:
        lead["notes"] = []
    elif isinstance(lead["notes"], str) and lead["notes"]:
        lead["notes"] = [{"ts": lead.get("created", ""), "text": lead["notes"], "by": "Legacy"}]

    lead.setdefault("calls", 1 if lead.get("status") == "Contacted" else 0)
    lead.setdefault(
        "assigned_to_branton",
        lead.get("assigned_to") == PARTNER_NAME or is_assigned_status(lead.get("status", "")),
    )
    lead.setdefault("activity", [])
    lead.setdefault("source", "manual")
    lead.setdefault("death_date_iso", "")
    lead.setdefault("days_since_death", None)

    apply_heat_classification(lead)

    if "follow_up_iso" not in lead:
        try:
            lead["follow_up_iso"] = (
                datetime.strptime(lead.get("follow_up", ""), "%A, %B %d, %Y").strftime("%Y-%m-%d")
                if lead.get("follow_up") else (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
            )
        except ValueError:
            lead["follow_up_iso"] = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    return lead


def _github_token() -> str:
    try:
        return st.secrets["github"]["token"]
    except Exception:
        return os.environ.get("GITHUB_TOKEN", "")


def _github_enabled() -> bool:
    return bool(_github_token())


def _github_headers() -> dict:
    return {
        "Authorization": f"Bearer {_github_token()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _github_fetch_leads() -> tuple:
    """Return (leads_list, file_sha) from GitHub, or (None, None) if unavailable."""
    if not _github_enabled():
        return None, None
    url = (
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_LEADS_PATH}"
        f"?ref={GITHUB_BRANCH}"
    )
    req = urllib.request.Request(url, headers=_github_headers())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
        content = base64.b64decode(data["content"]).decode("utf-8")
        leads = json.loads(content)
        if not isinstance(leads, list):
            return [], data.get("sha")
        return leads, data.get("sha")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return [], None
        return None, None
    except Exception:
        return None, None


def _github_push_leads(leads: list, sha: str = None) -> bool:
    if not _github_enabled():
        return False
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_LEADS_PATH}"
    payload = {
        "message": "ProbateGuardian CRM: update leads_data.json",
        "content": base64.b64encode(json.dumps(leads, indent=2).encode()).decode(),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={**_github_headers(), "Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode())
        st.session_state["_leads_github_sha"] = data.get("content", {}).get("sha")
        return True
    except Exception:
        return False


def _merge_leads_by_id(*lead_lists: list) -> list:
    merged: dict = {}
    for leads in lead_lists:
        for lead in leads:
            lid = lead.get("id")
            if not lid:
                continue
            existing = merged.get(lid)
            if not existing or lead.get("created", "") >= existing.get("created", ""):
                merged[lid] = lead
    return sorted(merged.values(), key=lambda x: x.get("created", ""), reverse=True)


def _load_leads_local() -> list:
    if not LEADS_FILE.exists():
        return []
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            leads = json.load(f)
        if not isinstance(leads, list):
            return []
        return [normalize_lead(l) for l in leads]
    except (json.JSONDecodeError, OSError):
        return []


def _save_leads_local(leads: list) -> None:
    LEADS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2)
        f.flush()
        os.fsync(f.fileno())


def load_leads() -> list:
    """Load leads from leads_data.json — GitHub repo when token configured, else local file."""
    local = _load_leads_local()
    if not _github_enabled():
        return local

    remote_raw, sha = _github_fetch_leads()
    if remote_raw is None:
        return local

    if sha:
        st.session_state["_leads_github_sha"] = sha

    remote = [normalize_lead(l) for l in remote_raw]
    merged = _merge_leads_by_id(remote, local)
    if merged != local:
        _save_leads_local(merged)
    return merged


def save_leads(leads: list) -> None:
    """Write leads to leads_data.json immediately — local disk + GitHub when configured."""
    if not leads:
        existing = _load_leads_local()
        if existing:
            return

    _save_leads_local(leads)

    if _github_enabled():
        sha = st.session_state.get("_leads_github_sha")
        if not _github_push_leads(leads, sha):
            _, fresh_sha = _github_fetch_leads()
            if fresh_sha:
                st.session_state["_leads_github_sha"] = fresh_sha
            _github_push_leads(leads, st.session_state.get("_leads_github_sha"))


def get_leads() -> list:
    """Return session leads, loading from leads_data.json on first access."""
    if "leads" not in st.session_state:
        st.session_state.leads = load_leads()
    return st.session_state.leads


def persist_leads() -> list:
    """Save session leads to leads_data.json and reload — keeps all views in sync."""
    save_leads(st.session_state.leads)
    st.session_state.leads = load_leads()
    return st.session_state.leads


def sync_leads_session() -> list:
    """Merge disk + session by lead id without dropping saved leads."""
    disk = load_leads()
    session = st.session_state.get("leads")
    if session is None:
        st.session_state.leads = disk
        return disk

    merged = _merge_leads_by_id(disk, session)
    st.session_state.leads = [normalize_lead(l) for l in merged]
    if merged != disk:
        save_leads(st.session_state.leads)
    return st.session_state.leads


VENDOR_SLOTS = 4

VENDOR_CATEGORIES = [
    "Probate Attorney",
    "Title Company",
    "CPA / Tax Professional",
    "Insurance for vacant homes",
    "Property Maintenance / Lawn / Security",
    "Property Management / Rental",
    "Deep Cleaning & Staging",
    "Estate Sale Companies",
    "Junk Removal / Dumpster",
    "Movers",
    "General Contractors / Handyman / Repairs",
    "Cash Buyers / Investor",
    "Traditional Listing Agent",
    "Buyout / Heir Mediation",
]

VENDOR_LEGACY_ALIASES = {
    "Estate Sale": "Estate Sale Companies",
    "Contents Removal / Dump Truck": "Junk Removal / Dumpster",
    "Cleaning": "Deep Cleaning & Staging",
    "Repairs / Funded Repairs": "General Contractors / Handyman / Repairs",
    "Repairs": "General Contractors / Handyman / Repairs",
    "Express Offers": "Cash Buyers / Investor",
    "Sentimental Item Shipping": "Movers",
    "CPA / Tax Professional (stepped-up basis, capital gains)": "CPA / Tax Professional",
    "Insurance Guidance for vacant homes": "Insurance for vacant homes",
    "Property Maintenance / Lawn Care / Security Checks": "Property Maintenance / Lawn / Security",
    "Property Management / Rental Option": "Property Management / Rental",
    "Junk Removal / Dumpster Rental": "Junk Removal / Dumpster",
    "General Contractors / Handyman / Repairs / Roofers / HVAC / Painters / Flooring": "General Contractors / Handyman / Repairs",
    "Cash Buyers / Investor Option": "Cash Buyers / Investor",
    "Buyout / Heir Mediation Services": "Buyout / Heir Mediation",
}

VENDOR_LEGACY_IMPORT = dict(VENDOR_LEGACY_ALIASES)


def _empty_vendor_contact() -> dict:
    return {"name": "", "phone": "", "notes": ""}


def _vendor_contact(name: str = "", phone: str = "", notes: str = "") -> dict:
    return {"name": name, "phone": phone, "notes": notes}


def _coerce_vendor_contact(raw) -> dict:
    if isinstance(raw, dict) and ("name" in raw or "phone" in raw or "notes" in raw):
        return {
            "name": (raw.get("name") or "").strip(),
            "phone": (raw.get("phone") or "").strip(),
            "notes": (raw.get("notes") or "").strip(),
        }
    if isinstance(raw, str) and raw.strip():
        return {"name": raw.strip(), "phone": "", "notes": ""}
    return _empty_vendor_contact()


def _vendor_slot(**primary) -> dict:
    slot = {
        "area_notes": primary.pop("area_notes", ""),
    }
    for i in range(1, VENDOR_SLOTS + 1):
        slot[f"vendor_{i}"] = primary.get(f"vendor_{i}", _empty_vendor_contact())
    return slot


DEFAULT_VENDORS = {
    "Probate Attorney": _vendor_slot(
        vendor_1=_vendor_contact("[Attorney Name]", "[Phone]", "fast with heirs"),
    ),
    "Title Company": _vendor_slot(),
    "CPA / Tax Professional": _vendor_slot(
        vendor_1=_vendor_contact("[CPA Name]", "[Phone]", "stepped-up basis · capital gains"),
    ),
    "Insurance for vacant homes": _vendor_slot(
        vendor_1=_vendor_contact("[Insurance Contact]", "[Phone]", "vacant home specialist"),
    ),
    "Property Maintenance / Lawn / Security": _vendor_slot(
        vendor_1=_vendor_contact("[Lawn / Security]", "[Phone]", "vacant home checks"),
    ),
    "Property Management / Rental": _vendor_slot(
        vendor_1=_vendor_contact("[PM Contact]", "[Phone]", "good for out-of-town families"),
    ),
    "Deep Cleaning & Staging": _vendor_slot(
        vendor_1=_vendor_contact("[Cleaning Co]", "[Phone]", "estate deep clean"),
    ),
    "Estate Sale Companies": _vendor_slot(
        vendor_1=_vendor_contact("[Estate Sale Co]", "[Phone]", "fast response"),
    ),
    "Junk Removal / Dumpster": _vendor_slot(
        vendor_1=_vendor_contact("[Haul-Off Service]", "[Phone]", "dumpster rental"),
    ),
    "Movers": _vendor_slot(
        vendor_1=_vendor_contact("[Mover]", "[Phone]", "good for out-of-town families"),
    ),
    "General Contractors / Handyman / Repairs": _vendor_slot(
        vendor_1=_vendor_contact("[Contractor]", "[Phone]", "funded repairs partner"),
    ),
    "Cash Buyers / Investor": _vendor_slot(
        vendor_1=_vendor_contact(
            "eXp Express Offers Network",
            "615-953-0758",
            "multiple vetted cash buyers",
        ),
    ),
    "Traditional Listing Agent": _vendor_slot(),
    "Buyout / Heir Mediation": _vendor_slot(
        vendor_1=_vendor_contact("[Mediator]", "[Phone]", "sibling buyout specialist"),
    ),
}


def migrate_vendors(raw: dict) -> dict:
    expanded = dict(raw or {})
    for old_key, new_key in VENDOR_LEGACY_IMPORT.items():
        if old_key in expanded and new_key not in expanded:
            expanded[new_key] = expanded[old_key]

    migrated = {}
    for category in VENDOR_CATEGORIES:
        val = expanded.get(category)
        if isinstance(val, str):
            migrated[category] = _vendor_slot(
                vendor_1=_vendor_contact(val, "", ""),
            )
        elif isinstance(val, dict):
            entry = {"area_notes": val.get("area_notes", "")}
            for i in range(1, VENDOR_SLOTS + 1):
                entry[f"vendor_{i}"] = _coerce_vendor_contact(val.get(f"vendor_{i}", ""))
            migrated[category] = entry
        else:
            migrated[category] = {
                "area_notes": DEFAULT_VENDORS[category].get("area_notes", ""),
            }
            for i in range(1, VENDOR_SLOTS + 1):
                migrated[category][f"vendor_{i}"] = dict(
                    DEFAULT_VENDORS[category].get(f"vendor_{i}", _empty_vendor_contact())
                )
    return migrated


def _format_vendor_contact(contact: dict, idx: int) -> str:
    contact = _coerce_vendor_contact(contact)
    parts = [contact["name"], contact["phone"], contact["notes"]]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return f"V{idx}: " + " · ".join(parts)


def format_vendors_display(vendors: dict, category: str) -> str:
    resolved = VENDOR_LEGACY_ALIASES.get(category, category)
    entry = vendors.get(resolved, {})
    if isinstance(entry, str):
        return entry or "[TBD]"

    lines = []
    for i in range(1, VENDOR_SLOTS + 1):
        line = _format_vendor_contact(entry.get(f"vendor_{i}", ""), i)
        if line:
            lines.append(line)
    notes = entry.get("area_notes", "").strip()
    if notes:
        lines.append(f"Area: {notes}")
    return " · ".join(lines) if lines else "[TBD]"


if "vendors" not in st.session_state:
    st.session_state.vendors = migrate_vendors(dict(DEFAULT_VENDORS))
else:
    st.session_state.vendors = migrate_vendors(st.session_state.vendors)


# ── Death date / heat classification ─────────────────────────────────────────
MONTH_NAME_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

DEATH_DATE_RE = re.compile(
    r"(?:died|death(?:\s+date)?|passed(?:\s+away)?|deceased|date\s+of\s+death)"
    r"\s*(?:on|:)?\s*"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}"
    r"|\d{1,2}/\d{1,2}/\d{2,4})",
    re.I,
)


def _parse_flexible_date(value: str):
    value = (value or "").strip()
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    m = re.match(
        r"([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})",
        value,
    )
    if m:
        month = MONTH_NAME_MAP.get(m.group(1).lower()[:3])
        if month:
            try:
                return datetime(int(m.group(3)), month, int(m.group(2)))
            except ValueError:
                pass
    return None


def extract_death_date(text: str):
    text = text or ""
    m = DEATH_DATE_RE.search(text)
    if m:
        dt = _parse_flexible_date(m.group(1))
        if dt:
            return dt
    for line in text.splitlines():
        dt = _parse_flexible_date(line.strip())
        if dt and dt.year >= 1990:
            return dt
    return None


def classify_heat_status(days_since: int) -> tuple:
    """Return (status, pipeline_stage) from days since death."""
    if days_since is None:
        return "Warm", "Warm"
    if days_since <= HEAT_WINDOW_DAYS:
        return "New/Hot", "New/Hot"
    return "Warm", "Warm"


def get_lead_notes_full_text(lead: dict) -> str:
    notes = lead.get("notes") or []
    if not notes:
        raw = (lead.get("raw") or "").strip()
        return raw
    parts = [(n.get("text") or "").strip() for n in notes if (n.get("text") or "").strip()]
    return "\n\n".join(parts)


def set_lead_notes_full_text(lead_id: str, text: str, author: str = None) -> None:
    lead = find_lead(lead_id)
    if not lead:
        return
    author = author or PARTNER_NAME
    cleaned = (text or "").strip()
    if cleaned:
        lead["notes"] = [{
            "ts": datetime.now().isoformat(),
            "text": cleaned,
            "by": author,
        }]
    else:
        lead["notes"] = []
    persist_leads()


def _on_dash_notes_saved(lead_id: str, widget_key: str) -> None:
    if lead_id:
        set_lead_notes_full_text(lead_id, st.session_state.get(widget_key, ""))


def _flush_dash_notes(lead_id: str) -> None:
    """Persist the notes text area for a lead before switching to another."""
    if not lead_id:
        return
    widget_key = f"dash_notes_{lead_id}"
    if widget_key in st.session_state:
        set_lead_notes_full_text(lead_id, st.session_state.get(widget_key, ""))


def _flush_dash_notes_in_memory(lead_id: str) -> None:
    """Copy notes widget into the one matching lead — no full-list reload."""
    if not lead_id:
        return
    widget_key = f"dash_notes_{lead_id}"
    if widget_key not in st.session_state:
        return
    lead = find_lead(lead_id)
    if not lead:
        return
    cleaned = (st.session_state.get(widget_key, "") or "").strip()
    if cleaned:
        lead["notes"] = [{
            "ts": datetime.now().isoformat(),
            "text": cleaned,
            "by": PARTNER_NAME,
        }]
    else:
        lead["notes"] = []


def _lead_list_button_label(lead: dict) -> str:
    name = lead.get("decedent", "Unknown")
    addr = (lead.get("address") or "—")[:48]
    phone = lead.get("phone") or "—"
    score = lead.get("score", 0)
    status = lead.get("status", "—")
    return f"{name}\n{addr}\n📞 {phone}  ·  [{score}]  ·  {status}"


def _select_crm_lead(lead_id: str) -> None:
    prev = st.session_state.get("crm_selected_lead_id")
    if prev and prev != lead_id:
        _flush_dash_notes(prev)
    st.session_state.crm_selected_lead_id = lead_id
    st.session_state.pop("_dash_notes_sync_id", None)


def _is_high_score_lead(lead: dict) -> bool:
    return int(lead.get("score") or 0) >= HIGH_SCORE_THRESHOLD


def _filter_leads_due_today(leads: list) -> list:
    today = datetime.now().strftime("%Y-%m-%d")
    result = [
        l for l in leads
        if effective_pipeline_stage(l) != "Closed"
        and (l.get("follow_up_iso", "") == today or _is_high_score_lead(l))
    ]
    result.sort(key=lambda x: (
        0 if x.get("follow_up_iso", "") == today else 1,
        -int(x.get("score") or 0),
        x.get("follow_up_iso", "9999-12-31"),
    ))
    return result


def _apply_crm_list_filters(leads: list) -> list:
    result = list(leads)
    if st.session_state.get("crm_list_mode") == "due_today":
        result = _filter_leads_due_today(result)
    stage_filter = st.session_state.get("crm_stage_list_filter", "All")
    if stage_filter and stage_filter != "All":
        result = [l for l in result if detail_pipeline_stage(l) == stage_filter]
    return result


def _on_pipeline_stage_list_filter(lead_id: str) -> None:
    stage = st.session_state.get(f"stage_{lead_id}")
    if stage:
        st.session_state.crm_stage_list_filter = stage


def _quick_stage_status(stage: str, lead: dict) -> str:
    if stage in CLOSED_DETAIL_STAGES:
        return "Closed"
    if stage == "🔥 Hot / New (call today)":
        return "New/Hot"
    if stage == "Warm / Talking":
        return "Contacted"
    if stage == "Not Interested / Keeping":
        return "Low Priority"
    return lead.get("status", "New")


def _quick_stage_callback(lead_id: str, stage: str) -> None:
    """Update exactly one lead by unique ID — never replace or reload the full list."""
    if not lead_id:
        return
    _flush_dash_notes_in_memory(lead_id)
    lead = find_lead(lead_id)
    if not lead:
        return
    if not patch_lead_by_id(
        lead_id,
        pipeline_stage=stage,
        status=_quick_stage_status(stage, lead),
    ):
        return
    st.session_state.crm_selected_lead_id = lead_id
    st.session_state[f"stage_{lead_id}"] = stage
    st.session_state.crm_stage_list_filter = stage
    st.session_state.pop("_dash_notes_sync_id", None)


def _is_manual_pipeline_stage(stage: str) -> bool:
    """Stages set by Branton in Lead Detail — never auto-overwrite on reload."""
    if stage in DETAIL_PIPELINE_STAGES:
        return True
    return stage in (
        "Appt", "Contract", "Closed",
        "Appointment Set", "Listed / Under Contract", "Closed / Sold", "Archived",
    )


def apply_heat_classification(lead: dict) -> dict:
    """Classify New/Hot (≤60 days) vs Warm from death date in raw/notes."""
    blob = "\n".join(filter(None, [
        lead.get("raw", ""),
        get_lead_notes_full_text(lead),
        lead.get("filing_date", ""),
    ]))
    death_dt = extract_death_date(blob)
    days = None
    if death_dt:
        days = (datetime.now() - death_dt).days
        lead["death_date_iso"] = death_dt.strftime("%Y-%m-%d")
        lead["days_since_death"] = days
    if _is_manual_pipeline_stage(lead.get("pipeline_stage", "")):
        return lead
    status, pipeline = classify_heat_status(days)
    active_progress = lead.get("pipeline_stage") in (
        "Appt", "Contract", "Closed",
        "Appointment Set", "Listed / Under Contract", "Closed / Sold", "Archived",
    )
    contacted = lead.get("status") in ("Contacted", ASSIGN_STATUS) or lead.get("calls", 0) > 0
    if not active_progress and not contacted:
        lead["status"] = status
        if lead.get("pipeline_stage") in ("Cold", "New/Hot", "Warm", None, ""):
            lead["pipeline_stage"] = pipeline
    elif lead.get("pipeline_stage") == "Cold":
        lead["pipeline_stage"] = "Warm"
    return lead


def heat_from_import_block(block: str) -> tuple:
    death_dt = extract_death_date(block)
    days = (datetime.now() - death_dt).days if death_dt else None
    return classify_heat_status(days)


def initial_notes_from_block(block: str, source: str = "Scott") -> list:
    cleaned = (block or "").strip()
    if not cleaned:
        return []
    return [{
        "ts": datetime.now().isoformat(),
        "text": cleaned,
        "by": source,
    }]


# ── Lead parsing helpers ─────────────────────────────────────────────────────
def parse_lead(raw: str) -> dict:
    lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
    text = raw.strip()

    decedent = lines[0] if lines else "Unknown Decedent"
    address = "Address TBD"
    county = "Middle TN"
    heirs = ""
    phone = ""
    email = ""

    addr_match = re.search(
        r"(\d+\s+[\w\s\.\#]+(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Ln|Lane|Ct|Court|Way|Blvd)\.?,?\s*[\w\s]+,?\s*TN\s*\d{5})",
        text,
        re.IGNORECASE,
    )
    if addr_match:
        address = addr_match.group(1).strip()

    county_match = re.search(
        r"(Wilson|Davidson|Rutherford|Williamson|Sumner|Robertson|Cheatham|Dickson|Montgomery|Maury|Bedford|Coffee|DeKalb|Smith|Putnam|Cannon|Marshall|Lincoln|Franklin|Warren|Grundy|Hickman|Giles|Lawrence|Lewis|Perry|Wayne|Hardin|Henry|Stewart|Houston|Humphreys|Overton|Pickett|Fentress|Clay|Jackson|Macon|Trousdale)\s+County",
        text,
        re.IGNORECASE,
    )
    if county_match:
        county = county_match.group(0)

    phone_match = re.search(r"\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}", text)
    if phone_match:
        phone = phone_match.group(0)

    email_match = re.search(r"[\w\.\-]+@[\w\.\-]+\.\w+", text)
    if email_match:
        email = email_match.group(0)

    if len(lines) > 1:
        heirs = lines[1] if not re.search(r"\d{3}", lines[1]) else (lines[2] if len(lines) > 2 else "")

    return {
        "decedent": decedent,
        "address": address,
        "county": county,
        "heirs": heirs,
        "phone": phone,
        "email": email,
        "raw": raw,
    }


def score_lead(parsed: dict) -> tuple:
    has_address = parsed["address"] != "Address TBD"
    has_county = "County" in parsed["county"] or parsed["county"] != "Middle TN"
    score = 0
    flags = []

    if parsed["decedent"] != "Unknown Decedent":
        score += 30
        flags.append("✓ Decedent identified")
    if has_address:
        score += 35
        flags.append("✓ Property address found")
    if has_county:
        score += 20
        flags.append("✓ County confirmed")
    if parsed.get("phone"):
        score += 10
        flags.append("✓ Phone number found")
    if parsed.get("email"):
        score += 5
        flags.append("✓ Email found")

    if score >= 65:
        status = "Qualified"
    elif score >= 40:
        status = "Needs Review"
    else:
        status = "Low Priority"

    return score, status, flags


_lead_id_seq = 0


def new_lead_id() -> str:
    global _lead_id_seq
    _lead_id_seq += 1
    return datetime.now().strftime("%Y%m%d%H%M%S") + f"{_lead_id_seq:04d}"


def follow_up_date(days: int = 3) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%A, %B %d, %Y")


def follow_up_iso(days: int = 3) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def build_lead(parsed: dict, **extra) -> dict:
    days = extra.get("follow_up_days", 2)
    branton = extra.get("assigned_to_branton", False)
    stage = extra.get("pipeline_stage", "Warm" if branton else "New/Hot")
    lead = {
        "id": new_lead_id(),
        "decedent": parsed["decedent"],
        "address": parsed["address"],
        "county": parsed["county"],
        "heirs": parsed["heirs"],
        "phone": parsed.get("phone", ""),
        "email": parsed.get("email", ""),
        "pipeline_stage": stage,
        "status": extra.get("status", ASSIGN_STATUS if branton else "New"),
        "assigned_to_branton": branton,
        "assigned_to": PARTNER_NAME if branton else extra.get("assigned_to", ""),
        "score": extra.get("score", 0),
        "notes": extra.get("notes", []),
        "calls": extra.get("calls", 0),
        "activity": extra.get("activity", []),
        "source": extra.get("source", "manual"),
        "created": datetime.now().isoformat(),
        "follow_up_days": days,
        "follow_up_iso": follow_up_iso(days),
        "follow_up": follow_up_date(days),
        "raw": parsed.get("raw", ""),
    }
    return normalize_lead(lead)


def find_lead(lead_id: str):
    for lead in st.session_state.leads:
        if lead.get("id") == lead_id:
            return lead
    return None


def patch_lead_by_id(lead_id: str, **updates) -> bool:
    """Update exactly one lead by unique ID — all other leads stay untouched."""
    if not lead_id or not updates:
        return False

    leads = st.session_state.get("leads")
    if not isinstance(leads, list):
        return False

    new_leads = []
    patched = False
    for item in leads:
        if item.get("id") == lead_id:
            updated = dict(item)
            updated.update(updates)
            new_leads.append(updated)
            patched = True
        else:
            new_leads.append(item)

    if not patched:
        return False

    st.session_state.leads = new_leads
    save_leads(new_leads)
    return True


def update_lead(lead_id: str, **fields) -> None:
    if not lead_id:
        return
    updated = False
    for lead in st.session_state.leads:
        if lead.get("id") != lead_id:
            continue
        lead.update(fields)
        if fields.get("assigned_to_branton") is True:
            lead["assigned_to"] = PARTNER_NAME
            lead["status"] = ASSIGN_STATUS
        elif fields.get("assigned_to_branton") is False:
            lead["assigned_to"] = ""
        if "follow_up_iso" in fields:
            try:
                d = datetime.strptime(fields["follow_up_iso"], "%Y-%m-%d")
                lead["follow_up"] = d.strftime("%A, %B %d, %Y")
            except ValueError:
                pass
        updated = True
        break
    if updated:
        save_leads(st.session_state.leads)


def log_call(lead_id: str) -> None:
    lead = find_lead(lead_id)
    if lead:
        lead["calls"] = lead.get("calls", 0) + 1
        lead["activity"].insert(0, {
            "ts": datetime.now().isoformat(),
            "type": "call",
            "detail": f"Call logged (#{lead['calls']})",
        })
        persist_leads()


def add_note(lead_id: str, text: str, author: str = "Scott") -> None:
    lead = find_lead(lead_id)
    if lead and text.strip():
        lead["notes"].insert(0, {
            "ts": datetime.now().isoformat(),
            "text": text.strip(),
            "by": author,
        })
        lead["activity"].insert(0, {
            "ts": datetime.now().isoformat(),
            "type": "note",
            "detail": text.strip()[:80],
        })
        persist_leads()


def detail_pipeline_stage(lead: dict) -> str:
    stage = lead.get("pipeline_stage", "")
    if stage in DETAIL_PIPELINE_STAGES:
        return stage
    return LEGACY_TO_DETAIL.get(stage, DETAIL_PIPELINE_STAGES[0])


def effective_pipeline_stage(lead: dict) -> str:
    stage = lead.get("pipeline_stage", "")
    if stage in DETAIL_TO_ANALYTICS:
        return DETAIL_TO_ANALYTICS[stage]
    if stage in PIPELINE_STAGES:
        return stage
    if stage == "Cold":
        return "Warm"
    return STATUS_TO_PIPELINE.get(lead.get("status", "Warm"), "Warm")


def compute_analytics(leads: list) -> dict:
    total = len(leads)
    stages = {s: 0 for s in PIPELINE_STAGES}
    for lead in leads:
        stages[effective_pipeline_stage(lead)] = stages.get(effective_pipeline_stage(lead), 0) + 1
    total_calls = sum(l.get("calls", 0) for l in leads)
    branton_count = sum(1 for l in leads if l.get("assigned_to_branton"))
    today = datetime.now().strftime("%Y-%m-%d")
    due_today = sum(
        1 for l in leads
        if l.get("follow_up_iso", "") <= today and effective_pipeline_stage(l) != "Closed"
    )

    new_hot = stages.get("New/Hot", 0)
    warm = stages.get("Warm", 0)
    appt = stages.get("Appt", 0)
    contract = stages.get("Contract", 0)
    closed = stages.get("Closed", 0)
    funnel_top = new_hot + warm or 1

    conv_warm = round((warm + appt + contract + closed) / funnel_top * 100, 1) if funnel_top else 0
    conv_appt = round((appt + contract + closed) / max(warm, 1) * 100, 1) if warm else 0
    conv_close = round(closed / max(total, 1) * 100, 1)

    counties: dict = {}
    for l in leads:
        c = l.get("county", "Unknown")
        counties[c] = counties.get(c, 0) + 1
    top_counties = sorted(counties.items(), key=lambda x: -x[1])[:5]

    sources: dict = {}
    for l in leads:
        s = l.get("source", "manual")
        sources[s] = sources.get(s, 0) + 1

    return {
        "total": total,
        "stages": stages,
        "total_calls": total_calls,
        "branton_count": branton_count,
        "due_today": due_today,
        "conv_warm": conv_warm,
        "conv_appt": conv_appt,
        "conv_close": conv_close,
        "top_counties": top_counties,
        "sources": sources,
        "avg_calls": round(total_calls / max(total, 1), 1),
    }


def get_call_first_leads(leads: list) -> list:
    """Bulk Qualifier green leads — highest score first for Branton's daily calls."""
    queue = [
        l for l in leads
        if l.get("source") == "bulk"
        and effective_pipeline_stage(l) != "Closed"
    ]
    queue.sort(
        key=lambda x: (
            -int(x.get("score") or 0),
            x.get("follow_up_iso", "9999-12-31"),
        )
    )
    return queue


def import_leads_from_text(text: str, source: str = "import") -> int:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    count = 0
    for block in blocks:
        parsed = parse_lead(block)
        parsed["raw"] = block
        score, qual_status, _ = score_lead(parsed)
        heat_status, heat_pipeline = heat_from_import_block(block)
        if qual_status == "Qualified":
            lead_status, lead_pipeline = heat_status, heat_pipeline
        else:
            lead_status, lead_pipeline = qual_status, "Warm"
        st.session_state.leads.insert(0, build_lead(
            parsed,
            pipeline_stage=lead_pipeline,
            source=source,
            score=score,
            status=lead_status,
            notes=initial_notes_from_block(block),
        ))
        count += 1
    persist_leads()
    return count


def import_leads_from_csv(file_bytes: bytes, source: str = "csv") -> int:
    reader = csv.DictReader(io.StringIO(file_bytes.decode("utf-8", errors="ignore")))
    count = 0
    for row in reader:
        raw = "\n".join(str(v) for v in row.values() if v)
        parsed = parse_lead(raw)
        parsed["decedent"] = row.get("decedent") or row.get("Decedent") or parsed["decedent"]
        parsed["address"] = row.get("address") or row.get("Address") or parsed["address"]
        parsed["county"] = row.get("county") or row.get("County") or parsed["county"]
        parsed["heirs"] = row.get("heirs") or row.get("Heirs") or parsed["heirs"]
        parsed["phone"] = row.get("phone") or row.get("Phone") or parsed.get("phone", "")
        parsed["email"] = row.get("email") or row.get("Email") or parsed.get("email", "")
        row_blob = raw + "\n" + "\n".join(str(v) for v in row.values() if v)
        heat_status, heat_pipeline = heat_from_import_block(row_blob)
        st.session_state.leads.insert(0, build_lead(
            parsed,
            pipeline_stage=heat_pipeline,
            status=heat_status,
            source=source,
            notes=initial_notes_from_block(row_blob, source="CSV Import"),
        ))
        count += 1
    persist_leads()
    return count


def pipeline_class(stage: str) -> str:
    return {
        "New/Hot": "pipe-newhot",
        "Cold": "pipe-warm",
        "Warm": "pipe-warm",
        "Appt": "pipe-appt",
        "Contract": "pipe-contract",
        "Closed": "pipe-closed",
    }.get(stage, "pipe-cold")


# ── Content generators ───────────────────────────────────────────────────────
def generate_phone_script(parsed: dict) -> str:
    decedent = parsed["decedent"]
    address = parsed["address"]
    county = parsed["county"]
    heir = parsed["heirs"] or "[Heir Name]"

    return f"""═══════════════════════════════════════════════════════
  AARON NOVELLO + RICK YEN — ELITE PROBATE PHONE SCRIPT
  Scott Hardesty · eXp Realty · Mount Juliet, TN
  📞 615-953-0758
═══════════════════════════════════════════════════════

OPENING — RESPECTFUL, UNHURRIED (Aaron Novello)
─────────────────────────────────────────────
"Hi, is this {heir}?"

[Wait for response]

"Hey {heir}, my name is Scott Hardesty — I'm a local Realtor here in
Mount Juliet with eXp Realty. First, I want to say I'm truly sorry
for your loss. I know this is probably the last call you want to
receive right now."

RESPECTFUL EARLY-OUTREACH (Aaron — disarm in first 30 seconds)
─────────────────────────────────────────────
"I realize I may be reaching out a little early in the process, and I
want to do that very respectfully. Nothing needs to happen today —
I'm not calling with an agenda."

"I came across the probate filing for {decedent}'s property at
{address} in {county}. I simply wanted to introduce myself as a
local resource — so when questions come up, you have someone in your
corner who does this every day in Middle Tennessee."

HONEST EXPECTATIONS (Aaron + Rick Yen)
─────────────────────────────────────────────
"Can I share something upfront? In my experience, more likely than
not the goal will be to sell the property at some point — but that
might be months from now, and that's completely okay."

"My job isn't to rush you. It's to make sure that whenever your family
IS ready, you have real numbers, real options, and the right people
around you."

EMPATHY BRIDGE — THEN GO SILENT (Aaron core)
─────────────────────────────────────────────
"Before I share how I might help — if you don't mind me asking —
what's been the hardest part of all this so far?"

[STOP TALKING. Let them answer. Take notes. Do not interrupt.]

"Tell me more about that."

[Use 2–3 times during the call. Rick Yen: let silence work for you.]

RICK YEN CONVERSATION STYLE — COLLABORATIVE DISCOVERY
─────────────────────────────────────────────
"Help me understand — walk me through where things stand with the
estate right now."

"What's your role in all of this — are you the executor, a beneficiary,
or helping a family member?"

"Who else is involved in the decision? I'd love to understand the
full picture so I'm not speaking out of turn."

[Mirror their words back: "So it sounds like the biggest thing right
now is ___ — did I get that right?"]

FAMILY DYNAMICS PROBES (Aaron / Jose / Rick)
─────────────────────────────────────────────
"How many heirs are involved in the decision?"

"Is everyone on the same page about what to do with the property —
or are there different opinions?"

"Is anyone living in the home currently, or is it sitting vacant?"

"Has anyone expressed interest in buying out the other heirs and
keeping the property?"

"Are there any estate debts, mortgages, or liens you're aware of?"

"Is anyone out of state who can't easily get to the property?"

"Has anyone in the family already formed a strong opinion on price —
or is everyone still figuring that out?"

[Tell me more about that — after every answer that hints at tension.]

FINANCIAL FEASIBILITY PROBES
─────────────────────────────────────────────
"Would it be helpful to know what you'd actually NET after debts,
closing costs, and repairs — not just a Zillow guess?"

"Is there pressure to get funds to the heirs quickly — or is
timeline flexible?"

"If one sibling wanted to keep the house and the others wanted cash,
has anyone run the buyout numbers yet?"

PRICE ANCHORING (Rick Yen — context without commitment)
─────────────────────────────────────────────
"Have you guys talked at all about what the property might be worth —
even a rough range?"

[If no / unsure / they mention Zillow:]

"That makes total sense — and I wouldn't trust an online estimate on
a probate property anyway. Every heir situation is different."

"In {county}, properties around {address} can fall in a pretty wide
range depending on condition — I've seen similar homes anywhere from
$[LOW RANGE] as-is, up toward $[HIGH RANGE] fully updated. But that's
me talking from the outside without having walked through."

"The only way to know YOUR real number — what the estate would
actually net — is a proper Equity Snapshot. That's the piece I'd love
to help with, completely free, whenever you're ready."

[Never quote a single firm price on call #1. Anchor the RANGE, then
pivot to the Net Sheet appointment.]

VALUE OFFER — PROJECT COORDINATOR (Jose / Bruce-Heath concierge model)
─────────────────────────────────────────────
"Here's what I'd love to do — completely free, no obligation:

  ✓  Prepare a complimentary Equity Snapshot / Net Sheet
  ✓  Act as your Project Coordinator — one call, we handle the rest
  ✓  Coordinate everything: estate sales, contents removal, dump truck,
     cleaning, shipping sentimental items, lockbox, utilities, lawn care
  ✓  Walk you through every path: traditional, Express Offers, Muniment
     of Title, or sibling buyout — subject to court approval
  ✓  Funded repairs if you want top dollar — zero out of pocket before close"

EXPRESS OFFERS PIVOT (when overwhelmed, out-of-state, or need speed)
─────────────────────────────────────────────
"One option a lot of families don't know about — Express Offers
through eXp Realty."

  • Multiple vetted cash buyers compete — you compare, not one lowball
  • ZERO repairs, ZERO showings, ZERO staging
  • Close in as little as 14 days — subject to court approval
  • Commission protected — you pay nothing extra
  • Perfect when heirs live out of state or want certainty"

CLOSE — "MAY I MAKE A SUGGESTION?" (Aaron signature)
─────────────────────────────────────────────
"{heir}, I'm not asking you to decide anything today."

"May I make a suggestion?"

[Wait for yes.]

"Would a brief 10-to-15-minute call later this week make sense —
or a quick walk-through if you're local — just to leave you with a
free Equity Snapshot? No pressure, no commitment."

"What works better — [Day A] or [Day B]?"

OBJECTION HANDLERS
─────────────────────────────────────────────
"We already have an attorney."
  → "Perfect — I work alongside attorneys every day. I handle the
     property side; they handle the legal piece. Tell me more about
     where they are in the process."

"We're not ready to sell."
  → "Totally understand. Can I send a free Net Sheet so you have real
     numbers when you ARE ready? No strings."

"It's too early."
  → "That's exactly why I'm calling early — so you have a resource
     before you need one. Very respectfully, zero timeline."

"We already have a price in mind."
  → "Tell me more about that. I'd love to see if the Net Sheet aligns
     — sometimes estates are pleasantly surprised, sometimes not.
     Either way, good information."

POST-CALL CHECKLIST ({PARTNER_NAME})
─────────────────────────────────────────────
□ Log outcome on Dashboard
□ Note: heirs, buyout interest, price expectations, debts, out-of-state
□ Schedule 10–15 min follow-up
□ Generate Guardian Kit · Notify Scott if attorney already involved

CONTACT CARD
─────────────────────────────────────────────
Scott Hardesty | eXp Realty | Mount Juliet, TN
📞 615-953-0758
ProbateGuardian Free TN — Compassion. Clarity. Closings.
═══════════════════════════════════════════════════════"""


def generate_attorney_template(template_type: str, attorney: str, firm: str, parsed: dict) -> str:
    decedent = parsed.get("decedent", "[Decedent Name]")
    address = parsed.get("address", "[Property Address]")
    county = parsed.get("county", "[County]")
    heir = parsed.get("heirs", "[Executor / Heir]")
    today = datetime.now().strftime("%B %d, %Y")

    if template_type == "contract_forwarding":
        return f"""Subject: Listing Coordination — Estate of {decedent} · {address}

Dear {attorney},

Thank you for trusting me with the property side of the **Estate of {decedent}** at **{address}** ({county}).

Per our conversation, I am forwarding the listing agreement and property coordination documents for your review. Key points for your file:

• **Primary contact:** {heir}
• **Property:** {address}
• **Timeline:** All marketing and offers subject to court approval
• **My role:** Project Coordinator — property, vendors, showings/cash offers, Net Sheet delivery
• **Your role:** Legal counsel — court filings, heir authorization, closing approval

I will not market the property or accept offers until you confirm the estate has authority to sell. Please reply with any provisions you need added or modified.

I coordinate ancillary services (estate sale, cleanout, repairs) only with your client's approval.

Respectfully,
Scott Hardesty · eXp Realty · Mount Juliet, TN
📞 615-953-0758
{today}"""

    if template_type == "thank_you_video":
        return f"""Subject: Quick Thank You + Resource for Your Probate Clients — Scott Hardesty

Dear {attorney},

I hope this finds you well. I wanted to say thank you again for the trust you place in me when your clients need help with real property in probate.

I recorded a brief 2-minute video for you and your team that explains how I work alongside probate attorneys — Project Coordinator role, Net Sheets, Express Offers, and **subject to court approval** on every timeline.

**Video link:** [Paste your Loom/YouTube thank-you video URL here]

When your clients ask "what do we do with the house?" — feel free to forward my info. I will always:

✓ Loop you in before any property decisions
✓ Defer all legal questions back to your office
✓ Deliver a free Equity Snapshot / Net Sheet
✓ Handle the heavy lifting: estate sales, cleanout, lockbox, utilities, lawn

Current estate I'm happy to discuss as a reference: **{decedent}** · {address}

Grateful for the partnership,
Scott Hardesty · eXp Realty
📞 615-953-0758 · Mount Juliet, TN"""

    if template_type == "pie_campaign":
        return f"""Subject: Thinking of You — {firm} · {today}

Dear {attorney},

Probate season is heavy work — you're carrying families through the hardest moments while keeping every detail straight. I see it, and I'm grateful for professionals like you.

I'd love to drop a small thank-you by your office this week — **[pumpkin pie / pie from Five Daughters / local bakery]** — just to say I appreciate our partnership. No meeting needed unless you want one.

**Why I keep showing up for {firm}:**
• Your clients get a Project Coordinator, not just a listing agent
• Every timeline I quote is **subject to court approval**
• I make your job easier — property handled, you stay focused on the law

If you have an estate with real property right now — like **{decedent}** at {address} — I'm happy to help. One call, we handle the heavy lifting.

Can I drop by Thursday or Friday?

With respect,
Scott Hardesty · eXp Realty · Mount Juliet, TN
📞 615-953-0758"""

    if template_type == "review_request":
        return f"""Subject: Quick Favor — 2-Minute Review? · Scott Hardesty / eXp Realty

Dear {attorney},

I hope the closing on **{decedent}** / **{address}** went smoothly for your client and your office.

If you felt I handled the property side well — communicated clearly, stayed subject to court approval, and made your job easier — would you mind leaving a brief Google review? It helps other probate attorneys find a Realtor who actually coordinates instead of complicates.

**Review link:** [Paste your Google Review link here]

Suggested one-liner (feel free to edit):
*"Scott handled the property coordination on our probate estate — Net Sheets, vendors, Express Offers — always looped us in and respected court timelines."*

If there is anything I could have done better on this file, please tell me directly first. I want to earn the referral long-term, not just the transaction.

Thank you again for the partnership, {attorney}.

Scott Hardesty · eXp Realty · Mount Juliet, TN
📞 615-953-0758 · {today}"""

    return ""


def generate_guardian_kit(parsed: dict, vendors: dict) -> str:
    decedent = parsed["decedent"]
    address = parsed["address"]
    county = parsed["county"]
    heir = parsed["heirs"] or "Estate Heirs / Executor"
    heir_first = heir.split("(")[0].strip() if heir else "Friend"
    today = datetime.now().strftime("%B %d, %Y")
    year = datetime.now().year

    return f"""# 🏠 ProbateGuardian Guardian Kit
### *Clarity · Compassion · Confident decisions for your family*

---

## Prepared exclusively for
# **{heir}**
### Estate of **{decedent}**
**{address}** · **{county}**

| | |
|---|---|
| **Prepared by** | Scott Hardesty, eXp Realty |
| **Office** | Mount Juliet, Tennessee |
| **Direct line** | **615-953-0758** |
| **Date** | {today} |
| **Confidential** | For estate heirs and authorized representatives only |

---

## 💙 Empathy Opener — A Personal Note from Scott

Dear {heir_first},

I realize I may be reaching out a little early in your process, and I want to do that **very respectfully**. I am not here to rush you, pressure you, or pretend this is a normal real estate transaction.

**{decedent}**'s home at **{address}** holds a lifetime of memories. I am truly sorry for your loss. ProbateGuardian exists so Tennessee families have **one trusted person** to turn to when the questions feel overwhelming — whether that day is today or six months from now.

In my experience, more likely than not the goal will be to sell the property at some point — but **on your family's timeline**, not mine. This kit gives you real options, real numbers, and real support. Share it with siblings, your attorney, or anyone helping you navigate the estate.

---

## 🧭 Your Project Coordinator — *One Call, We Handle the Rest*

**You should not have to be the project manager of your own grief.**

Scott is your family's **Project Coordinator** — not just a Realtor. Think personal assistant for the property: one point of contact, every vendor dispatched, every detail tracked, every timeline aligned with your attorney's court calendar.

| You Shouldn't Have To… | Scott Handles It |
|------------------------|------------------|
| Chase contractors and get bids | ✓ Vendor dispatch from vetted Rolodex |
| Coordinate sibling conversations | ✓ Neutral third party for buyout & proceeds talks |
| Figure out what the home is worth | ✓ Free Equity Snapshot / Net Sheet |
| Manage lockbox, utilities, lawn | ✓ Property secured and maintained while estate is open |
| Wonder what's happening week to week | ✓ Proactive updates — you always know the status |

*One call to Scott. We handle the rest.*

---

## 💪 We Handle the Heavy Lifting

**Probate is not just a sale — it is a full estate resettlement.** You focus on family. Scott coordinates everything below through vetted Middle Tennessee partners.

| Service | What We Handle | Your Resource |
|---------|----------------|---------------|
| **Estate Sales** | Tag, price, sell contents on-site or online | {format_vendors_display(vendors, 'Estate Sale')} |
| **Contents Removal** | Furniture, junk, attic and garage cleanout | {format_vendors_display(vendors, 'Contents Removal / Dump Truck')} |
| **Dump Truck / Haul-Off** | Large debris, bulk removal, full cleanouts | {format_vendors_display(vendors, 'Contents Removal / Dump Truck')} |
| **Post-Estate Cleaning** | Deep clean after contents removed | {format_vendors_display(vendors, 'Cleaning')} |
| **Sentimental Item Shipping** | Pack and ship heirlooms to out-of-state heirs | {format_vendors_display(vendors, 'Sentimental Item Shipping')} |
| **Movers** | Heir relocations and estate moves | {format_vendors_display(vendors, 'Movers')} |
| **Lockbox & Property Access** | Secure access — you stay home | Scott coordinates |
| **Utilities & Lawn Care** | Lights on, lawn mowed, property maintained | Scott coordinates |
| **Probate Attorney** | Court filings, letters testamentary, muniment | {format_vendors_display(vendors, 'Probate Attorney')} |
| **Funded Repairs** | Repairs paid at closing — **$0 out of pocket** | {format_vendors_display(vendors, 'Repairs / Funded Repairs')} |
| **Express Offers** | Multiple competing cash buyers — as-is | {format_vendors_display(vendors, 'Express Offers')} |

> **Bruce & Heath concierge principle:** The families who close smoothly aren't the ones who work hardest — they're the ones who let a Project Coordinator handle the heavy lifting.

### Free Equity Snapshot & Net Sheet

| Line Item | Your Property |
|-----------|---------------|
| **Decedent** | {decedent} |
| **Property** | {address} |
| **County / Court** | {county} |
| **Primary Contact** | {heir} |
| **Estimated Market Value (ARV)** | *Pending property review* |
| **Estimated As-Is Value** | *Condition-adjusted* |
| **Mortgage / Liens Payoff** | *Title verified* |
| **Estimated Net Proceeds** | **Delivered on your Net Sheet — per-heir breakdown available** |
| **Buyout Feasibility** | *If one heir wants the home — we run the math* |

*Families agree when everyone sees the same Net Sheet — not a Zillow guess.*

---

## 🚀 Express Offers — *The Probate Game-Changer*

### *Multiple cash buyers compete. You choose. Subject to court approval.*

When speed, certainty, and simplicity matter more than squeezing every last dollar, **Express Offers through eXp Realty** gives your family something traditional listings cannot: **competing cash offers without repairs, showings, or months of uncertainty.**

### Why Heirs Across Middle TN Choose Express Offers

| Advantage | What It Means for {heir_first}'s Family |
|-----------|----------------------------------------|
| **Multiple Competing Offers** | Several vetted buyers bid — you compare, never one take-it-or-leave-it lowball |
| **Sell 100% As-Is** | Roof, HVAC, foundation, hoarding conditions — no repairs required |
| **Zero Showings** | No strangers walking through **{decedent}**'s home |
| **Zero Staging / Prep** | No painting, cleaning, or fix-up before closing |
| **Close in 14–30 Days** | **Subject to court approval** — Scott aligns with your attorney's timeline |
| **Commission Protected** | Professional fee covered — **heirs pay nothing extra** |
| **Cash = Certainty** | No buyer financing fall-through, no inspection renegotiation drama |
| **Multi-Heir Friendly** | Clean proceeds split per court order — ideal for out-of-state siblings |

### Express Offers Process

1. **Submit** — Scott enters {address} into the eXp Express Offers network
2. **Compete** — Multiple cash buyers submit offers within **48–72 hours**
3. **Compare** — You review all offers side-by-side on your Net Sheet
4. **Choose** — Pick the best number and timeline — or walk away, no obligation
5. **Close** — **Subject to court approval**, buyer closes on your terms

### When Express Offers Is the Right Call

- ✅ Heirs live out of state and cannot manage a listing
- ✅ Property needs more work than the family wants to fund
- ✅ Siblings disagree on price, timing, or strategy
- ✅ Estate debts need settlement quickly
- ✅ Emotional toll of showings is too much right now
- ✅ You need a **guaranteed close date** without financing risk

> **Express Offers is not giving up.** It is choosing peace of mind. For many probate families, that is the most valuable thing on the table.

---

## 📜 Muniment of Title — *Transfer Without Selling*

### *Tennessee's fastest path when the property has no mortgage*

If **{decedent}**'s home at **{address}** has **no outstanding mortgage or lien**, your family may qualify for a **Muniment of Title** — a simplified probate proceeding that transfers ownership **without listing, selling, or showings**.

| Step | What Happens |
|------|--------------|
| **1** | Will filed with **{county}** Probate Court |
| **2** | Court admits will as **muniment of title only** — no full administration |
| **3** | Title transfers to named heir(s) by court order |
| **4** | Heirs keep, rent, or sell later — on their own timeline |

**Ideal when:** Property is free and clear · No significant creditor claims · One or more heirs want to **retain** the home · Family wants the **least expensive** probate path

**Scott's role:** Connect you with a vetted probate attorney, provide a market valuation for retention or future sale decisions, and stand ready when you choose to list or submit to Express Offers.

*Muniment of Title is a legal process — Scott coordinates but does not provide legal advice.*

---

## 🔨 Funded Repairs + Express Offers — *Two Paths, One Coordinator*

**Want top dollar?** Funded repairs let you list at peak value — costs recovered at closing, **$0 out of pocket**.

**Want speed and certainty?** Express Offers delivers competing cash bids — as-is, no showings, close **subject to court approval**.

| | Funded Repairs + List | Express Offers |
|---|---|---|
| **Upfront cost** | $0 — repaid at closing | $0 — sell as-is |
| **Repairs** | Funded & managed by Scott | None required |
| **Showings** | Yes | None |
| **Timeline** | 60–120 days typical | 14–30 days possible |
| **Court language** | Subject to court approval | Subject to court approval |
| **Best when** | Strong ARV upside | Speed, simplicity, out-of-state heirs |

*Scott presents both with real Net Sheet numbers — you choose.*

---

## 🛤️ Your Four Paths — *You Stay in Control*

| Path | Summary | Best When |
|------|---------|-----------|
| **A · Express Offers** | Multiple cash offers, as-is, fast close *subject to court approval* | Overwhelmed heirs, out-of-state family, property needs work |
| **B · Traditional Listing** | Full MLS + funded repairs available | Maximum net proceeds, strong ARV upside |
| **C · Muniment of Title** | Court transfer — no sale required | No mortgage, heirs keeping the property |
| **D · Sibling Buyout** | Feasibility analysis + financed purchase between heirs | One heir wants the home, others want cash |

*There is no wrong choice — only the right one for your family. Scott presents all four with real numbers.*

---

## 📅 What Happens Next

| Step | When | What |
|------|------|------|
| **1** | This week | **10–15 minute call or property walk-through** — no pressure |
| **2** | Within 48 hrs | Free Equity Snapshot, Net Sheet & Express Offers analysis |
| **3** | Your pace | Review with siblings and attorney |
| **4** | When ready | Scott executes your chosen path — start to close |

---

## ✅ Call to Action

**You do not need to decide anything today. No pressure. No timeline.**

When you are ready — even for questions only — Scott is here:

### 📞 Call or Text: **615-953-0758**
**Scott Hardesty · eXp Realty · Mount Juliet, TN**

**May I suggest a simple next step?**

Schedule a complimentary **10–15 minute call** — phone or in-person at the property — to review your Equity Snapshot and answer every question on your list.

| | |
|---|---|
| **Option A** | [Day / Time — e.g., Thursday 10:00 AM] |
| **Option B** | [Day / Time — e.g., Friday 2:00 PM] |

*Reply STOP to opt out of texts. Email always welcome.*

---

*"I'm not here to sell you a house. I'm here to be your Project Coordinator — real numbers, real options, real compassion. That's my promise."*

— **Scott Hardesty**

---
*ProbateGuardian Free TN · Middle Tennessee Probate Real Estate Specialists*
*Not legal advice · All sales subject to court approval where required · © {year} Scott Hardesty, eXp Realty* 🏠"""


# ── Load persisted leads (after all helpers are defined) ─────────────────────
get_leads()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Scott Hardesty")
    st.markdown("**eXp Realty** · Mount Juliet, TN")
    st.markdown(
        '<div class="phone-banner">📞 615-953-0758</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("**ProbateGuardian Free TN**")
    st.markdown("Compassion · Clarity · Closings")
    st.markdown("---")
    analytics = compute_analytics(get_leads())
    st.metric("Total Leads", analytics["total"])
    st.metric(f"{PARTNER_NAME.split()[0]}", analytics["branton_count"])
    st.metric("Due Today", analytics["due_today"])
    st.metric("Calls", analytics["total_calls"])

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">🏠 ProbateGuardian Free TN</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">24/7 Partnership CRM for Scott Hardesty + Branton Walker</p>',
    unsafe_allow_html=True,
)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Lead Workflow",
    "Bulk Qualifier",
    "Dashboard",
    "📘 Partner Kit",
    "🛠️ Vendors Rolodex",
    "🎥 Training",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Lead Workflow
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Lead Workflow")
    st.caption("Paste county lead data below, then choose your action.")

    raw_lead = st.text_area(
        "County Lead Data",
        height=220,
        placeholder=(
            "Paste lead details here...\n\n"
            "Example:\n"
            "Estate of Mary Johnson\n"
            "John Johnson (Executor)\n"
            "4521 Saundersville Rd, Mount Juliet, TN 37122\n"
            "Wilson County\n"
            "615-555-1234\n"
            "john@email.com"
        ),
        key="workflow_lead",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        gen_outreach = st.button("Generate Full Outreach", use_container_width=True, type="primary")
    with col2:
        gen_kit = st.button("Create Guardian Kit", use_container_width=True, type="primary")
    with col3:
        assign_partner = st.button(f"Assign to {PARTNER_NAME}", use_container_width=True, type="primary")

    if gen_outreach:
        if not raw_lead.strip():
            st.warning("Paste county lead data first.")
        else:
            parsed = parse_lead(raw_lead)
            st.success("✅ Elite outreach script — Aaron + Rick Yen with price anchoring & family dynamics probes.")
            st.text_area("Phone Script", generate_phone_script(parsed), height=700)

    if gen_kit:
        if not raw_lead.strip():
            st.warning("Paste county lead data first.")
        else:
            parsed = parse_lead(raw_lead)
            st.success("✅ Ultimate Guardian Kit — heavy lifting, Express Offers, funded repairs, subject to court approval.")
            st.markdown(generate_guardian_kit(parsed, st.session_state.vendors))

    if assign_partner:
        if not raw_lead.strip():
            st.warning("Paste county lead data first.")
        else:
            parsed = parse_lead(raw_lead)
            parsed["raw"] = raw_lead
            heat_status, heat_pipeline = heat_from_import_block(raw_lead)
            lead_entry = build_lead(
                parsed,
                assigned_to_branton=True,
                pipeline_stage=heat_pipeline,
                status=heat_status,
                source="workflow",
                notes=initial_notes_from_block(raw_lead, source="Lead Workflow"),
            )
            st.session_state.leads.insert(0, lead_entry)
            persist_leads()
            st.success(
                f"🎯 **Assigned to {PARTNER_NAME}!** · {parsed['decedent']} · {parsed['address']} · "
                f"Follow-up: **{lead_entry['follow_up']}**"
            )
            st.info(
                f"{PARTNER_NAME} has been notified. Lead is live on the Dashboard. "
                "Next step: Generate outreach script and schedule first contact within 24 hours."
            )
            st.rerun()

    st.markdown("---")
    st.subheader("⚖️ Attorney Outreach")
    st.caption("Templates for attorney relationships — contract forwarding, thank-you video, pie campaign, review request.")

    att_col1, att_col2 = st.columns(2)
    with att_col1:
        attorney_name = st.text_input("Attorney Name", placeholder="e.g., Jane Smith, Esq.", key="att_name")
    with att_col2:
        attorney_firm = st.text_input("Firm Name", placeholder="e.g., Smith & Associates", key="att_firm")

    att_parsed = parse_lead(raw_lead) if raw_lead.strip() else {
        "decedent": "[Decedent Name]",
        "address": "[Property Address]",
        "county": "[County]",
        "heirs": "[Executor / Heir]",
    }

    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        btn_contract = st.button("Contract Forwarding", use_container_width=True)
    with ac2:
        btn_video = st.button("Thank-You Video", use_container_width=True)
    with ac3:
        btn_pie = st.button("Pie Campaign", use_container_width=True)
    with ac4:
        btn_review = st.button("Review Request", use_container_width=True)

    if btn_contract:
        if not attorney_name.strip():
            st.warning("Enter attorney name first.")
        else:
            st.success("✅ Contract forwarding email generated.")
            st.text_area(
                "Contract Forwarding Email",
                generate_attorney_template("contract_forwarding", attorney_name, attorney_firm, att_parsed),
                height=380,
            )
    if btn_video:
        if not attorney_name.strip():
            st.warning("Enter attorney name first.")
        else:
            st.success("✅ Thank-you video outreach email generated.")
            st.text_area(
                "Thank-You Video Email",
                generate_attorney_template("thank_you_video", attorney_name, attorney_firm, att_parsed),
                height=380,
            )
    if btn_pie:
        if not attorney_name.strip():
            st.warning("Enter attorney name first.")
        else:
            st.success("✅ Pie campaign touch email generated.")
            st.text_area(
                "Pie Campaign Email",
                generate_attorney_template("pie_campaign", attorney_name, attorney_firm, att_parsed),
                height=380,
            )
    if btn_review:
        if not attorney_name.strip():
            st.warning("Enter attorney name first.")
        else:
            st.success("✅ Review request email generated.")
            st.text_area(
                "Review Request Email",
                generate_attorney_template("review_request", attorney_name, attorney_firm, att_parsed),
                height=380,
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Bulk Qualifier
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Bulk Qualifier")
    st.caption("Paste raw county export data — petitions, heir info, addresses. We'll parse and qualify.")

    bulk_flash = st.session_state.pop("bulk_qualify_flash", None)
    if bulk_flash:
        st.success(bulk_flash)

    bulk_raw = st.text_area(
        "Raw County Data",
        height=280,
        placeholder=(
            "Paste multiple leads separated by blank lines...\n\n"
            "Estate of Robert Smith\n"
            "4521 Main St, Lebanon, TN 37087\n"
            "Wilson County\n\n"
            "Estate of Linda Davis\n"
            "890 Heritage Dr, Murfreesboro, TN 37129\n"
            "Rutherford County"
        ),
        key="bulk_data",
    )

    if st.button("Analyze & Qualify Leads", use_container_width=True, type="primary"):
        if not bulk_raw.strip():
            st.warning("Paste raw county data first.")
        else:
            blocks = [b.strip() for b in re.split(r"\n\s*\n", bulk_raw.strip()) if b.strip()]
            qualified_count = 0

            for block in blocks:
                parsed = parse_lead(block)
                score, status, flags = score_lead(parsed)

                if status == "Qualified":
                    qualified_count += 1
                    parsed["raw"] = block
                    heat_status, heat_pipeline = heat_from_import_block(block)
                    st.session_state.leads.insert(0, build_lead(
                        parsed,
                        pipeline_stage=heat_pipeline,
                        status=heat_status,
                        score=score,
                        source="bulk",
                        follow_up_days=1,
                        notes=initial_notes_from_block(block, source="Bulk Qualifier"),
                    ))

            persist_leads()
            st.session_state.bulk_qualify_flash = (
                f"✅ Analysis complete — **{qualified_count} of {len(blocks)}** leads qualified "
                f"and synced to Dashboard · **{len(st.session_state.leads)}** total leads."
            )
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Dashboard / CRM
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.session_state.setdefault("crm_list_mode", "all")
    st.session_state.setdefault("crm_stage_list_filter", "All")

    st.markdown('<div class="crm-top-filters-start"></div>', unsafe_allow_html=True)
    due_col, all_col, _ = st.columns([1, 1, 3], gap="small")
    with due_col:
        if st.button("📅 Due Today", key="crm_due_today_btn", use_container_width=True, type="primary"):
            st.session_state.crm_list_mode = "due_today"
            st.session_state.crm_stage_list_filter = "All"
            st.rerun()
    with all_col:
        if st.button("All Leads", key="crm_all_leads_btn", use_container_width=True, type="secondary"):
            st.session_state.crm_list_mode = "all"
            st.session_state.crm_stage_list_filter = "All"
            st.rerun()

    analytics = compute_analytics(get_leads())

    st.markdown("### 📈 Analytics")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Total Leads", analytics["total"])
    m2.metric("Total Calls", analytics["total_calls"])
    m3.metric("Avg Calls/Lead", analytics["avg_calls"])
    m4.metric("→ Warm %", f"{analytics['conv_warm']}%")
    m5.metric("→ Appt %", f"{analytics['conv_appt']}%")
    m6.metric("Closed %", f"{analytics['conv_close']}%")

    pcols = st.columns(5)
    for i, stage in enumerate(PIPELINE_STAGES):
        pcols[i].metric(stage, analytics["stages"][stage])

    ins1, ins2 = st.columns(2)
    with ins1:
        st.markdown("**🏆 Top Counties**")
        if analytics["top_counties"]:
            for county, cnt in analytics["top_counties"]:
                st.markdown(f"- **{county}** — {cnt} leads")
        else:
            st.caption("Import leads to see county breakdown.")
    with ins2:
        st.markdown("**✅ What's Working**")
        if analytics["total"] > 0:
            best = analytics["top_counties"][0][0] if analytics["top_counties"] else "Wilson County"
            st.markdown(f"- **Best county:** {best}")
            st.markdown(f"- **Branton assignments:** {analytics['branton_count']} active")
            st.markdown(f"- **Follow-ups due today:** {analytics['due_today']}")
            top_src = max(analytics["sources"], key=analytics["sources"].get) if analytics["sources"] else "workflow"
            st.markdown(f"- **Top lead source:** {top_src}")
        else:
            st.caption("Start in Wilson County · use Bulk Qualifier · assign to Branton.")

    st.markdown("---")
    dash_tab1, dash_tab2, dash_tab3 = st.tabs(["📋 Leads Table", "📅 Follow-Up Scheduler", "📥 Import Leads"])

    with dash_tab3:
        st.markdown("**Paste county data** (blank line between leads) or **upload CSV**.")
        import_text = st.text_area("Bulk Import", height=160, key="crm_import_text", placeholder="Estate of...\nAddress...\nWilson County")
        ic1, ic2 = st.columns(2)
        with ic1:
            if st.button("Import Pasted Leads", use_container_width=True, type="primary"):
                if import_text.strip():
                    n = import_leads_from_text(import_text, source="paste")
                    st.success(f"✅ Imported {n} leads.")
                    st.rerun()
                else:
                    st.warning("Paste lead data first.")
        with ic2:
            csv_file = st.file_uploader("Upload CSV", type=["csv"], key="crm_csv")
            if csv_file and st.button("Import CSV", use_container_width=True):
                n = import_leads_from_csv(csv_file.getvalue())
                st.success(f"✅ Imported {n} leads from CSV.")
                st.rerun()

    with dash_tab2:
        st.markdown("**Leads due for follow-up** (today or overdue, not Closed)")
        today = datetime.now().strftime("%Y-%m-%d")
        due_leads = [
            l for l in st.session_state.leads
            if l.get("follow_up_iso", "9999") <= today and effective_pipeline_stage(l) != "Closed"
        ]
        due_leads.sort(key=lambda x: x.get("follow_up_iso", ""))
        if not due_leads:
            st.success("No follow-ups due — you're caught up!")
        for lead in due_leads:
            with st.expander(f"📅 {lead.get('decedent')} — due {lead.get('follow_up_iso')} · {lead.get('pipeline_stage')}"):
                st.markdown(f"**{lead.get('address')}** · {lead.get('phone', 'No phone')}")
                new_date = st.date_input(
                    "Reschedule",
                    value=datetime.strptime(lead.get("follow_up_iso", today), "%Y-%m-%d").date(),
                    key=f"sched_{lead['id']}",
                )
                if st.button("Save Follow-Up Date", key=f"savefu_{lead['id']}"):
                    update_lead(lead["id"], follow_up_iso=new_date.strftime("%Y-%m-%d"))
                    st.rerun()
                if st.button("Log Call + Move to Warm", key=f"schedcall_{lead['id']}"):
                    log_call(lead["id"])
                    update_lead(lead["id"], pipeline_stage="Warm / Talking", status="Contacted")
                    st.rerun()

    with dash_tab1:
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            pipe_filter = st.selectbox("Pipeline", ["All"] + PIPELINE_STAGES, key="crm_pipe_filter")
        with fc2:
            branton_filter = st.selectbox("Assignment", ["All", f"Assigned to {PARTNER_NAME}", "Unassigned"], key="crm_branton_filter")
        with fc3:
            county_filter = st.selectbox(
                "County",
                ["All"] + sorted({l.get("county", "") for l in st.session_state.leads if l.get("county")}),
                key="crm_county_filter",
            )

        filtered = st.session_state.leads
        if pipe_filter != "All":
            filtered = [l for l in filtered if effective_pipeline_stage(l) == pipe_filter]
        if branton_filter == f"Assigned to {PARTNER_NAME}":
            filtered = [l for l in filtered if l.get("assigned_to_branton")]
        elif branton_filter == "Unassigned":
            filtered = [l for l in filtered if not l.get("assigned_to_branton")]
        if county_filter != "All":
            filtered = [l for l in filtered if l.get("county") == county_filter]

        list_filtered = _apply_crm_list_filters(filtered)
        filter_bits = []
        if st.session_state.get("crm_list_mode") == "due_today":
            filter_bits.append("due today + high-score")
        if st.session_state.get("crm_stage_list_filter", "All") != "All":
            filter_bits.append(st.session_state.crm_stage_list_filter)
        filter_note = f" · List: **{', '.join(filter_bits)}**" if filter_bits else ""
        st.caption(
            f"Showing **{len(list_filtered)}** in list / **{len(filtered)}** matched / "
            f"**{len(st.session_state.leads)}** total{filter_note}"
        )

        if not filtered:
            st.info("No leads match filters. Import via **Import Leads** tab or use Lead Workflow.")
        else:
            list_ids = {l["id"] for l in list_filtered}
            if list_filtered and st.session_state.get("crm_selected_lead_id") not in list_ids:
                _flush_dash_notes(st.session_state.get("crm_selected_lead_id"))
                st.session_state.crm_selected_lead_id = list_filtered[0]["id"]
                st.session_state.pop("_dash_notes_sync_id", None)

            list_col, detail_col = st.columns([2, 3], gap="medium")

            with list_col:
                st.markdown("**Leads**")
                if not list_filtered:
                    st.info("No leads match the current list filter. Tap **All Leads** to reset.")
                with st.container(height=520):
                    for item in list_filtered:
                        is_selected = st.session_state.get("crm_selected_lead_id") == item["id"]
                        if st.button(
                            _lead_list_button_label(item),
                            key=f"pick_{item['id']}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary",
                        ):
                            _select_crm_lead(item["id"])
                            st.rerun()

            selected_id = st.session_state.get("crm_selected_lead_id")
            lead = find_lead(selected_id)

            with detail_col:
                st.markdown("#### Lead Detail & Edit")

                if not lead:
                    st.info("Select a lead from the list.")
                else:
                    e1, e2, e3, e4 = st.columns([3, 2, 2, 1])
                    current_stage = detail_pipeline_stage(lead)
                    with e1:
                        new_stage = st.selectbox(
                            "Pipeline Stage",
                            DETAIL_PIPELINE_STAGES,
                            index=DETAIL_PIPELINE_STAGES.index(current_stage),
                            key=f"stage_{lead['id']}",
                            on_change=_on_pipeline_stage_list_filter,
                            args=(lead["id"],),
                        )
                    with e2:
                        fu_label = "Next Follow-up Date" if new_stage == NURTURE_STAGE else "Follow-Up"
                        new_fu = st.date_input(
                            fu_label,
                            value=datetime.strptime(lead.get("follow_up_iso", follow_up_iso()), "%Y-%m-%d").date(),
                            key=f"fu_{lead['id']}",
                        )
                    with e3:
                        branton_toggle = st.toggle(
                            f"Assign to {PARTNER_NAME}",
                            value=bool(lead.get("assigned_to_branton")),
                            key=f"branton_{lead['id']}",
                        )
                    with e4:
                        st.metric("Calls", lead.get("calls", 0))

                    st.markdown('<div class="crm-quick-stage-start"></div>', unsafe_allow_html=True)
                    qs1, qs2, qs3, qs4, qs5 = st.columns(5, gap="small")
                    with qs1:
                        st.button(
                            "🔥 Move to Hot",
                            key=f"qhot_{lead['id']}",
                            use_container_width=True,
                            type="primary",
                            on_click=_quick_stage_callback,
                            args=(lead["id"], "🔥 Hot / New (call today)"),
                        )
                    with qs2:
                        st.button(
                            "Move to Warm",
                            key=f"qwarm_{lead['id']}",
                            use_container_width=True,
                            on_click=_quick_stage_callback,
                            args=(lead["id"], "Warm / Talking"),
                        )
                    with qs3:
                        st.button(
                            "Set Appointment",
                            key=f"qappt_{lead['id']}",
                            use_container_width=True,
                            on_click=_quick_stage_callback,
                            args=(lead["id"], "Appointment Set"),
                        )
                    with qs4:
                        st.button(
                            "Not Interested",
                            key=f"qni_{lead['id']}",
                            use_container_width=True,
                            on_click=_quick_stage_callback,
                            args=(lead["id"], "Not Interested / Keeping"),
                        )
                    with qs5:
                        st.button(
                            "Archive",
                            key=f"qarch_{lead['id']}",
                            use_container_width=True,
                            on_click=_quick_stage_callback,
                            args=(lead["id"], "Archived"),
                        )

                    st.caption(
                        f"**{lead.get('decedent', 'Unknown')}** · {lead.get('address', '—')} · "
                        f"📞 {lead.get('phone') or '—'} · Score **{lead.get('score', 0)}** · "
                        f"{lead.get('county', '—')}"
                    )

                    note_text = st.text_area(
                        "Add Note",
                        key=f"note_{lead['id']}",
                        placeholder="Call outcome, heir feedback, next steps...",
                    )
                    b1, b2, b3, b4 = st.columns(4)
                    with b1:
                        if st.button("💾 Save Changes", key=f"save_{lead['id']}", use_container_width=True, type="primary"):
                            _flush_dash_notes(lead["id"])
                            update_lead(
                                lead["id"],
                                pipeline_stage=new_stage,
                                follow_up_iso=new_fu.strftime("%Y-%m-%d"),
                                assigned_to_branton=branton_toggle,
                                status="Closed" if new_stage in CLOSED_DETAIL_STAGES else lead.get("status", "New"),
                            )
                            if note_text.strip():
                                add_note(lead["id"], note_text, author=PARTNER_NAME if branton_toggle else "Scott")
                            st.session_state.pop("_dash_notes_sync_id", None)
                            st.rerun()
                    with b2:
                        if st.button("📞 Log Call", key=f"call_{lead['id']}", use_container_width=True):
                            _flush_dash_notes(lead["id"])
                            log_call(lead["id"])
                            st.rerun()
                    with b3:
                        if st.button("⬆️ → Warm", key=f"warm_{lead['id']}", use_container_width=True):
                            _flush_dash_notes(lead["id"])
                            update_lead(lead["id"], pipeline_stage="Warm / Talking", status="Contacted")
                            st.rerun()
                    with b4:
                        if st.button("🗑️ Remove", key=f"del_{lead['id']}", use_container_width=True):
                            _flush_dash_notes(lead["id"])
                            st.session_state.leads = [l for l in st.session_state.leads if l["id"] != lead["id"]]
                            persist_leads()
                            st.session_state.pop("crm_selected_lead_id", None)
                            st.session_state.pop("_dash_notes_sync_id", None)
                            st.rerun()

                    st.markdown("**Notes**")
                    notes_widget_key = f"dash_notes_{lead['id']}"
                    if st.session_state.get("_dash_notes_sync_id") != lead["id"]:
                        st.session_state[notes_widget_key] = get_lead_notes_full_text(lead)
                        st.session_state["_dash_notes_sync_id"] = lead["id"]
                    st.markdown('<div class="dash-notes-marker"></div>', unsafe_allow_html=True)
                    st.text_area(
                        "Full lead notes",
                        height=220,
                        key=notes_widget_key,
                        label_visibility="collapsed",
                        on_change=_on_dash_notes_saved,
                        args=(lead["id"], notes_widget_key),
                    )
                    if lead.get("days_since_death") is not None:
                        st.caption(
                            f"Death ~{lead.get('days_since_death')} days ago · "
                            f"Status: **{lead.get('status', '—')}** · Pipeline: **{lead.get('pipeline_stage', '—')}**"
                        )

                    if lead.get("activity"):
                        st.markdown("**Activity**")
                        for act in lead["activity"][:5]:
                            st.caption(f"{act.get('ts', '')[:16]} · {act.get('type', '')} · {act.get('detail', '')}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Partner Kit
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📘 Partner Kit — Branton Walker Partnership")
    st.markdown(
        """
        **We are building this together.**

        **Branton Walker + Scott Hardesty = true 50/50 partners** on every probate deal we close in Middle TN.

        You keep **100% of everything else** you sell.

        We split probate listings and any JV flips.

        **Goal:** Build a scalable, profitable probate & flip operation that makes both of us serious money
        while solving the massive problem of overwhelmed families who just lost a loved one.
        """
    )

    st.markdown("---")
    st.markdown(f"## 🎯 Your Role — {PARTNER_NAME}")
    st.markdown(
        f"""
        You are the **execution engine** of ProbateGuardian. Scott builds the systems,
        sources the leads, and closes the strategy — **{PARTNER_NAME}** runs the daily playbook that
        turns county filings into signed contracts.

        **Your core responsibilities:**

        | Area | What You Own |
        |------|-------------|
        | **Lead Contact** | First call within 24 hours — early-outreach script, "Tell me more about that" |
        | **Appointments** | Book 10–15 min calls or visits within 48 hours with printed Guardian Kit |
        | **Follow-Up** | 3-touch minimum: call → Net Sheet delivery → Express Offers analysis |
        | **Pipeline** | Keep Dashboard updated. Mark leads Contacted, Qualified, Under Contract |
        | **Closings** | Manage transaction through close — coordinate vendors, attorneys, title |
        | **Reporting** | Weekly pipeline report to Scott: leads touched, appointments set, contracts out |
        | **Express Offers** | Present competing cash offers at every appointment — your #1 probate closer |
        """
    )

    st.markdown("---")
    st.markdown("## 🏗️ Scott's Role — Systems & Scale")
    st.markdown(
        """
        | Area | What Scott Owns |
        |------|----------------|
        | **Lead Generation** | County data sourcing, Bulk Qualifier, lead scoring |
        | **Systems** | ProbateGuardian app, CRM, vendor relationships, Express Offers network |
        | **Strategy** | Pricing, offer structure, deal negotiation, $20M+ volume roadmap |
        | **Training** | Scripts, Guardian Kits, Aaron Novello methodology, ongoing coaching |
        | **High-Level Relationships** | eXp leadership, attorney partnerships, investor network |
        | **Overflow Support** | Jump on calls for complex deals, sibling disputes, or high-value properties |
        """
    )

    st.markdown("---")
    st.markdown("## 📅 Daily Action Plan")
    st.markdown(
        f"""
        ### Morning Block (8:00 – 10:00 AM)
        1. Open **Dashboard** — review new assignments and follow-ups due today
        2. Make **first-contact calls** on all leads assigned to {PARTNER_NAME} in last 24 hours
        3. Use **Generate Full Outreach** — Aaron + Rick Yen script with price anchoring
        4. Log every call outcome on Dashboard (Contacted / No Answer / Callback)

        ### Midday Block (10:00 AM – 2:00 PM)
        5. Run **property appointments** — bring printed Guardian Kit (Express Offers section first)
        6. Present **all four options**: Express Offers, Traditional + Funded Repairs, Muniment of Title, Off-Market
        7. Same-day follow-up text: *"Great speaking with you. Your free Equity Snapshot + Net Sheet coming within 48 hours."*

        ### Afternoon Block (2:00 – 5:00 PM)
        8. **Follow-up calls** on leads from prior days — 3-touch minimum before archiving
        9. Update Dashboard statuses — move qualified leads to Under Contract when applicable
        10. Send Scott your **daily recap**: calls made, appointments set, contracts out

        ### Weekly (Friday by 4 PM)
        - Pipeline report: total leads, contacted %, appointments, contracts, projected GCI
        - Review **🎥 Training** tab — one featured video (Aaron, Rick, Jose, or Bruce/Heath)
        - Send one **Attorney Outreach** touch (pie campaign, thank-you video, or review)
        - Update **🛠️ Vendors Rolodex** with any new contacts
        """
    )

    st.markdown("---")
    st.markdown("## 🎓 Training Instructions")
    st.markdown(
        f"""
        1. **Read this entire Partner Kit** before making your first call
        2. Go to the **🎥 Training** tab — start with Aaron Novello's probate overview videos
        3. Practice the **phone script** out loud 3 times before your first real call
        4. Print a sample **Guardian Kit** and bring it to every appointment
        5. Master the close: **"May I make a suggestion?"** → 10–15 min call, not a listing pitch
        6. Position as **Project Coordinator** — "we handle the heavy lifting" (Jose / Bruce-Heath)
        7. Use **Rick Yen price anchoring** — range on call #1, Net Sheet on call #2
        8. Use **Attorney Outreach** templates after every attorney referral
        9. Memorize **Express Offers** + always say **subject to court approval**
        10. Save Scott's number: **615-953-0758** — call anytime you're stuck on a deal

        > **Golden Rule (Aaron Novello):** You're not calling to sell. You're calling to help a family
        > in pain make a good decision. The deals follow the compassion. Every time.
        """
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Vendors Rolodex
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("🛠️ Vendors Rolodex")
    st.caption(
        "Up to 4 vendors per category — name, phone, and quick notes "
        '(e.g. "fast with heirs", "vacant home specialist", "good for out-of-town families"). '
        "Auto-populates in every Guardian Kit."
    )

    for category in VENDOR_CATEGORIES:
        entry = st.session_state.vendors.get(category, _vendor_slot())
        with st.expander(f"**{category}**", expanded=False):
            for slot in range(1, VENDOR_SLOTS + 1):
                contact = _coerce_vendor_contact(entry.get(f"vendor_{slot}", ""))
                st.markdown(f"**Vendor {slot}**")
                n1, n2, n3 = st.columns([2, 1, 2])
                with n1:
                    contact["name"] = st.text_input(
                        "Name",
                        value=contact.get("name", ""),
                        placeholder="Company or contact name",
                        key=f"vname_{slot}_{category}",
                        label_visibility="collapsed",
                    )
                with n2:
                    contact["phone"] = st.text_input(
                        "Phone",
                        value=contact.get("phone", ""),
                        placeholder="Phone",
                        key=f"vphone_{slot}_{category}",
                        label_visibility="collapsed",
                    )
                with n3:
                    contact["notes"] = st.text_input(
                        "Notes",
                        value=contact.get("notes", ""),
                        placeholder='e.g. fast with heirs · vacant home specialist',
                        key=f"vnotes_{slot}_{category}",
                        label_visibility="collapsed",
                    )
                entry[f"vendor_{slot}"] = contact
            entry["area_notes"] = st.text_input(
                "Category area notes",
                value=entry.get("area_notes", ""),
                placeholder="e.g., Wilson County preferred · Mount Juliet area",
                key=f"area_{category}",
            )
        st.session_state.vendors[category] = entry

    if st.button("💾 Save Vendors", use_container_width=True, type="primary"):
        st.session_state.vendors = migrate_vendors(st.session_state.vendors)
        st.success("✅ Vendor Rolodex saved — all Guardian Kits will reflect these contacts.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Training
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("🎥 Training — Elite Probate Playbook")
    st.caption("Aaron Novello · Rick Yen · Jose · Bruce & Heath — study before every call.")

    st.markdown("---")
    st.markdown("### ⭐ Featured Training — Start Here")
    st.markdown(
        """
        | Trainer | Session | Direct Link |
        |---------|---------|-------------|
        | **Aaron Novello** | Probate Role-Play (live call breakdown) | [▶ Watch Role-Play Training](https://www.youtube.com/results?search_query=aaron+novello+probate+role+play+phone+call) |
        | **Aaron Novello** | "May I Make a Suggestion?" Close | [▶ Watch the Close](https://www.youtube.com/results?search_query=aaron+novello+may+i+make+a+suggestion+probate) |
        | **Rick Yen** | Probate Conversation & Price Anchoring | [▶ Watch Rick Yen Conversation](https://www.youtube.com/results?search_query=rick+yen+probate+real+estate+conversation) |
        | **Rick Yen** | Collaborative Discovery Scripts | [▶ Watch Rick Yen Scripts](https://www.youtube.com/results?search_query=rick+yen+probate+scripts+anchoring) |
        | **Jose** | Attorney Referral & Partnership Strategies | [▶ Watch Jose Attorney Strategies](https://www.youtube.com/results?search_query=jose+probate+attorney+referral+strategy) |
        | **Jose** | Project Coordinator & Ancillary Services | [▶ Watch Jose Coordinator Model](https://www.youtube.com/results?search_query=jose+probate+project+coordinator+ancillary) |
        | **Bruce & Heath** | Concierge / Heavy Lifting Model | [▶ Watch Bruce Heath Concierge](https://www.youtube.com/results?search_query=bruce+heath+probate+concierge+real+estate) |
        | **Bruce & Heath** | Vendor Coordination & Estate Reset | [▶ Watch Estate Reset Playbook](https://www.youtube.com/results?search_query=bruce+heath+estate+sale+cleanout+probate) |
        """
    )

    st.markdown("---")
    st.markdown("### 📺 Aaron Novello — Core Library")
    st.markdown(
        """
        | Resource | Topic | Link |
        |----------|-------|------|
        | Probate Real Estate 101 | Why probate is the #1 niche | [YouTube](https://www.youtube.com/results?search_query=aaron+novello+probate+real+estate+101) |
        | Empathy-First Call | Compassion before pitch | [YouTube](https://www.youtube.com/results?search_query=aaron+novello+empathy+first+probate+call) |
        | Early Outreach | "Very respectfully" positioning | [YouTube](https://www.youtube.com/results?search_query=aaron+novello+early+outreach+probate) |
        | Listing Presentation | Options, not pressure | [YouTube](https://www.youtube.com/results?search_query=aaron+novello+probate+listing+presentation) |
        | Objection Handling | Not ready / have attorney / too early | [YouTube](https://www.youtube.com/results?search_query=aaron+novello+probate+objections) |
        | Follow-Up System | 3-touch minimum | [YouTube](https://www.youtube.com/results?search_query=aaron+novello+probate+follow+up+system) |
        """
    )

    st.markdown("---")
    st.markdown("### 🎙️ Elite Script Swipes — Memorize These")
    st.markdown(
        """
        **Respectful opener (Aaron):**
        > *"I realize I may be reaching out a little early… very respectfully. Nothing needs to happen today."*

        **Honest expectations (Aaron + Rick):**
        > *"More likely than not the goal will be to sell — but that might be months from now."*

        **Power listen (Aaron + Rick):**
        > *"Tell me more about that."* — use 2–3 times per call.

        **Rick Yen price anchoring:**
        > *"In [county], similar homes range from $[LOW] as-is to $[HIGH] updated — but that's from the outside. The Net Sheet gives YOUR number."*

        **Rick Yen collaborative:**
        > *"Help me understand — walk me through where things stand with the estate."*

        **Family dynamics (Jose):**
        - *"How many heirs? Everyone on the same page?"*
        - *"Anyone want to buy out the others?"*
        - *"Anyone out of state?"*

        **Bruce/Heath concierge:**
        > *"You focus on family. We handle the heavy lifting — estate sale, cleanout, lockbox, utilities, lawn."*

        **Close (Aaron):**
        > *"May I make a suggestion?"* → 10–15 min call → free Equity Snapshot

        **Court language (always):**
        > *"Subject to court approval"* — every timeline, every offer, every close.
        """
    )

    st.markdown("---")
    st.markdown("### ⚖️ Attorney Outreach Playbook")
    st.markdown(
        """
        Use **Lead Workflow → Attorney Outreach** templates after every attorney touch:

        | Template | When to Send |
        |----------|--------------|
        | **Contract Forwarding** | Listing agreement ready — loop attorney before marketing |
        | **Thank-You Video** | After first referral or quarterly relationship touch |
        | **Pie Campaign** | Seasonal gratitude drop — Thanksgiving, Christmas, Q1 |
        | **Review Request** | 48 hours after smooth closing — Google review ask |

        **Jose attorney rules:**
        - Never market property until attorney confirms authority to sell
        - Defer every legal question back to their office
        - Make their job easier — they refer you again
        """
    )

    st.markdown("---")
    st.markdown(f"### ⚡ {PARTNER_NAME}'s Daily Checklist")
    st.markdown(
        f"""
        **Before calls:** Generate Full Outreach script · Guardian Kit ready · Dashboard open

        **On calls:** Respectful opener → tell me more → family probes → price anchor → may I suggest

        **After calls:** Log Dashboard · Send Net Sheet in 48 hrs · Attorney loop-in if involved

        **Guardian Kit highlights:** Project Coordinator · Heavy lifting table · Express Offers · funded repairs

        **Escalate to Scott (615-953-0758):** Sibling disputes · buyout math · competing agent · $500K+
        """
    )

    st.markdown("---")
    st.markdown("### 📖 Quick Links")
    st.markdown(
        """
        - [eXp Express Offers](https://www.exprealty.com) — Multi-buyer cash submissions
        - [TN Muniment of Title — T.C.A. 32](https://www.tn.gov/content/tn/tcas/search.html) — No-debt transfer path
        - **Lead Workflow** — Full Outreach · Guardian Kit · Attorney Outreach templates
        - **615-953-0758** — Scott Hardesty · Mount Juliet, TN
        """
    )