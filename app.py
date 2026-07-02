import base64
import csv
import html
import io
import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

st.cache_data.clear = lambda: None
st.cache_resource.clear = lambda: None

# ── Constants ────────────────────────────────────────────────────────────────
PARTNER_NAME = "Branton Walker"
DEDICATED_PHONE = "(615) 669-7075"
DEDICATED_PHONE_TEL = "6156697075"
DEDICATED_PHONE_LINE = f"Call or text {DEDICATED_PHONE}"
DEDICATED_PHONE_HTML = f'Call or text <strong>{DEDICATED_PHONE}</strong>'
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
VENDORS_FILE = (Path(__file__).resolve().parent / "vendors_data.json")
GITHUB_REPO = "scotterh23/ProbateGuardian_TN"
GITHUB_LEADS_PATH = "leads_data.json"
GITHUB_VENDORS_PATH = "vendors_data.json"
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
    .crm-top-filters-start + div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button:hover {
        transform: none !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
    }
    .crm-lead-contact-head-md-marker { display: none; }
    .crm-lead-contact-head-md-marker + div {
        margin: 0.35rem 0 0.2rem 0 !important;
        padding: 0.55rem 0.65rem !important;
        background: linear-gradient(135deg, #1c2128 0%, #161b22 100%) !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    .crm-lead-contact-head-md-marker + div h3 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: 1.22rem !important;
        font-weight: 900 !important;
        line-height: 1.35 !important;
        color: #ffffff !important;
    }
    .crm-lead-contact-head-md-marker + div strong {
        color: #ffffff !important;
        font-weight: 900 !important;
    }
    .crm-lead-primary-contact-md-marker { display: none; }
    .crm-lead-primary-contact-md-marker + div {
        margin-bottom: 0.75rem !important;
        padding: 0.85rem 1rem !important;
        background: linear-gradient(135deg, #1a3a2a 0%, #0d2818 100%) !important;
        border: 2px solid #2ea043 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(46, 160, 67, 0.22) !important;
    }
    .crm-lead-primary-contact-md-marker + div h2 {
        margin: 0 !important;
        padding: 0 !important;
        font-size: clamp(1.55rem, 5vw, 2rem) !important;
        font-weight: 900 !important;
        line-height: 1.3 !important;
        color: #ffffff !important;
    }
    .crm-lead-primary-contact-md-marker + div strong {
        color: #ffffff !important;
        font-weight: 900 !important;
    }
    [data-testid="stToast"] {
        background: linear-gradient(135deg, #1a4d2e, #238636) !important;
        color: #ffffff !important;
        border: 1px solid #3fb950 !important;
    }
    .notes-saved-caption {
        color: #3fb950 !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        margin-top: 0.35rem !important;
    }
    .export-notes-marker { display: none; }
    .export-notes-marker + div [data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #b62324, #da3633) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        min-height: 3.25rem !important;
        width: 100% !important;
        box-shadow: 0 4px 18px rgba(218, 54, 51, 0.45) !important;
    }
    .export-notes-marker + div [data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(135deg, #da3633, #f85149) !important;
        color: #ffffff !important;
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
    .crusher-glow-marker { display: none; }
    .crusher-glow-marker + div [data-testid="stTextArea"] textarea {
        min-height: 14rem !important;
        font-size: 1rem !important;
        border: 2px solid #3fb950 !important;
        box-shadow: 0 0 22px rgba(63, 185, 80, 0.42), inset 0 0 12px rgba(63, 185, 80, 0.08) !important;
    }
    .crusher-title {
        font-size: 1.55rem;
        font-weight: 800;
        color: #f0b429 !important;
        margin: 0.25rem 0 0.5rem 0;
    }
    .crusher-vacant-pill {
        display: inline-block;
        background: linear-gradient(135deg, #b62324, #ff7b72);
        color: #fff;
        font-weight: 700;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        font-size: 0.82rem;
        margin-left: 0.35rem;
    }
    .crusher-mega-btn-marker { display: none; }
    .crusher-mega-btn-marker + div [data-testid="stButton"] > button {
        min-height: 4.25rem !important;
        font-size: 1.12rem !important;
        font-weight: 800 !important;
        box-shadow: 0 6px 24px rgba(46, 160, 67, 0.5) !important;
    }
    .crusher-smart-glow-marker { display: none; }
    .crusher-smart-glow-marker + div [data-testid="stTextArea"] textarea {
        min-height: 16rem !important;
        font-size: 1.02rem !important;
        border: 2px solid #58a6ff !important;
        box-shadow: 0 0 24px rgba(88, 166, 255, 0.38), inset 0 0 14px rgba(88, 166, 255, 0.06) !important;
    }
    .crusher-hero-callout {
        font-size: clamp(1rem, 3.8vw, 1.18rem);
        font-weight: 800;
        line-height: 1.55;
        color: #ffe08a;
        background: linear-gradient(135deg, #2d1f0f 0%, #1a1208 100%);
        border: 2px solid #f0b429;
        border-radius: 12px;
        padding: 1rem 1.15rem;
        margin: 0.65rem 0 1.1rem 0;
        box-shadow: 0 4px 18px rgba(240, 180, 41, 0.22);
    }
    .crusher-phone-hint {
        font-size: clamp(0.95rem, 3.4vw, 1.05rem);
        font-weight: 700;
        line-height: 1.5;
        color: #79c0ff;
        background: linear-gradient(135deg, #0d2137 0%, #0a1628 100%);
        border: 1px solid #388bfd;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.35rem 0 0.85rem 0;
    }
    .crusher-kpi-card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 2px solid #3fb950;
        border-radius: 14px;
        padding: 1rem 1.1rem 0.85rem 1.1rem;
        margin: 1rem 0 1.25rem 0;
        box-shadow: 0 6px 22px rgba(63, 185, 80, 0.2);
    }
    .crusher-kpi-title {
        font-size: 1.28rem;
        font-weight: 800;
        color: #aff5b4 !important;
        margin: 0 0 0.35rem 0;
    }
    .crusher-kpi-points {
        font-size: clamp(2rem, 8vw, 2.75rem);
        font-weight: 900;
        color: #f0b429;
        text-align: center;
        margin: 0.25rem 0 0.5rem 0;
        line-height: 1.1;
    }
    .call-mode-enter-marker { display: none; }
    .call-mode-enter-marker + div [data-testid="stButton"] > button {
        min-height: 4rem !important;
        font-size: 1.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #1a7f37, #2ea043) !important;
        box-shadow: 0 6px 26px rgba(46, 160, 67, 0.55) !important;
    }
    .call-mode-lead-card {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 2px solid #30363d;
        border-radius: 14px;
        padding: 0.85rem 1rem;
        margin: 0.65rem 0;
    }
    .call-mode-lead-card.call-mode-vacant {
        border-color: #f85149;
        box-shadow: 0 0 16px rgba(248, 81, 73, 0.25);
    }
    .call-mode-lead-title {
        font-size: 1.12rem;
        font-weight: 800;
        color: #f0f6fc;
        margin: 0 0 0.25rem 0;
    }
    .call-mode-paste-marker + div [data-testid="stTextArea"] textarea {
        min-height: 10rem !important;
        border: 2px solid #2ea043 !important;
    }
    .hospice-mega-marker { display: none; }
    .hospice-mega-marker + div [data-testid="stLinkButton"] > a,
    .hospice-mega-marker + div [data-testid="stButton"] > button {
        min-height: 4.25rem !important;
        font-size: 1.05rem !important;
        font-weight: 800 !important;
        box-shadow: 0 6px 24px rgba(46, 160, 67, 0.5) !important;
    }
    .hospice-mega-marker + div [data-testid="stLinkButton"] > a {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: linear-gradient(135deg, #1a7f37, #2ea043) !important;
        border: none !important;
        color: #fff !important;
        border-radius: 0.5rem !important;
        text-decoration: none !important;
        padding: 0.75rem 1rem !important;
    }
    .hospice-hero {
        font-size: clamp(1rem, 3.6vw, 1.12rem);
        font-weight: 700;
        line-height: 1.5;
        color: #aff5b4;
        background: linear-gradient(135deg, #0f1f14 0%, #0d1117 100%);
        border: 2px solid #2ea043;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin: 0.5rem 0 1rem 0;
    }
    .call-mode-thumb-start { display: none; }
    .call-mode-thumb-start + div[data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
        min-height: 3.35rem !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        white-space: normal !important;
        line-height: 1.2 !important;
        padding: 0.6rem 0.35rem !important;
    }
    .gk-action-marker { display: none; }
    .gk-action-marker + div [data-testid="stLinkButton"] > a,
    .gk-action-marker + div [data-testid="stButton"] > button,
    .gk-action-marker + div [data-testid="stDownloadButton"] > button {
        min-height: 3.5rem !important;
        font-size: 1rem !important;
        font-weight: 800 !important;
    }
    .gk-action-marker + div [data-testid="stLinkButton"] > a {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: linear-gradient(135deg, #1a4d32, #2d6a4f) !important;
        color: #faf6ee !important;
        border-radius: 10px !important;
        text-decoration: none !important;
    }
    .income-goal-card {
        background: linear-gradient(135deg, #0f1f14 0%, #142d22 55%, #1a3d2e 100%);
        border: 2px solid #2ea043;
        border-radius: 14px;
        padding: 1rem 1.1rem 0.9rem 1.1rem;
        margin: 0.65rem 0 1rem 0;
        box-shadow: 0 6px 22px rgba(46, 160, 67, 0.22);
    }
    .income-goal-title {
        font-size: clamp(1.15rem, 4vw, 1.35rem);
        font-weight: 800;
        color: #aff5b4 !important;
        margin: 0 0 0.35rem 0;
    }
    .income-goal-motivate {
        font-size: clamp(1rem, 3.8vw, 1.12rem);
        font-weight: 800;
        color: #ffe08a;
        background: linear-gradient(135deg, #1a3d2e, #0f1f14);
        border: 1px solid #3fb950;
        border-radius: 10px;
        padding: 0.75rem 0.85rem;
        margin: 0.65rem 0 0.35rem 0;
        text-align: center;
        line-height: 1.45;
    }
    .income-goal-status-green { color: #3fb950 !important; font-weight: 800; }
    .income-goal-status-red { color: #f85149 !important; font-weight: 800; }
    .income-goal-status-yellow { color: #f0b429 !important; font-weight: 800; }
    .income-goal-metrics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.65rem;
        margin: 0.75rem 0 0.5rem 0;
    }
    @media (min-width: 640px) {
        .income-goal-metrics-grid { grid-template-columns: repeat(4, 1fr); }
    }
    .income-goal-metric-card {
        background: linear-gradient(160deg, #0d1117 0%, #161b22 100%);
        border: 2px solid #30363d;
        border-radius: 12px;
        padding: 0.75rem 0.65rem 0.65rem 0.65rem;
        text-align: center;
    }
    .income-goal-metric-card.ig-on-pace {
        border-color: #2ea043;
        box-shadow: 0 0 18px rgba(46, 160, 67, 0.35);
    }
    .income-goal-metric-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #8b949e;
        margin: 0 0 0.25rem 0;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .income-goal-big-num {
        font-size: clamp(2rem, 11vw, 2.85rem);
        font-weight: 900;
        color: #aff5b4;
        line-height: 1;
        margin: 0.15rem 0 0.45rem 0;
    }
    .income-goal-bar-track {
        background: #0d1117;
        border-radius: 999px;
        height: 12px;
        overflow: hidden;
        border: 1px solid #30363d;
    }
    .income-goal-bar-fill {
        height: 100%;
        border-radius: 999px;
        min-width: 4px;
    }
    .ig-bar-green { background: linear-gradient(90deg, #1a7f37, #3fb950); }
    .ig-bar-amber { background: linear-gradient(90deg, #9a6700, #f0b429); }
    .income-goal-bar-caption {
        font-size: 0.68rem;
        color: #6e7681;
        margin: 0.35rem 0 0 0;
    }
    .income-goal-projected {
        font-size: clamp(1.35rem, 5vw, 1.75rem);
        font-weight: 900;
        margin: 0.5rem 0 0.25rem 0;
        text-align: center;
    }
    .income-goal-pace-line {
        font-size: clamp(1rem, 3.8vw, 1.15rem);
        font-weight: 800;
        text-align: center;
        margin: 0.25rem 0 0.5rem 0;
    }
    .income-goal-save-marker { display: none; }
    .income-goal-save-marker + div [data-testid="stButton"] > button {
        min-height: 3.85rem !important;
        font-size: 1.12rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #1a7f37, #2ea043) !important;
        box-shadow: 0 6px 24px rgba(46, 160, 67, 0.55) !important;
        border: 2px solid #3fb950 !important;
    }
    .income-goal-calc-marker { display: none; }
    .income-goal-calc-marker + div [data-testid="stButton"] > button {
        min-height: 3.85rem !important;
        font-size: 1.12rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #b45309, #f0b429) !important;
        color: #1a1208 !important;
        box-shadow: 0 6px 24px rgba(240, 180, 41, 0.45) !important;
        border: 2px solid #f0b429 !important;
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


def _github_fetch_vendors() -> tuple:
    """Return (vendors_dict, file_sha) from GitHub, or (None, None) if unavailable."""
    if not _github_enabled():
        return None, None
    url = (
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_VENDORS_PATH}"
        f"?ref={GITHUB_BRANCH}"
    )
    req = urllib.request.Request(url, headers=_github_headers())
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode())
        content = base64.b64decode(data["content"]).decode("utf-8")
        vendors = json.loads(content)
        if not isinstance(vendors, dict):
            return {}, data.get("sha")
        return vendors, data.get("sha")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {}, None
        return None, None
    except Exception:
        return None, None


def _github_push_vendors(vendors: dict, sha: str = None) -> bool:
    if not _github_enabled():
        return False
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_VENDORS_PATH}"
    payload = {
        "message": "ProbateGuardian CRM: update vendors_data.json",
        "content": base64.b64encode(json.dumps(vendors, indent=2).encode()).decode(),
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
        st.session_state["_vendors_github_sha"] = data.get("content", {}).get("sha")
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
        st.session_state["_notes_loaded_banner_pending"] = True
    return st.session_state.leads


def persist_leads() -> list:
    """Save session leads to leads_data.json atomically — no destructive reload."""
    save_leads(st.session_state.leads)
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
            DEDICATED_PHONE,
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


def _vendors_category_has_user_data(entry: dict) -> bool:
    if not isinstance(entry, dict):
        return False
    if (entry.get("area_notes") or "").strip():
        return True
    for i in range(1, VENDOR_SLOTS + 1):
        contact = _coerce_vendor_contact(entry.get(f"vendor_{i}", ""))
        name = (contact.get("name") or "").strip()
        phone = (contact.get("phone") or "").strip()
        notes = (contact.get("notes") or "").strip()
        if name and not (name.startswith("[") and name.endswith("]")):
            return True
        if phone and not (phone.startswith("[") and phone.endswith("]")):
            return True
        if notes:
            return True
    return False


def _merge_vendors_dict(remote: dict, local: dict) -> dict:
    remote_m = migrate_vendors(remote or {})
    local_m = migrate_vendors(local or {})
    merged = migrate_vendors(dict(DEFAULT_VENDORS))
    for category in VENDOR_CATEGORIES:
        local_entry = local_m.get(category, {})
        remote_entry = remote_m.get(category, {})
        if _vendors_category_has_user_data(local_entry):
            merged[category] = local_entry
        elif _vendors_category_has_user_data(remote_entry):
            merged[category] = remote_entry
        else:
            merged[category] = local_entry or remote_entry
    return merged


def _load_vendors_local() -> dict:
    if not VENDORS_FILE.exists():
        return {}
    try:
        with open(VENDORS_FILE, "r", encoding="utf-8") as f:
            vendors = json.load(f)
        if not isinstance(vendors, dict):
            return {}
        return migrate_vendors(vendors)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_vendors_local(vendors: dict) -> None:
    VENDORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VENDORS_FILE, "w", encoding="utf-8") as f:
        json.dump(vendors, f, indent=2)
        f.flush()
        os.fsync(f.fileno())


def load_vendors() -> dict:
    """Load vendors from vendors_data.json — GitHub repo when token configured, else local file."""
    local = _load_vendors_local()
    if not _github_enabled():
        return local if local else migrate_vendors(dict(DEFAULT_VENDORS))

    remote_raw, sha = _github_fetch_vendors()
    if remote_raw is None:
        return local if local else migrate_vendors(dict(DEFAULT_VENDORS))

    if sha:
        st.session_state["_vendors_github_sha"] = sha

    remote = migrate_vendors(remote_raw)
    if not local:
        _save_vendors_local(remote)
        return remote

    merged = _merge_vendors_dict(remote, local)
    if merged != local:
        _save_vendors_local(merged)
    return merged


def save_vendors(vendors: dict) -> None:
    """Write vendors to vendors_data.json immediately — local disk + GitHub when configured."""
    vendors = migrate_vendors(vendors or {})
    _save_vendors_local(vendors)

    if _github_enabled():
        sha = st.session_state.get("_vendors_github_sha")
        if not _github_push_vendors(vendors, sha):
            _, fresh_sha = _github_fetch_vendors()
            if fresh_sha:
                st.session_state["_vendors_github_sha"] = fresh_sha
            _github_push_vendors(vendors, st.session_state.get("_vendors_github_sha"))


def get_vendors() -> dict:
    """Return session vendors, loading from vendors_data.json on first access."""
    if "vendors" not in st.session_state:
        st.session_state.vendors = load_vendors()
    else:
        st.session_state.vendors = migrate_vendors(st.session_state.vendors)
    return st.session_state.vendors


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


NOTES_AUTOSAVE_DEBOUNCE_SEC = 3
NOTES_SAVED_FEEDBACK_SEC = 3
NOTES_TOAST_MESSAGE = "💾 Saved to disk"


def get_lead_notes_full_text(lead: dict) -> str:
    """Full notes text for the dashboard editor — respects saved empty notes."""
    if lead.get("notes_user_edited"):
        notes = lead.get("notes") or []
        parts = [(n.get("text") or "").strip() for n in notes if (n.get("text") or "").strip()]
        return "\n\n".join(parts)
    notes = lead.get("notes") or []
    if notes:
        parts = [(n.get("text") or "").strip() for n in notes if (n.get("text") or "").strip()]
        if parts:
            return "\n\n".join(parts)
    return (lead.get("raw") or "").strip()


def _notes_disk_snapshot_key(lead_id: str) -> str:
    return f"_notes_disk_snapshot_{lead_id}"


def _sync_notes_disk_snapshot(lead_id: str, text: str) -> None:
    st.session_state[_notes_disk_snapshot_key(lead_id)] = text or ""


def _get_notes_disk_snapshot(lead_id: str, lead: dict = None) -> str:
    key = _notes_disk_snapshot_key(lead_id)
    if key in st.session_state:
        return st.session_state[key]
    if lead is None:
        lead = _leads_lookup_by_id().get(lead_id)
    snapshot = get_lead_notes_full_text(lead) if lead else ""
    st.session_state[key] = snapshot
    return snapshot


def _show_notes_saved_feedback(lead_id: str) -> None:
    st.session_state["_notes_saved_lead_id"] = lead_id
    st.session_state["_notes_saved_at"] = time.time()
    st.toast(NOTES_TOAST_MESSAGE, icon="✅", duration=NOTES_SAVED_FEEDBACK_SEC)


def set_lead_notes_by_id(
    lead_id: str,
    text: str,
    author: str = None,
    *,
    show_saved: bool = False,
) -> bool:
    """Dict lookup by lead ID — atomically save full notes text to leads_data.json."""
    if not lead_id:
        return False
    target = _leads_lookup_by_id().get(lead_id)
    if not target:
        return False
    author = author or PARTNER_NAME
    cleaned = (text or "").strip()
    target["notes_user_edited"] = True
    if cleaned:
        target["notes"] = [{
            "ts": datetime.now().isoformat(),
            "text": cleaned,
            "by": author,
        }]
    else:
        target["notes"] = []
    save_leads(st.session_state.leads)
    _sync_notes_disk_snapshot(lead_id, cleaned)
    st.session_state.pop(f"_notes_dirty_since_{lead_id}", None)
    if show_saved:
        _show_notes_saved_feedback(lead_id)
    return True


def set_lead_notes_full_text(lead_id: str, text: str, author: str = None) -> None:
    set_lead_notes_by_id(lead_id, text, author)


def _notes_saved_visible(lead_id: str) -> bool:
    if st.session_state.get("_notes_saved_lead_id") != lead_id:
        return False
    saved_at = st.session_state.get("_notes_saved_at", 0)
    return (time.time() - saved_at) < NOTES_SAVED_FEEDBACK_SEC


def _on_dash_notes_saved(lead_id: str, widget_key: str) -> None:
    if lead_id:
        set_lead_notes_by_id(
            lead_id,
            st.session_state.get(widget_key, ""),
            show_saved=True,
        )


def _flush_dash_notes(lead_id: str, show_saved: bool = False) -> None:
    """Force-save the notes text area for a lead before switching or saving."""
    if not lead_id:
        return
    widget_key = f"dash_notes_{lead_id}"
    if widget_key not in st.session_state:
        return
    set_lead_notes_by_id(
        lead_id,
        st.session_state.get(widget_key, ""),
        show_saved=show_saved,
    )


def _flush_all_dash_notes_in_session(show_saved: bool = False) -> None:
    """Force-save every open notes editor in session state."""
    for key in list(st.session_state.keys()):
        if not key.startswith("dash_notes_"):
            continue
        lead_id = key[len("dash_notes_"):]
        if lead_id:
            _flush_dash_notes(lead_id, show_saved=show_saved)


def _flush_dash_notes_in_memory(lead_id: str) -> None:
    """Persist notes widget for one lead by ID before other in-place mutations."""
    if not lead_id:
        return
    widget_key = f"dash_notes_{lead_id}"
    if widget_key not in st.session_state:
        return
    set_lead_notes_by_id(lead_id, st.session_state.get(widget_key, ""))


def build_notes_export_csv(leads: list) -> bytes:
    """Backup CSV of all lead notes for instant download."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "lead_id",
        "decedent",
        "address",
        "county",
        "phone",
        "email",
        "contact_name",
        "contact_role",
        "pipeline_stage",
        "status",
        "notes_full_text",
        "notes_updated",
        "notes_by",
    ])
    for lead in leads:
        notes = lead.get("notes") or []
        writer.writerow([
            lead.get("id", ""),
            lead.get("decedent", ""),
            lead.get("address", ""),
            lead.get("county", ""),
            lead.get("phone", ""),
            lead.get("email", ""),
            lead.get("contact_name", ""),
            lead.get("contact_role", ""),
            lead.get("pipeline_stage", ""),
            lead.get("status", ""),
            get_lead_notes_full_text(lead),
            notes[0].get("ts", "") if notes else "",
            notes[0].get("by", "") if notes else "",
        ])
    return buf.getvalue().encode("utf-8")


@st.fragment(run_every=timedelta(seconds=1))
def _render_lead_notes_editor(lead: dict) -> None:
    """Auto-save notes 3 seconds after typing stops; polls widget value every second."""
    lead_id = lead["id"]
    notes_widget_key = f"dash_notes_{lead_id}"
    dirty_key = f"_notes_dirty_since_{lead_id}"

    if st.session_state.get("_dash_notes_sync_id") != lead_id:
        loaded = get_lead_notes_full_text(lead)
        st.session_state[notes_widget_key] = loaded
        _sync_notes_disk_snapshot(lead_id, loaded)
        st.session_state["_dash_notes_sync_id"] = lead_id
        st.session_state.pop(dirty_key, None)

    st.markdown("**Notes**")
    st.markdown('<div class="dash-notes-marker"></div>', unsafe_allow_html=True)
    st.text_area(
        "Full lead notes",
        height=220,
        key=notes_widget_key,
        label_visibility="collapsed",
        on_change=_on_dash_notes_saved,
        args=(lead_id, notes_widget_key),
    )

    current = st.session_state.get(notes_widget_key, "")
    disk = _get_notes_disk_snapshot(lead_id, lead)
    if current != disk:
        if dirty_key not in st.session_state:
            st.session_state[dirty_key] = time.time()
        elif time.time() - st.session_state[dirty_key] >= NOTES_AUTOSAVE_DEBOUNCE_SEC:
            set_lead_notes_by_id(lead_id, current, show_saved=True)
    else:
        st.session_state.pop(dirty_key, None)

    if _notes_saved_visible(lead_id):
        st.markdown(
            '<p class="notes-saved-caption">💾 Saved to disk</p>',
            unsafe_allow_html=True,
        )


def _format_poc_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return ""
    return re.sub(r"\b([A-Z])\b(?!\.)", r"\1.", name)


def _extract_human_name_from_text(text: str) -> str:
    text = (text or "").strip()
    if not text or re.search(r"estate of|deceased|notice to creditors", text, re.I):
        return ""
    m = re.search(
        r"(?:personal representative|petitioner|executor|primary contact|contact|primary)"
        r"[:\s]+([A-Z][^\n,;|]{2,70})",
        text,
        re.I,
    )
    if m:
        return m.group(1).strip()
    m = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][\.'-]?[a-z]+)+)\s*\(", text)
    if m:
        return m.group(1).strip()
    m = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][\.'-]?[a-z]+){1,4})$", text)
    if m:
        return m.group(1).strip()
    return ""


def _clean_poc_candidate(name: str) -> str:
    clean = (name or "").split("(")[0].split("|")[0].strip()
    clean = re.sub(r"\s*\+\s*.*$", "", clean).strip()
    if not clean or clean.lower() in ("contact tbd", "tbd", "unknown", "—", "family contact"):
        return ""
    if re.search(r"estate of|deceased|@\w", clean, re.I):
        return ""
    return _format_poc_name(clean)


def _lead_poc_name(lead: dict) -> str:
    candidates = []
    for key in ("contact_name", "name", "primary", "primary_contact"):
        val = (lead.get(key) or "").strip()
        if val:
            candidates.append(val)
    for key in ("summary", "note"):
        val = (lead.get(key) or "").strip()
        if val:
            for line in val.split("\n"):
                hit = _extract_human_name_from_text(line.strip())
                if hit:
                    candidates.append(hit)
                    break
    notes = lead.get("notes") or []
    if notes and isinstance(notes, list):
        first = notes[0]
        note_text = (first.get("text") if isinstance(first, dict) else str(first)) or ""
        for line in note_text.split("\n"):
            line = line.strip()
            if not line or re.fullmatch(r"[\d\(\)\-\+\s\.]+", line):
                continue
            hit = _extract_human_name_from_text(line)
            if hit:
                candidates.append(hit)
                break
    heirs = (lead.get("heirs") or "").strip()
    if heirs:
        m = re.match(r"^([^(]+)", heirs)
        if m:
            candidates.append(m.group(1).strip())
    for line in (lead.get("raw") or "").split("\n"):
        line = line.strip()
        if not line or re.search(r"^estate of\b", line, re.I):
            continue
        hit = _extract_human_name_from_text(line)
        if hit:
            candidates.append(hit)
            break
        m = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][\.'-]?[a-z]+)+)\s*\(", line)
        if m:
            candidates.append(m.group(1).strip())
            break
    for cand in candidates:
        cleaned = _clean_poc_candidate(cand)
        if cleaned:
            return cleaned
    return "Contact TBD"


def _lead_poc_role(lead: dict) -> str:
    role = (lead.get("contact_role") or "").strip()
    if not role:
        heirs = (lead.get("heirs") or "").strip()
        m = re.search(r"\(([^)]+)\)", heirs)
        if m:
            role = m.group(1).strip()
    if not role:
        return ""
    parts = re.split(r"[/,;&]+|\band\b", role, flags=re.I)
    return " / ".join(p.strip().title() for p in parts if p.strip())


def _format_poc_phone(phone: str) -> str:
    phone = (phone or "").strip()
    if not phone or phone in ("—", "TBD"):
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone


def _lead_poc_phone(lead: dict) -> str:
    phone = _format_poc_phone(lead.get("phone") or "")
    if phone:
        return phone
    for blob in (lead.get("raw") or "", lead.get("summary") or "", lead.get("note") or ""):
        m = re.search(r"\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}", blob)
        if m:
            return _format_poc_phone(m.group(0))
    notes = lead.get("notes") or []
    if notes and isinstance(notes, list):
        first = notes[0]
        note_text = (first.get("text") if isinstance(first, dict) else str(first)) or ""
        m = re.search(r"\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}", note_text)
        if m:
            return _format_poc_phone(m.group(0))
    return ""


def _lead_poc_email_display(lead: dict) -> str:
    email = (lead.get("email") or "").strip()
    if not email:
        for blob in (lead.get("raw") or "", lead.get("summary") or "", lead.get("note") or ""):
            m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", blob, re.I)
            if m:
                email = m.group(0)
                break
    return email


def _lead_poc_email(lead: dict) -> str:
    email = _lead_poc_email_display(lead)
    return email.upper() if email else ""


def _lead_poc_name_role(lead: dict) -> str:
    name = _lead_poc_name(lead)
    role = _lead_poc_role(lead)
    if role:
        return f"{name} ({role})"
    return name


def _lead_call_line(lead: dict) -> str:
    identity = _lead_poc_name_role(lead)
    phone = _lead_poc_phone(lead)
    if phone:
        return f"Call {identity} • {phone}"
    return f"Call {identity}"


def _lead_primary_contact_line(lead: dict) -> str:
    segments = [_lead_poc_name_role(lead)]
    phone = _lead_poc_phone(lead)
    if phone:
        segments.append(phone)
    email = _lead_poc_email(lead)
    if email:
        segments.append(email)
    return " • ".join(segments)


def _lead_primary_contact_line_md(lead: dict) -> str:
    """Markdown: **NAME** • phone • email for sidebar cards and detail header."""
    name = _lead_poc_name(lead)
    phone = _lead_poc_phone(lead)
    email = _lead_poc_email_display(lead)
    line = f"**{name}**"
    if phone:
        line += f" • {phone}"
    if email:
        line += f" • {email}"
    return line


def _render_lead_primary_contact(lead: dict, *, detail: bool = False) -> None:
    """Primary contact — largest bold text at top of list card or detail panel."""
    line = _lead_primary_contact_line_md(lead)
    if detail:
        st.markdown('<div class="crm-lead-primary-contact-md-marker"></div>', unsafe_allow_html=True)
        st.markdown(f"## {line}")
    else:
        st.markdown('<div class="crm-lead-contact-head-md-marker"></div>', unsafe_allow_html=True)
        st.markdown(f"### {line}")


def _lead_list_button_label(lead: dict) -> str:
    name = lead.get("decedent", "Unknown")
    addr = (lead.get("address") or "—")[:48]
    score = lead.get("score", 0)
    status = lead.get("status", "—")
    return f"{name}\n{addr}\n[{score}]  ·  {status}"


def _select_crm_lead(lead_id: str) -> None:
    prev = st.session_state.get("crm_selected_lead_id")
    if prev and prev != lead_id:
        _flush_dash_notes(prev, show_saved=True)
    st.session_state.crm_selected_lead_id = lead_id
    st.session_state.pop("_dash_notes_sync_id", None)


def _is_high_score_lead(lead: dict) -> bool:
    return int(lead.get("score") or 0) >= HIGH_SCORE_THRESHOLD


def _is_hot_lead(lead: dict) -> bool:
    stage = lead.get("pipeline_stage", "")
    if stage in ("🔥 Hot / New (call today)", "New/Hot", "New"):
        return True
    return effective_pipeline_stage(lead) == "New/Hot"


def _filter_leads_due_today(leads: list) -> list:
    """Today's follow-ups plus all Hot leads — Hot sorted first."""
    today = datetime.now().strftime("%Y-%m-%d")
    result = [
        l for l in leads
        if effective_pipeline_stage(l) != "Closed"
        and (l.get("follow_up_iso", "") == today or _is_hot_lead(l))
    ]
    result.sort(key=lambda x: (
        0 if _is_hot_lead(x) else 1,
        0 if x.get("follow_up_iso", "") == today else 1,
        -int(x.get("score") or 0),
        x.get("follow_up_iso", "9999-12-31"),
    ))
    return result


def _apply_crm_list_filters(leads: list) -> list:
    result = list(leads)
    if st.session_state.get("crm_list_mode") == "due_today":
        result = _filter_leads_due_today(result)
    return result


def _set_due_today_list_mode() -> None:
    st.session_state.crm_list_mode = "due_today"
    st.session_state.crm_pipe_filter = "All"


def _sync_top_pipe_filter_from_detail(detail_stage: str) -> None:
    """Keep top Pipeline dropdown (All / New/Hot / Warm / …) in sync with detail stage."""
    st.session_state.crm_pipe_filter = DETAIL_TO_ANALYTICS.get(detail_stage, "All")


def _on_detail_pipeline_change(lead_id: str) -> None:
    """Detail Pipeline Stage changed — save lead, sync top filter, refresh list."""
    stage = st.session_state.get(f"stage_{lead_id}")
    if not stage:
        return
    set_lead_pipeline_stage_by_id(lead_id, stage)
    _sync_top_pipe_filter_from_detail(stage)
    st.session_state.pop("_dash_notes_sync_id", None)


def _on_top_pipe_filter_change() -> None:
    """Pipeline dropdown changed — exit Do Today mode and filter via dropdown."""
    st.session_state.crm_list_mode = "all"


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


def _leads_lookup_by_id() -> dict:
    return {
        lead["id"]: lead
        for lead in st.session_state.get("leads", [])
        if lead.get("id")
    }


def set_lead_pipeline_stage_by_id(lead_id: str, pipeline_stage: str) -> bool:
    """Dict lookup by unique ID — mutate only pipeline_stage, never replace the list."""
    if not lead_id or not pipeline_stage:
        return False
    target = _leads_lookup_by_id().get(lead_id)
    if not target:
        return False
    target["pipeline_stage"] = pipeline_stage
    save_leads(st.session_state.leads)
    return True


def _quick_stage_callback(lead_id: str, stage: str) -> None:
    """Quick stage button: update pipeline_stage on exactly one lead by ID."""
    if not lead_id:
        return
    _flush_dash_notes_in_memory(lead_id)
    if not set_lead_pipeline_stage_by_id(lead_id, stage):
        return
    st.session_state.crm_selected_lead_id = lead_id
    st.session_state[f"stage_{lead_id}"] = stage
    _sync_top_pipe_filter_from_detail(stage)
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


# ── 90-Day Probate Crusher — vacant scoring & flexible bulk parse ─────────────
VACANT_DISTANCE_MILES = 50
CRUSHER_KPI_FILE = Path(__file__).resolve().parent / "crusher_kpi.json"
HOSPICE_REFERRALS_FILE = Path(__file__).resolve().parent / "hospice_referrals.json"
INCOME_GOAL_FILE = Path(__file__).resolve().parent / "income_goal.json"
INCOME_GOAL_DEFAULTS = {
    "target_homes": 2,
    "target_income": 20000,
    "dials_per_convo": 2.8,
    "close_rate": 25.0,
}
INCOME_GOAL_KIT_PER_CONVO = 0.55
INCOME_GOAL_APPT_PER_KIT = 0.40
CRUSHER_KPI_POINTS = {
    "pipeline_add": 10,
    "attorney_call": 25,
    "content": 20,
    "vacant_flag": 15,
}
CRUSHER_WEEKLY_POINT_GOAL = 200
CRUSHER_CASE_RE = re.compile(r"\b(PR\s*20\d{2}\s*[-–—]\s*\d+)\b", re.I)
CRUSHER_STREET_RE = re.compile(
    r"(\d+\s+[\w\s\.\#'-]+(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Ln|Lane|"
    r"Ct|Court|Way|Blvd|Pike|Circle|Cir|Place|Pl|Trl|Trail|Ter|Terrace|Hwy|Highway)\.?,?\s*"
    r"[\w\s,.'-]+(?:TN\s*\d{5}|\bNashville\b|\bTN\b|\d{5}))",
    re.I,
)
CRUSHER_ZIP_RE = re.compile(r"\b(\d{5})\b")
CRUSHER_OOS_RE = re.compile(
    r",\s*(AL|AR|AZ|CA|CO|FL|GA|IL|IN|KS|KY|LA|MI|MO|MS|NC|NY|OH|OK|PA|SC|TX|VA|WA|WI)\s*(\d{5})?",
    re.I,
)
CRUSHER_PR_LINE_RE = re.compile(
    r"^(.+?),\s*(?:Administratrix|Executrix|Administrator|Executor|Personal Representative|PR)\b",
    re.I | re.M,
)
CRUSHER_CASE_BULK_RE = re.compile(
    r"^(PR\s*20\d{2}\s*[-–—]\s*\d+|PR\d{4}-\d+|26P\d+|20\d{2}P\d+).*$",
    re.I,
)

TN_ZIP_AREA_CODES = {
    "370": ["615"],
    "371": ["615", "931"],
    "372": ["615", "629"],
    "373": ["423", "931"],
    "374": ["423"],
    "376": ["423"],
    "377": ["865", "423"],
    "378": ["865"],
    "379": ["865"],
    "380": ["901", "731"],
    "381": ["901"],
    "382": ["731"],
    "383": ["731"],
    "384": ["931", "615"],
    "385": ["931"],
}

STATE_AREA_CODES = {
    "AL": ["205", "251", "256"],
    "AR": ["501", "479"],
    "AZ": ["480", "602", "623"],
    "CA": ["213", "310", "415", "619"],
    "CO": ["303", "719", "720"],
    "FL": ["305", "407", "813", "904"],
    "GA": ["404", "470", "678", "912"],
    "IL": ["312", "773", "847"],
    "IN": ["317", "574", "812"],
    "KS": ["316", "785", "913"],
    "KY": ["502", "606", "859"],
    "LA": ["225", "318", "504"],
    "MI": ["313", "616", "734", "248"],
    "MO": ["314", "417", "573", "816"],
    "MS": ["601", "662", "228"],
    "NC": ["336", "704", "919", "828"],
    "NY": ["212", "315", "516", "718"],
    "OH": ["216", "330", "419", "513"],
    "OK": ["405", "539", "918"],
    "PA": ["215", "412", "484", "717"],
    "SC": ["803", "843", "864"],
    "TX": ["214", "281", "512", "713", "817"],
    "VA": ["276", "434", "540", "703", "804"],
    "WA": ["206", "253", "360", "425"],
    "WI": ["414", "608", "920"],
}

TN_ZIP_GEO = {
    "37013": (36.0606, -86.5736),
    "37027": (36.0012, -86.7936),
    "37064": (35.9251, -86.8689),
    "37066": (36.3884, -86.4467),
    "37067": (35.9806, -86.8128),
    "37072": (36.5298, -86.8844),
    "37075": (36.3206, -86.7133),
    "37087": (36.2081, -86.2911),
    "37115": (36.3134, -86.7133),
    "37122": (36.2006, -86.5186),
    "37127": (35.8234, -86.4103),
    "37129": (35.8456, -86.3903),
    "37130": (35.8460, -86.3920),
    "37167": (35.6170, -86.8936),
    "37174": (35.7853, -86.9169),
    "37201": (36.1627, -86.7816),
    "37203": (36.1500, -86.8025),
    "37205": (36.1028, -86.8722),
    "37206": (36.1810, -86.7350),
    "37207": (36.2176, -86.7784),
    "37209": (36.1536, -86.8570),
    "37211": (36.0750, -86.7240),
    "37214": (36.1450, -86.6600),
    "37215": (36.1020, -86.8200),
    "37217": (36.0830, -86.6400),
    "37221": (36.0750, -86.9500),
}


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def _is_plausible_address(value: str) -> bool:
    value = (value or "").strip()
    if not value or len(value) < 6:
        return False
    return bool(re.search(r"\d+\s+\w", value)) and bool(
        re.search(
            r"(Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Ln|Lane|Ct|Court|Way|Blvd|Pike|TN|\d{5})",
            value,
            re.I,
        )
    )


def _looks_like_case_number(value: str) -> bool:
    v = (value or "").strip()
    return bool(CRUSHER_CASE_BULK_RE.match(v)) or bool(re.search(r"PR20\d{2}|26P\d+", v, re.I))


def _looks_like_filing_date(value: str) -> bool:
    return bool(re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", (value or "").strip()))


def _bulk_line_parts(line: str) -> list:
    if "|" in line:
        return [p.strip() for p in line.split("|")]
    if "\t" in line:
        return [p.strip() for p in line.split("\t")]
    if "," in line and _is_plausible_address(line):
        return [p.strip() for p in line.split(",")]
    return [line.strip()]


def _split_poc_field(poc_field: str) -> tuple:
    poc = (poc_field or "").strip()
    if not poc:
        return "", ""
    m = re.search(r"\(([^)]+)\)\s*$", poc)
    if m:
        return poc[: m.start()].strip(), m.group(1).strip()
    m2 = CRUSHER_PR_LINE_RE.search(poc)
    if m2:
        return m2.group(1).strip(), "Personal Representative"
    return poc, "Personal Representative"


def _format_phone_digits(digits: str) -> str:
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return digits


def _extract_all_phones(text: str) -> list:
    """Return [(formatted, digits, position), ...] deduped."""
    seen: set = set()
    found = []
    for m in re.finditer(r"(?:\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}", text or ""):
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]
        if len(digits) != 10 or digits in seen:
            continue
        seen.add(digits)
        found.append((_format_phone_digits(digits), digits, m.start()))
    return found


def _extract_phone_email_from_text(text: str) -> tuple:
    blob = (text or "").strip()
    phones = _extract_all_phones(blob)
    phone = phones[0][0] if phones else ""
    em = re.search(r"[\w\.\-]+@[\w\.\-]+\.\w+", blob, re.I)
    email = em.group(0).strip() if em else ""
    return phone, email


def _extract_city_from_address(addr: str) -> str:
    if not addr:
        return ""
    m = re.search(r",\s*([^,]+)\s*,\s*TN\b", addr, re.I)
    if m:
        return m.group(1).strip()
    m2 = re.search(r",\s*([^,]+)\s*,\s*[A-Z]{2}\b", addr)
    if m2:
        return m2.group(1).strip()
    return ""


def _area_codes_for_address(addr: str) -> list:
    if not addr:
        return ["615", "629"]
    oos = CRUSHER_OOS_RE.search(addr)
    if oos and not re.search(r"\bTN\b", addr, re.I):
        return STATE_AREA_CODES.get(oos.group(1).upper(), ["—"])
    zips = CRUSHER_ZIP_RE.findall(addr)
    if zips:
        prefix = zips[-1][:3]
        return TN_ZIP_AREA_CODES.get(prefix, ["615", "629"])
    county_city = addr.lower()
    if any(k in county_city for k in ("nashville", "davidson", "franklin", "brentwood", "murfreesboro")):
        return ["615", "629"]
    if any(k in county_city for k in ("clarksville", "columbia", "cookeville")):
        return ["931"]
    return ["615", "931"]


def _clean_pr_token(name: str) -> str:
    name = re.sub(
        r"(?i)\b(estate of|administratrix|executrix|administrator|executor|"
        r"personal representative|pr|contact tbd)\b",
        "",
        name or "",
    )
    return name.strip(" ,()")


def enrich_lead_phones(parsed: dict) -> list:
    """Smart phone finder — extract from paste or infer area-code guesses from PR location."""
    raw = parsed.get("raw", "")
    pr_name = _clean_pr_token(parsed.get("contact_name") or parsed.get("heirs") or "")
    pr_tokens = [t for t in re.split(r"\s+", pr_name) if len(t) > 2]

    phones = _extract_all_phones(raw)
    if phones:
        if pr_tokens:
            anchor = raw.lower().find(pr_tokens[0].lower())
            if anchor < 0:
                anchor = 0
            phones.sort(key=lambda item: abs(item[2] - anchor))
        guesses = [p[0] for p in phones[:3]]
        if not parsed.get("phone"):
            parsed["phone"] = guesses[0]
        parsed["phone_guesses"] = guesses
        return guesses

    pr_addr = parsed.get("pr_address") or parsed.get("address", "")
    prop_addr = parsed.get("address", "")
    city = _extract_city_from_address(pr_addr) or _extract_city_from_address(prop_addr)
    county = (parsed.get("county") or "").replace(" County", "").strip()
    location = city or county or "Middle TN"
    codes = _area_codes_for_address(pr_addr or prop_addr)

    guesses = []
    for code in codes[:3]:
        if code != "—":
            guesses.append(f"{code}-???-???? · {location}")
    if pr_name:
        guesses.append(f"🔍 Search: {pr_name} {location} TN")
    if not guesses:
        guesses = ["615-???-???? · Middle TN"]
    parsed["phone_guesses"] = guesses
    return guesses


def _extract_all_addresses(text: str) -> list:
    found = []
    seen = set()
    for m in CRUSHER_STREET_RE.finditer(text or ""):
        addr = re.sub(r"\s+", " ", m.group(1).strip())
        key = addr.lower()
        if key not in seen:
            seen.add(key)
            found.append(addr)
    return found


def _guess_pr_address(raw: str, property_addr: str) -> str:
    text = raw or ""
    prop_key = (property_addr or "").lower().strip()
    for label in (
        r"mailing\s+address[:\s]+(.+)",
        r"address\s+of\s+(?:personal\s+representative|pr|petitioner)[:\s]+(.+)",
        r"pr\s+address[:\s]+(.+)",
        r"petitioner\s+address[:\s]+(.+)",
    ):
        m = re.search(label, text, re.I)
        if m:
            candidate = m.group(1).split("\n")[0].strip()
            if _is_plausible_address(candidate):
                return candidate

    addresses = _extract_all_addresses(text)
    for addr in addresses:
        if addr.lower().strip() != prop_key:
            return addr

    for line in text.splitlines():
        line = line.strip()
        if _is_plausible_address(line) and line.lower().strip() != prop_key:
            return line
    return ""


def _coords_for_address(addr: str):
    if not addr:
        return None
    if CRUSHER_OOS_RE.search(addr) and not re.search(r"\bTN\b", addr, re.I):
        return "OOS"
    zips = CRUSHER_ZIP_RE.findall(addr)
    for z in reversed(zips):
        if z in TN_ZIP_GEO:
            return TN_ZIP_GEO[z]
    return None


def _address_distance_miles(addr1: str, addr2: str):
    if not addr1 or not addr2:
        return None
    a1 = addr1.strip()
    a2 = addr2.strip()
    if not a1 or not a2 or a1.lower() == a2.lower():
        return 0.0
    if CRUSHER_OOS_RE.search(a2) and not re.search(r"\bTN\b", a2, re.I):
        return 750.0
    if CRUSHER_OOS_RE.search(a1) and not re.search(r"\bTN\b", a1, re.I):
        return 750.0
    c1 = _coords_for_address(a1)
    c2 = _coords_for_address(a2)
    if c1 == "OOS" or c2 == "OOS":
        return 600.0
    if c1 and c2:
        return round(_haversine_miles(c1[0], c1[1], c2[0], c2[1]), 1)
    return None


def _split_estate_chunks(text: str) -> list:
    text = (text or "").strip()
    if not text:
        return []
    if re.search(r"^Estate of ", text, re.I | re.M):
        parts = re.split(r"(?=^Estate of )", text, flags=re.I | re.M)
        return [p.strip() for p in parts if p.strip()]
    if re.search(r"PR\s*20\d{2}", text, re.I):
        parts = re.split(r"(?=\bPR\s*20\d{2}\s*[-–—]\s*\d+\b)", text, flags=re.I)
        chunks = [p.strip() for p in parts if p.strip()]
        if len(chunks) > 1:
            return chunks
    triple = re.split(r"\n\s*\n\s*\n+", text)
    if len(triple) > 1:
        return [p.strip() for p in triple if p.strip()]
    double = re.split(r"\n\s*\n", text)
    if len(double) > 1:
        return [p.strip() for p in double if p.strip()]
    return [text]


def _parse_delimited_bulk_row(parts: list) -> dict:
    parts = [p.strip() for p in parts if p and str(p).strip()]
    if len(parts) < 2:
        return {}
    decedent = parts[0].strip()
    if decedent.lower().startswith("estate of"):
        decedent = decedent[9:].strip()
    if not decedent:
        return {}

    addr_idx = next((i for i, p in enumerate(parts) if _is_plausible_address(p)), None)
    if addr_idx is None:
        return {}

    address = parts[addr_idx]
    case_no = filing = poc = ""
    notes_parts = []
    for i, part in enumerate(parts):
        if i in (0, addr_idx):
            continue
        if _looks_like_case_number(part) and not case_no:
            case_no = part
        elif _looks_like_filing_date(part) and not filing:
            filing = part
        elif not poc:
            poc = part
        else:
            notes_parts.append(part)

    notes = "\n\n".join(notes_parts)
    phone, email = _extract_phone_email_from_text(f"{poc}\n{notes}")
    contact_name, contact_role = _split_poc_field(poc)
    heirs = f"{contact_name} ({contact_role})" if contact_role else contact_name
    return {
        "decedent": decedent,
        "address": address,
        "county": "Middle TN",
        "heirs": heirs or poc,
        "contact_name": contact_name or poc,
        "contact_role": contact_role,
        "phone": phone,
        "email": email,
        "case_number": case_no,
        "filing_date": filing,
        "raw": " | ".join(parts),
    }


def _parse_multiline_bulk_block(lines: list) -> dict:
    lines = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
    if len(lines) < 2:
        return {}
    decedent = lines[0]
    if decedent.lower().startswith("estate of"):
        decedent = decedent[9:].strip()

    case_no = filing = poc = address = ""
    notes_lines = []
    after_address = False
    for line in lines[1:]:
        if re.match(r"^NOTES:\s*", line, re.I):
            after_address = True
            tail = re.sub(r"^NOTES:\s*", "", line, flags=re.I).strip()
            if tail:
                notes_lines.append(tail)
            continue
        if after_address:
            notes_lines.append(line)
            continue
        if _looks_like_case_number(line) and not case_no:
            case_no = line
        elif _looks_like_filing_date(line) and not filing:
            filing = line
        elif _is_plausible_address(line) and not address:
            address = line
            after_address = True
        elif not poc and not _is_plausible_address(line):
            poc = line
        else:
            notes_lines.append(line)

    if not decedent or not address:
        return {}

    notes = "\n\n".join(notes_lines)
    phone, email = _extract_phone_email_from_text(f"{poc}\n{notes}\n" + "\n".join(lines))
    contact_name, contact_role = _split_poc_field(poc)
    heirs = f"{contact_name} ({contact_role})" if contact_role else (contact_name or poc)
    county_m = re.search(
        r"(Wilson|Davidson|Rutherford|Williamson|Sumner|Robertson|Cheatham|Dickson|Montgomery|Maury)\s+County",
        "\n".join(lines),
        re.I,
    )
    return {
        "decedent": decedent,
        "address": address,
        "county": county_m.group(0) if county_m else "Middle TN",
        "heirs": heirs,
        "contact_name": contact_name or poc,
        "contact_role": contact_role,
        "phone": phone,
        "email": email,
        "case_number": case_no,
        "filing_date": filing,
        "raw": "\n".join(lines),
    }


def parse_lead_enhanced(raw: str) -> dict:
    """Flexible parse — court PDF text, pipe/tab rows, or classic blocks."""
    text = (raw or "").strip()
    if not text:
        return parse_lead("")

    rows = []
    seen = set()

    def _add(parsed: dict) -> None:
        if not parsed or not parsed.get("decedent") or not parsed.get("address"):
            return
        key = (parsed["decedent"].lower(), parsed["address"].lower())
        if key in seen:
            return
        seen.add(key)
        rows.append(parsed)

    for block in _split_estate_chunks(text):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        has_delimited = any("|" in ln or "\t" in ln for ln in lines)
        if not has_delimited and len(lines) >= 2:
            _add(_parse_multiline_bulk_block(lines))
            continue
        for line in lines:
            parts = _bulk_line_parts(line)
            if len(parts) >= 2:
                _add(_parse_delimited_bulk_row(parts))

    if len(rows) == 1:
        parsed = rows[0]
    elif len(rows) > 1:
        parsed = rows[0]
    else:
        parsed = dict(parse_lead(text))

    if not parsed.get("case_number"):
        cm = CRUSHER_CASE_RE.search(text)
        if cm:
            parsed["case_number"] = re.sub(r"\s+", "", cm.group(1).upper())

    if not parsed.get("phone") or not parsed.get("email"):
        bp, be = _extract_phone_email_from_text(text)
        parsed["phone"] = parsed.get("phone") or bp
        parsed["email"] = parsed.get("email") or be

    if not parsed.get("contact_name"):
        m = CRUSHER_PR_LINE_RE.search(text)
        if m:
            parsed["contact_name"] = m.group(1).strip()
            parsed["contact_role"] = "Personal Representative"
            if not parsed.get("heirs"):
                parsed["heirs"] = f"{parsed['contact_name']} (Personal Representative)"

    parsed["pr_address"] = _guess_pr_address(text, parsed.get("address", ""))
    parsed["raw"] = text
    return parsed


def split_batch_text(text: str) -> list:
    """Split a large paste into individual lead blocks."""
    text = (text or "").strip()
    if not text:
        return []

    chunks = _split_estate_chunks(text)
    blocks = []
    for chunk in chunks:
        lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]
        if not lines:
            continue
        if any("|" in ln or "\t" in ln for ln in lines):
            for line in lines:
                parts = _bulk_line_parts(line)
                if len(parts) >= 2:
                    row = _parse_delimited_bulk_row(parts)
                    if row:
                        row["raw"] = line
                        blocks.append(row.get("raw", line))
            continue
        blocks.append(chunk)
    return blocks if blocks else [text]


def score_vacant_lead(parsed: dict) -> dict:
    property_addr = parsed.get("address", "")
    pr_addr = parsed.get("pr_address") or _guess_pr_address(parsed.get("raw", ""), property_addr)
    parsed["pr_address"] = pr_addr
    pr_name = parsed.get("contact_name") or parsed.get("heirs") or "—"
    phone_guesses = enrich_lead_phones(parsed)

    distance = _address_distance_miles(property_addr, pr_addr) if pr_addr else None
    base_score, qual_status, flags = score_lead(parsed)
    if phone_guesses and parsed.get("phone"):
        flags.append("✓ Phone enriched")

    vacant = bool(distance is not None and distance > VACANT_DISTANCE_MILES)
    if vacant:
        base_score = max(base_score, 92)
        flags.append("🔥 Likely Vacant • High Motivation")

    if vacant:
        action = "🔥 CALL FIRST"
    elif base_score >= 65:
        action = "✅ Queue"
    elif base_score >= 40:
        action = "Review"
    else:
        action = "Skip"

    sort_score = base_score + (100 if vacant else 0)
    dist_display = f"{distance:.0f} mi" if distance is not None else "—"

    vacant_label = "🔥 Likely Vacant • High Motivation" if vacant else "—"
    phone_display = " · ".join(phone_guesses[:3]) if phone_guesses else "—"

    return {
        "parsed": parsed,
        "name": parsed.get("decedent", "Unknown"),
        "property": property_addr,
        "pr": pr_name,
        "pr_address": pr_addr or "—",
        "phone_guesses": phone_guesses,
        "phone_display": phone_display,
        "distance": dist_display,
        "distance_miles": distance,
        "score": base_score,
        "sort_score": sort_score,
        "qual_status": qual_status,
        "vacant_likely": vacant,
        "vacant_label": vacant_label,
        "action": action,
        "flags": flags,
    }


def crusher_score_batch(text: str) -> list:
    blocks = split_batch_text(text)
    scored = []
    for block in blocks:
        parsed = parse_lead_enhanced(block)
        if parsed.get("address") == "Address TBD" and parsed.get("decedent") == "Unknown Decedent":
            continue
        scored.append(score_vacant_lead(parsed))
    scored.sort(key=lambda x: (-x["sort_score"], -(x.get("distance_miles") or 0)))
    return scored


def _crusher_week_start_iso() -> str:
    now = datetime.now()
    week_start = now - timedelta(days=now.weekday())
    return week_start.strftime("%Y-%m-%d")


def _crusher_week_label() -> str:
    start = datetime.strptime(_crusher_week_start_iso(), "%Y-%m-%d")
    end = start + timedelta(days=6)
    return f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"


def load_crusher_kpi() -> dict:
    default = {
        "week_iso": _crusher_week_start_iso(),
        "attorney_calls": 0,
        "content": 0,
        "vacant_flagged": 0,
    }
    if not CRUSHER_KPI_FILE.exists():
        return default
    try:
        data = json.loads(CRUSHER_KPI_FILE.read_text(encoding="utf-8"))
        if data.get("week_iso") != _crusher_week_start_iso():
            return default
        return {**default, **data}
    except (json.JSONDecodeError, OSError):
        return default


def save_crusher_kpi(data: dict) -> None:
    data["week_iso"] = _crusher_week_start_iso()
    tmp = CRUSHER_KPI_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(CRUSHER_KPI_FILE)
    except OSError:
        pass


def load_income_goal() -> dict:
    data = dict(INCOME_GOAL_DEFAULTS)
    if not INCOME_GOAL_FILE.exists():
        return data
    try:
        saved = json.loads(INCOME_GOAL_FILE.read_text(encoding="utf-8"))
        if isinstance(saved, dict):
            data.update({k: saved[k] for k in INCOME_GOAL_DEFAULTS if k in saved})
    except (json.JSONDecodeError, OSError):
        pass
    return data


def save_income_goal(data: dict) -> None:
    payload = {k: data.get(k, INCOME_GOAL_DEFAULTS[k]) for k in INCOME_GOAL_DEFAULTS}
    payload["updated"] = datetime.now().isoformat()
    tmp = INCOME_GOAL_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(INCOME_GOAL_FILE)
    except OSError:
        pass


def _income_goal_closes_this_month(leads: list) -> int:
    ym = datetime.now().strftime("%Y-%m")
    count = 0
    for lead in leads:
        if lead.get("pipeline_stage") != "Closed / Sold":
            continue
        closed_month = (lead.get("created") or "")[:7]
        for act in lead.get("activity") or []:
            text = act.get("text") or act.get("detail") or ""
            if "Closed" in text or act.get("stage") == "Closed / Sold":
                closed_month = (act.get("ts") or "")[:7]
                break
        if closed_month == ym:
            count += 1
    return count


def _income_goal_week_activity(leads: list) -> dict:
    week_start = _crusher_week_start_iso()
    dials = kits = appts = 0
    for lead in leads:
        created = (lead.get("created") or "")[:10]
        if created >= week_start:
            if lead.get("source") in ("guardian_kit",):
                kits += 1
            if lead.get("pipeline_stage") == "Appointment Set":
                appts += 1
        for act in lead.get("activity") or []:
            ts = (act.get("ts") or "")[:10]
            if ts < week_start:
                continue
            if act.get("type") == "call":
                dials += 1
            detail = (act.get("detail") or act.get("text") or "").lower()
            if "guardian kit" in detail:
                kits += 1
            if "appointment" in detail or "appt set" in detail:
                appts += 1
    return {"dials": dials, "kits": kits, "appts": appts}


def compute_income_goal_metrics(
    target_homes: float,
    target_income: float,
    dials_per_convo: float,
    close_rate: float,
    leads: list | None = None,
) -> dict:
    homes = max(float(target_homes or 0), 0)
    income = max(float(target_income or 0), 0)
    dpc = max(float(dials_per_convo or 0.1), 0.1)
    cr = max(float(close_rate or 1), 1) / 100.0
    income_per_home = income / homes if homes > 0 else 0.0

    # Funnel math — work backwards from monthly home closes to weekly activity
    weekly_closes = homes / 4.0
    weekly_appts = weekly_closes / cr if cr else 0.0
    weekly_kits = weekly_appts / INCOME_GOAL_APPT_PER_KIT
    weekly_convos = weekly_kits / INCOME_GOAL_KIT_PER_CONVO
    weekly_dials = weekly_convos * dpc

    # Plan income always equals the target $ he sets (when he hits weekly goals)
    plan_monthly_income = round(income)

    leads = leads or []
    closed_month = _income_goal_closes_this_month(leads)
    earned_so_far = closed_month * income_per_home
    activity = _income_goal_week_activity(leads)
    actual_dials = activity["dials"]
    actual_convos = actual_dials / dpc if dpc else float(actual_dials)
    actual_kits = activity["kits"]
    actual_appts = activity["appts"]

    now = datetime.now()
    if now.month == 12:
        month_end = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
    days_in_month = month_end.day
    day_of_month = now.day
    month_progress = day_of_month / days_in_month
    weeks_remaining = max((days_in_month - day_of_month) / 7.0, 0.0)
    week_progress = (now.weekday() + 1) / 7.0

    expected_closes_by_now = homes * month_progress
    projected_closes = closed_month + weekly_closes * weeks_remaining
    projected_closes = min(projected_closes, homes) if homes else 0.0
    projected_raw = projected_closes * income_per_home

    on_pace_month = (
        homes > 0
        and (
            closed_month >= expected_closes_by_now * 0.9
            or earned_so_far >= income * month_progress * 0.9
            or projected_raw >= income * 0.92
        )
    )
    if on_pace_month or closed_month >= homes:
        projected_monthly_income = plan_monthly_income
        pace_line = f"You're on pace for ${income:,.0f} 🔥"
        status = "green"
    else:
        projected_monthly_income = round(min(projected_raw, income))
        pace_line = (
            f"You're on pace for ${projected_monthly_income:,.0f} — "
            f"hit weekly goals for ${income:,.0f} 🔥"
        )
        if projected_monthly_income >= income * 0.65:
            status = "yellow"
        else:
            status = "red"

    def _metric_pace(actual: float, target: float) -> tuple:
        if target <= 0:
            return 0, True
        pct = min(100, int((actual / target) * 100))
        on_pace = actual >= target * week_progress * 0.85
        return pct, on_pace

    dials_pct, dials_on_pace = _metric_pace(actual_dials, weekly_dials)
    convos_pct, convos_on_pace = _metric_pace(actual_convos, weekly_convos)
    kits_pct, kits_on_pace = _metric_pace(actual_kits, weekly_kits)
    appts_pct, appts_on_pace = _metric_pace(actual_appts, weekly_appts)

    return {
        "weekly_dials": round(weekly_dials, 1),
        "weekly_conversations": round(weekly_convos, 1),
        "weekly_kits": round(weekly_kits, 1),
        "weekly_appointments": round(weekly_appts, 1),
        "income_per_home": round(income_per_home),
        "plan_monthly_income": plan_monthly_income,
        "target_monthly_income": plan_monthly_income,
        "projected_monthly_income": projected_monthly_income,
        "earned_so_far": round(earned_so_far),
        "closed_this_month": closed_month,
        "status": status,
        "pace_line": pace_line,
        "on_pace_month": on_pace_month,
        "actual_dials": actual_dials,
        "actual_convos": round(actual_convos, 1),
        "actual_kits": actual_kits,
        "actual_appts": actual_appts,
        "dials_pct": dials_pct,
        "convos_pct": convos_pct,
        "kits_pct": kits_pct,
        "appts_pct": appts_pct,
        "dials_on_pace": dials_on_pace,
        "convos_on_pace": convos_on_pace,
        "kits_on_pace": kits_on_pace,
        "appts_on_pace": appts_on_pace,
    }


def _income_goal_metric_card(
    label: str,
    target: float,
    actual: float,
    pct: int,
    on_pace: bool,
) -> str:
    fire = "🔥" if on_pace else "📞"
    bar_cls = "ig-bar-green" if on_pace else "ig-bar-amber"
    card_cls = "income-goal-metric-card ig-on-pace" if on_pace else "income-goal-metric-card"
    return (
        f'<div class="{card_cls}">'
        f'<p class="income-goal-metric-label">{html.escape(label)} {fire}</p>'
        f'<p class="income-goal-big-num">{target:.0f}</p>'
        f'<div class="income-goal-bar-track">'
        f'<div class="income-goal-bar-fill {bar_cls}" style="width:{pct}%"></div></div>'
        f'<p class="income-goal-bar-caption">{actual:.0f} this week · goal {target:.0f}</p>'
        f"</div>"
    )


def render_income_goal_crusher(leads: list) -> None:
    st.markdown(
        '<div class="income-goal-card">'
        '<p class="income-goal-title">🎯 Income Goal Crusher</p>'
        f'<p style="color:#8b949e;margin:0;font-size:0.88rem;">'
        f'{PARTNER_NAME} — change targets below · numbers update instantly.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    ig_saved = load_income_goal()
    ig1, ig2 = st.columns(2)
    with ig1:
        ig_homes = st.number_input(
            "Target Homes per Month",
            min_value=0,
            max_value=50,
            value=int(ig_saved.get("target_homes", 2)),
            step=1,
            key="income_goal_homes",
        )
    with ig2:
        ig_income = st.number_input(
            "Target Monthly Income $",
            min_value=0,
            max_value=500000,
            value=int(ig_saved.get("target_income", 20000)),
            step=500,
            key="income_goal_income",
        )
    ig_sl1, ig_sl2 = st.columns(2)
    with ig_sl1:
        ig_dials_ratio = st.slider(
            "Conversion Ratio (dials per conversation)",
            min_value=1.0,
            max_value=8.0,
            value=float(ig_saved.get("dials_per_convo", 2.8)),
            step=0.1,
            key="income_goal_dials_ratio",
        )
    with ig_sl2:
        ig_close_rate = st.slider(
            "Close Rate (% of appointments → closed home)",
            min_value=5.0,
            max_value=80.0,
            value=float(ig_saved.get("close_rate", 25.0)),
            step=1.0,
            key="income_goal_close_rate",
        )

    igm = compute_income_goal_metrics(
        ig_homes, ig_income, ig_dials_ratio, ig_close_rate, leads,
    )

    ig_btn1, ig_btn2 = st.columns(2)
    with ig_btn1:
        st.markdown('<div class="income-goal-calc-marker"></div>', unsafe_allow_html=True)
        ig_calc = st.button(
            "⚡ Auto-Calculate",
            use_container_width=True,
            type="primary",
            key="income_goal_calculate",
        )
    with ig_btn2:
        st.markdown('<div class="income-goal-save-marker"></div>', unsafe_allow_html=True)
        ig_save = st.button(
            "💾 SAVE My Targets",
            use_container_width=True,
            type="primary",
            key="income_goal_save",
        )
    if ig_save:
        save_income_goal({
            "target_homes": ig_homes,
            "target_income": ig_income,
            "dials_per_convo": ig_dials_ratio,
            "close_rate": ig_close_rate,
        })
        st.success("✅ Targets saved permanently.")
    if ig_calc:
        st.toast("⚡ Weekly targets recalculated!", icon="🔥")

    metrics_html = (
        '<div class="income-goal-metrics-grid">'
        + _income_goal_metric_card(
            "Weekly Dials", igm["weekly_dials"], igm["actual_dials"],
            igm["dials_pct"], igm["dials_on_pace"],
        )
        + _income_goal_metric_card(
            "Conversations", igm["weekly_conversations"], igm["actual_convos"],
            igm["convos_pct"], igm["convos_on_pace"],
        )
        + _income_goal_metric_card(
            "Guardian Kits", igm["weekly_kits"], igm["actual_kits"],
            igm["kits_pct"], igm["kits_on_pace"],
        )
        + _income_goal_metric_card(
            "Appointments", igm["weekly_appointments"], igm["actual_appts"],
            igm["appts_pct"], igm["appts_on_pace"],
        )
        + "</div>"
    )
    st.markdown(metrics_html, unsafe_allow_html=True)

    status_class = {
        "green": "income-goal-status-green",
        "yellow": "income-goal-status-yellow",
        "red": "income-goal-status-red",
    }.get(igm["status"], "income-goal-status-red")
    st.markdown(
        f'<p style="margin:0.35rem 0 0;font-size:0.85rem;color:#8b949e;text-align:center;">'
        f'Closed: <strong>{igm["closed_this_month"]}</strong> / {ig_homes} homes · '
        f'Earned: <strong>${igm["earned_so_far"]:,}</strong> · '
        f'Per home: <strong>${igm["income_per_home"]:,}</strong></p>'
        f'<p class="income-goal-projected {status_class}">'
        f'Projected Monthly Income: ${igm["projected_monthly_income"]:,}</p>'
        f'<p class="income-goal-pace-line {status_class}">{html.escape(igm["pace_line"])}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="income-goal-motivate">'
        f'Hit these numbers = ${ig_income:,.0f} extra while leads call {DEDICATED_PHONE} 🔥'
        f'</div>',
        unsafe_allow_html=True,
    )


def _count_pipeline_adds_this_week(leads: list) -> int:
    week_start = _crusher_week_start_iso()
    count = 0
    for lead in leads:
        created = (lead.get("created") or "")[:10]
        if created >= week_start:
            count += 1
    return count


def _count_attorney_touchpoints_this_week(leads: list) -> int:
    week_start = _crusher_week_start_iso()
    count = 0
    for lead in leads:
        for note in lead.get("notes") or []:
            if not isinstance(note, dict):
                continue
            ts = (note.get("ts") or "")[:10]
            text = note.get("text") or ""
            if ts >= week_start and re.search(
                r"\battorney\b|\besq\.?\b|law\s+firm|legal\s+counsel",
                text,
                re.I,
            ):
                count += 1
        for act in lead.get("activity") or []:
            ts = (act.get("ts") or "")[:10]
            detail = act.get("detail") or ""
            if ts >= week_start and re.search(r"attorney|esq", detail, re.I):
                count += 1
    return count


def record_crusher_vacant_flags(vacant_count: int) -> None:
    if vacant_count <= 0:
        return
    kpi = load_crusher_kpi()
    kpi["vacant_flagged"] = int(kpi.get("vacant_flagged", 0)) + vacant_count
    save_crusher_kpi(kpi)


def compute_crusher_kpi_scorecard(leads: list) -> dict:
    kpi = load_crusher_kpi()
    pipeline_adds = _count_pipeline_adds_this_week(leads)
    manual_attorney = int(kpi.get("attorney_calls", 0))
    auto_attorney = _count_attorney_touchpoints_this_week(leads)
    attorney_calls = max(manual_attorney, auto_attorney)
    content = int(kpi.get("content", 0))
    vacant_flagged = int(kpi.get("vacant_flagged", 0))

    weekly_points = (
        pipeline_adds * CRUSHER_KPI_POINTS["pipeline_add"]
        + attorney_calls * CRUSHER_KPI_POINTS["attorney_call"]
        + content * CRUSHER_KPI_POINTS["content"]
        + vacant_flagged * CRUSHER_KPI_POINTS["vacant_flag"]
    )

    return {
        "week_label": _crusher_week_label(),
        "weekly_points": weekly_points,
        "weekly_goal": CRUSHER_WEEKLY_POINT_GOAL,
        "attorney_calls": attorney_calls,
        "content": content,
        "pipeline_adds": pipeline_adds,
        "vacant_flagged": vacant_flagged,
        "point_breakdown": {
            "pipeline": pipeline_adds * CRUSHER_KPI_POINTS["pipeline_add"],
            "attorney": attorney_calls * CRUSHER_KPI_POINTS["attorney_call"],
            "content": content * CRUSHER_KPI_POINTS["content"],
            "vacant": vacant_flagged * CRUSHER_KPI_POINTS["vacant_flag"],
        },
    }


def crusher_push_to_call_queue(scored_rows: list) -> int:
    """Insert qualified / vacant leads at top of CRM — hottest first for Branton."""
    eligible = [
        row for row in scored_rows
        if row.get("vacant_likely") or row.get("qual_status") == "Qualified" or row.get("score", 0) >= 65
    ]
    if not eligible:
        return 0

    eligible.sort(key=lambda x: (-x["sort_score"], -(x.get("distance_miles") or 0)))
    added = 0
    for row in reversed(eligible):
        parsed = dict(row["parsed"])
        parsed["distance_miles"] = row.get("distance_miles")
        parsed["vacant_likely"] = row.get("vacant_likely", False)
        heat_status, heat_pipeline = heat_from_import_block(parsed.get("raw", ""))
        if row.get("vacant_likely"):
            heat_pipeline = "🔥 Hot / New (call today)"
            heat_status = "New/Hot"
        score = row.get("score", 0)
        flags_txt = " · ".join(row.get("flags") or [])
        phone_txt = row.get("phone_display") or "—"
        notes = initial_notes_from_block(
            f"{parsed.get('raw', '')}\n\nPhone guesses: {phone_txt}\n{flags_txt}".strip(),
            source="90-Day Crusher",
        )
        st.session_state.leads.insert(
            0,
            build_lead(
                parsed,
                pipeline_stage=heat_pipeline,
                status=heat_status,
                score=score,
                source="bulk",
                assigned_to_branton=True,
                follow_up_days=0,
                notes=notes,
            ),
        )
        added += 1
    persist_leads()
    return added


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
    for opt in (
        "case_number", "contact_name", "contact_role", "pr_address",
        "distance_miles", "vacant_likely", "filing_date",
    ):
        if parsed.get(opt) not in (None, "", False):
            lead[opt] = parsed[opt]
    return normalize_lead(lead)


def find_lead(lead_id: str):
    for lead in st.session_state.leads:
        if lead.get("id") == lead_id:
            return lead
    return None


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


def _is_crusher_queue_lead(lead: dict) -> bool:
    if lead.get("source") == "bulk":
        return True
    if lead.get("vacant_likely"):
        return True
    for note in lead.get("notes") or []:
        if isinstance(note, dict) and (note.get("by") or "") == "90-Day Crusher":
            return True
    return False


def get_branton_call_mode_leads(leads: list, limit: int = 10) -> list:
    """Top hottest Crusher-queue leads — 🔥 vacant first."""
    pool = [
        l for l in leads
        if l.get("pipeline_stage") not in CLOSED_DETAIL_STAGES
        and effective_pipeline_stage(l) != "Closed"
        and (_is_crusher_queue_lead(l) or l.get("assigned_to_branton"))
    ]
    if not pool:
        pool = [
            l for l in leads
            if l.get("pipeline_stage") not in CLOSED_DETAIL_STAGES
            and effective_pipeline_stage(l) != "Closed"
        ]

    pool.sort(
        key=lambda x: (
            0 if x.get("vacant_likely") else 1,
            0 if _is_hot_lead(x) else 1,
            -int(x.get("score") or 0),
            0 if x.get("assigned_to_branton") else 1,
            x.get("follow_up_iso", "9999-12-31"),
        )
    )
    return pool[:limit]


def lead_to_parsed_dict(lead: dict) -> dict:
    return {
        "decedent": lead.get("decedent", "Unknown Decedent"),
        "address": lead.get("address", "Address TBD"),
        "county": lead.get("county", "Middle TN"),
        "heirs": lead.get("heirs") or lead.get("contact_name") or "[Heir Name]",
        "phone": lead.get("phone", ""),
        "email": lead.get("email", ""),
    }


def generate_roadmap_message(lead: dict) -> str:
    parsed = lead_to_parsed_dict(lead)
    heir = (parsed["heirs"] or "[Heir Name]").split("(")[0].strip()
    return f"""Hi {heir},

Branton Walker here with Probate Guardians TN — on Scott Hardesty's team helping Middle Tennessee families with inherited property.

Your free Probate Family Roadmap is ready: plain-English next steps, Muniment basics, and real options (fast cash, funded repairs, or list for maximum value).

Property: {parsed['address']}
County: {parsed['county']}

No pressure, ever. Reply YES and we'll send it — or {DEDICATED_PHONE_LINE.lower()} anytime.

— Branton Walker
Probate Guardians TN · Serving all of Middle Tennessee"""


def _enter_branton_call_mode() -> None:
    st.session_state.branton_call_mode = True


def _exit_branton_call_mode() -> None:
    st.session_state.branton_call_mode = False
    st.session_state.pop("call_mode_panel", None)


def _call_mode_show_script(lead_id: str) -> None:
    st.session_state.call_mode_panel = {"lead_id": lead_id, "type": "script"}


def _call_mode_show_roadmap(lead_id: str) -> None:
    st.session_state.call_mode_panel = {"lead_id": lead_id, "type": "roadmap"}


def _call_mode_mark_contacted(lead_id: str) -> None:
    log_call(lead_id)
    update_lead(lead_id, pipeline_stage="Warm / Talking", status="Contacted")
    add_note(lead_id, "Call Mode: Marked Contacted", author=PARTNER_NAME)


def _call_mode_set_stage(lead_id: str, stage: str, status: str, label: str) -> None:
    update_lead(lead_id, pipeline_stage=stage, status=status)
    add_note(lead_id, f"Call Mode: {label}", author=PARTNER_NAME)


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
  ProbateGuardian TN · Mount Juliet, Tennessee
  📞 {DEDICATED_PHONE_LINE}
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
📞 {DEDICATED_PHONE_LINE}
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
📞 {DEDICATED_PHONE_LINE}
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
📞 {DEDICATED_PHONE_LINE} · Mount Juliet, TN"""

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
📞 {DEDICATED_PHONE_LINE}"""

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
📞 {DEDICATED_PHONE_LINE} · {today}"""

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
| **Phone** | **{DEDICATED_PHONE_LINE}** |
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

When you are ready — even for questions only, we are here:

### 📞 {DEDICATED_PHONE_LINE}
**ProbateGuardian TN · Mount Juliet, Tennessee**

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


GUARDIAN_KIT_ROADMAP_STEPS = [
    ("🌿", "Pause & breathe", "Grief and paperwork together is overwhelming. Gather the death certificate, will, and property address — one folder, one step."),
    ("🏠", "Secure the home", "Lock up, forward mail, keep vacant-home insurance active, and name one calm heir contact."),
    ("⚖️", "Probate attorney first", "Your attorney handles court. We coordinate property only — always subject to court approval."),
    ("📊", "Real numbers for every heir", "Free CMA + Net Sheet — not a Zillow guess. Same facts for siblings."),
    ("📋", "Muniment of Title?", "TN shortcut when will is valid and debts are clear. Attorney decides; we align timelines."),
    ("🛤️", "Choose your path", "List for max value, Express cash, funded repairs, or hold — zero pressure."),
    ("🤝", "We handle heavy lifting", "Vendors, buyers, signage, insurance, clean-out — you focus on family."),
]

GUARDIAN_KIT_VENDOR_FALLBACKS = {
    "Probate Attorney": [
        ("Wilson County Probate Group", "(615) 669-7075", "Lebanon · Mt. Juliet"),
        ("Davidson Estate Counsel", "(615) 669-7075", "Nashville"),
        ("Rutherford Probate Partners", "(615) 669-7075", "Murfreesboro"),
    ],
    "Title Company": [
        ("Stewart Title — Wilson", "(615) 669-7075", "Lebanon"),
        ("Fidelity National — Davidson", "(615) 669-7075", "Nashville"),
    ],
    "CPA / Tax Professional": [
        ("Middle TN Estate CPA", "(615) 669-7075", "Stepped-up basis · K-1"),
        ("Wilson Tax Advisors", "(615) 669-7075", "Estate returns"),
    ],
    "Insurance for vacant homes": [
        ("Vacant Home TN Specialist", "(615) 669-7075", "Liability + vacancy rider"),
        ("Farm Bureau — Wilson", "(615) 669-7075", "Estate property policies"),
    ],
    "Property Maintenance / Lawn / Security": [
        ("GreenKeep Lawn — Wilson", "(615) 669-7075", "Weekly mow + drive-by"),
        ("SecureEstate Checks", "(615) 669-7075", "Lockbox · photo logs"),
    ],
    "Property Management / Rental": [
        ("Middle TN Estate PM", "(615) 669-7075", "Short-term hold option"),
    ],
    "Deep Cleaning & Staging": [
        ("Sparkle Estate Clean", "(615) 669-7075", "Post-cleanout deep clean"),
        ("Wilson Staging Co.", "(615) 669-7075", "Light staging for list"),
    ],
    "Estate Sale Companies": [
        ("Heirloom Estate Sales", "(615) 669-7075", "On-site tag sale"),
        ("Wilson Online Estate", "(615) 669-7075", "Hybrid online + onsite"),
    ],
    "Junk Removal / Dumpster": [
        ("DumpCo Wilson", "(615) 669-7075", "20-yd dumpster · haul-off"),
        ("QuickHaul Middle TN", "(615) 669-7075", "Attic · garage · bulk"),
    ],
    "Movers": [
        ("Careful Moves MTN", "(615) 669-7075", "Heir relocations"),
        ("Heirloom Packing & Ship", "(615) 669-7075", "Out-of-state shipping"),
    ],
    "General Contractors / Handyman / Repairs": [
        ("Funded Repairs Partner", "(615) 669-7075", "Roof · HVAC · paint — paid at close"),
        ("Wilson Handyman Pro", "(615) 669-7075", "Pre-list punch list"),
    ],
    "Cash Buyers / Investor": [
        ("eXp Express Offers Network", "(615) 669-7075", "Multiple vetted cash buyers"),
        ("Middle TN Investor Desk", "(615) 669-7075", "Backup cash bid"),
    ],
    "Traditional Listing Agent": [
        ("Scott Hardesty — eXp Realty", "(615) 669-7075", "Full MLS · Mt. Juliet"),
    ],
    "Buyout / Heir Mediation": [
        ("Sibling Buyout Mediation", "(615) 669-7075", "Neutral third-party math"),
    ],
}


def _gk_esc(value: str) -> str:
    return html.escape(str(value or "").strip())


def _gk_vendor_entries(vendors: dict, category: str) -> list:
    resolved = VENDOR_LEGACY_ALIASES.get(category, category)
    entry = vendors.get(resolved, {})
    rows = []
    if isinstance(entry, str) and entry.strip():
        rows.append((entry.strip(), "", ""))
    elif isinstance(entry, dict):
        for i in range(1, VENDOR_SLOTS + 1):
            contact = _coerce_vendor_contact(entry.get(f"vendor_{i}", ""))
            if contact["name"] or contact["phone"]:
                rows.append((contact["name"], contact["phone"], contact["notes"]))
        notes = (entry.get("area_notes") or "").strip()
        if notes and rows:
            rows[0] = (rows[0][0], rows[0][1], notes if not rows[0][2] else rows[0][2])
    if not rows:
        rows = list(GUARDIAN_KIT_VENDOR_FALLBACKS.get(category, []))
    return rows[:4]


def _gk_vendors_html(vendors: dict) -> str:
    blocks = []
    for category in VENDOR_CATEGORIES:
        entries = _gk_vendor_entries(vendors, category)
        if not entries:
            continue
        item_parts = []
        for name, phone, notes in entries:
            line = f"<li><strong>{_gk_esc(name)}</strong>"
            if phone:
                line += f" · {_gk_esc(phone)}"
            if notes:
                line += f'<br><span class="gk-vendor-note">{_gk_esc(notes)}</span>'
            item_parts.append(line + "</li>")
        items = "".join(item_parts)
        blocks.append(
            f'<div class="gk-vendor-card"><h4>{_gk_esc(category)}</h4><ul>{items}</ul></div>'
        )
    return "".join(blocks)


def guardian_kit_family_share_text(parsed: dict) -> str:
    heir = (parsed.get("heirs") or "your family").split("(")[0].strip()
    decedent = parsed.get("decedent") or "your loved one"
    address = parsed.get("address") or "the property"
    return (
        f"Hi {heir},\n\n"
        f"Branton Walker here with ProbateGuardian TN (Scott Hardesty's team). "
        f"We prepared your Guardian Kit for {decedent}'s home at {address}.\n\n"
        f"One call — we handle clean-out, insurance, vendors, and every sale path "
        f"(cash, funded repairs, or list). Zero pressure.\n\n"
        f"Free 7-step roadmap: https://probateguardians.com/roadmap/\n"
        f"{DEDICATED_PHONE_LINE}\n\n"
        f"With compassion,\nBranton Walker · ProbateGuardian TN"
    )


def guardian_kit_social_worker_text(parsed: dict) -> str:
    decedent = parsed.get("decedent") or "resident"
    address = parsed.get("address") or "family property"
    return (
        f"Hi — Branton Walker, ProbateGuardian TN. We remove the house burden so families "
        f"can focus on care. Even before probate we coordinate placement support, Medicaid "
        f"planning referrals, clean-out, insurance & signage.\n\n"
        f"Guardian Kit ready for {decedent} / {address}. "
        f"One-pager for your office? {DEDICATED_PHONE_LINE} Zero cost to families."
    )


def build_guardian_kit_html(parsed: dict, vendors: dict, *, standalone: bool = False) -> str:
    decedent = _gk_esc(parsed.get("decedent") or "Estate")
    address = _gk_esc(parsed.get("address") or "Address TBD")
    county = _gk_esc(parsed.get("county") or "Middle Tennessee")
    heir = _gk_esc(parsed.get("heirs") or "Estate Heirs / Executor")
    heir_first = _gk_esc((parsed.get("heirs") or "Friend").split("(")[0].strip())
    today = datetime.now().strftime("%B %d, %Y")
    year = datetime.now().year
    vendors_html = _gk_vendors_html(vendors)
    roadmap_html = "".join(
        f'<div class="gk-road-step">'
        f'<span class="gk-road-icon">{icon}</span>'
        f'<div><strong>{_gk_esc(title)}</strong><p>{_gk_esc(desc)}</p></div></div>'
        for icon, title, desc in GUARDIAN_KIT_ROADMAP_STEPS
    )

    styles = """
    .gk-root {
        --gk-green-dark: #142d22;
        --gk-green: #1f4d35;
        --gk-green-mid: #2d6a4f;
        --gk-cream: #faf6ee;
        --gk-cream-muted: #ede8dc;
        --gk-ink: #1a2e22;
        --gk-gold: #c9a227;
        font-family: Georgia, 'Times New Roman', serif;
        color: var(--gk-ink);
        line-height: 1.55;
        max-width: 42rem;
        margin: 0 auto 1.5rem auto;
    }
    .gk-root * { box-sizing: border-box; }
    .gk-hero {
        background: linear-gradient(145deg, var(--gk-green-dark) 0%, var(--gk-green) 55%, var(--gk-green-mid) 100%);
        color: var(--gk-cream);
        border-radius: 16px;
        padding: 1.35rem 1.2rem 1.2rem 1.2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(20, 45, 34, 0.45);
        margin-bottom: 1rem;
    }
    .gk-hero-badge {
        display: inline-block;
        background: var(--gk-gold);
        color: var(--gk-green-dark);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        margin-bottom: 0.65rem;
    }
    .gk-hero h1 {
        font-size: clamp(1.15rem, 4.5vw, 1.45rem);
        font-weight: 800;
        line-height: 1.35;
        margin: 0 0 0.5rem 0;
        color: var(--gk-cream) !important;
    }
    .gk-hero-sub { font-size: 0.92rem; opacity: 0.92; margin: 0; }
    .gk-meta {
        background: var(--gk-cream);
        border: 2px solid var(--gk-green-mid);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.85rem;
    }
    .gk-meta h2 { font-size: 1.05rem; margin: 0 0 0.2rem 0; color: var(--gk-green-dark) !important; }
    .gk-meta p { margin: 0.15rem 0; font-size: 0.9rem; }
    .gk-meta .gk-phone { font-size: 1.15rem; font-weight: 800; color: var(--gk-green); }
    .gk-section {
        background: var(--gk-cream);
        border-radius: 12px;
        padding: 1rem 1.05rem;
        margin-bottom: 0.75rem;
        border-left: 4px solid var(--gk-green-mid);
    }
    .gk-section h3 {
        font-size: 1rem;
        color: var(--gk-green-dark) !important;
        margin: 0 0 0.5rem 0;
    }
    .gk-section p, .gk-section li { font-size: 0.88rem; margin: 0.35rem 0; }
    .gk-hospice {
        background: linear-gradient(135deg, #1a3d2e 0%, #254d3a 100%);
        color: var(--gk-cream);
        border-left-color: var(--gk-gold);
    }
    .gk-hospice h3 { color: var(--gk-cream) !important; }
    .gk-roadmap { display: flex; flex-direction: column; gap: 0.55rem; }
    .gk-road-step {
        display: flex; gap: 0.65rem; align-items: flex-start;
        background: var(--gk-cream-muted);
        border-radius: 10px;
        padding: 0.55rem 0.65rem;
    }
    .gk-road-icon { font-size: 1.35rem; line-height: 1; flex-shrink: 0; }
    .gk-road-step strong { display: block; font-size: 0.88rem; color: var(--gk-green-dark); }
    .gk-road-step p { margin: 0.15rem 0 0 0; font-size: 0.8rem; color: #3d4f44; }
    .gk-tiers { display: flex; flex-direction: column; gap: 0.6rem; }
    .gk-tier {
        border-radius: 10px;
        padding: 0.75rem 0.85rem;
        border: 2px solid var(--gk-green-mid);
    }
    .gk-tier-high { background: linear-gradient(135deg, #e8f5ec, var(--gk-cream)); }
    .gk-tier-mid { background: var(--gk-cream-muted); }
    .gk-tier-low { background: #f5f2ea; border-style: dashed; }
    .gk-tier h4 { margin: 0 0 0.35rem 0; font-size: 0.92rem; color: var(--gk-green-dark) !important; }
    .gk-tier .gk-price { font-weight: 800; color: var(--gk-green); font-size: 0.85rem; }
    .gk-tier ul { margin: 0.35rem 0 0 0; padding-left: 1.1rem; }
    .gk-warn {
        background: #fff8e6;
        border: 2px solid var(--gk-gold);
        border-radius: 10px;
        padding: 0.75rem 0.85rem;
        margin-bottom: 0.75rem;
    }
    .gk-warn h3 { color: #7a5c00 !important; }
    .gk-signage {
        font-family: 'Arial Black', Arial, sans-serif;
        background: #1a1a1a;
        color: #f5f0e6;
        text-align: center;
        padding: 0.85rem 0.5rem;
        border: 3px solid #c9a227;
        border-radius: 6px;
        font-size: clamp(0.72rem, 3vw, 0.88rem);
        letter-spacing: 0.04em;
        margin: 0.5rem 0;
    }
    .gk-bullets { display: flex; flex-direction: column; gap: 0.5rem; }
    .gk-bullet-card {
        background: var(--gk-cream-muted);
        border-radius: 10px;
        padding: 0.65rem 0.75rem;
    }
    .gk-bullet-card h4 { margin: 0 0 0.3rem 0; font-size: 0.88rem; color: var(--gk-green) !important; }
    .gk-bullet-card ul { margin: 0; padding-left: 1rem; font-size: 0.82rem; }
    .gk-vendors-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.5rem;
    }
    @media (min-width: 480px) {
        .gk-vendors-grid { grid-template-columns: 1fr 1fr; }
    }
    .gk-vendor-card {
        background: var(--gk-cream-muted);
        border-radius: 8px;
        padding: 0.55rem 0.65rem;
        font-size: 0.78rem;
    }
    .gk-vendor-card h4 {
        margin: 0 0 0.3rem 0;
        font-size: 0.78rem;
        color: var(--gk-green-dark) !important;
    }
    .gk-vendor-card ul { margin: 0; padding-left: 1rem; }
    .gk-vendor-note { color: #5a6b5f; font-size: 0.72rem; }
    .gk-cta {
        background: var(--gk-green-dark);
        color: var(--gk-cream);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin-top: 0.5rem;
    }
    .gk-cta .gk-phone { font-size: 1.35rem; font-weight: 800; color: var(--gk-gold); }
    .gk-footer { font-size: 0.72rem; color: #5a6b5f; text-align: center; margin-top: 0.75rem; }
    @media print {
        .gk-root { max-width: 100%; }
        .gk-hero, .gk-hospice, .gk-cta { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    }
    """

    body = f"""
<div class="gk-root">
<style>{styles}</style>
<div class="gk-hero">
  <div class="gk-hero-badge">ProbateGuardian Guardian Kit</div>
  <h1>One Call. Everything Handled.<br>We Remove the House Burden So You Can Focus on Family.</h1>
  <p class="gk-hero-sub">Compassion · Clarity · Court-aware coordination · Middle Tennessee</p>
  <p class="gk-phone" style="margin-top:0.75rem;font-size:1rem;">{DEDICATED_PHONE_HTML}</p>
</div>

<div class="gk-meta">
  <h2>Prepared for {heir}</h2>
  <p><strong>Estate of {decedent}</strong></p>
  <p>{address} · {county}</p>
  <p>ProbateGuardian TN · Mount Juliet, Tennessee</p>
  <p class="gk-phone">{DEDICATED_PHONE_HTML}</p>
  <p style="font-size:0.8rem;color:#5a6b5f;">{today} · Confidential — heirs &amp; authorized reps only</p>
</div>

<div class="gk-section gk-hospice">
  <h3>🩺 Pre-Death &amp; Hospice Support</h3>
  <p>Dear {heir_first}, even <strong>before probate opens</strong> — we coordinate care placement referrals, Medicaid planning introductions, estate clean-out, vacant-home insurance, and professional signage so social workers and families get <strong>peace now</strong>, not panic later.</p>
  <p><em>We never rush grief. We remove the house burden so you can focus on Mom's care.</em></p>
</div>

<div class="gk-section">
  <h3>🗺️ 7-Step Probate Family Roadmap</h3>
  <div class="gk-roadmap">{roadmap_html}</div>
  <p style="font-size:0.78rem;margin-top:0.5rem;">Full guide: <strong>probateguardians.com/roadmap</strong></p>
</div>

<div class="gk-section">
  <h3>🎯 3-Tier Service Options</h3>
  <div class="gk-tiers">
    <div class="gk-tier gk-tier-high">
      <h4>⭐ High Concierge — Full Project Coordinator</h4>
      <p class="gk-price">$0 out of pocket to start · We pay initial haul-off ($500–$2,500), lockbox, signage, 1st lawn cut</p>
      <ul>
        <li>Every vendor dispatched · sibling buyout math · attorney loop-in</li>
        <li>Express Offers + funded repairs presented side-by-side on one Net Sheet</li>
        <li><strong>Best when:</strong> out-of-state heirs, overwhelm, or property needs work</li>
      </ul>
    </div>
    <div class="gk-tier gk-tier-mid">
      <h4>✓ Middle Path — Coordinated Sale</h4>
      <p class="gk-price">Listing 5–6% · We pay CMA, Net Sheet, signage kit &amp; vendor scheduling</p>
      <ul>
        <li>MLS listing with optional funded repairs at closing ($0 upfront)</li>
        <li>Express Offers as cash backup if listing stalls</li>
        <li><strong>Best when:</strong> strong ARV upside, family can wait 60–90 days</li>
      </ul>
    </div>
    <div class="gk-tier gk-tier-low">
      <h4>◎ Low Touch — Guidance + Rolodex</h4>
      <p class="gk-price">No upfront fees · Commission only if/when you sell with us</p>
      <ul>
        <li>Roadmap, one Net Sheet, attorney &amp; insurance introductions</li>
        <li>You manage vendors — we stay on call for questions</li>
        <li><strong>Best when:</strong> local heir with time and DIY comfort</li>
      </ul>
    </div>
  </div>
</div>

<div class="gk-warn">
  <h3>⚠️ Insurance + Signage — Protect the Estate Now</h3>
  <p><strong>Vacant home insurance</strong> is required once the property is unoccupied. Standard homeowner policies may void after 30–60 days. We connect you with Middle TN vacant-home specialists — <strong>we coordinate so you don't have to chase carriers.</strong></p>
  <div class="gk-signage">ESTATE PROPERTY — NO TRESPASSING<br>Authorized Access Only · {DEDICATED_PHONE_LINE}</div>
  <p style="font-size:0.82rem;">Posted at front entry &amp; rear access · photographed for estate file · deters squatters &amp; copper theft</p>
</div>

<div class="gk-section">
  <h3>🚀 Sale Paths — Pick Your Peace of Mind</h3>
  <div class="gk-bullets">
    <div class="gk-bullet-card">
      <h4>Express Offers · Multiple Cash Buyers</h4>
      <ul>
        <li>Competing bids in 48–72 hrs · sell 100% as-is · zero showings</li>
        <li>Close 14–30 days · <strong>subject to court approval</strong></li>
        <li>Ideal when speed &amp; certainty beat top dollar</li>
      </ul>
    </div>
    <div class="gk-bullet-card">
      <h4>Cash Backup Plan</h4>
      <ul>
        <li>Every listing includes Express Offers as Plan B — no stranded listing</li>
        <li>Compare cash vs. net proceeds on one sheet before you decide</li>
      </ul>
    </div>
    <div class="gk-bullet-card">
      <h4>Funded Repairs</h4>
      <ul>
        <li>Roof, HVAC, paint, flooring — <strong>$0 out of pocket</strong>, repaid at closing</li>
        <li>List at peak ARV without heir arguments over who pays</li>
      </ul>
    </div>
  </div>
</div>

<div class="gk-section">
  <h3>📇 Vendors Rolodex — Middle TN (multiple per category)</h3>
  <p style="font-size:0.82rem;">Vetted partners — updated from your live CRM rolodex. One call dispatches all.</p>
  <div class="gk-vendors-grid">{vendors_html}</div>
</div>

<div class="gk-cta">
  <p style="margin:0 0 0.35rem 0;">You don't have to decide today. When you're ready:</p>
  <p class="gk-phone">{DEDICATED_PHONE_HTML}</p>
</div>
<p class="gk-footer">Not legal advice · All sales subject to court approval · © {year} Scott Hardesty, eXp Realty</p>
</div>
"""

    if standalone:
        return (
            f"<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>Guardian Kit — {decedent}</title></head><body style=\"margin:0;padding:1rem;"
            f"background:#0d1117;\">{body}</body></html>"
        )
    return body


def generate_guardian_kit_html(parsed: dict, vendors: dict) -> str:
    return build_guardian_kit_html(parsed, vendors, standalone=False)


FACILITY_VISIT_CHECKLIST = f"""═══════════════════════════════════════════════════════════
  PROBATEGUARDIAN — FACILITY VISIT CHECKLIST (print & clip)
  {DEDICATED_PHONE_LINE}
═══════════════════════════════════════════════════════════

BEFORE YOU WALK IN
□ Laminated referral one-pagers (5–10)
□ Business cards — Scott + Branton
□ Value script on phone (notes app)
□ Facility name + social worker target written down

AT THE FRONT DESK
□ Ask for Director of Social Services or Discharge Planner
□ Leave one-pager even if SW unavailable ("for families worrying about the house")

WITH THE SOCIAL WORKER (2 min pitch)
□ "We remove the house burden so families can focus on care"
□ Not probate attorneys — property Project Coordinators
□ Zero cost, zero pressure, court-aware
□ Hand one-pager + card

DATA TO CAPTURE
□ Social Worker Name: _______________________________
□ Facility: _______________________________________
□ Typical discharge path (SNF / home / hospice / hospital)
□ Best callback number / email
□ Notes: __________________________________________

FOLLOW-UP (within 48 hrs)
□ Log in Referral Tracker tab
□ Text Scott if warm family named
□ Send thank-you email with digital Guardian Kit link

BRANTON QUEUE RULE
Any named family + address → tap "Send to Branton Queue" with 🔥 tag

═══════════════════════════════════════════════════════════
"""


def hospice_google_url(query: str) -> str:
    return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"


def load_hospice_referrals() -> list:
    if not HOSPICE_REFERRALS_FILE.exists():
        return []
    try:
        data = json.loads(HOSPICE_REFERRALS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_hospice_referrals(rows: list) -> None:
    HOSPICE_REFERRALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = HOSPICE_REFERRALS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    tmp.replace(HOSPICE_REFERRALS_FILE)


def get_hospice_referrals() -> list:
    if "hospice_referrals" not in st.session_state:
        st.session_state.hospice_referrals = load_hospice_referrals()
    return st.session_state.hospice_referrals


def generate_hospice_value_script(
    facility: str,
    family_name: str,
    social_worker: str,
) -> str:
    facility_txt = (facility or "your facility").strip()
    family_txt = (family_name or "the family").strip()
    sw_txt = (social_worker or "there").strip()
    return f"""Hi {sw_txt},

I'm Scott Hardesty with ProbateGuardian / eXp Realty in Middle Tennessee. I partner with {PARTNER_NAME} to help families through the property side of estate transitions.

I know you're focused on {family_txt}'s care at {facility_txt} — that's what matters most right now.

When families are ready (often before or right after passing), **the house becomes the burden**: locks, utilities, contents, siblings, court timelines. **We remove that entire burden so you and the family can focus on Mom's care and grieving** — not becoming accidental project managers.

**What we offer your families (zero cost, zero pressure):**
- One Project Coordinator (Scott) — estate sales, cleanout, vendors, Net Sheet
- Express Offers + funded repairs paths
- We never rush; we respect the hospice timeline

If you ever meet a family worrying about "what happens to the house," hand them our Guardian Kit or my card:

{DEDICATED_PHONE_LINE}

Happy to drop laminated one-pagers for your social work office — no strings attached.

With respect,
Scott Hardesty"""


def generate_referral_one_pager(
    parsed: dict,
    vendors: dict,
    facility: str,
    social_worker: str,
) -> str:
    sw_txt = (social_worker or "Facility Social Work").strip()
    fac_txt = (facility or "Partner Facility").strip()
    header = f"""# 🩺 ProbateGuardian Referral One-Pager
### For families referred by **{sw_txt}** · **{fac_txt}**

| | |
|---|---|
| **Phone** | **{DEDICATED_PHONE_LINE}** |
| **Web** | probateguardians.com |

*{DEDICATED_PHONE_LINE}*

*Hand this to families worrying about the house. We remove the property burden so they can focus on care.*

---

"""
    return header + generate_guardian_kit(parsed, vendors)


def push_hospice_to_branton_queue(
    decedent: str,
    address: str,
    county: str,
    contact_name: str,
    contact_phone: str,
    facility: str,
    social_worker: str,
    notes: str,
) -> int:
    decedent_txt = (decedent or "Pre-Probate Referral").strip()
    address_txt = (address or "Address TBD").strip()
    county_txt = (county or "Middle TN").strip()
    contact_txt = (contact_name or "Family Contact").strip()
    phone_txt = (contact_phone or "").strip()
    facility_txt = (facility or "—").strip()
    sw_txt = (social_worker or "—").strip()
    notes_txt = (notes or "").strip()

    raw = (
        f"🩺 HOSPICE PRE-PROBATE REFERRAL 🔥\n"
        f"Facility: {facility_txt}\n"
        f"Social Worker: {sw_txt}\n"
        f"Family Contact: {contact_txt}\n"
        f"Phone: {phone_txt or '—'}\n\n"
        f"Decedent: {decedent_txt}\n"
        f"Property: {address_txt}\n"
        f"County: {county_txt}\n\n"
        f"{notes_txt}"
    ).strip()

    parsed = {
        "decedent": decedent_txt,
        "address": address_txt,
        "county": county_txt,
        "heirs": contact_txt,
        "phone": phone_txt,
        "email": "",
        "raw": raw,
        "vacant_likely": True,
        "contact_name": contact_txt,
    }
    note_block = (
        f"🔥 HOSPICE PRE-PROBATE — Referred by {sw_txt} @ {facility_txt}\n{notes_txt}"
    ).strip()
    st.session_state.leads.insert(
        0,
        build_lead(
            parsed,
            pipeline_stage="🔥 Hot / New (call today)",
            status="New/Hot",
            score=85,
            source="hospice",
            assigned_to_branton=True,
            follow_up_days=0,
            notes=initial_notes_from_block(note_block, source="Hospice Pipeline"),
        ),
    )
    persist_leads()
    return 1


# ── Load persisted data (after all helpers are defined) ───────────────────────
get_leads()
get_vendors()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Scott Hardesty")
    st.markdown("**eXp Realty** · Mount Juliet, TN")
    st.markdown(
        f'<div class="phone-banner">📞 {DEDICATED_PHONE_HTML}</div>',
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

# ── Newspaper Scraper tab helpers (isolated — used only by tab_newspaper) ─────
_NS_LINKS = {
    "tnpublicnotice.com": "https://www.tnpublicnotice.com/",
    "Gallatin News": "https://www.gallatinnews.com/",
    "Hendersonville Standard": "https://www.hendersonvillestandard.com/",
    "Sumner County Assessor": "https://sumnertn.geopowered.com/propertysearch/",
}
_NS_PROBATE_KW = (
    "deceased", "estate of", "notice to creditors", "died on", "in re:", "probate",
    "letters testamentary", "personal representative", "executor", "administrator",
)
_NS_ADDR_KW = (
    "pike", "road", "rd", "drive", "dr", "lane", "ln", "avenue", "ave",
    "street", "st", "court", "ct", "way", "blvd", "gallatin", "hendersonville",
    "portland", "white house", "cottontown", "westmoreland",
)
_NS_SUMNER_CITIES = (
    "Hendersonville", "Gallatin", "Portland", "White House", "Cottontown", "Westmoreland",
)
_NS_QUEUE_NOTE = "Newspaper Scrape • High Potential Asset"
_NS_SPLIT_RE = re.compile(
    r"\n\s*\n+|\n(?=(?:NOTICE|Notice|Estate of|IN RE|In Re|Published|Probate|Obituary)\b)",
    re.I,
)
_NS_PR_RE = re.compile(
    r"(?:personal representative|petitioner|executor|executrix|administrator|"
    r"administratrix)[:\s]+([A-Z][^\n.;]{2,70})",
    re.I,
)
_NS_SURVIVED_RE = re.compile(
    r"survived by\s+(.+?)(?:\.|;|\n|He was|She was|A\s+(?:memorial|service))",
    re.I | re.S,
)
_NS_DATE_RE = re.compile(
    r"(?:published|filed|died|passed|deceased)\s+(?:on\s+)?"
    r"([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4})",
    re.I,
)
_NS_SCORE_LABEL = {"High": "🔥 High", "Med": "🟡 Med", "Low": "⚪ Low"}
_NS_SCORE_RANK = {"High": 3, "Med": 2, "Low": 1}


def _ns_score_display(score: str) -> str:
    return _NS_SCORE_LABEL.get(score, score)


def _ns_score_from_block(text: str, address_clue: str) -> str:
    lower = (text or "").lower()
    addr_lower = (address_clue or "").lower()
    has_street = bool(re.search(r"\d+\s+\w+.*(?:rd|road|st|street|ave|dr|drive|ln|lane|ct|way|pike|blvd)", lower))
    if has_street or (address_clue and address_clue != "—"):
        return "High"
    if any(word in lower or word in addr_lower for word in _NS_ADDR_KW):
        return "High"
    if any(kw in lower for kw in _NS_PROBATE_KW):
        return "Med"
    return "Low"


def _ns_extract_decedent(text: str) -> str:
    m = re.search(r"estate of\s+(.+?)(?:,|\.|\n|$)", text, re.I)
    if m:
        return m.group(1).strip()[:90]
    m2 = re.search(r"^([A-Z][a-z]+(?:\s+[A-Z][\.'-]?[a-z]+)+)", text.strip(), re.M)
    if m2:
        return m2.group(1).strip()[:90]
    first = text.strip().split("\n")[0][:90]
    return first or "Unknown Decedent"


def _ns_extract_date(text: str) -> str:
    dm = _NS_DATE_RE.search(text)
    if dm:
        return dm.group(1).strip()
    m = DEATH_DATE_RE.search(text)
    if m:
        return m.group(0).strip()
    m2 = re.search(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b", text)
    if m2:
        return m2.group(1)
    return "—"


def _ns_extract_pr_heir(text: str) -> str:
    pr = _NS_PR_RE.search(text)
    if pr:
        return pr.group(1).strip()[:80]
    surv = _NS_SURVIVED_RE.search(text)
    if surv:
        return surv.group(1).strip()[:80]
    return "Contact TBD"


def _ns_extract_address(text: str) -> str:
    m = CRUSHER_STREET_RE.search(text)
    if m:
        return re.sub(r"\s+", " ", m.group(1).strip())
    m2 = re.search(
        r"(\d+\s+[\w\s\.\#]+(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Ln|Lane|Ct|Court|Way|Blvd)\.?,?\s*[\w\s]+,?\s*TN\s*\d{5})",
        text,
        re.I,
    )
    if m2:
        return m2.group(1).strip()
    for city in _NS_SUMNER_CITIES:
        if city.lower() in text.lower():
            return f"{city}, TN"
    return "—"


def _ns_phone_search_string(pr_heir: str, address_clue: str, text: str) -> str:
    contact = (pr_heir or "").split("(")[0].strip()
    if contact in ("", "Contact TBD"):
        words = [w for w in re.sub(r"[^A-Za-z\s]", " ", text).split() if len(w) > 2]
        if len(words) >= 2:
            return f"{words[0]} {words[-1]} · Sumner County, TN"
        return "— need heir/PR name —"
    parts = [p for p in re.sub(r"[,\\.]", " ", contact).split() if p]
    city = "Sumner County"
    if address_clue and address_clue != "—":
        cm = re.search(r",\s*([^,]+)\s*,\s*TN", address_clue, re.I)
        if cm:
            city = cm.group(1).strip()
        elif ", TN" in address_clue:
            city = address_clue.replace(", TN", "").strip()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[-1]} · {city}, TN"
    return f"{contact} · {city}, TN"


def _ns_split_blocks(raw: str) -> list:
    text = (raw or "").strip()
    if not text:
        return []
    blocks = [b.strip() for b in _NS_SPLIT_RE.split(text) if b.strip()]
    if len(blocks) <= 1 and len(text) > 40:
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        blocks = [ln for ln in lines if any(kw in ln.lower() for kw in _NS_PROBATE_KW)]
        if not blocks:
            blocks = [text]
    return [b for b in blocks if len(b) >= 20]


def _ns_parse_block(block: str) -> dict:
    decedent = _ns_extract_decedent(block)
    date = _ns_extract_date(block)
    pr_heir = _ns_extract_pr_heir(block)
    address_clue = _ns_extract_address(block)
    score = _ns_score_from_block(block, address_clue)
    return {
        "decedent": decedent,
        "date": date,
        "pr_heir": pr_heir,
        "address_clue": address_clue,
        "real_estate_score": score,
        "score_display": _ns_score_display(score),
        "phone_search_string": _ns_phone_search_string(pr_heir, address_clue, block),
        "status": "Ready",
        "raw": block,
        "county": "Sumner County",
    }


def _ns_analyze_text(raw: str) -> list:
    results = []
    seen = set()
    for block in _ns_split_blocks(raw):
        if not any(kw in block.lower() for kw in _NS_PROBATE_KW):
            continue
        row = _ns_parse_block(block)
        key = (row["decedent"], row.get("date"), row.get("address_clue"))
        if key in seen:
            continue
        seen.add(key)
        results.append(row)
    results.sort(
        key=lambda x: (_NS_SCORE_RANK.get(x.get("real_estate_score"), 0), x.get("decedent", "")),
        reverse=True,
    )
    return results


def _ns_results_for_json(results: list) -> list:
    export = []
    for row in results:
        export.append({
            "decedent": row.get("decedent", ""),
            "date": row.get("date", ""),
            "heir_pr": row.get("pr_heir", ""),
            "real_estate_score": row.get("real_estate_score", "Low"),
            "address_clue": row.get("address_clue", ""),
            "phone_search_string": row.get("phone_search_string", ""),
            "status": row.get("status", ""),
            "county": row.get("county", "Sumner County"),
            "source_note": _NS_QUEUE_NOTE,
            "raw": row.get("raw", ""),
        })
    return export


def _ns_push_high_to_queue(results: list, selected: list) -> int:
    added = 0
    for row in selected:
        if row.get("real_estate_score") != "High" or row.get("status") == "Queued":
            continue
        decedent = (row.get("decedent") or "").strip()
        if not decedent or decedent == "Unknown Decedent":
            continue
        address = row.get("address_clue", "—")
        if address == "—":
            address = "Address TBD"
        note_text = _NS_QUEUE_NOTE
        if row.get("phone_search_string"):
            note_text += f"\nBV: {row['phone_search_string']}"
        if row.get("pr_heir") and row["pr_heir"] != "Contact TBD":
            note_text += f"\nPR/Heir: {row['pr_heir']}"
        if row.get("raw"):
            note_text += f"\n{row['raw'][:500]}"
        parsed = {
            "decedent": decedent,
            "address": address,
            "county": row.get("county", "Sumner County"),
            "heirs": row.get("pr_heir", "Contact TBD"),
            "phone": "",
            "email": "",
            "raw": row.get("raw", decedent),
            "filing_date": row.get("date", "") if row.get("date") != "—" else "",
        }
        st.session_state.leads.insert(
            0,
            build_lead(
                parsed,
                pipeline_stage="🔥 Hot / New (call today)",
                status="New/Hot",
                score=90 if address != "Address TBD" else 85,
                source="newspaper_scraper",
                assigned_to_branton=True,
                follow_up_days=0,
                notes=initial_notes_from_block(note_text, source="Newspaper Scraper"),
            ),
        )
        row["status"] = "Queued"
        added += 1
    if added:
        persist_leads()
    return added


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<p class="hero-title">🏠 ProbateGuardian Free TN</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">24/7 Partnership CRM for Scott Hardesty + Branton Walker</p>',
    unsafe_allow_html=True,
)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_dashboard, tab_crusher, tab_add_leads, tab_newspaper, tab_outreach, tab_partner, tab_vendors, tab_training, tab_hospice = st.tabs([
    "Dashboard",
    "💰 90-Day Probate Crusher",
    "Add New Leads",
    "📰 Newspaper Scraper • Small Counties",
    "Generate Outreach",
    "📘 Partner Kit",
    "🛠️ Vendors Rolodex",
    "🎥 Training",
    "🩺 Hospice & Pre-Probate Pipeline",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB — Generate Outreach (Lead Workflow)
# ══════════════════════════════════════════════════════════════════════════════
with tab_outreach:
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
            "heir-phone-from-paste\n"
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
            st.session_state.guardian_kit_parsed = parsed
            st.session_state.guardian_kit_raw = raw_lead

    if st.session_state.get("guardian_kit_parsed"):
        gk_parsed = st.session_state.guardian_kit_parsed
        gk_vendors = st.session_state.vendors
        st.success(
            "✅ Premium Guardian Kit ready — dark-green one-pager with roadmap, tiers, "
            "vendors & one-tap send buttons below."
        )
        st.markdown(generate_guardian_kit_html(gk_parsed, gk_vendors), unsafe_allow_html=True)

        family_share = guardian_kit_family_share_text(gk_parsed)
        sw_text = guardian_kit_social_worker_text(gk_parsed)
        heir_email = (gk_parsed.get("email") or "").strip()
        mail_target = heir_email if heir_email else ""
        mail_subject = urllib.parse.quote(
            f"Guardian Kit — {gk_parsed.get('decedent', 'Estate')} · ProbateGuardian TN"
        )
        mail_body = urllib.parse.quote(family_share)
        mailto = f"mailto:{mail_target}?subject={mail_subject}&body={mail_body}"
        sms_body = urllib.parse.quote(sw_text)
        sms_link = f"sms:?&body={sms_body}"
        gk_slug = re.sub(r"[^\w\-]+", "_", (gk_parsed.get("decedent") or "estate"))[:40]
        pdf_html = build_guardian_kit_html(gk_parsed, gk_vendors, standalone=True)

        st.markdown("#### 📲 One-Tap Actions")
        gk_a1, gk_a2 = st.columns(2)
        with gk_a1:
            st.markdown('<div class="gk-action-marker"></div>', unsafe_allow_html=True)
            st.link_button(
                "📧 Send to Family",
                mailto,
                use_container_width=True,
                type="primary",
            )
        with gk_a2:
            st.markdown('<div class="gk-action-marker"></div>', unsafe_allow_html=True)
            st.download_button(
                label="📥 Download PDF",
                data=pdf_html,
                file_name=f"guardian_kit_{gk_slug}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True,
                help="Open file → Print → Save as PDF on your phone",
                key="gk_download_pdf",
            )
        gk_a3, gk_a4 = st.columns(2)
        with gk_a3:
            st.markdown('<div class="gk-action-marker"></div>', unsafe_allow_html=True)
            st.link_button(
                "💬 Text to Social Worker",
                sms_link,
                use_container_width=True,
                type="primary",
            )
        with gk_a4:
            st.markdown('<div class="gk-action-marker"></div>', unsafe_allow_html=True)
            if st.button(
                f"🔥 Add to {PARTNER_NAME} Queue",
                use_container_width=True,
                type="primary",
                key="gk_add_branton_queue",
            ):
                gk_raw = st.session_state.get("guardian_kit_raw", "")
                gk_push = dict(gk_parsed)
                gk_push["raw"] = gk_raw
                heat_status, heat_pipeline = heat_from_import_block(gk_raw)
                lead_entry = build_lead(
                    gk_push,
                    assigned_to_branton=True,
                    pipeline_stage=heat_pipeline,
                    status=heat_status,
                    source="guardian_kit",
                    score=75,
                    notes=initial_notes_from_block(
                        f"🔥 Guardian Kit sent\n{gk_raw}".strip(),
                        source="Guardian Kit",
                    ),
                )
                st.session_state.leads.insert(0, lead_entry)
                persist_leads()
                st.success(
                    f"🔥 Added to {PARTNER_NAME}'s queue — {gk_parsed.get('decedent')} · "
                    f"Follow-up: **{lead_entry['follow_up']}**"
                )
        st.caption(
            "Download PDF: open the HTML file in Safari/Chrome → Share → Print → Save as PDF. "
            "Family email auto-fills if an email was in the lead paste."
        )

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

# ── Bulk Qualifier tab helpers (isolated — used only by tab_add_leads) ─────────
try:
    from pypdf import PdfReader as _BqPdfReader
except ImportError:
    _BqPdfReader = None

try:
    import pytesseract as _bq_tesseract
    from PIL import Image as _BqImage
except ImportError:
    _bq_tesseract = None
    _BqImage = None

_BQ_DAVIDSON_RE = re.compile(r"probate\s+court\s+of\s+davidson|davidson\s+county.*probate", re.I)
_BQ_DECEDENT_RE = (
    re.compile(r"estate\s+of\s+(.+?)(?:,|\n|deceased|\.|$)", re.I),
    re.compile(r"in\s+re:?\s*(?:the\s+)?estate\s+of\s+(.+?)(?:,|\n|\.|$)", re.I),
    re.compile(r"(?:decedent|deceased)[:\s]+(.+?)(?:\n|,|\.|$)", re.I),
)
_BQ_HEIR_BLOCK_RE = re.compile(
    r"(?:heirs?|beneficiaries|survived\s+by|children)[:\s]*\n?(.+?)(?:\n\n|personal\s+representative|executor|administrator|waiver)",
    re.I | re.S,
)
_BQ_RE_PROPERTY_RE = re.compile(
    r"(?:real\s+property|real\s+estate|parcel|land\s+located|property\s+located|"
    r"residence\s+of\s+the\s+decedent)",
    re.I,
)


def _bq_extract_pdf_text(data: bytes) -> str:
    if not _BqPdfReader or not data:
        return ""
    try:
        reader = _BqPdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception:
        return ""


def _bq_extract_image_text(data: bytes) -> str:
    if not _bq_tesseract or not _BqImage or not data:
        return ""
    try:
        img = _BqImage.open(io.BytesIO(data))
        return (_bq_tesseract.image_to_string(img) or "").strip()
    except Exception:
        return ""


def _bq_case_key_from_text(text: str) -> str:
    text = text or ""
    m = CRUSHER_CASE_RE.search(text)
    if m:
        return re.sub(r"\s+", "", m.group(1).upper())
    m2 = re.search(r"\b(26P\d+)\b", text, re.I)
    if m2:
        return m2.group(1).upper()
    m3 = re.search(r"\b(PR\d{4}-\d+)\b", text, re.I)
    if m3:
        return m3.group(1).upper()
    for pat in _BQ_DECEDENT_RE:
        dm = pat.search(text)
        if dm:
            slug = re.sub(r"[^A-Za-z0-9]+", "_", dm.group(1).strip().lower())[:40]
            if slug:
                return f"EST_{slug}"
    return ""


def _bq_group_page_texts(pages: list) -> list:
    groups = []
    current = []
    current_key = None
    for text in pages:
        text = (text or "").strip()
        if not text:
            continue
        key = _bq_case_key_from_text(text)
        if key and current_key and key != current_key:
            groups.append("\n\n--- PAGE ---\n\n".join(current))
            current = [text]
            current_key = key
        else:
            if key:
                current_key = key
            current.append(text)
    if current:
        groups.append("\n\n--- PAGE ---\n\n".join(current))
    return groups


def _bq_split_case_chunks(text: str, davidson_fast: bool) -> list:
    text = (text or "").strip()
    if not text:
        return []
    chunks = _split_estate_chunks(text)
    if davidson_fast:
        expanded = []
        for chunk in chunks:
            parts = re.split(r"(?=\bPR\s*20\d{2}\s*[-–—]\s*\d+\b)", chunk, flags=re.I)
            expanded.extend([p.strip() for p in parts if p.strip()])
        if expanded:
            chunks = expanded
    return [c for c in chunks if c.strip()]


def _bq_parse_davidson_case(text: str, davidson_fast: bool = False) -> dict:
    parsed = dict(parse_lead_enhanced(text))
    if davidson_fast or _BQ_DAVIDSON_RE.search(text):
        parsed["county"] = "Davidson County"
        for pat in _BQ_DECEDENT_RE:
            dm = pat.search(text)
            if dm:
                name = dm.group(1).strip().rstrip(",.")
                if name and name.lower() not in ("the", "unknown"):
                    parsed["decedent"] = name
                    break
        hm = _BQ_HEIR_BLOCK_RE.search(text)
        if hm and not parsed.get("heirs"):
            parsed["heirs"] = hm.group(1).strip()[:200]
        if _BQ_RE_PROPERTY_RE.search(text):
            parsed["has_real_estate"] = True
        if not parsed.get("contact_name"):
            for pr_pat in (
                CRUSHER_PR_LINE_RE,
                re.compile(
                    r"(?:personal\s+representative|executor|administrator|petitioner)"
                    r"[:\s]+([A-Z][^\n,;]{2,70})",
                    re.I,
                ),
            ):
                pm = pr_pat.search(text)
                if pm:
                    parsed["contact_name"] = pm.group(1).strip()
                    parsed["contact_role"] = "Personal Representative"
                    if not parsed.get("heirs"):
                        parsed["heirs"] = f"{parsed['contact_name']} (Personal Representative)"
                    break
    death_dt = extract_death_date(text)
    if death_dt:
        parsed["death_date_iso"] = death_dt.strftime("%Y-%m-%d")
        if not parsed.get("filing_date"):
            parsed["filing_date"] = parsed["death_date_iso"]
    parsed["raw"] = text
    return parsed


def _bq_poc_display(parsed: dict) -> str:
    stub = {
        "contact_name": parsed.get("contact_name"),
        "heirs": parsed.get("heirs"),
        "phone": parsed.get("phone"),
        "email": parsed.get("email"),
        "raw": parsed.get("raw", ""),
        "notes": [],
    }
    return _lead_primary_contact_line_md(stub)


def _bq_qualify_parsed(parsed: dict) -> dict:
    scored = score_vacant_lead(parsed)
    score = int(scored.get("score") or 0)
    vacant = bool(scored.get("vacant_likely"))
    flags = scored.get("flags") or []
    if parsed.get("has_real_estate"):
        score = min(100, score + 8)
        flags = list(flags) + ["✓ Real estate mentioned"]
    if vacant or score >= 65:
        tier = "🔥 HOT"
        reason = scored.get("vacant_label") if vacant and scored.get("vacant_label") != "—" else (
            " · ".join(flags[:2]) if flags else "Strong property + contact signals"
        )
    elif score >= 40:
        tier = "🔥 Warm"
        reason = " · ".join(flags[:2]) if flags else "Partial case data — review & call"
    else:
        tier = "Skip"
        reason = "Missing address or too little contact data"
    death_filing = parsed.get("filing_date") or parsed.get("death_date_iso") or "—"
    return {
        "parsed": parsed,
        "case_number": parsed.get("case_number") or "—",
        "decedent": parsed.get("decedent") or "Unknown Decedent",
        "poc_display": _bq_poc_display(parsed),
        "address": parsed.get("address") or "Address TBD",
        "death_filing": death_filing,
        "tier": tier,
        "reason": reason[:120],
        "score": score,
        "sort_rank": {"🔥 HOT": 3, "🔥 Warm": 2, "Skip": 1}.get(tier, 0),
        "vacant_likely": vacant,
        "scored": scored,
        "raw": parsed.get("raw", ""),
    }


def _bq_google_doc_text(row: dict) -> str:
    p = row.get("parsed") or {}
    poc = _bq_poc_display(p).replace("**", "")
    return (
        f"CASE: {row.get('case_number', '—')}\n"
        f"DECEDENT: {row.get('decedent', '—')}\n"
        f"PRIMARY CONTACT: {poc}\n"
        f"PROPERTY: {row.get('address', '—')}\n"
        f"COUNTY: {p.get('county', 'Middle TN')}\n"
        f"DEATH / FILING: {row.get('death_filing', '—')}\n"
        f"SCORE: {row.get('tier', '—')} — {row.get('reason', '')}\n"
        f"PR ADDRESS: {p.get('pr_address') or '—'}\n"
        f"HEIRS: {p.get('heirs') or '—'}\n"
        f"---\n"
        f"{(row.get('raw') or '')[:1200]}"
    ).strip()


def _bq_analyze_inputs(paste: str, uploads: list, davidson_fast: bool) -> list:
    page_texts = []
    if paste.strip():
        page_texts.append(paste.strip())
    for upl in uploads or []:
        data = upl.getvalue()
        name = (upl.name or "").lower()
        if name.endswith(".pdf"):
            extracted = _bq_extract_pdf_text(data)
            if extracted:
                page_texts.append(extracted)
        elif name.endswith((".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp")):
            extracted = _bq_extract_image_text(data)
            if extracted:
                page_texts.append(extracted)
    if not page_texts:
        return []
    grouped = _bq_group_page_texts(page_texts)
    case_chunks = []
    for blob in grouped:
        case_chunks.extend(_bq_split_case_chunks(blob, davidson_fast))
    results = []
    seen = set()
    for chunk in case_chunks:
        parsed = _bq_parse_davidson_case(chunk, davidson_fast)
        if parsed.get("decedent") == "Unknown Decedent" and parsed.get("address") == "Address TBD":
            continue
        key = (
            (parsed.get("case_number") or "").upper(),
            (parsed.get("decedent") or "").lower(),
            (parsed.get("address") or "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        row = _bq_qualify_parsed(parsed)
        row["google_doc"] = _bq_google_doc_text(row)
        row["status"] = "Ready"
        results.append(row)
    results.sort(key=lambda r: (-r["sort_rank"], -r["score"], r.get("decedent", "")))
    return results


def _bq_push_row_to_branton(row: dict) -> bool:
    if row.get("tier") != "🔥 HOT" or row.get("status") == "Queued":
        return False
    parsed = dict(row.get("parsed") or {})
    parsed["raw"] = row.get("raw") or parsed.get("raw", "")
    heat_status, heat_pipeline = heat_from_import_block(parsed.get("raw", ""))
    if row.get("vacant_likely"):
        heat_pipeline = "🔥 Hot / New (call today)"
        heat_status = "New/Hot"
    scored = row.get("scored") or {}
    flags_txt = " · ".join(scored.get("flags") or [])
    notes_blob = (
        f"Bulk Qualifier • {row.get('tier')}\n"
        f"{row.get('reason')}\n\n"
        f"{parsed.get('raw', '')}\n\n"
        f"Phone: {parsed.get('phone') or '—'}\n{flags_txt}"
    ).strip()
    st.session_state.leads.insert(
        0,
        build_lead(
            parsed,
            pipeline_stage=heat_pipeline,
            status=heat_status,
            score=row.get("score", 75),
            source="bulk_qualifier",
            assigned_to_branton=True,
            follow_up_days=0,
            notes=initial_notes_from_block(notes_blob, source="Bulk Qualifier"),
        ),
    )
    row["status"] = "Queued"
    return True


# ══════════════════════════════════════════════════════════════════════════════
# TAB — Add New Leads (Bulk Qualifier)
# ══════════════════════════════════════════════════════════════════════════════
with tab_add_leads:
    st.session_state.setdefault("bq_results", [])
    st.session_state.setdefault("bq_pushed_flash", None)

    st.markdown(
        """
        <style>
        .bq-hero {
            background: linear-gradient(135deg, #0d2818 0%, #161b22 55%, #1a2332 100%);
            border: 1px solid #238636;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.85rem;
        }
        .bq-hero h3 { margin: 0 0 0.35rem 0; color: #e6edf3; font-size: 1.15rem; }
        .bq-hero p { margin: 0; color: #8b949e; font-size: 0.88rem; line-height: 1.5; }
        .bq-drop-hint {
            background: #161b22;
            border: 2px dashed #3fb950;
            border-radius: 12px;
            padding: 0.75rem 0.9rem;
            margin-bottom: 0.65rem;
            font-size: 0.86rem;
            color: #8b949e;
            line-height: 1.45;
        }
        .bq-btn-green-marker { display: none; }
        .bq-btn-green-marker + div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, #0d2818 0%, #238636 45%, #2ea043 100%) !important;
            border: 2px solid #3fb950 !important;
            color: #fff !important;
            font-weight: 800 !important;
            font-size: 1.08rem !important;
            min-height: 3.4rem !important;
        }
        .bq-poc-name { font-weight: 900 !important; color: #ffffff !important; }
        .bq-row-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 0.65rem 0.75rem;
            margin-bottom: 0.55rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="bq-hero">'
        "<h3>📋 Bulk Qualifier — Davidson County Destroyer</h3>"
        "<p>Drop 10–20 Caselink PDFs or screenshot pages, paste raw exports, "
        "qualify in seconds, one-click push 🔥 HOT cases to Branton.</p></div>",
        unsafe_allow_html=True,
    )

    davidson_fast = st.toggle(
        "⚡ Davidson Fast Mode",
        value=st.session_state.get("bq_davidson_fast", True),
        help="Optimized for 4–6 page Davidson petitions — merges pages, extracts decedent, heirs, RE, executor.",
        key="bq_davidson_fast",
    )

    st.markdown(
        '<div class="bq-drop-hint">'
        "<b>Drag &amp; drop zone</b> — upload multiple screenshots (4–6 pages per case), "
        "one multi-page Caselink PDF, or mix with pasted text below.</div>",
        unsafe_allow_html=True,
    )
    bq_uploads = st.file_uploader(
        "Drop cases here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "tif", "tiff", "bmp"],
        accept_multiple_files=True,
        key="bq_file_drop",
        label_visibility="collapsed",
    )

    bulk_raw = st.text_area(
        "Raw County Data",
        height=220,
        placeholder=(
            "Or paste raw text — court exports, CaseLink copy, pipe rows…\n\n"
            "Estate of Robert Smith, deceased\n"
            "PR 2024-0142\n"
            "4521 Main St, Nashville, TN 37214\n"
            "Davidson County\n"
            "Personal Representative: Jane Smith\n"
            "(615) 555-1212 · jane@email.com\n\n"
            "Separate multiple cases with blank lines…"
        ),
        key="bulk_data",
    )

    if st.session_state.pop("bq_pushed_flash", None):
        st.success(st.session_state.pop("_bq_last_push_msg", "🔥 Lead pushed to Branton's HOT queue."))
        st.balloons()

    bulk_flash = st.session_state.pop("bulk_qualify_flash", None)
    if bulk_flash:
        st.success(bulk_flash)

    st.markdown('<div class="bq-btn-green-marker"></div>', unsafe_allow_html=True)
    if st.button("🔥 Analyze All Cases & Qualify", use_container_width=True, type="primary", key="bq_analyze_all"):
        has_uploads = bool(bq_uploads)
        has_paste = bool(bulk_raw.strip())
        if not has_uploads and not has_paste:
            st.warning("Drop PDFs/screenshots or paste raw county data first.")
        else:
            results = _bq_analyze_inputs(bulk_raw, bq_uploads or [], davidson_fast)
            st.session_state.bq_results = results
            hot_n = sum(1 for r in results if r.get("tier") == "🔥 HOT")
            warm_n = sum(1 for r in results if r.get("tier") == "🔥 Warm")
            if results:
                st.session_state.bulk_qualify_flash = (
                    f"🔥 **{len(results)}** cases analyzed — **{hot_n}** HOT · **{warm_n}** Warm "
                    f"(sorted HOT first)"
                )
            else:
                st.session_state.bulk_qualify_flash = (
                    "No cases parsed — try Davidson Fast Mode, a clearer PDF, or paste the petition text."
                )
            st.rerun()

    bq_results = st.session_state.get("bq_results", [])
    if bq_results:
        hot_n = sum(1 for r in bq_results if r.get("tier") == "🔥 HOT")
        warm_n = sum(1 for r in bq_results if r.get("tier") == "🔥 Warm")
        st.markdown(f"**Results** — {len(bq_results)} cases · **{hot_n}** HOT · **{warm_n}** Warm")

        for idx, row in enumerate(bq_results):
            tier = row.get("tier", "Skip")
            tier_color = "#3fb950" if tier == "🔥 HOT" else ("#d29922" if tier == "🔥 Warm" else "#8b949e")
            st.markdown(
                f'<div class="bq-row-card">'
                f'<span style="color:{tier_color};font-weight:800;">{html.escape(tier)}</span>'
                f' · <b>{html.escape(row.get("case_number", "—"))}</b>'
                f' · {html.escape(row.get("decedent", "—"))}'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"### {row.get('poc_display', '**Contact TBD**')}")

            tbl = st.data_editor(
                [{
                    "Property Address": row.get("address", "—"),
                    "Death/Filing Date": row.get("death_filing", "—"),
                    "Score Reason": f"{tier} — {row.get('reason', '')}",
                    "Status": row.get("status", "Ready"),
                }],
                column_config={
                    "Property Address": st.column_config.TextColumn("Property Address", disabled=True),
                    "Death/Filing Date": st.column_config.TextColumn("Death/Filing Date", disabled=True),
                    "Score Reason": st.column_config.TextColumn("Score + Reason", disabled=True),
                    "Status": st.column_config.TextColumn("Status", disabled=True),
                },
                disabled=["Property Address", "Death/Filing Date", "Score Reason", "Status"],
                hide_index=True,
                use_container_width=True,
                key=f"bq_row_tbl_{idx}",
            )

            with st.expander("📄 Ready Google Doc text — copy", expanded=False):
                st.code(row.get("google_doc", ""), language="text")

            if tier == "🔥 HOT" and row.get("status") != "Queued":
                if st.button(
                    "✅ Push to Branton's HOT Queue",
                    key=f"bq_push_{idx}",
                    use_container_width=True,
                    type="primary",
                ):
                    if _bq_push_row_to_branton(row):
                        persist_leads()
                        st.session_state.bq_results = bq_results
                        st.session_state.bq_pushed_flash = True
                        st.session_state._bq_last_push_msg = (
                            f"🔥 **{row.get('decedent')}** pushed to {PARTNER_NAME}'s HOT queue — "
                            "Dashboard → Branton Call Mode."
                        )
                        st.rerun()
            elif row.get("status") == "Queued":
                st.caption("✅ Queued on Dashboard")
            else:
                st.caption("Warm/Skip — review Google Doc text; only 🔥 HOT rows push to queue.")

            st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TAB — Dashboard / CRM (default)
# ══════════════════════════════════════════════════════════════════════════════
with tab_dashboard:
    _flush_all_dash_notes_in_session(show_saved=False)
    if st.session_state.pop("_notes_loaded_banner_pending", False):
        st.success("✅ All notes loaded safely")


    st.session_state.setdefault("branton_call_mode", False)
    st.session_state.setdefault("call_mode_panel", {})

    if st.session_state.branton_call_mode:
        hdr_l, hdr_r = st.columns([2, 1])
        with hdr_l:
            st.markdown("## 📞 Branton Call Mode")
            st.caption("Focus only — hottest Crusher leads. Call, text, move pipeline.")
        with hdr_r:
            st.button(
                "Exit Call Mode — Back to Full System",
                key="exit_call_mode",
                use_container_width=True,
                on_click=_exit_branton_call_mode,
            )

        st.markdown('<div class="call-mode-paste-marker"></div>', unsafe_allow_html=True)
        call_paste = st.text_area(
            "Quick paste — push hottest to your queue",
            height=140,
            placeholder="Paste court batch here…",
            key="call_mode_paste",
            label_visibility="collapsed",
        )
        if st.button("🚀 Push Hottest", key="call_mode_push", use_container_width=True, type="primary"):
            if not call_paste.strip():
                st.warning("Paste leads first.")
            else:
                rows = crusher_score_batch(call_paste)
                added = crusher_push_to_call_queue(rows)
                vacant_n = sum(1 for r in rows if r.get("vacant_likely"))
                record_crusher_vacant_flags(vacant_n)
                st.success(f"✅ Pushed **{added}** hottest leads to queue.")
                st.rerun()

        hot_leads = get_branton_call_mode_leads(get_leads(), limit=10)
        if not hot_leads:
            st.info("No hot leads yet — paste above and tap **Push Hottest**, or use the Crusher tab.")
        for lead in hot_leads:
            vacant = lead.get("vacant_likely")
            card_class = "call-mode-lead-card call-mode-vacant" if vacant else "call-mode-lead-card"
            fire = " 🔥 Likely Vacant" if vacant else ""
            st.markdown(
                f'<div class="{card_class}">'
                f'<p class="call-mode-lead-title">{html.escape(lead.get("decedent", "Unknown"))}{fire}</p>'
                f'<p style="color:#8b949e;margin:0;font-size:0.9rem;">'
                f'{html.escape(lead.get("address", "—"))}</p>'
                f'<p style="color:#3fb950;margin:0.35rem 0 0 0;font-weight:700;">'
                f'{html.escape(_lead_call_line(lead))}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="call-mode-thumb-start"></div>', unsafe_allow_html=True)
            b1, b2, b3, b4, b5, b6 = st.columns(6)
            lid = lead["id"]
            with b1:
                st.button("Call Script", key=f"cm_script_{lid}", use_container_width=True, on_click=_call_mode_show_script, args=(lid,))
            with b2:
                st.button("Send Roadmap", key=f"cm_road_{lid}", use_container_width=True, on_click=_call_mode_show_roadmap, args=(lid,))
            with b3:
                st.button("Mark Contacted", key=f"cm_cont_{lid}", use_container_width=True, on_click=_call_mode_mark_contacted, args=(lid,))
            with b4:
                st.button("Appt Set", key=f"cm_appt_{lid}", use_container_width=True, on_click=_call_mode_set_stage, args=(lid, "Appointment Set", "Qualified", "Appt Set"))
            with b5:
                st.button("Listed", key=f"cm_list_{lid}", use_container_width=True, on_click=_call_mode_set_stage, args=(lid, "Listed / Under Contract", "Under Contract", "Listed"))
            with b6:
                st.button("Closed", key=f"cm_close_{lid}", use_container_width=True, on_click=_call_mode_set_stage, args=(lid, "Closed / Sold", "Closed", "Closed"))

            panel = st.session_state.get("call_mode_panel") or {}
            if panel.get("lead_id") == lid:
                if panel.get("type") == "script":
                    st.text_area("Call Script", generate_phone_script(lead_to_parsed_dict(lead)), height=320, key=f"cm_script_txt_{lid}")
                elif panel.get("type") == "roadmap":
                    st.text_area("Send Roadmap (copy & text/email)", generate_roadmap_message(lead), height=220, key=f"cm_road_txt_{lid}")

    if not st.session_state.branton_call_mode:
        st.markdown('<div class="call-mode-enter-marker"></div>', unsafe_allow_html=True)
        st.button(
            "📞 Branton Call Mode — Focus Only",
            key="enter_call_mode",
            use_container_width=True,
            type="primary",
            on_click=_enter_branton_call_mode,
        )

        st.session_state.setdefault("crm_list_mode", "all")
        st.session_state.setdefault("crm_pipe_filter", "All")

        st.markdown('<div class="crm-top-filters-start"></div>', unsafe_allow_html=True)
        due_col, _ = st.columns([1, 4], gap="small")
        with due_col:
            st.button(
                "📅 Do Today",
                key="crm_due_today_btn",
                use_container_width=True,
                type="primary",
                on_click=_set_due_today_list_mode,
            )

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

        render_income_goal_crusher(get_leads())

        st.markdown("---")
        st.markdown('<div class="export-notes-marker"></div>', unsafe_allow_html=True)
        st.download_button(
            label="📥 Export All Notes to CSV",
            data=build_notes_export_csv(get_leads()),
            file_name=f"probate_notes_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="export_all_notes_csv",
        )

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
                pipe_filter = st.selectbox(
                    "Pipeline",
                    ["All"] + PIPELINE_STAGES,
                    key="crm_pipe_filter",
                    on_change=_on_top_pipe_filter_change,
                )
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

            if st.session_state.get("crm_list_mode") == "due_today":
                list_base = list(st.session_state.leads)
                if branton_filter == f"Assigned to {PARTNER_NAME}":
                    list_base = [l for l in list_base if l.get("assigned_to_branton")]
                elif branton_filter == "Unassigned":
                    list_base = [l for l in list_base if not l.get("assigned_to_branton")]
                if county_filter != "All":
                    list_base = [l for l in list_base if l.get("county") == county_filter]
                list_filtered = _filter_leads_due_today(list_base)
            else:
                list_filtered = filtered

            filter_bits = []
            if st.session_state.get("crm_list_mode") == "due_today":
                filter_bits.append("due today + 🔥 Hot")
            elif pipe_filter != "All":
                filter_bits.append(pipe_filter)
            filter_note = f" · List: **{', '.join(filter_bits)}**" if filter_bits else ""
            st.caption(
                f"Showing **{len(list_filtered)}** in list / **{len(filtered)}** matched / "
                f"**{len(st.session_state.leads)}** total{filter_note}"
            )

            if not list_filtered:
                st.info(
                    "No leads match the current filter. "
                    "Set **Pipeline** to **All** to show every lead, or tap **📅 Do Today** for today's calls."
                )
            else:
                list_ids = {l["id"] for l in list_filtered}
                if st.session_state.get("crm_selected_lead_id") not in list_ids:
                    _flush_dash_notes(st.session_state.get("crm_selected_lead_id"), show_saved=True)
                    st.session_state.crm_selected_lead_id = list_filtered[0]["id"]
                    st.session_state.pop("_dash_notes_sync_id", None)

                list_col, detail_col = st.columns([2, 3], gap="medium")

                with list_col:
                    st.markdown("**Leads**")
                    with st.container(height=520):
                        for item in list_filtered:
                            is_selected = st.session_state.get("crm_selected_lead_id") == item["id"]
                            _render_lead_primary_contact(item)
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
                    if not lead:
                        st.markdown("#### Lead Detail & Edit")
                        st.info("Select a lead from the list.")
                    else:
                        _render_lead_primary_contact(lead, detail=True)
                        st.markdown("#### Lead Detail & Edit")
                        e1, e2, e3, e4 = st.columns([3, 2, 2, 1])
                        current_stage = detail_pipeline_stage(lead)
                        with e1:
                            new_stage = st.selectbox(
                                "Pipeline Stage",
                                DETAIL_PIPELINE_STAGES,
                                index=DETAIL_PIPELINE_STAGES.index(current_stage),
                                key=f"stage_{lead['id']}",
                                on_change=_on_detail_pipeline_change,
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
                            f"Score **{lead.get('score', 0)}** · {lead.get('county', '—')}"
                        )

                        note_text = st.text_area(
                            "Add Note",
                            key=f"note_{lead['id']}",
                            placeholder="Call outcome, heir feedback, next steps...",
                        )
                        b1, b2, b3, b4 = st.columns(4)
                        with b1:
                            if st.button("💾 Save Changes", key=f"save_{lead['id']}", use_container_width=True, type="primary"):
                                _flush_dash_notes(lead["id"], show_saved=True)
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
                                _flush_dash_notes(lead["id"], show_saved=True)
                                log_call(lead["id"])
                                st.rerun()
                        with b3:
                            if st.button("⬆️ → Warm", key=f"warm_{lead['id']}", use_container_width=True):
                                _flush_dash_notes(lead["id"], show_saved=True)
                                update_lead(lead["id"], pipeline_stage="Warm / Talking", status="Contacted")
                                st.rerun()
                        with b4:
                            if st.button("🗑️ Remove", key=f"del_{lead['id']}", use_container_width=True):
                                _flush_dash_notes(lead["id"], show_saved=True)
                                st.session_state.leads = [l for l in st.session_state.leads if l["id"] != lead["id"]]
                                persist_leads()
                                st.session_state.pop("crm_selected_lead_id", None)
                                st.session_state.pop("_dash_notes_sync_id", None)
                                st.rerun()

                        _render_lead_notes_editor(lead)
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
# TAB — 💰 90-Day Probate Crusher
# ══════════════════════════════════════════════════════════════════════════════
with tab_crusher:
    st.markdown('<p class="crusher-title">💰 90-Day Probate Crusher</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="crusher-hero-callout">'
        "🔥 <strong>Vacant Scorer:</strong> Compares <strong>PR address</strong> vs <strong>Property address</strong> "
        "(like Probate Mastery video). <strong>&gt;50 miles = Likely Vacant • High Motivation</strong>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Paste court exports, pipe-delimited rows, or raw PDF text — score vacant-motivation leads "
        f"and push the hottest straight to {PARTNER_NAME}'s call list."
    )

    crusher_flash = st.session_state.pop("crusher_flash", None)
    if crusher_flash:
        st.success(crusher_flash)

    st.markdown("### 📱 Smart Phone Finder + Vacant Scorer")
    st.markdown(
        '<div class="crusher-phone-hint">'
        "📱 <strong>Phone guesses</strong> = ready-to-search strings for <strong>BeenVerified / Google</strong>. "
        "Paste the <strong>🔥 leads only</strong> to save time."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="crusher-smart-glow-marker"></div>', unsafe_allow_html=True)
    crusher_smart_batch = st.text_area(
        "Paste any batch of leads here (raw court text, pipe-delimited, or names/addresses OK)",
        height=260,
        placeholder=(
            "Paste anything — names, addresses, PR lines, phones mixed in…\n\n"
            "Estate of Linda Davis | 890 Heritage Dr, Murfreesboro, TN 37129 | "
            "Tom Davis, PR | heir-phone-from-paste\n\n"
            "Estate of Robert Smith\n"
            "4521 Saundersville Rd, Mount Juliet, TN 37122\n"
            "Jane Smith, Personal Representative\n"
            "1420 Ocean Blvd, Jacksonville, FL 32250"
        ),
        key="crusher_smart_batch_text",
        label_visibility="visible",
    )

    st.markdown('<div class="crusher-mega-btn-marker"></div>', unsafe_allow_html=True)
    smart_enrich_btn = st.button(
        "🔍 Enrich Phones + Score Vacant + Push to Branton",
        use_container_width=True,
        type="primary",
        key="crusher_smart_enrich_btn",
    )

    if smart_enrich_btn:
        if not crusher_smart_batch.strip():
            st.warning("Paste a batch of leads first.")
        else:
            smart_rows = crusher_score_batch(crusher_smart_batch)
            st.session_state.crusher_smart_scored = smart_rows
            st.session_state.crusher_scored = smart_rows
            vacant_n = sum(1 for r in smart_rows if r.get("vacant_likely"))
            phone_n = sum(1 for r in smart_rows if r["parsed"].get("phone"))
            record_crusher_vacant_flags(vacant_n)
            st.session_state.crusher_flash = (
                f"📱 Enriched **{len(smart_rows)}** leads — **{phone_n}** with extracted phones, "
                f"**{vacant_n}** 🔥 Likely Vacant (PR > {VACANT_DISTANCE_MILES} mi)."
            )
            st.rerun()

    smart_scored = st.session_state.get("crusher_smart_scored") or []
    if smart_scored:
        smart_table = []
        for row in smart_scored:
            smart_table.append({
                "Decedent": row.get("name", "—"),
                "Property": (row.get("property") or "—")[:55],
                "PR Name": (row.get("pr") or "—")[:35],
                "Best Phone Guess(es)": (row.get("phone_display") or "—")[:80],
                "Distance": row.get("distance", "—"),
                "Score": row.get("score", 0),
                "🔥 Likely Vacant": row.get("vacant_label", "—"),
            })
        st.markdown("**Smart enrichment queue** — tap column headers to sort")
        st.dataframe(
            smart_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.NumberColumn("Score", format="%d"),
            },
        )
        vacant_smart = [r for r in smart_scored if r.get("vacant_likely")]
        if vacant_smart:
            st.markdown(
                f'<span class="crusher-vacant-pill">🔥 {len(vacant_smart)} Likely Vacant • High Motivation</span>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="crusher-mega-btn-marker"></div>', unsafe_allow_html=True)
    push_hottest_btn = st.button(
        "✅ Push All Hottest to Branton Queue",
        use_container_width=True,
        type="primary",
        key="crusher_push_hottest_btn",
    )
    if push_hottest_btn:
        rows = st.session_state.get("crusher_smart_scored") or st.session_state.get("crusher_scored") or []
        if not rows and crusher_smart_batch.strip():
            rows = crusher_score_batch(crusher_smart_batch)
            st.session_state.crusher_smart_scored = rows
            st.session_state.crusher_scored = rows
        if not rows:
            st.warning("Enrich & score a batch first — tap **🔍 Enrich Phones + Score Vacant + Push to Branton**.")
        else:
            added = crusher_push_to_call_queue(rows)
            if added:
                st.session_state.crusher_flash = (
                    f"✅ **{added}** hottest leads pushed to Branton's queue (sorted 🔥 vacant first). "
                    "Open **Dashboard → 📅 Do Today** to call."
                )
            else:
                st.session_state.crusher_flash = (
                    "No qualified leads to push — need decedent + property address at minimum."
                )
            st.rerun()

    crusher_kpi = compute_crusher_kpi_scorecard(get_leads())
    st.markdown('<div class="crusher-kpi-card">', unsafe_allow_html=True)
    st.markdown('<p class="crusher-kpi-title">📊 90-Day Crusher KPI Scorecard — This Week</p>', unsafe_allow_html=True)
    st.caption(f"Week of **{crusher_kpi['week_label']}** · Goal **{crusher_kpi['weekly_goal']}+** weekly points (Probate Mastery style)")
    st.markdown(
        f'<p class="crusher-kpi-points">{crusher_kpi["weekly_points"]} pts</p>',
        unsafe_allow_html=True,
    )
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Pipeline Adds", crusher_kpi["pipeline_adds"], help=f"+{CRUSHER_KPI_POINTS['pipeline_add']} pts each")
    k2.metric("Attorney Calls", crusher_kpi["attorney_calls"], help=f"+{CRUSHER_KPI_POINTS['attorney_call']} pts each")
    k3.metric("Content", crusher_kpi["content"], help=f"+{CRUSHER_KPI_POINTS['content']} pts each")
    k4.metric("🔥 Vacant Flags", crusher_kpi["vacant_flagged"], help=f"+{CRUSHER_KPI_POINTS['vacant_flag']} pts each")
    bd = crusher_kpi["point_breakdown"]
    st.caption(
        f"Points breakdown — Pipeline **{bd['pipeline']}** · Attorney **{bd['attorney']}** · "
        f"Content **{bd['content']}** · Vacant **{bd['vacant']}**"
    )
    kpi_data = load_crusher_kpi()
    ac1, ac2, cc1, cc2 = st.columns(4)
    with ac1:
        if st.button("➕ Attorney Call", key="crusher_kpi_attorney_plus", use_container_width=True):
            kpi_data["attorney_calls"] = int(kpi_data.get("attorney_calls", 0)) + 1
            save_crusher_kpi(kpi_data)
            st.rerun()
    with ac2:
        if st.button("➕ Content Post", key="crusher_kpi_content_plus", use_container_width=True):
            kpi_data["content"] = int(kpi_data.get("content", 0)) + 1
            save_crusher_kpi(kpi_data)
            st.rerun()
    with cc1:
        if st.button("↩️ Undo Attorney", key="crusher_kpi_attorney_minus", use_container_width=True):
            kpi_data["attorney_calls"] = max(0, int(kpi_data.get("attorney_calls", 0)) - 1)
            save_crusher_kpi(kpi_data)
            st.rerun()
    with cc2:
        if st.button("↩️ Undo Content", key="crusher_kpi_content_minus", use_container_width=True):
            kpi_data["content"] = max(0, int(kpi_data.get("content", 0)) - 1)
            save_crusher_kpi(kpi_data)
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔥 AI Vacant House Scorer")
    st.markdown('<div class="crusher-glow-marker"></div>', unsafe_allow_html=True)
    crusher_batch = st.text_area(
        "Paste batch of leads here (raw court text or pipe-delimited OK)",
        height=240,
        placeholder=(
            "Paste anything — tncrtinfo export, CaseLink dump, pipe rows, or PDF copy…\n\n"
            "Estate of Mary Johnson | 4521 Main St, Lebanon, TN 37087 | John Johnson, PR | PR2024-1234\n\n"
            "Estate of Robert Smith\n"
            "PR2024-5678\n"
            "4521 Saundersville Rd, Mount Juliet, TN 37122\n"
            "Jane Smith, Personal Representative\n"
            "1420 Ocean Blvd, Jacksonville, FL 32250"
        ),
        key="crusher_batch_text",
        label_visibility="visible",
    )

    score_col, ready_col = st.columns(2)
    with score_col:
        score_btn = st.button(
            "🚀 Score & Prioritize for Branton",
            use_container_width=True,
            type="primary",
            key="crusher_score_btn",
        )
    with ready_col:
        ready_btn = st.button(
            "✅ Ready for Branton",
            use_container_width=True,
            type="primary",
            key="crusher_ready_btn",
        )

    if score_btn:
        if not crusher_batch.strip():
            st.warning("Paste a batch of leads first.")
        else:
            st.session_state.crusher_scored = crusher_score_batch(crusher_batch)
            vacant_n = sum(1 for r in st.session_state.crusher_scored if r.get("vacant_likely"))
            record_crusher_vacant_flags(vacant_n)
            st.session_state.crusher_flash = (
                f"Scored **{len(st.session_state.crusher_scored)}** leads — "
                f"**{vacant_n}** flagged 🔥 Likely Vacant (PR > {VACANT_DISTANCE_MILES} mi from property)."
            )
            st.rerun()

    if ready_btn:
        rows = st.session_state.get("crusher_scored") or []
        if not rows and crusher_batch.strip():
            rows = crusher_score_batch(crusher_batch)
            st.session_state.crusher_scored = rows
        if not rows:
            st.warning("Score a batch first — tap **🚀 Score & Prioritize for Branton**.")
        else:
            added = crusher_push_to_call_queue(rows)
            if added:
                st.session_state.crusher_flash = (
                    f"✅ **{added}** leads pushed to the top of Branton's call queue "
                    f"(🔥 vacant + qualified first). Open **Dashboard → 📅 Do Today** to start calling."
                )
            else:
                st.session_state.crusher_flash = (
                    "No qualified leads found — need decedent + property address at minimum."
                )
            st.rerun()

    scored_rows = st.session_state.get("crusher_scored") or []
    if scored_rows:
        table_rows = []
        for row in scored_rows:
            name_cell = row["name"]
            if row.get("vacant_likely"):
                name_cell += " 🔥"
            table_rows.append({
                "Name": name_cell,
                "Property": (row.get("property") or "—")[:60],
                "PR": (row.get("pr") or "—")[:40],
                "Distance": row.get("distance", "—"),
                "Score": row.get("score", 0),
                "Action": row.get("action", "—"),
            })
        st.markdown("**Priority queue** — tap column headers to sort")
        st.dataframe(
            table_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.NumberColumn("Score", format="%d"),
            },
        )
        vacant_top = [r for r in scored_rows if r.get("vacant_likely")]
        if vacant_top:
            st.markdown(
                f'<span class="crusher-vacant-pill">🔥 {len(vacant_top)} Likely Vacant • High Motivation</span>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("### 📋 Bulk Qualifier Upgrade")
    st.caption(
        "Same paste box above accepts **court PDF text**, **pipe/tab rows**, or **one lead per blank line**. "
        "We auto-extract decedent, property, PR name, phone, email, and case #."
    )
    if scored_rows:
        preview = scored_rows[:8]
        for row in preview:
            p = row["parsed"]
            st.markdown(
                f"**{p.get('decedent', '—')}** · {p.get('address', '—')[:50]}  \n"
                f"PR: {row.get('pr', '—')} · Case: {p.get('case_number') or '—'} · "
                f"📞 {p.get('phone') or '—'} · ✉️ {p.get('email') or '—'}"
            )
    else:
        st.info("Paste a batch above and tap **🚀 Score & Prioritize** to preview extracted fields.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Partner Kit
# ══════════════════════════════════════════════════════════════════════════════
with tab_partner:
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
        10. Save our line: **{DEDICATED_PHONE_LINE}**

        > **Golden Rule (Aaron Novello):** You're not calling to sell. You're calling to help a family
        > in pain make a good decision. The deals follow the compassion. Every time.
        """
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Vendors Rolodex
# ══════════════════════════════════════════════════════════════════════════════
with tab_vendors:
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
        save_vendors(st.session_state.vendors)
        st.success("✅ Vendor Rolodex saved — all Guardian Kits will reflect these contacts.")

def _render_training_swipe_section(title: str, scripts: list) -> None:
    """One swipe category — label, attribution, copy-paste body."""
    with st.expander(title, expanded=False):
        for label, attribution, body in scripts:
            st.markdown(f"**{label}** · *{attribution}*")
            st.code(body.strip(), language=None)


TRAINING_SWIPE_FILES = [
    (
        "📞 Call Scripts by Stage",
        [
            (
                "Stage 1 — First Contact (Cold)",
                "Aaron Novello + David Pannell",
                """Hi, is this [Heir Name]?

Hey [Heir Name], my name is [Your Name] — I'm a local Realtor here in Middle Tennessee with eXp Realty. First, I want to say I'm truly sorry for your loss. I know this is probably the last call you want right now.

I realize I may be reaching out a little early, and I want to do that very respectfully. Nothing needs to happen today — I'm not calling with an agenda.

I came across the probate filing for [Decedent]'s property at [Address] in [County]. I simply wanted to introduce myself as a local resource — so when questions come up, you have someone in your corner who does this every day.

Before I share how I might help — if you don't mind me asking — what's been the hardest part of all this so far?

[STOP. Listen. Use "Tell me more about that" 2–3 times.]""",
            ),
            (
                "Stage 2 — Warm / Nurture (Call Back)",
                "Rick Yen + David Pannell",
                """Hi [Heir Name], it's [Your Name] — we spoke briefly about [Decedent]'s property at [Address]. I hope things have been a little easier this week.

I wasn't calling to push anything — just checking in. Has anything changed with the estate or the property since we last talked?

Help me understand — where are you in the process right now? Attorney engaged? Letters issued? Still sorting things out?

If it would help, I can still put together a free Equity Snapshot / Net Sheet — real numbers, not a Zillow guess — whenever you're ready. No pressure, no timeline.

Would a quick 10-minute call later this week make sense, or is now still too early?""",
            ),
            (
                "Stage 3 — Appointment Set Confirmation",
                "Aaron Novello",
                """Hi [Heir Name], [Your Name] here — confirming our [walk-through / Zoom] on [Day] at [Time] for [Address].

I'll bring a complimentary Equity Snapshot — what the estate would actually NET after debts, closing costs, and repairs. No obligation.

Quick prep that helps me serve you better:
• How many heirs are involved?
• Is the property vacant or occupied?
• Any known mortgage, liens, or estate debts?
• Is your probate attorney already involved?

If anything changes, just call or text (615) 669-7075. Looking forward to helping your family get clarity.""",
            ),
            (
                "Stage 4 — Post-Appointment / Net Sheet Delivery",
                "Rick Yen + Jose",
                """Hi [Heir Name], [Your Name] here — thank you again for your time at [Address].

As promised, I'm sending your Equity Snapshot / Net Sheet today. This shows what the estate could realistically net across your main options — traditional listing, Express Offers, or as-is — subject to court approval.

Three paths most families consider:
1. List traditionally — funded repairs available, zero out of pocket before close
2. Express Offers — multiple vetted cash buyers compete, as-is, fast certainty
3. Hold / rent / sibling buyout — we can run those numbers too

No decision needed today. What questions came up after you reviewed the numbers?

May I make a suggestion? Would it help to walk through this with your attorney on a brief 3-way call?""",
            ),
            (
                "Stage 5 — Listed / Under Contract Check-in",
                "Bruce & Heath + Jose",
                """Hi [Heir Name], [Your Name] checking in on [Address].

Quick status for your file:
• Marketing / showings: [status]
• Vendor coordination: [estate sale / cleanout / lawn / lockbox — as applicable]
• Attorney loop-in: [done / scheduled]
• Target timeline: subject to court approval

You focus on family — we handle the heavy lifting. Anything worrying you that I should address today?

I'll keep you updated at every milestone. Call or text (615) 669-7075.""",
            ),
        ],
    ),
    (
        "🛡️ Objection Handlers",
        [
            (
                "We already have an attorney",
                "Aaron Novello + Jose",
                """Perfect — that's exactly who should be handling the legal piece. I work alongside probate attorneys every day; I handle the property side only.

I never give legal advice — I defer everything to their office. My job is to make sure when you're ready to sell, you have real numbers, vetted vendors, and a clear path — subject to court approval.

Tell me more about where they are in the process — have letters been issued yet?""",
            ),
            (
                "We're not ready to sell",
                "David Pannell + Aaron Novello",
                """Totally understand — and you shouldn't feel rushed. Most families I work with aren't ready on call one either.

Can I make a suggestion? Let me send a free Net Sheet / Equity Snapshot so when you ARE ready — next month or next year — you're not starting from zero or trusting a Zillow guess.

No strings, no follow-up pressure. Would that be helpful?""",
            ),
            (
                "It's too early",
                "Aaron Novello",
                """That's exactly why I'm calling early — so you have a resource before you need one. Very respectfully, zero timeline.

I'm not asking you to decide anything. I just want you to know there's a local specialist who handles probate property every day in [County] when questions come up.

Can I stay in touch lightly — maybe one check-in in a few weeks?""",
            ),
            (
                "We already have a price in mind",
                "Rick Yen",
                """Tell me more about that — where did that number come from?

I'd love to see if the Net Sheet aligns. Sometimes estates are pleasantly surprised; sometimes the number includes costs they haven't accounted for yet. Either way, good information.

The only way to know what the estate actually nets is to run the real math — debts, closing costs, repairs, commissions. Happy to do that free whenever you're ready.""",
            ),
            (
                "We already have a Realtor / agent",
                "David Pannell",
                """Good — it sounds like you're taking this seriously. I'm not here to step on anyone's toes.

I specialize in probate — Net Sheets, heir coordination, estate sales, Express Offers, Muniment paths, court timelines. If your current agent doesn't do probate every week, happy to be a second opinion — free, no obligation.

If you're all set, I respect that completely. Can I ask — have they walked you through what you'd NET, not just list price?""",
            ),
            (
                "Don't call again / not interested",
                "Aaron Novello",
                """I completely respect that — and I'm sorry if the timing was wrong.

I'll make a note not to reach out by phone. If it's okay, I'd love to send one email with a free Net Sheet template and a vendor list — something useful if things change down the road. Totally fine if not.

Thank you for your time, and again, I'm sorry for your loss.""",
            ),
            (
                "Property needs too much work",
                "Bruce & Heath + Rick Yen",
                """That's more common than you'd think — and it's exactly why families use a Project Coordinator.

We handle the heavy lifting: estate sale, junk removal, cleaning, lockbox, lawn, utilities — and funded repairs so you're not paying out of pocket before close.

Or, if speed matters more than top dollar, Express Offers brings multiple as-is cash buyers — you compare, not one lowball. Subject to court approval either way.

Would it help to see both numbers side by side?""",
            ),
            (
                "Siblings don't agree",
                "Jose + Aaron Novello",
                """That's one of the hardest parts — and more common than people admit.

Tell me more about that. How many heirs? Does anyone want to buy out the others? Anyone out of state?

I can run buyout math and present neutral Net Sheet options so everyone works from the same facts — not emotions. Sometimes one short call with all parties saves months of conflict.

Would a neutral third-party walkthrough help — or should I call or text (615) 669-7075?""",
            ),
        ],
    ),
    (
        "🔀 Transition Scripts (Probate Help → Real Estate Options)",
        [
            (
                "From sympathy → discovery",
                "Rick Yen",
                """I appreciate you sharing that — it sounds like [mirror their words].

Help me understand — walk me through where things stand with the estate right now. What's your role — executor, beneficiary, or helping a family member?

Who else is involved in the decision? I'd love the full picture so I'm not speaking out of turn.""",
            ),
            (
                "From overwhelmed → Project Coordinator",
                "Jose + Bruce & Heath",
                """It sounds like there's a lot on your plate — property, paperwork, family, and grief all at once.

Here's what a lot of families find helpful: one Project Coordinator who handles the property heavy lifting — estate sale, cleanout, vendors, lockbox, utilities, showings or cash offers — while you focus on family and what your attorney needs.

You don't have to figure it all out today. Would it help if I mapped what that would look like for [Address] — free, no obligation?""",
            ),
            (
                "From 'just clearing the estate' → sale options",
                "David Pannell + Aaron Novello",
                """That makes sense — most families start with 'we just need to clear it out' and then realize they need real numbers before anyone can agree.

Once contents are handled, there are usually three paths:
• Traditional listing — top dollar, funded repairs available
• Express Offers — as-is, multiple cash buyers, fast certainty
• Sibling buyout — one heir keeps it, others take cash

All subject to court approval. Want me to show you what each path looks like in dollars for this estate?""",
            ),
            (
                "From legal process → property readiness",
                "Jose",
                """While your attorney handles court authority, there are things we can prepare now so you're not losing months later:

• Equity Snapshot / Net Sheet — so heirs agree on facts
• Property walkthrough — condition, repairs, as-is value
• Vendor quotes — estate sale, cleanout, lawn, insurance for vacant home
• Timeline map — what happens after letters testamentary

I never market before your attorney confirms authority to sell. I just get you ready. Make sense?""",
            ),
            (
                "From curiosity → appointment",
                "Aaron Novello",
                """I'm not asking you to decide anything today.

May I make a suggestion?

Would a brief 10-to-15-minute call — or a quick walk-through if you're local — make sense, just to leave you with a free Equity Snapshot? No pressure, no commitment.

What works better — [Day A] or [Day B]?""",
            ),
        ],
    ),
    (
        "📦 Guardian Kit Templates",
        [
            (
                "Text — send with Guardian Kit link/PDF",
                "Bruce & Heath + Scott Hardesty",
                """Hi [Heir Name], [Your Name] here — as promised, here's your Guardian Kit for [Decedent]'s property at [Address].

Inside you'll find:
✓ Your personalized vendor rolodex (attorney, estate sale, cleanout, cash buyers)
✓ Property path options — list, Express Offers, Muniment, buyout
✓ What to expect timeline — subject to court approval
✓ Call or text (615) 669-7075

No obligation — built so your family has one clear resource. Questions? Just reply here.""",
            ),
            (
                "Email subject lines",
                "David Pannell",
                """Guardian Kit — Estate of [Decedent] · [Address]
Your Free Probate Property Resource Kit — [County]
[Decedent] Property — Vendor List + Options (No Obligation)
Equity Snapshot Request — Estate of [Decedent]""",
            ),
            (
                "Voicemail — no answer (first touch)",
                "Aaron Novello",
                """Hi [Heir Name], this is [Your Name] with eXp Realty in Middle Tennessee. I'm sorry for your loss — I know this is a difficult time.

I'm reaching out very respectfully about [Decedent]'s property at [Address]. No agenda, no pressure — I simply help probate families with property questions, Net Sheets, and vendor coordination.

I'll try you once more, or feel free to call or text (615) 669-7075. Again, I'm sorry for your loss.""",
            ),
            (
                "Voicemail — follow-up after speaking",
                "Rick Yen",
                """Hi [Heir Name], [Your Name] again — we spoke briefly about [Address]. Just following up on the free Equity Snapshot I mentioned.

Happy to keep this simple — 10 minutes, your questions answered, no obligation. Call or text (615) 669-7075 when it's convenient. Thanks, [Heir Name].""",
            ),
            (
                "Guardian Kit intro — live on call",
                "Jose + Bruce & Heath",
                """What I'd like to put together for you is something we call a Guardian Kit — think of it as a probate property playbook for your family.

It includes your vendor contacts, every sale path explained in plain English, funded repair options, Express Offers if you want speed, and a timeline map — all subject to court approval.

It's free, there's no obligation, and it gives everyone involved the same information. Would that be helpful?""",
            ),
        ],
    ),
    (
        "📅 Follow-up Sequences",
        [
            (
                "3-Touch Minimum — Day 0 / 2 / 7",
                "Aaron Novello + David Pannell",
                """TOUCH 1 — Day 0 (First call)
Respectful opener → empathy → discovery → "May I make a suggestion?" → schedule or soft close.

TOUCH 2 — Day 2 (Follow-up call or VM)
"Hi [Heir], [Your Name] — just checking in on [Address]. No pressure — did any questions come up since we talked? Happy to send the free Net Sheet if helpful — (615) 669-7075."

TOUCH 3 — Day 7 (Value add)
"Hi [Heir], following up one last time for now. I put together [Guardian Kit / vendor list / market snapshot for County] — want me to send it? Either way, I'm here when your family is ready."

[Log every touch on Dashboard. Set nurture follow-up date if not ready.]""",
            ),
            (
                "Nurture — monthly light touch (90 days)",
                "David Pannell",
                """Hi [Heir Name], [Your Name] — hope the estate process is moving along.

No agenda — just wanted you to know I'm still here if property questions come up on [Address]. Market in [County] has shifted slightly since we last spoke — happy to refresh your Net Sheet free if useful.

Reply STOP anytime and I'll only check in quarterly. Take care.""",
            ),
            (
                "Post–Net Sheet — 48-hour follow-up",
                "Rick Yen",
                """Hi [Heir Name], did you get a chance to look at the Net Sheet for [Address]?

What questions came up? Sometimes the heir numbers surprise people — happy to walk through line by line.

If siblings need to see it too, I can join a short group call — neutral facts, less arguing. When works for you?""",
            ),
            (
                "Attorney loop-in — after heir engagement",
                "Jose",
                """Subject: Property Coordination — Estate of [Decedent] · [Address]

Dear [Attorney Name],

Thank you for handling the legal side for the [Decedent] estate. [Heir Name] asked me to coordinate the property piece.

I will not market or show the property until you confirm authority to sell. Attached/linked: proposed listing timeline, Net Sheet, and vendor list for your file.

Please let me know if you need anything from me. Call or text (615) 669-7075.""",
            ),
            (
                "Long-term check-in — 6+ months",
                "Aaron Novello",
                """Hi [Heir Name], [Your Name] — it's been a while since we spoke about [Address].

Totally understand probate timelines vary. If the property is still on your plate, I'm happy to refresh your numbers — no cost, no pressure.

If you've already moved forward with someone else, congrats — and I'm glad your family got taken care of. If not, I'm still here — (615) 669-7075.""",
            ),
        ],
    ),
    (
        "🎯 Positioning Language",
        [
            (
                "Project Coordinator — core positioning",
                "Jose + Bruce & Heath",
                """I work as a Project Coordinator for probate families — not just a listing agent.

That means one call and we handle: Net Sheet, estate sale, contents removal, cleaning, lockbox, utilities, lawn, showings or Express Offers, and attorney coordination — subject to court approval.

You focus on family and grief. We handle the heavy lifting.""",
            ),
            (
                "Probate specialist — David Pannell frame",
                "David Pannell",
                """I specialize in probate real estate — it's the only niche I focus on in Middle Tennessee.

That means I understand court timelines, heir dynamics, Muniment of Title paths, sibling buyouts, and how to net the estate — not just get a list price.

I'm not calling to sell you anything today. I'm calling to see if I can be your property resource while your attorney handles the legal piece.""",
            ),
            (
                "Court approval — always say it",
                "Jose + Aaron Novello",
                """Use in every timeline, offer, and close:

"Subject to court approval."

"Your attorney will confirm when we have authority to market."

"We won't list or accept offers until your attorney gives the green light."

"Timeline depends on court — I'll coordinate with their office every step." """,
            ),
            (
                "Not a salesperson — compassion first",
                "Aaron Novello",
                """You're not calling to sell. You're calling to help a family in pain make a good decision.

"I realize I may be reaching out a little early — very respectfully."

"Nothing needs to happen today."

"Tell me more about that." [Use 2–3 times — then stop talking.]

The deals follow the compassion. Every time.""",
            ),
            (
                "Price anchoring without quoting",
                "Rick Yen",
                """In [County], similar homes can range from $[LOW] as-is to $[HIGH] updated — but that's from the outside without walking through.

I wouldn't trust an online estimate on a probate property anyway — every heir situation is different.

The only number that matters is what the estate NETS after debts, costs, and repairs. That's the Equity Snapshot — free, whenever you're ready.""",
            ),
            (
                "Express Offers — speed positioning",
                "Bruce & Heath + eXp",
                """Express Offers through eXp brings multiple vetted cash buyers — you compare, not one lowball.

Zero repairs, zero showings, close in as little as 14 days — subject to court approval.

Perfect when heirs live out of state, the property needs work, or the family wants certainty over top dollar.""",
            ),
            (
                "Partnership with Scott — escalation",
                "Scott Hardesty team",
                """For anything complex — sibling disputes, buyout math, competing agents, $500K+ estates, or attorney conflicts — Scott Hardesty jumps in directly.

Call or text (615) 669-7075

You never have to figure out the hard stuff alone.""",
            ),
        ],
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# TAB — Newspaper Scraper • Small Counties (isolated)
# ══════════════════════════════════════════════════════════════════════════════
with tab_newspaper:
    st.session_state.setdefault("ns_scraper_raw", "")
    st.session_state.setdefault("ns_scraper_results", [])
    st.session_state.setdefault("ns_preselect_high", False)
    st.session_state.setdefault("ns_json_visible", False)
    st.session_state.setdefault("ns_pipeline_ran", False)

    _NS_SCORE_BADGE = {"High": "🔥 HIGH", "Med": "● MED", "Low": "○ LOW"}
    _NS_SCORE_PILL = {
        "High": '<span class="ns-pill ns-pill-high">🔥 HIGH</span>',
        "Med": '<span class="ns-pill ns-pill-med">● MED</span>',
        "Low": '<span class="ns-pill ns-pill-low">○ LOW</span>',
    }

    st.markdown(
        """
        <style>
        .ns-shell { margin-bottom: 0.5rem; }
        .ns-quicklinks {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 0.7rem 0.85rem;
            margin-bottom: 0.8rem;
            font-size: 0.86rem;
            line-height: 1.6;
            word-break: break-word;
        }
        .ns-quicklinks a { color: #58a6ff; font-weight: 700; text-decoration: none; }
        .ns-quicklinks a:hover { text-decoration: underline; }
        .ns-hero {
            background: linear-gradient(135deg, #0d2818 0%, #161b22 55%, #1a2332 100%);
            border: 1px solid #238636;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.8rem;
        }
        .ns-hero h3 { margin: 0 0 0.35rem 0; color: #e6edf3; font-size: 1.15rem; }
        .ns-hero p { margin: 0; color: #8b949e; font-size: 0.88rem; line-height: 1.5; }
        .ns-agent-bar {
            background: #161b22;
            border-left: 3px solid #58a6ff;
            border-radius: 8px;
            padding: 0.65rem 0.8rem;
            margin-bottom: 0.8rem;
            font-size: 0.84rem;
            color: #c9d1d9;
            line-height: 1.45;
        }
        .ns-paste-shell {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 1rem 1.05rem;
            margin-bottom: 0.7rem;
        }
        .ns-paste-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #e6edf3;
            margin-bottom: 0.4rem;
        }
        .ns-paste-sub {
            font-size: 0.82rem;
            color: #8b949e;
            margin-bottom: 0.5rem;
            line-height: 1.45;
        }
        .ns-btn-green-marker { display: none; }
        .ns-btn-green-marker + div[data-testid="stButton"] > button {
            background: linear-gradient(135deg, #0d2818 0%, #238636 45%, #2ea043 100%) !important;
            border: 2px solid #3fb950 !important;
            color: #fff !important;
            font-weight: 800 !important;
            font-size: 1.05rem !important;
            min-height: 3.4rem !important;
        }
        .ns-results-title {
            font-size: 1rem;
            font-weight: 700;
            color: #e6edf3;
            margin: 0.65rem 0 0.4rem 0;
        }
        .ns-badge-row {
            display: flex; flex-wrap: wrap; gap: 0.4rem;
            margin-bottom: 0.55rem;
        }
        .ns-pill {
            display: inline-block;
            padding: 0.18rem 0.6rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.05em;
        }
        .ns-pill-high { background: #238636; color: #fff; border: 1px solid #3fb950; }
        .ns-pill-med { background: #6e4c0a; color: #fff; border: 1px solid #d29922; }
        .ns-pill-low { background: #30363d; color: #c9d1d9; border: 1px solid #484f58; }
        .ns-stats {
            display: flex; flex-wrap: wrap; gap: 0.5rem;
            margin: 0.5rem 0 0.75rem 0;
        }
        .ns-stat {
            flex: 1 1 6rem;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 0.5rem 0.65rem;
            text-align: center;
        }
        .ns-stat b { display: block; font-size: 1.2rem; color: #e6edf3; }
        .ns-stat span { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; }
        .ns-idle {
            background: #161b22;
            border: 1px dashed #30363d;
            border-radius: 10px;
            padding: 1.1rem;
            text-align: center;
            color: #8b949e;
            font-size: 0.88rem;
            margin-top: 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ns-shell">', unsafe_allow_html=True)

    ns_ql = " | ".join(
        f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in _NS_LINKS.items()
    )
    st.markdown(f'<div class="ns-quicklinks">Quick links: {ns_ql}</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="ns-hero">'
        "<h3>📰 Newspaper Scraper • Small Counties</h3>"
        "<p>Premium Sumner County harvester — paste notices, run the agent pipeline, "
        f"push 🔥 HIGH leads to {PARTNER_NAME}'s queue, export JSON for full AI automation.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="ns-agent-bar">'
        "<b>Agent workflow:</b> Open quick links → paste all notices → "
        "<b>Run Full Agent Pipeline</b> → review table → push HIGH → copy JSON."
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ns-paste-shell">', unsafe_allow_html=True)
    st.markdown(
        '<div class="ns-paste-title">📋 Paste raw obituaries, Notice to Creditors, or court text</div>'
        '<div class="ns-paste-sub">Separate each estate with a blank line. '
        "Pipeline auto-extracts decedent, date, heir/PR, address clues, and phone search strings.</div>",
        unsafe_allow_html=True,
    )
    ns_raw = st.text_area(
        "Newspaper scraper paste",
        value=st.session_state.get("ns_scraper_raw", ""),
        height=420,
        placeholder=(
            "EXAMPLE — Notice to Creditors:\n"
            "Estate of Mary Jane Thompson, deceased\n"
            "Personal Representative: Robert Thompson\n"
            "Published March 12, 2026 — Sumner County Probate Court\n"
            "Creditors must file claims within 4 months…\n\n"
            "EXAMPLE — Obituary with address (🔥 HIGH score):\n"
            "William R. Davis — died January 4, 2026\n"
            "Survived by daughter Susan Davis of Hendersonville, TN\n"
            "Residence: 412 Old Hickory Blvd, Gallatin, TN 37066\n\n"
            "Paste more notices below — one block per estate…"
        ),
        key="ns_scraper_paste",
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="ns-btn-green-marker"></div>', unsafe_allow_html=True)
    if st.button(
        "🚀 Run Full Agent Pipeline",
        use_container_width=True,
        type="primary",
        key="ns_analyze_btn",
    ):
        if not ns_raw.strip():
            st.error("Paste notice text first — then run the pipeline.")
        else:
            st.session_state.ns_scraper_raw = ns_raw
            st.session_state.ns_scraper_results = _ns_analyze_text(ns_raw)
            st.session_state.ns_pipeline_ran = True
            st.session_state.ns_preselect_high = False
            st.session_state.pop("ns_push_flash", None)
            st.session_state.ns_json_visible = bool(st.session_state.ns_scraper_results)
            st.rerun()

    if st.session_state.get("ns_push_flash"):
        st.success(st.session_state.pop("ns_push_flash"))
        st.balloons()

    ns_results = st.session_state.get("ns_scraper_results", [])
    if ns_results:
        ns_high_n = sum(1 for r in ns_results if r.get("real_estate_score") == "High")
        ns_med_n = sum(1 for r in ns_results if r.get("real_estate_score") == "Med")
        ns_low_n = sum(1 for r in ns_results if r.get("real_estate_score") == "Low")
        ns_queued_n = sum(1 for r in ns_results if r.get("status") == "Queued")

        st.markdown('<div class="ns-results-title">📊 Pipeline Results</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="ns-badge-row">'
            f'{_NS_SCORE_PILL["High"]} {_NS_SCORE_PILL["Med"]} {_NS_SCORE_PILL["Low"]}'
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="ns-stats">'
            f'<div class="ns-stat"><b>{len(ns_results)}</b><span>Total</span></div>'
            f'<div class="ns-stat"><b style="color:#3fb950">{ns_high_n}</b><span>High</span></div>'
            f'<div class="ns-stat"><b style="color:#d29922">{ns_med_n}</b><span>Med</span></div>'
            f'<div class="ns-stat"><b style="color:#8b949e">{ns_low_n}</b><span>Low</span></div>'
            f'<div class="ns-stat"><b style="color:#58a6ff">{ns_queued_n}</b><span>Queued</span></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

        ns_sel_a, ns_sel_b = st.columns(2)
        with ns_sel_a:
            if st.button("☑️ Select All 🔥 HIGH", use_container_width=True, key="ns_select_all_high"):
                st.session_state.ns_preselect_high = True
                st.rerun()
        with ns_sel_b:
            if st.button("Clear Selection", use_container_width=True, key="ns_clear_select"):
                st.session_state.ns_preselect_high = False
                st.rerun()

        ns_preselect = st.session_state.get("ns_preselect_high", False)
        ns_editor_rows = [
            {
                "Select": ns_preselect and row.get("real_estate_score") == "High",
                "_row_id": i,
                "Decedent": row.get("decedent", ""),
                "Date": row.get("date", "—"),
                "Heir/PR": row.get("pr_heir", "Contact TBD"),
                "Real Estate Score": _NS_SCORE_BADGE.get(
                    row.get("real_estate_score", "Low"), "○ LOW"
                ),
                "Address Clue": row.get("address_clue", "—"),
                "Phone Search String": row.get("phone_search_string", ""),
                "Status": row.get("status", "Ready"),
            }
            for i, row in enumerate(ns_results)
        ]
        ns_edited = st.data_editor(
            ns_editor_rows,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "✓",
                    help="Select 🔥 HIGH rows to push to Branton's HOT queue",
                    default=False,
                ),
                "_row_id": None,
                "Decedent": st.column_config.TextColumn("Decedent", width="medium", disabled=True),
                "Date": st.column_config.TextColumn("Date", width="small", disabled=True),
                "Heir/PR": st.column_config.TextColumn("Heir/PR", width="medium", disabled=True),
                "Real Estate Score": st.column_config.TextColumn(
                    "Real Estate Score", width="small", disabled=True,
                ),
                "Address Clue": st.column_config.TextColumn("Address Clue", width="medium", disabled=True),
                "Phone Search String": st.column_config.TextColumn(
                    "Phone Search String", width="large", disabled=True,
                ),
                "Status": st.column_config.TextColumn("Status", width="small", disabled=True),
            },
            disabled=[
                "_row_id", "Decedent", "Date", "Heir/PR",
                "Real Estate Score", "Address Clue", "Phone Search String", "Status",
            ],
            hide_index=True,
            use_container_width=True,
            key="ns_scraper_table",
        )

        ns_high_selected = []
        for r in ns_edited:
            if not r.get("Select"):
                continue
            row_idx = r.get("_row_id")
            if row_idx is None or row_idx >= len(ns_results):
                continue
            if ns_results[row_idx].get("real_estate_score") != "High":
                continue
            ns_high_selected.append(ns_results[row_idx])

        if st.button(
            "📋 Copy Full JSON for Hermes / Open Claw / Claude",
            use_container_width=True,
            key="ns_show_json_btn",
        ):
            st.session_state.ns_json_visible = True

        ns_json_payload = {
            "agent": "ProbateGuardian Newspaper Scraper",
            "tab": "📰 Newspaper Scraper • Small Counties",
            "workflow": "paste → run pipeline → push high → export json",
            "county": "Sumner County, TN",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "lead_count": len(ns_results),
            "high_count": ns_high_n,
            "leads": _ns_results_for_json(ns_results),
        }
        ns_json_str = json.dumps(ns_json_payload, indent=2, ensure_ascii=False)
        if st.session_state.get("ns_json_visible"):
            st.code(ns_json_str, language="json")
            st.text_area(
                "Select all & copy for Hermes / Open Claw / Claude",
                value=ns_json_str,
                height=220,
                key="ns_json_copy_area",
            )
            st.download_button(
                "⬇️ Download JSON",
                data=ns_json_str,
                file_name=f"newspaper_scraper_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True,
                key="ns_json_download",
            )

        st.markdown('<div class="ns-btn-green-marker"></div>', unsafe_allow_html=True)
        if st.button(
            "✅ Push Selected High-Score Leads to Branton's HOT Queue 🔥",
            use_container_width=True,
            type="primary",
            key="ns_push_selected_btn",
        ):
            if not ns_high_selected:
                st.warning("Select at least one **🔥 HIGH** row (or tap Select All 🔥 HIGH).")
            else:
                n = _ns_push_high_to_queue(ns_results, ns_high_selected)
                st.session_state.ns_scraper_results = ns_results
                st.session_state.ns_preselect_high = False
                if n:
                    st.session_state.ns_push_flash = (
                        f"🔥 **{n}** high-score lead{'s' if n != 1 else ''} pushed to "
                        f"{PARTNER_NAME}'s HOT queue — open Dashboard → Branton Call Mode."
                    )
                    st.rerun()
                else:
                    st.info("No new leads added — selected rows may already be Queued.")

        st.caption(
            "Only **🔥 HIGH** rows push to the HOT queue. Status updates to *Queued* after a successful push."
        )

    elif st.session_state.get("ns_pipeline_ran"):
        st.warning("No probate notices detected — paste full notice blocks and run the pipeline again.")
    else:
        st.markdown(
            '<div class="ns-idle">'
            "Paste notices above and tap <b>🚀 Run Full Agent Pipeline</b> to score leads."
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Training
# ══════════════════════════════════════════════════════════════════════════════
with tab_training:
    st.subheader("🎥 Training — Elite Probate Playbook")
    st.caption(
        "Aaron Novello · Rick Yen · David Pannell · Jose · Bruce & Heath — "
        "study before every call."
    )

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
    st.markdown("### 📋 Swipe Files & Scripts — Copy & Paste")
    st.caption(
        "Tap a category · tap the copy icon on any block · paste into calls, texts, or emails. "
        f"Built for {PARTNER_NAME} on mobile."
    )
    for section_title, scripts in TRAINING_SWIPE_FILES:
        _render_training_swipe_section(section_title, scripts)

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

        **Escalate complex deals — {DEDICATED_PHONE_LINE}:** Sibling disputes · buyout math · competing agent · $500K+
        """
    )

    st.markdown("---")
    st.markdown("### 📖 Quick Links")
    st.markdown(
        """
        - [eXp Express Offers](https://www.exprealty.com) — Multi-buyer cash submissions
        - [TN Muniment of Title — T.C.A. 32](https://www.tn.gov/content/tn/tcas/search.html) — No-debt transfer path
        - **Lead Workflow** — Full Outreach · Guardian Kit · Attorney Outreach templates
        - **{DEDICATED_PHONE_LINE}**
        """
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB — Hospice & Pre-Probate Pipeline
# ══════════════════════════════════════════════════════════════════════════════
with tab_hospice:
    st.subheader("🩺 Hospice & Pre-Probate Pipeline")
    st.caption(
        f"Warm referrals before probate opens — built for {PARTNER_NAME} on his phone."
    )
    st.markdown(
        '<div class="hospice-hero">'
        "Tap a green button → copy scripts → log social workers → "
        "push 🔥 warm families straight to Branton's call list."
        "</div>",
        unsafe_allow_html=True,
    )

    hospice_county = st.text_input(
        "County (for hospice social worker search)",
        value="Wilson",
        key="hospice_county_input",
        placeholder="Wilson, Davidson, Rutherford…",
    )
    county_q = (hospice_county or "Middle Tennessee").strip()

    st.markdown("### 🔍 Quick Google Searches")
    st.markdown('<div class="hospice-mega-marker"></div>', unsafe_allow_html=True)
    st.link_button(
        "🔍 Google End-of-Life Social Workers",
        hospice_google_url("end of life social worker skilled nursing facility Middle Tennessee"),
        use_container_width=True,
        type="primary",
    )
    st.markdown('<div class="hospice-mega-marker"></div>', unsafe_allow_html=True)
    st.link_button(
        "🔍 Google Skilled Nursing Placement Advisors",
        hospice_google_url("skilled nursing facility placement advisor social worker Tennessee"),
        use_container_width=True,
        type="primary",
    )
    st.markdown('<div class="hospice-mega-marker"></div>', unsafe_allow_html=True)
    st.link_button(
        f"🔍 Google Hospice Social Workers — {county_q} County",
        hospice_google_url(f"hospice social worker {county_q} County Tennessee"),
        use_container_width=True,
        type="primary",
    )
    st.markdown('<div class="hospice-mega-marker"></div>', unsafe_allow_html=True)
    st.download_button(
        label="📋 Facility Visit Checklist (printable)",
        data=FACILITY_VISIT_CHECKLIST,
        file_name=f"facility_visit_checklist_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True,
        key="hospice_checklist_download",
    )

    st.markdown("---")
    st.markdown("### 📱 Value Script Generator")
    st.caption('Pre-death offer: "We remove the house burden so you can focus on Mom\'s care."')
    vs1, vs2 = st.columns(2)
    with vs1:
        hospice_facility = st.text_input("Facility name", key="hospice_vs_facility", placeholder="ABC Skilled Nursing")
    with vs2:
        hospice_family = st.text_input("Family / resident name", key="hospice_vs_family", placeholder="Smith family")
    hospice_sw = st.text_input("Social worker first name", key="hospice_vs_sw", placeholder="Sarah")
    st.markdown('<div class="hospice-mega-marker"></div>', unsafe_allow_html=True)
    gen_value_script = st.button(
        "✨ Generate Value Script",
        use_container_width=True,
        type="primary",
        key="hospice_gen_value_script",
    )
    if gen_value_script or st.session_state.get("hospice_value_script"):
        if gen_value_script:
            st.session_state.hospice_value_script = generate_hospice_value_script(
                hospice_facility, hospice_family, hospice_sw
            )
        st.text_area(
            "Copy & text / email to social worker",
            value=st.session_state.get("hospice_value_script", ""),
            height=320,
            key="hospice_value_script_display",
        )

    st.markdown("---")
    st.markdown("### 📄 Create Referral One-Pager")
    st.caption("Beautiful Guardian Kit sheet with phone numbers — hand to social workers & families.")
    op1, op2 = st.columns(2)
    with op1:
        op_decedent = st.text_input("Decedent name", key="hospice_op_decedent", placeholder="Mary Smith")
        op_address = st.text_input("Property address", key="hospice_op_address", placeholder="123 Main St, Lebanon, TN")
    with op2:
        op_county = st.text_input("County", key="hospice_op_county", value=county_q + " County")
        op_heir = st.text_input("Family contact", key="hospice_op_heir", placeholder="John Smith, son")
    op3, op4 = st.columns(2)
    with op3:
        op_facility = st.text_input("Referring facility", key="hospice_op_facility")
    with op4:
        op_sw = st.text_input("Social worker name", key="hospice_op_sw")
    st.markdown('<div class="hospice-mega-marker"></div>', unsafe_allow_html=True)
    gen_one_pager = st.button(
        "📄 Create Referral One-Pager",
        use_container_width=True,
        type="primary",
        key="hospice_gen_one_pager",
    )
    if gen_one_pager:
        op_parsed = {
            "decedent": op_decedent or "Estate",
            "address": op_address or "Address TBD",
            "county": op_county or county_q,
            "heirs": op_heir or "Estate Heirs",
            "phone": "",
            "email": "",
            "raw": "",
        }
        st.session_state.hospice_one_pager = generate_referral_one_pager(
            op_parsed,
            st.session_state.vendors,
            op_facility,
            op_sw,
        )
    if st.session_state.get("hospice_one_pager"):
        st.success("✅ Referral One-Pager ready — scroll to preview or download.")
        st.download_button(
            label="📥 Download One-Pager (.md)",
            data=st.session_state.hospice_one_pager,
            file_name=f"referral_one_pager_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
            key="hospice_one_pager_download",
        )
        st.markdown(st.session_state.hospice_one_pager)

    st.markdown("---")
    st.markdown("### 📊 Referral Tracker")
    st.caption("Social Worker Name · Facility · Notes · Last Contact · Next Action")
    hospice_rows = get_hospice_referrals()
    if not hospice_rows:
        hospice_rows = [{
            "Social Worker Name": "",
            "Facility": "",
            "Notes": "",
            "Last Contact": "",
            "Next Action": "",
        }]
    edited_hospice = st.data_editor(
        hospice_rows,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "Social Worker Name": st.column_config.TextColumn("Social Worker Name", width="medium"),
            "Facility": st.column_config.TextColumn("Facility", width="medium"),
            "Notes": st.column_config.TextColumn("Notes", width="large"),
            "Last Contact": st.column_config.TextColumn("Last Contact", width="small"),
            "Next Action": st.column_config.TextColumn("Next Action", width="medium"),
        },
        key="hospice_referral_editor",
    )
    hc1, hc2 = st.columns(2)
    with hc1:
        st.markdown('<div class="hospice-mega-marker"></div>', unsafe_allow_html=True)
        if st.button("💾 Save Referral Tracker", use_container_width=True, type="primary", key="hospice_save_tracker"):
            cleaned = [
                row for row in edited_hospice
                if any(str(v).strip() for v in row.values())
            ]
            st.session_state.hospice_referrals = cleaned
            save_hospice_referrals(cleaned)
            st.success(f"✅ Saved {len(cleaned)} referral(s).")
            st.rerun()
    with hc2:
        if st.button("🔄 Reload Tracker", use_container_width=True, key="hospice_reload_tracker"):
            st.session_state.hospice_referrals = load_hospice_referrals()
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔥 Send to Branton Queue")
    st.caption("Push warm pre-probate leads to the top of Branton's call list — tagged 🔥 Hot.")
    bq1, bq2 = st.columns(2)
    with bq1:
        bq_decedent = st.text_input("Decedent / resident", key="hospice_bq_decedent")
        bq_address = st.text_input("Property address", key="hospice_bq_address")
        bq_county = st.text_input("County", key="hospice_bq_county", value=county_q + " County")
    with bq2:
        bq_contact = st.text_input("Family contact name", key="hospice_bq_contact")
        bq_phone = st.text_input("Family phone", key="hospice_bq_phone")
        bq_facility = st.text_input("Facility", key="hospice_bq_facility")
    bq_sw = st.text_input("Referring social worker", key="hospice_bq_sw")
    bq_notes = st.text_area("Warm lead notes", key="hospice_bq_notes", height=100, placeholder="Pre-death — family worried about house…")
    st.markdown('<div class="hospice-mega-marker"></div>', unsafe_allow_html=True)
    if st.button(
        "🔥 Send to Branton Queue",
        use_container_width=True,
        type="primary",
        key="hospice_push_branton",
    ):
        if not (bq_decedent.strip() or bq_contact.strip() or bq_address.strip()):
            st.warning("Enter at least a decedent, contact, or address.")
        else:
            n = push_hospice_to_branton_queue(
                bq_decedent,
                bq_address,
                bq_county,
                bq_contact,
                bq_phone,
                bq_facility,
                bq_sw,
                bq_notes,
            )
            st.success(
                f"🔥 Pushed **{n}** warm pre-probate lead to {PARTNER_NAME}'s queue — "
                "check Dashboard → Branton Call Mode."
            )
            st.balloons()