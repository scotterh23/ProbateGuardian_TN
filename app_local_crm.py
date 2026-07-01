import csv
import html
import io
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import streamlit as st

# ── Constants ────────────────────────────────────────────────────────────────
PARTNER_NAME = "Branton Walker"
PHONE_PLACEHOLDER = "— add phone —"
ASSIGN_STATUS = f"Assigned to {PARTNER_NAME}"
LEGACY_ASSIGN_STATUSES = ("Assigned to Brantley", ASSIGN_STATUS)
PIPELINE_STAGES = ["Cold", "Warm", "Appt", "Contract", "Closed"]
WORKFLOW_STATUSES = ["New", "Qualified", "Contacted", "Interested", "Appt", "Listed"]

BRANTON_STAGES = [
    "New", "Attempted", "Contacted", "Interested", "Appt Set",
    "Listing Signed", "Under Contract", "Court Pending", "Closed Won",
    "Nurture", "Dead",
]
BRANTON_STAGE_ALIASES = {"Listed": "Listing Signed"}
BRANTON_STAGE_NEXT = {
    "New": "Attempted",
    "Attempted": "Contacted",
    "Contacted": "Interested",
    "Interested": "Appt Set",
    "Appt Set": "Listing Signed",
    "Listing Signed": "Under Contract",
    "Listed": "Under Contract",
    "Under Contract": "Court Pending",
    "Court Pending": "Closed Won",
    "Closed Won": "Closed Won",
    "Nurture": "Nurture",
    "Dead": "Dead",
}
BRANTON_TO_STATUS = {
    "New": "New",
    "Attempted": "Qualified",
    "Contacted": "Contacted",
    "Interested": "Interested",
    "Appt Set": "Appt",
    "Listing Signed": "Listed",
    "Listed": "Listed",
    "Under Contract": "Under Contract",
    "Court Pending": "Under Contract",
    "Closed Won": "Closed",
    "Nurture": "Qualified",
    "Dead": "Low Priority",
}
DRIP_STOP_STAGES = {
    "Contacted", "Interested", "Appt Set", "Listing Signed", "Listed",
    "Under Contract", "Court Pending", "Closed Won",
}
CRM_ACTIVE_STAGES = {
    "New", "Attempted", "Contacted", "Interested", "Appt Set",
    "Listing Signed", "Listed", "Under Contract", "Court Pending",
}
CRM_DEAL_STAGES = {"Listing Signed", "Listed", "Under Contract", "Court Pending", "Closed Won"}
DRIP_AGGRESSIVE_SEQUENCE = [
    {"day": 0, "type": "call", "label": "Touch 1 — Day 0 Call + VM"},
    {"day": 1, "type": "text", "label": "Touch 2 — Day 1 Compassion Text"},
    {"day": 2, "type": "call", "label": "Touch 3 — Day 2 Follow-up Call"},
    {"day": 4, "type": "email", "label": "Touch 4 — Day 4 Net Sheet Offer"},
    {"day": 7, "type": "call", "label": "Touch 5 — Day 7 Check-in"},
    {"day": 10, "type": "text", "label": "Touch 6 — Day 10 Value Text"},
    {"day": 14, "type": "email", "label": "Touch 7 — Day 14 Market Update"},
    {"day": 21, "type": "call", "label": "Touch 8 — Day 21 Call"},
    {"day": 28, "type": "email", "label": "Touch 9 — Day 28 Vendor Offers"},
    {"day": 35, "type": "text", "label": "Touch 10 — Day 35 Gentle Nudge"},
    {"day": 42, "type": "call", "label": "Touch 11 — Day 42 Final Push"},
    {"day": 56, "type": "email", "label": "Touch 12 — Day 56 Nurture"},
]
DRIP_NURTURE_SEQUENCE = [
    {"day": 30, "type": "nurture", "label": "Probate Tips — What heirs forget"},
    {"day": 60, "type": "nurture", "label": "Market Update — Middle TN probate homes"},
    {"day": 90, "type": "nurture", "label": "Vendor Offers — estate sale + funded repairs"},
    {"day": 120, "type": "nurture", "label": "Seasonal check-in — no pressure"},
]

STATUS_TO_PIPELINE = {
    "New": "Cold",
    "Qualified": "Warm",
    "Needs Review": "Cold",
    "Low Priority": "Cold",
    "Contacted": "Warm",
    "Interested": "Warm",
    "Appt": "Appt",
    "Listed": "Contract",
    ASSIGN_STATUS: "Warm",
    "Assigned to Brantley": "Warm",
    "Hot": "Warm",
    "Under Contract": "Contract",
    "Closed": "Closed",
}

RECENCY_HIGH_DAYS = 30

st.set_page_config(
    page_title="ProbateGuardian Free TN",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

LEADS_FILE = Path(__file__).parent / "leads_data.json"

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
    .pipe-cold { color: #8b949e; font-weight: 600; }
    .pipe-warm { color: #58a6ff; font-weight: 600; }
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
    .ftc-hero {
        background: linear-gradient(135deg, #1f3a5f 0%, #238636 55%, #2ea043 100%);
        color: #f0f6fc;
        padding: 1.1rem 1.25rem;
        border-radius: 14px;
        font-size: 1.05rem;
        font-weight: 600;
        text-align: center;
        margin: 0.5rem 0 1rem 0;
        box-shadow: 0 6px 24px rgba(35, 134, 54, 0.25);
        line-height: 1.45;
    }
    .ftc-section {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.75rem;
    }
    .ftc-badge-hot {
        display: inline-block;
        background: #da3633;
        color: #fff;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        margin-left: 0.35rem;
    }
    .ftc-badge-due {
        display: inline-block;
        background: #d29922;
        color: #0d1117;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        margin-left: 0.35rem;
    }
    .ftc-header-money {
        background: linear-gradient(135deg, #0d2818 0%, #238636 40%, #1f6feb 100%);
        color: #f0f6fc;
        padding: 1.25rem 1.1rem;
        border-radius: 16px;
        font-size: 1.15rem;
        font-weight: 800;
        text-align: center;
        margin: 0.25rem 0 0.75rem 0;
        box-shadow: 0 8px 28px rgba(35, 134, 54, 0.35);
        line-height: 1.4;
    }
    .ftc-role-split {
        background: #161b22;
        border: 2px solid #238636;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-size: 0.95rem;
        font-weight: 600;
        color: #3fb950;
        text-align: center;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    .ftc-role-split span.scott { color: #58a6ff; }
    .ftc-zone-green {
        background: linear-gradient(180deg, #0d2818 0%, #161b22 100%);
        border: 2px solid #238636;
        border-radius: 14px;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    .ftc-zone-blue {
        background: linear-gradient(180deg, #0d1d33 0%, #161b22 100%);
        border: 2px solid #1f6feb;
        border-radius: 14px;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    .ftc-zone-label {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.65rem;
    }
    .ftc-zone-green .ftc-zone-label { color: #3fb950; }
    .ftc-zone-blue .ftc-zone-label { color: #58a6ff; }
    .ftc-motivation {
        background: linear-gradient(135deg, #1a1f2e, #23863622);
        border-left: 4px solid #238636;
        border-radius: 10px;
        padding: 1rem 1.1rem;
        color: #e6edf3;
        font-size: 0.98rem;
        line-height: 1.55;
        margin-top: 1rem;
    }
    .ftc-targets {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 0.85rem 1rem;
    }
    div[data-testid="stLinkButton"] > a {
        font-weight: 600 !important;
        border-radius: 10px !important;
        min-height: 2.85rem;
    }
    .ftc-ready-green {
        background: linear-gradient(135deg, #0d2818 0%, #1a3d2a 100%);
        border: 2px solid #3fb950;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 18px rgba(63, 185, 80, 0.25);
    }
    .ftc-ready-label {
        color: #3fb950;
        font-weight: 800;
        font-size: 0.85rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .ftc-pending-row {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.45rem 0;
    }
    .ftc-paste-hero {
        background: linear-gradient(135deg, #0d2818, #1f6feb33);
        border: 2px solid #3fb950;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.75rem;
        color: #e6edf3;
        line-height: 1.5;
    }
    .ftc-btn-red-marker { display: none; }
    .ftc-btn-red-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #7d1a1a 0%, #da3633 45%, #f85149 100%) !important;
        border: 2px solid #ff7b72 !important;
        color: #fff !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        min-height: 3.5rem !important;
        box-shadow: 0 8px 28px rgba(218, 54, 51, 0.5) !important;
        letter-spacing: 0.02em;
    }
    .ftc-btn-red-marker + div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 32px rgba(248, 81, 73, 0.55) !important;
    }
    .branton-clear-red-marker { display: none; }
    .branton-clear-red-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #5a0f0f 0%, #b62324 40%, #da3633 100%) !important;
        border: 2px solid #ff7b72 !important;
        color: #fff !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        min-height: 3.75rem !important;
        box-shadow: 0 8px 28px rgba(218, 54, 51, 0.45) !important;
    }
    .branton-paste-zone {
        background: linear-gradient(135deg, #0d1117 0%, #1f6feb18 100%);
        border: 2px solid #58a6ff;
        border-radius: 16px;
        padding: 1.1rem 1.15rem;
        margin: 1rem 0 0.75rem 0;
        color: #e6edf3;
        line-height: 1.5;
    }
    .branton-paste-zone strong { color: #58a6ff; }
    .branton-quick-add-zone {
        background: linear-gradient(135deg, #0d2818 0%, #132f1f 50%, #1a3d2a 100%);
        border: 3px solid #3fb950;
        border-radius: 18px;
        padding: 1.15rem 1.1rem;
        margin: 0 0 1rem 0;
        box-shadow: 0 8px 32px rgba(63, 185, 80, 0.2);
    }
    .branton-quick-add-zone h3 {
        color: #3fb950 !important;
        font-size: 1.35rem !important;
        margin: 0 0 0.35rem 0 !important;
    }
    .branton-quick-add-green-marker { display: none; }
    .branton-quick-add-green-marker + div[data-testid="stFormSubmitButton"] > button,
    .branton-quick-add-green-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #1a4d2e 0%, #238636 45%, #3fb950 100%) !important;
        border: 2px solid #56d364 !important;
        color: #fff !important;
        font-size: 1.12rem !important;
        font-weight: 800 !important;
        min-height: 3.75rem !important;
        box-shadow: 0 8px 28px rgba(46, 160, 67, 0.45) !important;
    }
    .branton-quick-add-green-marker + div[data-testid="stFormSubmitButton"] > button:hover,
    .branton-quick-add-green-marker + div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 32px rgba(63, 185, 80, 0.55) !important;
    }
    .branton-crm-header {
        background: linear-gradient(135deg, #1a0a0a 0%, #da3633 25%, #238636 60%, #1f6feb 100%);
        color: #fff;
        padding: 1.35rem 1rem;
        border-radius: 18px;
        font-size: 1.35rem;
        font-weight: 900;
        text-align: center;
        margin: 0.5rem 0 1rem 0;
        box-shadow: 0 10px 36px rgba(218, 54, 51, 0.35);
        line-height: 1.35;
    }
    .branton-pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
        margin: 0.75rem 0 1rem 0;
    }
    .branton-pill {
        display: inline-block;
        padding: 0.55rem 0.9rem;
        border-radius: 999px;
        font-size: 0.92rem;
        font-weight: 700;
        border: 2px solid #30363d;
        background: #161b22;
        color: #e6edf3;
        min-width: 5.5rem;
        text-align: center;
    }
    .branton-pill-new { border-color: #58a6ff; color: #58a6ff; }
    .branton-pill-attempted { border-color: #8b949e; color: #c9d1d9; }
    .branton-pill-contacted { border-color: #a371f7; color: #a371f7; }
    .branton-pill-interested { border-color: #d29922; color: #d29922; }
    .branton-pill-appt { border-color: #f0883e; color: #f0883e; }
    .branton-pill-listed { border-color: #3fb950; color: #3fb950; }
    .branton-lead-card {
        background: #161b22;
        border: 2px solid #30363d;
        border-radius: 14px;
        padding: 1rem;
        margin: 0.65rem 0;
    }
    .branton-lead-card.hot {
        border-color: #da3633;
        box-shadow: 0 6px 24px rgba(218, 54, 51, 0.25);
    }
    .branton-lead-card.due {
        border-color: #d29922;
    }
    .branton-phone-big {
        display: block;
        background: linear-gradient(135deg, #238636, #2ea043);
        color: #fff !important;
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        padding: 0.85rem 1rem !important;
        border-radius: 12px !important;
        text-align: center;
        text-decoration: none !important;
        margin: 0.5rem 0;
    }
    .branton-big-action div[data-testid="stButton"] > button,
    .branton-big-action div[data-testid="stLinkButton"] > a {
        min-height: 3.25rem !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }
    .branton-action-row div[data-testid="stButton"] > button {
        min-height: 2.75rem !important;
        font-size: 0.88rem !important;
        font-weight: 700 !important;
    }
    .branton-touch-dots {
        font-size: 1.1rem;
        letter-spacing: 0.15rem;
        font-weight: 700;
    }
    .branton-queue-label {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 0.35rem;
    }
    .branton-queue-hot { background: #da3633; color: #fff; }
    .branton-queue-due { background: #d29922; color: #0d1117; }
    .branton-queue-new { background: #1f6feb; color: #fff; }
    .mm-header {
        background: linear-gradient(135deg, #1a0a0a 0%, #da3633 20%, #f0883e 45%, #238636 70%, #1f6feb 100%);
        color: #fff;
        padding: 1.5rem 1.1rem;
        border-radius: 20px;
        font-size: 1.45rem;
        font-weight: 900;
        text-align: center;
        margin: 0 0 1rem 0;
        box-shadow: 0 12px 40px rgba(218, 54, 51, 0.4);
        line-height: 1.35;
        letter-spacing: -0.02em;
    }
    .mm-pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        justify-content: center;
        margin: 0.5rem 0 1.25rem 0;
    }
    .mm-pill {
        display: inline-block;
        padding: 0.7rem 1.1rem;
        border-radius: 999px;
        font-size: 1.02rem;
        font-weight: 800;
        border: 2px solid #30363d;
        background: #0d1117;
        color: #e6edf3;
        min-width: 6.5rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    }
    .mm-queue-section-title {
        font-size: 1.35rem;
        font-weight: 900;
        color: #e6edf3;
        margin: 0.25rem 0 0.35rem 0;
    }
    .mm-queue-row {
        background: #161b22;
        border: 2px solid #30363d;
        border-radius: 16px;
        padding: 0.85rem 1rem 0.75rem 1rem;
        margin: 0.55rem 0;
    }
    .mm-queue-row.hot {
        border-color: #da3633;
        box-shadow: 0 6px 28px rgba(218, 54, 51, 0.28);
        background: linear-gradient(135deg, #1a1010 0%, #161b22 100%);
    }
    .mm-queue-row.due {
        border-color: #d29922;
        box-shadow: 0 4px 20px rgba(210, 153, 34, 0.2);
    }
    .mm-queue-row.new {
        border-color: #58a6ff;
    }
    .mm-drip-track {
        background: #21262d;
        border-radius: 8px;
        height: 8px;
        overflow: hidden;
        margin: 0.35rem 0 0.2rem 0;
    }
    .mm-drip-fill {
        background: linear-gradient(90deg, #238636, #3fb950);
        height: 100%;
        border-radius: 8px;
        transition: width 0.2s ease;
    }
    .mm-drip-label {
        font-size: 0.78rem;
        color: #8b949e;
        margin-bottom: 0.35rem;
    }
    .mm-queue-badge {
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.22rem 0.55rem;
        border-radius: 6px;
        display: inline-block;
        margin-bottom: 0.4rem;
    }
    .mm-field-label {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8b949e;
        margin-bottom: 0.1rem;
    }
    .mm-field-value {
        font-size: 0.95rem;
        font-weight: 600;
        color: #e6edf3;
        line-height: 1.3;
        word-break: break-word;
    }
    .mm-phone-tap {
        display: block;
        background: linear-gradient(135deg, #238636, #2ea043);
        color: #fff !important;
        font-size: 1.45rem !important;
        font-weight: 900 !important;
        padding: 0.9rem 0.75rem !important;
        border-radius: 14px !important;
        text-align: center;
        text-decoration: none !important;
        margin: 0.15rem 0;
        box-shadow: 0 6px 20px rgba(46, 160, 67, 0.35);
    }
    .mm-phone-tap:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 24px rgba(46, 160, 67, 0.45);
    }
    .mm-phone-missing {
        display: block;
        background: #21262d;
        border: 2px dashed #484f58;
        color: #8b949e;
        font-size: 0.88rem;
        font-weight: 700;
        padding: 0.65rem;
        border-radius: 12px;
        text-align: center;
    }
    .mm-touch-track {
        display: flex;
        gap: 0.35rem;
        align-items: center;
        flex-wrap: wrap;
        margin: 0.25rem 0;
    }
    .mm-touch-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.85rem;
        height: 1.85rem;
        border-radius: 50%;
        font-size: 0.82rem;
        font-weight: 800;
        border: 2px solid #30363d;
        color: #8b949e;
        background: #0d1117;
    }
    .mm-touch-num.done {
        background: #238636;
        border-color: #3fb950;
        color: #fff;
    }
    .mm-touch-num.now {
        background: #da3633;
        border-color: #ff7b72;
        color: #fff;
        box-shadow: 0 0 12px rgba(218, 54, 51, 0.5);
    }
    .mm-entry-zone {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        border: 2px solid #30363d;
        border-radius: 18px;
        padding: 1.1rem 1rem;
        margin: 1.25rem 0 0.75rem 0;
    }
    .mm-vendor-zone {
        background: #0d1117;
        border: 2px solid #30363d;
        border-radius: 16px;
        padding: 1rem;
        margin: 1.5rem 0 0.5rem 0;
    }
    .mm-log-next-marker { display: none; }
    .mm-log-next-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #1a4d2e 0%, #238636 45%, #3fb950 100%) !important;
        border: 2px solid #56d364 !important;
        color: #fff !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        min-height: 4rem !important;
        box-shadow: 0 8px 28px rgba(46, 160, 67, 0.45) !important;
    }
    .mm-stat-card {
        background: #161b22;
        border: 2px solid #30363d;
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
    }
    .mm-stat-num {
        font-size: 2rem;
        font-weight: 900;
        color: #3fb950;
        line-height: 1.1;
    }
    .mm-stat-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #8b949e;
        margin-top: 0.25rem;
    }
    .train-hero {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 40%, #1f6feb22 100%);
        border: 2px solid #30363d;
        border-radius: 18px;
        padding: 1.25rem 1.1rem;
        margin: 0 0 1.25rem 0;
        text-align: center;
    }
    .train-hero h2 {
        color: #e6edf3 !important;
        font-size: 1.45rem !important;
        font-weight: 900 !important;
        margin: 0 0 0.35rem 0 !important;
    }
    .train-hero p {
        color: #8b949e;
        margin: 0;
        font-size: 0.95rem;
    }
    .train-section {
        background: #0d1117;
        border: 2px solid #30363d;
        border-radius: 16px;
        padding: 1rem 0.85rem 0.75rem 0.85rem;
        margin: 0 0 1rem 0;
    }
    .train-section-title {
        font-size: 1.1rem;
        font-weight: 900;
        color: #e6edf3;
        margin: 0 0 0.65rem 0;
        padding: 0 0.15rem;
    }
    .train-cheat {
        background: linear-gradient(135deg, #1a0a0a 0%, #161b22 50%, #132f1f 100%);
        border: 2px solid #3fb950;
        border-radius: 16px;
        padding: 1.1rem 1rem;
        margin: 0 0 1.25rem 0;
    }
    .train-cheat h3 {
        color: #3fb950 !important;
        font-size: 1.15rem !important;
        margin: 0 0 0.65rem 0 !important;
    }
    .train-cheat p, .train-cheat li {
        color: #e6edf3;
        line-height: 1.55;
        font-size: 0.98rem;
    }
    .train-cheat blockquote {
        border-left: 4px solid #3fb950;
        margin: 0.5rem 0;
        padding: 0.35rem 0 0.35rem 0.85rem;
        color: #c9d1d9;
        font-style: italic;
    }
    .train-zone div[data-testid="stLinkButton"] > a {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 3.35rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        margin-bottom: 0.45rem !important;
        background: #21262d !important;
        border: 2px solid #30363d !important;
        color: #e6edf3 !important;
        text-decoration: none !important;
    }
    .train-zone div[data-testid="stLinkButton"] > a:hover {
        border-color: #58a6ff !important;
        background: #1f6feb22 !important;
    }
    a.train-link-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 3.35rem;
        font-size: 1rem;
        font-weight: 700;
        border-radius: 12px;
        margin-bottom: 0.45rem;
        background: #21262d;
        border: 2px solid #30363d;
        color: #e6edf3 !important;
        text-decoration: none !important;
        padding: 0.5rem 0.75rem;
        text-align: center;
    }
    a.train-link-btn:hover {
        border-color: #58a6ff;
        background: #1f6feb22;
    }
    .train-zone-hot div[data-testid="stLinkButton"] > a {
        background: linear-gradient(135deg, #1a4d2e 0%, #238636 100%) !important;
        border-color: #3fb950 !important;
        color: #fff !important;
        min-height: 3.75rem !important;
        font-size: 1.08rem !important;
    }
    .train-stuck {
        background: linear-gradient(135deg, #da3633 0%, #b62324 100%);
        border-radius: 16px;
        padding: 0.35rem;
        margin: 1.25rem 0 0.5rem 0;
    }
    a.train-stuck-btn {
        background: transparent !important;
        border: none !important;
        color: #fff !important;
        font-size: 1.15rem !important;
        font-weight: 900 !important;
        min-height: 3.75rem !important;
    }
    .crm-hero {
        background: linear-gradient(135deg, #0d1117 0%, #1f6feb18 50%, #23863618 100%);
        border: 2px solid #30363d;
        border-radius: 18px;
        padding: 1.2rem 1rem;
        margin: 0 0 1rem 0;
        text-align: center;
    }
    .crm-hero h2 {
        color: #e6edf3 !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        margin: 0 0 0.3rem 0 !important;
    }
    .crm-hero p { color: #8b949e; margin: 0; font-size: 0.92rem; }
    .crm-section-title {
        font-size: 1.25rem;
        font-weight: 900;
        color: #e6edf3;
        margin: 0.5rem 0 0.35rem 0;
    }
    .crm-funnel-cell {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 0.5rem 0.25rem;
        text-align: center;
        min-height: 3.5rem;
    }
    .crm-funnel-n {
        font-size: 1.35rem;
        font-weight: 900;
        color: #58a6ff;
        line-height: 1.1;
    }
    .crm-funnel-lbl {
        font-size: 0.62rem;
        font-weight: 700;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-top: 0.2rem;
        line-height: 1.2;
    }
    /* ── Branton Walker mobile money machine ── */
    .bw-hero {
        background: linear-gradient(135deg, #5a0f0f 0%, #da3633 35%, #238636 100%);
        color: #fff;
        padding: 1.15rem 1rem;
        border-radius: 16px;
        font-size: 1.12rem;
        font-weight: 800;
        text-align: center;
        margin: 0 0 0.85rem 0;
        box-shadow: 0 8px 32px rgba(218, 54, 51, 0.35);
        line-height: 1.4;
    }
    .bw-bulk-paste-zone {
        background: linear-gradient(180deg, #0d2818 0%, #132f1f 40%, #161b22 100%);
        border: 4px solid #3fb950;
        border-radius: 22px;
        padding: 1.15rem 1rem 1rem 1rem;
        margin: 0 0 1rem 0;
        box-shadow: 0 10px 40px rgba(63, 185, 80, 0.28);
    }
    .bw-bulk-paste-title {
        font-size: 1.45rem;
        font-weight: 900;
        color: #56d364;
        margin-bottom: 0.35rem;
        line-height: 1.25;
    }
    .bw-bulk-paste-hint {
        font-size: 0.88rem;
        color: #8b949e;
        margin-bottom: 0.65rem;
        line-height: 1.45;
    }
    .bw-paste-zone {
        background: linear-gradient(180deg, #0d2818 0%, #161b22 100%);
        border: 3px solid #3fb950;
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 0.85rem;
    }
    .bw-paste-label {
        font-size: 1.15rem;
        font-weight: 900;
        color: #3fb950;
        margin-bottom: 0.5rem;
    }
    .bw-card {
        background: #161b22;
        border: 2px solid #30363d;
        border-radius: 20px;
        padding: 1rem 1rem 0.85rem 1rem;
        margin: 0.75rem 0;
        box-shadow: 0 6px 24px rgba(0,0,0,0.35);
    }
    .bw-card.hot {
        border-color: #da3633;
        background: linear-gradient(160deg, #1a1010 0%, #161b22 55%);
        box-shadow: 0 8px 32px rgba(218, 54, 51, 0.3);
    }
    .bw-card-name {
        font-size: 1.45rem;
        font-weight: 900;
        color: #f0f6fc;
        line-height: 1.2;
        margin: 0.15rem 0 0.35rem 0;
    }
    .bw-card-addr {
        font-size: 1.05rem;
        font-weight: 700;
        color: #58a6ff;
        line-height: 1.35;
        margin-bottom: 0.35rem;
    }
    .bw-card-poc {
        font-size: 0.95rem;
        color: #c9d1d9;
        margin-bottom: 0.5rem;
    }
    .bw-status-pill {
        display: inline-block;
        padding: 0.4rem 0.85rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }
    .bw-pill-new { background: #1f3a5f; color: #58a6ff; border: 2px solid #58a6ff; }
    .bw-pill-contacted { background: #2d1f4e; color: #a371f7; border: 2px solid #a371f7; }
    .bw-pill-appt { background: #3d2a0a; color: #f0883e; border: 2px solid #f0883e; }
    .bw-pill-listed { background: #0d2818; color: #3fb950; border: 2px solid #3fb950; }
    .bw-pill-closed { background: #21262d; color: #8b949e; border: 2px solid #484f58; }
    .bw-pill-hot { background: #5a0f0f; color: #ff7b72; border: 2px solid #da3633; }
    .bw-script-btn-marker, .bw-action-green-marker, .bw-action-closed-marker,
    .bw-paste-btn-marker, .bw-bulk-btn-marker { display: none; }
    .bw-script-btn-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #5a0f0f 0%, #b62324 40%, #da3633 70%, #f85149 100%) !important;
        border: 3px solid #ff7b72 !important;
        color: #fff !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        min-height: 4.75rem !important;
        border-radius: 18px !important;
        box-shadow: 0 12px 40px rgba(218, 54, 51, 0.55) !important;
        letter-spacing: 0.02em;
    }
    .bw-action-green-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #1a4d2e 0%, #238636 50%, #3fb950 100%) !important;
        border: 2px solid #56d364 !important;
        color: #fff !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        min-height: 3.85rem !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 26px rgba(46, 160, 67, 0.45) !important;
    }
    .bw-action-closed-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #3d2e0a 0%, #9e6a03 50%, #d29922 100%) !important;
        border: 2px solid #e3b341 !important;
        color: #0d1117 !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        min-height: 4rem !important;
        border-radius: 16px !important;
    }
    .bw-bulk-btn-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #0d4d2a 0%, #1a7f37 35%, #238636 65%, #56d364 100%) !important;
        border: 3px solid #56d364 !important;
        color: #fff !important;
        font-size: 1.22rem !important;
        font-weight: 900 !important;
        min-height: 4.5rem !important;
        border-radius: 18px !important;
        box-shadow: 0 12px 36px rgba(46, 160, 67, 0.5) !important;
        line-height: 1.25 !important;
        white-space: normal !important;
    }
    .bw-delete-btn-marker { display: none; }
    .bw-delete-btn-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #5a0f0f, #da3633) !important;
        border: 2px solid #ff7b72 !important;
        color: #fff !important;
        font-size: 1.15rem !important;
        font-weight: 900 !important;
        min-height: 2.65rem !important;
        max-height: 2.65rem !important;
        padding: 0.2rem 0.5rem !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(218, 54, 51, 0.45) !important;
    }
    .bw-paste-btn-marker + div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #1a4d2e 0%, #238636 45%, #3fb950 100%) !important;
        border: 2px solid #56d364 !important;
        font-size: 1.2rem !important;
        font-weight: 900 !important;
        min-height: 3.75rem !important;
    }
    div[data-testid="stTextArea"] textarea {
        font-size: 1rem !important;
        line-height: 1.45 !important;
    }
    .bw-script-box {
        background: #0d1117;
        border: 2px solid #da3633;
        border-radius: 14px;
        padding: 0.85rem;
        margin: 0.5rem 0 0.65rem 0;
        font-size: 0.88rem;
        line-height: 1.55;
        color: #e6edf3;
        white-space: pre-wrap;
        max-height: 520px;
        overflow-y: auto;
    }
    .bw-notes-label {
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #8b949e;
        margin: 0.5rem 0 0.35rem 0;
    }
    .bw-notes-marker { display: none; }
    .bw-notes-marker + div[data-testid="stTextArea"] textarea {
        min-height: 12rem !important;
        font-size: 0.95rem !important;
        line-height: 1.55 !important;
        background: #0d1117 !important;
        border: 2px solid #30363d !important;
        border-radius: 12px !important;
        resize: vertical !important;
        color: #e6edf3 !important;
    }
    .bw-notes-marker + div[data-testid="stTextArea"] textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.25) !important;
    }
    .bw-card-flash {
        background: #12261e;
        border: 2px solid #3fb950;
        border-radius: 10px;
        padding: 0.5rem 0.75rem;
        margin: 0.35rem 0 0.5rem 0;
        font-size: 0.88rem;
        font-weight: 800;
        color: #3fb950;
        text-align: center;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 0.4rem !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
    }
    div[data-testid="stRadio"] label {
        background: #161b22 !important;
        border: 2px solid #30363d !important;
        border-radius: 999px !important;
        padding: 0.55rem 0.9rem !important;
        font-weight: 800 !important;
        font-size: 0.88rem !important;
        min-height: 2.75rem !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        border-color: #3fb950 !important;
        background: #0d2818 !important;
        color: #3fb950 !important;
    }
    [data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 0.75rem !important; max-width: 720px !important; }
    @media (max-width: 768px) {
        .hero-title { font-size: 1.85rem !important; }
        .ftc-hero { font-size: 0.95rem; padding: 0.9rem 1rem; }
        .ftc-header-money { font-size: 1rem; padding: 1rem 0.85rem; }
        .ftc-role-split { font-size: 0.88rem; }
        .branton-crm-header { font-size: 1.05rem; padding: 1rem 0.75rem; }
        .branton-pill { font-size: 0.82rem; padding: 0.45rem 0.65rem; min-width: 4.5rem; }
        .branton-phone-big { font-size: 1.2rem !important; }
        .mm-header { font-size: 1.05rem; padding: 1.1rem 0.75rem; }
        .mm-pill { font-size: 0.82rem; padding: 0.5rem 0.7rem; min-width: 5rem; }
        .mm-phone-tap { font-size: 1.2rem !important; }
        .train-hero h2 { font-size: 1.15rem !important; }
        .train-zone div[data-testid="stLinkButton"] > a { font-size: 0.92rem !important; min-height: 3.1rem !important; }
        .bw-card-name { font-size: 1.3rem; }
        .bw-hero { font-size: 1rem; padding: 1rem 0.85rem; }
        .bw-script-btn-marker + div[data-testid="stButton"] > button { font-size: 1.25rem !important; min-height: 3.85rem !important; }
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

    if "pipeline_stage" not in lead:
        lead["pipeline_stage"] = STATUS_TO_PIPELINE.get(lead.get("status", "New"), "Cold")

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
    lead.setdefault("has_real_estate", False)
    lead.setdefault("case_number", "")
    lead.setdefault("filing_date", lead.get("filing_date", ""))
    lead.setdefault("recency_days", None)
    lead.setdefault("recency_tier", "")
    lead.setdefault("branton_hot", False)
    if lead.get("branton_hot") and not lead.get("hot_queued_at"):
        lead["hot_queued_at"] = lead.get("created", datetime.now().isoformat())
    lead.setdefault("assessor_checked", False)
    lead.setdefault("contact_name", lead.get("heirs", ""))
    lead.setdefault("contact_role", "")
    lead.setdefault("court_status", "")
    lead.setdefault("assessor_url", "")
    lead.setdefault("drip_touch_index", 0)
    lead.setdefault("drip_started_iso", lead.get("created", datetime.now().isoformat())[:10])
    lead.setdefault("drip_paused", False)
    lead.setdefault("last_drip_touch_iso", "")
    lead.setdefault("drip_nurture_index", 0)
    lead.setdefault("deal_list_price", 0)
    lead.setdefault("deal_contract_price", 0)
    lead.setdefault("deal_commission_pct", 3.0)
    lead.setdefault("deal_gci", 0.0)
    lead.setdefault("deal_close_date", "")
    lead.setdefault("deal_attorney", "")
    lead.setdefault("deal_listing_date", "")
    lead.setdefault("court_approval_status", "Not started")
    lead.setdefault("re_score", 0)
    lead.setdefault("re_signals", [])
    lead.setdefault("attorney_name", "")

    if lead.get("branton_stage") in BRANTON_STAGE_ALIASES:
        lead["branton_stage"] = BRANTON_STAGE_ALIASES[lead["branton_stage"]]

    if "branton_stage" not in lead or lead.get("branton_stage") not in BRANTON_STAGES:
        lead["branton_stage"] = derive_branton_stage(lead)

    if lead.get("branton_hot"):
        lead["assigned_to_branton"] = True
        lead["assigned_to"] = PARTNER_NAME
        if lead.get("status") == "New":
            lead["status"] = "Qualified"

    if "follow_up_iso" not in lead:
        try:
            lead["follow_up_iso"] = (
                datetime.strptime(lead.get("follow_up", ""), "%A, %B %d, %Y").strftime("%Y-%m-%d")
                if lead.get("follow_up") else (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
            )
        except ValueError:
            lead["follow_up_iso"] = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    return lead


def derive_branton_stage(lead: dict) -> str:
    stage = lead.get("branton_stage", "")
    if stage in BRANTON_STAGE_ALIASES:
        return BRANTON_STAGE_ALIASES[stage]
    if stage in BRANTON_STAGES:
        return stage
    status = lead.get("status", "New")
    if status == "Listed":
        return "Listing Signed"
    if status == "Closed":
        return "Closed Won"
    if status == "Appt":
        return "Appt Set"
    if status == "Interested":
        return "Interested"
    if status == "Contacted":
        return "Contacted"
    if lead.get("calls", 0) > 0 or status in (ASSIGN_STATUS, "Qualified", "Hot", "Assigned to Brantley"):
        return "Attempted"
    return "New"


def _ensure_unique_lead_ids(leads: list) -> bool:
    seen: set = set()
    changed = False
    for i, lead in enumerate(leads):
        lid = lead.get("id", "")
        if lid and lid not in seen:
            seen.add(lid)
            continue
        case_id = re.sub(r"[^A-Za-z0-9]", "", lead.get("case_number", "") or "")
        new_id = case_id or f"lead{i:04d}{datetime.now().strftime('%Y%m%d')}"
        suffix = 0
        while new_id in seen:
            suffix += 1
            new_id = f"{case_id or f'lead{i:04d}'}{suffix}"
        lead["id"] = new_id
        seen.add(new_id)
        changed = True
    return changed


def load_leads() -> list:
    if LEADS_FILE.exists():
        try:
            with open(LEADS_FILE, "r") as f:
                leads = json.load(f)
            if _ensure_unique_lead_ids(leads):
                save_leads_raw(leads)
            return [normalize_lead(l) for l in leads]
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_leads_raw(leads: list) -> None:
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)


def save_leads(leads: list) -> None:
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)


def commit_leads_and_reload() -> list:
    """Persist leads and immediately reload session state — no stale queue."""
    save_leads(st.session_state.leads)
    st.session_state.leads = load_leads()
    st.session_state.queue_version = st.session_state.get("queue_version", 0) + 1
    return st.session_state.leads


def _promote_lead_to_top(lead_id: str) -> None:
    leads = st.session_state.leads
    idx = next((i for i, l in enumerate(leads) if l.get("id") == lead_id), None)
    if idx is not None and idx > 0:
        leads.insert(0, leads.pop(idx))


def _flash_hot_queue_add(lead: dict) -> None:
    decedent = lead.get("decedent", "Lead")
    address = lead.get("address", "")
    poc = poc_display_name(lead)
    note = ""
    if lead.get("notes"):
        note = lead["notes"][0].get("text", "")
    st.session_state.branton_last_added_id = lead.get("id", "")
    st.session_state.branton_queue_flash = (
        f"🔥 **{decedent}** added to HOT queue — **{address}** · POC: {poc}"
        + (f" · {note[:60]}" if note else "")
    )
    st.session_state.leads_need_reload = True


if "leads" not in st.session_state:
    st.session_state.leads = load_leads()
else:
    ids = [l.get("id") for l in st.session_state.leads]
    if len(ids) != len(set(ids)):
        st.session_state.leads = load_leads()
        save_leads(st.session_state.leads)

VENDOR_CATEGORIES = [
    "Probate Attorney",
    "Estate Sale",
    "Contents Removal / Dump Truck",
    "Movers",
    "Cleaning",
    "Sentimental Item Shipping",
    "Repairs / Funded Repairs",
    "Express Offers",
]


def _vendor_slot(primary: str = "") -> dict:
    return {
        "vendor_1": primary or "[Name] · [Contact] · [Phone]",
        "vendor_2": "",
        "vendor_3": "",
        "area_notes": "",
    }


DEFAULT_VENDORS = {
    "Probate Attorney": _vendor_slot("[Attorney Name] · [Firm] · [Phone]"),
    "Estate Sale": _vendor_slot("[Company Name] · [Contact] · [Phone]"),
    "Contents Removal / Dump Truck": _vendor_slot("[Haul-Off Service] · [Contact] · [Phone]"),
    "Movers": _vendor_slot("[Company Name] · [Contact] · [Phone]"),
    "Cleaning": _vendor_slot("[Cleaning Service] · [Contact] · [Phone]"),
    "Sentimental Item Shipping": _vendor_slot("[Packing & Shipping Service] · [Contact] · [Phone]"),
    "Repairs / Funded Repairs": _vendor_slot("[Contractor / Funded Repairs Partner] · [Phone]"),
    "Express Offers": _vendor_slot(
        "eXp Express Offers Network · Multiple vetted cash buyers · Scott Hardesty 615-953-0758"
    ),
}


def migrate_vendors(raw: dict) -> dict:
    if "Repairs" in raw and "Repairs / Funded Repairs" not in raw:
        raw["Repairs / Funded Repairs"] = raw.pop("Repairs")

    migrated = {}
    for category in VENDOR_CATEGORIES:
        val = raw.get(category)
        if isinstance(val, str):
            migrated[category] = _vendor_slot(val)
        elif isinstance(val, dict):
            migrated[category] = {
                "vendor_1": val.get("vendor_1", ""),
                "vendor_2": val.get("vendor_2", ""),
                "vendor_3": val.get("vendor_3", ""),
                "area_notes": val.get("area_notes", ""),
            }
        else:
            migrated[category] = dict(DEFAULT_VENDORS[category])
    return migrated


def format_vendors_display(vendors: dict, category: str) -> str:
    entry = vendors.get(category, {})
    if isinstance(entry, str):
        return entry or "[TBD]"

    lines = []
    for i in range(1, 4):
        name = entry.get(f"vendor_{i}", "").strip()
        if name:
            lines.append(f"V{i}: {name}")
    notes = entry.get("area_notes", "").strip()
    if notes:
        lines.append(f"Notes: {notes}")
    return " · ".join(lines) if lines else "[TBD]"


if "vendors" not in st.session_state:
    st.session_state.vendors = migrate_vendors(dict(DEFAULT_VENDORS))
else:
    st.session_state.vendors = migrate_vendors(st.session_state.vendors)


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
    if parsed.get("court_export"):
        return score_court_lead(parsed)

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


# ── County court export (tncrtinfo.com / CaseLink) ───────────────────────────
ESTATE_RE = re.compile(
    r"(?:Estate of|IN RE:?\s*(?:THE\s+)?ESTATE OF)\s+(.+?)(?:\s*,|\s*$|\s+Case|\t)",
    re.IGNORECASE,
)
CONTACT_RE = re.compile(
    r"^(.+?),\s*(?:Administratrix|Executrix|Administrator|Executor|Personal Representative)\b",
    re.IGNORECASE,
)
PR_OF_RE = re.compile(
    r"(.+?),\s*PR of the Estate of\s+(.+)",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b(\d{1,2}/\d{1,2}/(202[4-9]|\d{2}))\b|"
    r"\b((202[4-9])-\d{2}-\d{2})\b|"
    r"\b(\d{1,2}-\d{1,2}-(202[4-9]))\b"
)
CASE_NUMBER_RE = re.compile(r"\b(PR\s*20\d{2}\s*[-–]\s*\d+)\b", re.IGNORECASE)
DECEDENT_INLINE_RE = re.compile(
    r"(?:IN\s+RE:?\s*(?:THE\s+)?)?ESTATE\s+OF\s+([^,\t\n\|;]{2,80}?)"
    r"(?=\s*,|\s*\t|\s+\d{1,2}/\d{1,2}/\d{2,4}|\s+PR\s*20|\s+PENDING|\s+Probate|\s+Open|\s+Closed|\s+Case|\n|$)",
    re.IGNORECASE,
)
PR_NAME_RE = re.compile(
    r"Administratrix|Executrix|Administrator|Executor|Personal\s+Representative|"
    r"PR\s+of\s+the\s+Estate|Conservator|Guardian",
    re.IGNORECASE,
)
JUNK_WORDS_RE = re.compile(r"\b(PENDING|Probate|Open|Closed|Case\s+Type|Style\s+of\s+Case)\b", re.IGNORECASE)
CASELINK_JUNK_LINE_RE = re.compile(
    r"view\s+image|click\s+to\s+view|document\s+image|\.pdf\b|\.jpg\b|\.png\b|"
    r"javascript:|print\s+this\s+page|logout|sign\s+in|caselink\s+home|"
    r"return\s+to\s+(?:search|list|results)|back\s+to\s+list|search\s+again|"
    r"^\s*page\s+\d+\s+of\s+\d+\s*$|document\s+list|filing\s+queue",
    re.IGNORECASE,
)
CASELINK_LABEL_RE = re.compile(
    r"^(?:Case\s*(?:Number|#)|Style\s+of\s+Case|Case\s+Style|File\s*Date|"
    r"Filing\s+Date|Status|Party\s+Name|Party\s+Type)\s*:?\s*(.+)$",
    re.IGNORECASE,
)
STREET_ADDR_RE = re.compile(
    r"(\d+\s+[\w\s\.\#'-]+(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Ln|Lane|"
    r"Ct|Court|Way|Blvd|Pike|Circle|Cir|Place|Pl|Trl|Trail|Ter|Terrace)\.?,?\s*"
    r"[\w\s,.'-]+(?:TN\s*\d{5}|\bNashville\b|\bTN\b))",
    re.IGNORECASE,
)
REAL_ESTATE_RE = re.compile(
    r"real\s*property|real\s*estate|residence|homestead|devised|devise|parcel|"
    r"\d+\s+[\w\s]+(?:Rd|Road|St|Street|Ave|Avenue|Dr|Drive|Ln|Lane|Ct|Court|Way|Blvd|Pike)\.?,?\s*[\w\s]+,?\s*TN",
    re.IGNORECASE,
)
OPEN_RE = re.compile(r"\bOpen\b", re.IGNORECASE)
ROLE_RE = re.compile(r"Administratrix|Executrix|Administrator|Executor|Personal Representative|PR of the Estate", re.I)


def _parse_name_parts(full_name: str) -> tuple:
    parts = [p for p in re.sub(r"[,\\.]", " ", full_name).split() if p]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], parts[-1]


CASELINK_URL = "https://caselink.nashville.gov/"
DAVIDSON_FREE_BULK_URL = "https://davidson.tncrtinfo.com/"

MIDDLE_TN_COUNTY_LINKS = {
    "Wilson County": {
        "emoji": "🏡",
        "rank": 1,
        "mode": "courthouse",
        "tncrtinfo": "https://wilson.tncrtinfo.com/",
        "chancery": "https://wilcoclerkandmaster.com/chancery-court/",
        "assessor": "https://wilsontn.geopowered.com/propertysearch/",
        "clerk_phone": "615-443-2610",
        "courthouse": "228 E Main St, Lebanon, TN 37087",
        "maps": "https://maps.google.com/?q=228+E+Main+St+Lebanon+TN+37087",
    },
    "Davidson County": {
        "emoji": "🏙️",
        "rank": 2,
        "mode": "online",
        "tncrtinfo": "https://davidson.tncrtinfo.com/",
        "chancery": "https://ccc.nashville.gov/",
        "assessor": "https://www.padctn.org/real-property-search/",
        "probate_lookup": "https://circuitclerk.nashville.gov/probate-estate-lookup/",
        "dockets": "https://portal-tnnashville.tylertech.cloud/PublicAccess/default.aspx",
        "caselink": CASELINK_URL,
        "clerk_phone": "615-862-5721",
        "courthouse": "1 Public Sq, Nashville, TN 37201",
        "maps": "https://maps.google.com/?q=Davidson+County+Circuit+Court+Clerk+Nashville+TN",
    },
    "Rutherford County": {
        "emoji": "⚖️",
        "rank": 3,
        "mode": "courthouse",
        "tncrtinfo": "https://rutherford.tncrtinfo.com/",
        "chancery": "https://rcchancery.com/",
        "assessor": "https://rcpatn.com/",
        "clerk_phone": "615-898-7800",
        "courthouse": "20 Public Square, Murfreesboro, TN 37130",
        "maps": "https://maps.google.com/?q=20+Public+Square+Murfreesboro+TN+37130",
    },
    "Williamson County": {
        "emoji": "🌳",
        "rank": 4,
        "mode": "courthouse",
        "tncrtinfo": "https://williamson.tncrtinfo.com/",
        "chancery": "https://williamsonchancery.org/",
        "assessor": "https://inigo.williamson-tn.org/property_search/",
        "clerk_phone": "615-790-5454",
        "courthouse": "135 4th Ave S, Franklin, TN 37064",
        "maps": "https://maps.google.com/?q=135+4th+Ave+S+Franklin+TN+37064",
    },
    "Sumner County": {
        "emoji": "📋",
        "rank": 5,
        "mode": "courthouse",
        "primary_branton": True,
        "tncrtinfo": "https://sumner.tncrtinfo.com/",
        "chancery": "https://sumnerchancerycourt.com/probate/",
        "assessor": "https://sumnertn.geopowered.com/propertysearch/",
        "clerk_phone": "615-442-3411",
        "courthouse": "355 N Belvedere Dr, Gallatin, TN 37066",
        "maps": "https://maps.google.com/?q=355+N+Belvedere+Dr+Gallatin+TN+37066",
    },
}

OUTER_COUNTY_VISIT_CHECKLIST = [
    ("call_clerk", "📞 Call clerk — ask about new probate filings with real property"),
    ("scan_filings", "📂 Scan new filings (courthouse or tncrtinfo export)"),
    ("assessor_check", "🏠 Assessor check — confirm house exists + value range"),
    ("paste_batch", "📋 Paste batch here → auto-score → Branton Call Queue"),
]

DAILY_ROUTINE_BRANTON = [
    ("mon_am_queue", "☀️ Open Call Queue — hit all DUE TODAY + 🔥 hot leads first"),
    ("mon_davidson", "🏙️ Davidson: Scott pulls CaseLink · you paste + call new inventories"),
    ("tue_courthouse", "🏛️ Courthouse run per weekly schedule (Sumner primary)"),
    ("wed_followup", "📞 3-touch follow-ups on prior week leads (minimum)"),
    ("thu_assessor", "🏠 Assessor spot-check every lead before calling"),
    ("fri_blitz", "🔥 Friday blitz — clear queue · log CRM · send Scott recap"),
    ("daily_script", "🎙️ Generate script + Guardian Kit BEFORE every appointment"),
    ("daily_log", "✅ Log every call on Dashboard — status + notes same day"),
]

WEEKLY_TARGETS = [
    ("🎯 First contacts", "50+ calls/week on fresh filings"),
    ("📅 Appointments", "10+ booked (10–15 min, not listing pitch)"),
    ("🏠 Listings", "3 signed listings/month (50/50 split)"),
    ("🏛️ Courthouse", "2 runs/week — Sumner every week + 1 rotate county"),
    ("🏙️ Davidson", "2 CaseLink pulls/week — inventories + sell petitions"),
    ("🔥 Hot queue", "Zero 78+ leads older than 48 hours"),
]

WIN_NOTE = (
    "**This is How We Win:** Davidson = online speed (CaseLink beats paid services). "
    "Outer counties = sweat equity courthouse runs nobody else will do. "
    "We paste → auto-score → call FIRST → Guardian Kit → listing. "
    "Compassion wins the family. Speed wins the deal. **50/50 on every probate close.**"
)

ROTATE_COUNTIES = ["Wilson County", "Rutherford County", "Williamson County"]


def obituary_search_urls(decedent: str = "", county: str = "") -> dict:
    county_q = county.replace(" County", "") if county else "Middle Tennessee"
    month_year = datetime.now().strftime("%B %Y")
    name_q = decedent.strip() if decedent else ""
    templates = {
        "🔍 Google Obituaries": f"obituary {name_q} {county_q} TN".strip(),
        "📰 Legacy.com": f"site:legacy.com {name_q} {county_q} Tennessee".strip(),
        "🕊️ Dignity Memorial": f"site:dignitymemorial.com {name_q} Tennessee".strip(),
        "📰 Tennessean": f"site:tennessean.com obituary {name_q}".strip(),
        "🆕 Fresh 7-Day Scan": f"obituary {county_q} County TN {month_year}",
    }
    return {label: f"https://www.google.com/search?q={quote(q)}" for label, q in templates.items()}


def lead_to_parsed(lead: dict) -> dict:
    return {
        "decedent": lead.get("decedent", "Unknown Decedent"),
        "address": lead.get("address", "Address TBD"),
        "county": lead.get("county", "Middle TN"),
        "heirs": lead.get("heirs", "") or lead.get("contact_name", "Contact TBD"),
        "phone": lead.get("phone", ""),
        "email": lead.get("email", ""),
    }


def get_branton_call_queue(leads: list) -> list:
    """HOT queue = manually marked Has RE + recent (branton_hot only)."""
    today = datetime.now().strftime("%Y-%m-%d")
    queue = [l for l in leads if l.get("branton_hot")]

    def sort_key(lead: dict) -> tuple:
        due = lead.get("follow_up_iso", "9999-12-31") <= today
        recency = lead.get("recency_days") if lead.get("recency_days") is not None else 9999
        return (
            0 if lead.get("branton_hot") else 1,
            0 if due else 1,
            recency,
            -lead.get("score", 0),
        )

    return sorted(queue, key=sort_key)


def get_courthouse_run_schedule() -> dict:
    week = datetime.now().isocalendar()[1]
    rotation = ROTATE_COUNTIES[(week - 1) % len(ROTATE_COUNTIES)]
    days = [
        ("Monday", "Sumner County", "Branton PRIMARY — courthouse or tncrtinfo"),
        ("Tuesday", rotation, "Rotating outer county — in-person scan"),
        ("Wednesday", "Davidson County", "ONLINE — Scott CaseLink · Branton calls"),
        ("Thursday", "Sumner County", "Sumner follow-up + clerk call"),
        ("Friday", "All Counties", "Call Queue blitz + paste all batches"),
    ]
    return {"week": week, "rotation": rotation, "days": days}


def clerk_call_script(county: str) -> str:
    info = MIDDLE_TN_COUNTY_LINKS.get(county, {})
    phone = info.get("clerk_phone", "[clerk phone]")
    short = county.replace(" County", "")
    return f"""═══════════════════════════════════════════
  CLERK CALL SCRIPT — {county.upper()}
  {PARTNER_NAME} · ProbateGuardian · 615-953-0758
═══════════════════════════════════════════

"Hi, my name is Branton Walker — I'm a local Realtor helping
families with probate property questions in {short} County.

I'm not an attorney. I'm just trying to be respectful and early
for families who may need help with a residence in the estate.

Could you help me with one quick question?

**Are there any NEW probate estates filed this week that list
real property or a residence address?**

[If yes:] Could you share the case style or filing date so I
can look it up on tncrtinfo? I want to make sure I'm not
bothering anyone too early.

[If they can't share:] No problem — I'll pull tncrtinfo and
visit in person. Thank you for your time.

**Clerk phone:** {phone}
**Courthouse:** {info.get('courthouse', '')}

Always polite. Never pushy. Clerk is your ally."""


def lookup_urls(contact: str, address: str = "", county: str = "Sumner County") -> dict:
    fn, ln = _parse_name_parts(contact)
    city = "Gallatin" if "sumner" in county.lower() else "Mount Juliet"
    bv = f"https://www.beenverified.com/rf/search/v2?fn={quote(fn)}&ln={quote(ln)}&city={quote(city)}&state=TN"
    if address and address != "Address TBD":
        ps = f"https://www.google.com/search?q={quote('propstream ' + address)}"
    else:
        decedent_hint = contact.split(",")[0] if contact else ""
        ps = f"https://www.google.com/search?q={quote('propstream ' + decedent_hint + ' ' + county + ' TN')}"
    return {"beenverified": bv, "propstream": ps}


def _extract_filing_year(text: str) -> int:
    for m in DATE_RE.finditer(text):
        g = m.groups()
        if g[0]:
            return int(g[0].split("/")[-1])
        if g[2]:
            return int(g[2])
    yr = re.search(r"PR(202[4-6])-", text)
    if yr:
        return int(yr.group(1))
    return 0


def parse_filing_date_obj(text: str):
    text = (text or "").strip()
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    m = DATE_RE.search(text)
    if m:
        raw = m.group(0)
        for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                pass
    return None


def compute_recency(filing_dt) -> tuple:
    """Returns (days_ago, tier, bonus_score, is_recent_30)."""
    if not filing_dt:
        return None, "unknown", 0, False
    days = (datetime.now() - filing_dt).days
    if days < 0:
        days = 0
    if days <= RECENCY_HIGH_DAYS:
        return days, "high", 40, True
    if days <= 90:
        return days, "medium", 22, False
    if days <= 365:
        return days, "low", 8, False
    return days, "stale", 0, False


def assessor_search_url(county: str, decedent: str, address: str = "") -> str:
    info = MIDDLE_TN_COUNTY_LINKS.get(county, MIDDLE_TN_COUNTY_LINKS.get("Davidson County", {}))
    base = info.get("assessor", "https://www.padctn.org/real-property-search/")
    clean = re.sub(r"(?i)^estate of\s+", "", decedent).strip()
    parts = clean.split()
    last = parts[-1] if parts else clean
    first = parts[0] if parts else ""
    if address and address != "Address TBD":
        q = f"{address} {county} TN property"
        return f"https://www.google.com/search?q={quote(q)}"
    if "Davidson" in county:
        return (
            f"https://www.google.com/search?q={quote('site:padctn.org ' + last + ' ' + first + ' Davidson property')}"
        )
    return f"https://www.google.com/search?q={quote(last + ' ' + county + ' TN property assessor owner')}"


def _extract_decedent(text: str) -> str:
    m = ESTATE_RE.search(text)
    if m:
        return m.group(1).strip()
    if "Estate of" in text:
        chunk = text.split("Estate of", 1)[1].strip()
        return re.split(r"\t|,|\n", chunk)[0].strip()
    return "Unknown Decedent"


def _is_caselink_junk_line(line: str) -> bool:
    line = (line or "").strip()
    if not line:
        return True
    if CASELINK_JUNK_LINE_RE.search(line):
        return True
    if re.match(r"^[\s\-_=|*#]+$", line):
        return True
    return False


def _is_plausible_address(addr: str) -> bool:
    if not addr or addr == "Address TBD":
        return False
    return bool(STREET_ADDR_RE.search(addr))


def _normalize_address(addr: str, fallback_text: str = "") -> str:
    if _is_plausible_address(addr):
        return STREET_ADDR_RE.search(addr).group(1).strip()
    if fallback_text:
        m = STREET_ADDR_RE.search(fallback_text)
        if m:
            return m.group(1).strip()
    return ""


def _line_segments(line: str) -> list:
    line = (line or "").strip()
    if not line:
        return []
    if "\t" in line or "|" in line:
        return [p.strip() for p in re.split(r"[\t|]+", line) if p.strip()]
    return [line]


def _bulk_line_parts(line: str) -> list:
    """Split bulk row — 5th field keeps pipes/tabs inside long notes."""
    line = (line or "").strip()
    if not line:
        return []
    if "|" in line:
        return [p.strip() for p in line.split("|", 4) if p.strip()]
    if "\t" in line:
        return [p.strip() for p in line.split("\t", 4) if p.strip()]
    return [line]


def _extract_address_from_text(text: str) -> str:
    skip_vals = {"open", "closed", "probate", "pending", "unknown", "personal representative"}
    for line in (text or "").splitlines():
        for part in _line_segments(line):
            lower = part.lower()
            if lower in skip_vals or CASE_NUMBER_RE.search(part):
                continue
            if DATE_RE.fullmatch(part.strip()):
                continue
            m = STREET_ADDR_RE.search(part)
            if m:
                return m.group(1).strip()
            m2 = re.search(
                r"(?:Real\s+Property|Residence|homestead)\s*[-:]\s*(\d+\s+.+)",
                part,
                re.I,
            )
            if m2:
                cand = m2.group(1).strip()
                if STREET_ADDR_RE.search(cand):
                    return STREET_ADDR_RE.search(cand).group(1).strip()
    m = STREET_ADDR_RE.search(text or "")
    if m:
        return m.group(1).strip()
    return ""


def _extract_poc_hint(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip()
        if _is_caselink_junk_line(line):
            continue
        segments = _line_segments(line)
        for seg in segments:
            if re.search(r"estate\s+of|in\s+re", seg, re.I) and not PR_NAME_RE.search(seg):
                continue
            m = CONTACT_RE.match(seg)
            if m:
                return _sanitize_poc_name(m.group(1).strip())
            m2 = PR_OF_RE.search(seg)
            if m2:
                return _sanitize_poc_name(m2.group(1).strip())
            m3 = re.search(
                r"(?:Executrix|Administratrix|Administrator|Executor|Personal\s+Representative)"
                r"\s*:\s*([^,\n|]+)",
                seg,
                re.I,
            )
            if m3:
                return _sanitize_poc_name(m3.group(1).strip())
            if ROLE_RE.search(seg) and "," in seg:
                name = seg.split(",")[0].strip()
                if _sanitize_poc_name(name) != "POC TBD":
                    return _sanitize_poc_name(name)
            m4 = re.match(r"^PR\s*:\s*(.+)$", seg, re.I)
            if m4:
                return _sanitize_poc_name(m4.group(1).strip())
        m5 = CASELINK_LABEL_RE.match(line)
        if m5 and re.search(r"personal\s+representative|administratrix|executrix|administrator|executor", line, re.I):
            val = m5.group(1).strip()
            if "," in val:
                return _sanitize_poc_name(val.split(",")[0].strip())
    return ""


def _split_caselink_sections(raw: str) -> list:
    """Group lines into per-case sections (CaseLink pages + multi-line blocks)."""
    sections = []
    current_lines = []
    current_case = None
    for ln in (raw or "").splitlines():
        if _is_caselink_junk_line(ln):
            continue
        m = CASE_NUMBER_RE.search(ln)
        if m:
            key = _normalize_case_number(m.group(1))
            if current_lines and current_case and key != current_case:
                sections.append("\n".join(current_lines))
                current_lines = []
            current_case = key
        if m or current_lines:
            current_lines.append(ln)
    if current_lines:
        sections.append("\n".join(current_lines))
    return sections


def _parse_labeled_section(section: str) -> dict:
    """Extract labeled CaseLink / tncrtinfo fields from a section."""
    fields = {"case_number": "", "decedent": "", "filing_date": "", "poc_hint": "", "address": ""}
    for line in section.splitlines():
        m = CASELINK_LABEL_RE.match(line.strip())
        if not m:
            continue
        val = m.group(1).strip()
        lower_line = line.lower()
        if "case" in lower_line and "number" in lower_line and CASE_NUMBER_RE.search(val):
            fields["case_number"] = CASE_NUMBER_RE.search(val).group(1)
        elif "style" in lower_line:
            fields["decedent"] = _extract_decedent_from_chunk(val) or _clean_person_name(val)
        elif "file" in lower_line or "filing" in lower_line:
            dm = DATE_RE.search(val)
            if dm:
                fields["filing_date"] = dm.group(0)
        elif "party" in lower_line:
            if PR_NAME_RE.search(val) or PR_NAME_RE.search(line):
                fields["poc_hint"] = _sanitize_poc_name(val.split(",")[0].strip())
    if not fields["address"]:
        fields["address"] = _normalize_address(_extract_address_from_text(section), section)
    if not fields["poc_hint"]:
        fields["poc_hint"] = _extract_poc_hint(section)
    if not fields["decedent"]:
        fields["decedent"] = _extract_decedent_from_chunk(section)
    if not fields["case_number"]:
        cm = CASE_NUMBER_RE.search(section)
        if cm:
            fields["case_number"] = cm.group(1)
    if not fields["filing_date"]:
        dm = DATE_RE.search(section)
        if dm:
            fields["filing_date"] = dm.group(0)
    return fields


def _extract_contact(text: str) -> tuple:
    for line in text.splitlines():
        line = line.strip()
        if not line or _is_caselink_junk_line(line):
            continue
        m = CONTACT_RE.match(line)
        if m:
            return m.group(1).strip(), "PR/Administratrix/Executrix"
        m2 = PR_OF_RE.search(line)
        if m2:
            return m2.group(1).strip(), "PR of the Estate"
        if ROLE_RE.search(line) and "," in line:
            name = line.split(",")[0].strip()
            if name and "Estate of" not in name:
                return name, "Court Party"
    return "", ""


def parse_court_row_block(block: str, default_county: str = "Sumner County") -> dict:
    text = block.strip()
    decedent = _extract_decedent(text)
    contact, role = _extract_contact(text)
    address = _extract_address_from_text(text) or "Address TBD"
    if address != "Address TBD" and "\n" in address:
        address = _extract_address_from_text(address.split("\n")[0]) or address.split("\n")[-1].strip()
    county_m = re.search(
        r"(Wilson|Davidson|Rutherford|Williamson|Sumner|Robertson|Cheatham|Dickson|Montgomery|Maury)\s+County",
        text,
        re.IGNORECASE,
    )
    county = county_m.group(0) if county_m else default_county
    case_m = re.search(r"(PR\d{4}-\d+)", text, re.IGNORECASE)
    filing_year = _extract_filing_year(text)
    filing_display = ""
    dm = DATE_RE.search(text)
    if dm:
        filing_display = dm.group(0)
    filing_dt = parse_filing_date_obj(filing_display or text)
    recency_days, recency_tier, _, is_recent_30 = compute_recency(filing_dt)
    if not filing_year and filing_dt:
        filing_year = filing_dt.year

    return {
        "decedent": decedent,
        "address": address,
        "county": county,
        "heirs": contact or "Contact TBD",
        "contact_name": contact,
        "contact_role": role,
        "phone": "",
        "email": "",
        "case_number": case_m.group(1) if case_m else "",
        "filing_date": filing_display or (filing_dt.strftime("%m/%d/%Y") if filing_dt else ""),
        "filing_year": filing_year,
        "filing_dt": filing_dt.isoformat() if filing_dt else "",
        "recency_days": recency_days,
        "recency_tier": recency_tier,
        "is_recent_30": is_recent_30,
        "court_status": "Open" if OPEN_RE.search(text) else ("Closed" if re.search(r"\bClosed\b", text, re.I) else "Unknown"),
        "has_real_estate": address != "Address TBD",
        "court_export": True,
        "raw": text,
    }


def _block_from_minimal_fields(decedent: str, case_no: str, filing: str, county: str) -> str:
    dec = decedent if re.search(r"estate of", decedent, re.I) else f"Estate of {decedent}"
    return f"{dec}\n{case_no}\n{filing}\nOpen\n{county}"


def _normalize_case_number(case_no: str) -> str:
    c = re.sub(r"\s+", "", (case_no or "").upper())
    return c.replace("–", "-").replace("—", "-")


def _clean_person_name(name: str) -> str:
    name = (name or "").strip()
    name = re.sub(r"(?i)^in\s+re:?\s*(the\s+)?estate\s+of\s+", "", name)
    name = re.sub(r"(?i)^estate\s+of\s+", "", name)
    name = DATE_RE.sub("", name)
    name = JUNK_WORDS_RE.sub("", name)
    name = re.split(
        r",\s*(?:Administratrix|Executrix|Administrator|Executor|Personal Representative|PR)\b",
        name,
        flags=re.I,
    )[0]
    name = re.sub(r"\s*[-–—|]\s*$", "", name)
    return name.strip(" ,;|.\t")


def _is_valid_decedent(name: str) -> bool:
    if not name or len(name) < 3:
        return False
    lower = name.lower()
    if lower in (
        "unknown", "pending", "probate", "open", "closed", "contact tbd",
        "unknown decedent", "n/a", "none", "davidson county", "nashville tn",
    ):
        return False
    if CASE_NUMBER_RE.search(name):
        return False
    if PR_NAME_RE.search(name) and "," not in name:
        return False
    if re.fullmatch(r"[\W\d]+", name):
        return False
    return True


def _nearest_date_in_text(text: str, pos: int, window: int = 220) -> str:
    start = max(0, pos - window)
    end = min(len(text), pos + window)
    chunk = text[start:end]
    dates = list(DATE_RE.finditer(chunk))
    if not dates:
        return ""
    rel_pos = pos - start
    best = min(dates, key=lambda m: abs(m.start() - rel_pos))
    return best.group(0)


def _extract_decedent_from_chunk(chunk: str) -> str:
    for pattern in (DECEDENT_INLINE_RE, ESTATE_RE):
        m = pattern.search(chunk)
        if m:
            name = _clean_person_name(m.group(1))
            if _is_valid_decedent(name):
                return name
    return ""


def _extract_county_from_snippet(snippet: str, default_county: str) -> str:
    county_m = re.search(
        r"(Wilson|Davidson|Rutherford|Williamson|Sumner|Robertson|Cheatham|Dickson|Montgomery|Maury)\s+County",
        snippet,
        re.IGNORECASE,
    )
    return county_m.group(0) if county_m else default_county


def _caselink_cases_from_raw(raw: str, default_county: str = "Davidson County") -> dict:
    """Build merged case records dict keyed by normalized case number."""
    raw = (raw or "").strip()
    cases: dict = {}
    if not raw:
        return cases

    lines = [ln for ln in raw.splitlines() if ln.strip()]

    def _upsert_case(
        case_no: str,
        decedent: str,
        filing: str,
        snippet: str,
        county: str = "",
        source_rank: int = 1,
    ) -> None:
        key = _normalize_case_number(case_no)
        if not key or not re.search(r"PR20\d{2}-\d+", key, re.I):
            return
        case_display = re.sub(r"\s+", "", case_no.upper()).replace("–", "-").replace("—", "-")
        dec = _clean_person_name(decedent) if decedent else ""
        filing_dt = parse_filing_date_obj(filing)
        filing_display = filing or (filing_dt.strftime("%m/%d/%Y") if filing_dt else "")
        cnty = county or _extract_county_from_snippet(snippet, default_county)
        clean_snippet = (snippet or "").strip()
        if len(clean_snippet) > 240:
            line_start = clean_snippet.find("\n")
            clean_snippet = clean_snippet[: line_start if line_start > 0 else 240]

        poc_hint = _extract_poc_hint(clean_snippet) if source_rank >= 3 else ""
        address = _normalize_address(
            _extract_address_from_text(clean_snippet) if source_rank >= 3 else "",
            clean_snippet,
        )

        if key in cases:
            existing = cases[key]
            prev_rank = existing.get("decedent_rank", 0)
            if _is_valid_decedent(dec) and (
                existing.get("decedent") == "Unknown Decedent"
                or source_rank >= prev_rank
            ):
                existing["decedent"] = dec
                existing["decedent_rank"] = source_rank
            if not existing.get("filing_date") and filing_display:
                existing["filing_date"] = filing_display
                existing["filing_dt"] = filing_dt.isoformat() if filing_dt else ""
            if poc_hint and (not existing.get("poc_hint") or source_rank >= existing.get("snippet_rank", 0)):
                existing["poc_hint"] = poc_hint
            if address and (not existing.get("address") or source_rank >= existing.get("snippet_rank", 0)):
                existing["address"] = address
            if clean_snippet and source_rank >= existing.get("snippet_rank", 0):
                existing["source_line"] = clean_snippet
                existing["snippet_rank"] = source_rank
            return

        cases[key] = {
            "case_number": case_display,
            "decedent": dec if _is_valid_decedent(dec) else "Unknown Decedent",
            "decedent_rank": source_rank if _is_valid_decedent(dec) else 0,
            "filing_date": filing_display,
            "filing_dt": filing_dt.isoformat() if filing_dt else "",
            "county": cnty,
            "source_line": clean_snippet,
            "snippet_rank": source_rank,
            "poc_hint": poc_hint,
            "address": address,
        }

    header_like = bool(lines) and re.search(
        r"case\s*(number|#)|style\s+of\s+case|file\s*date|party\s+name",
        lines[0],
        re.I,
    )
    data_lines = lines[1:] if header_like else lines

    for ln in data_lines:
        if _is_caselink_junk_line(ln):
            continue
        if "\t" in ln:
            cols = [c.strip() for c in ln.split("\t") if c.strip()]
            if len(cols) < 2:
                continue
            case_col = next((c for c in cols if CASE_NUMBER_RE.search(c)), cols[0])
            case_m = CASE_NUMBER_RE.search(case_col)
            if not case_m:
                continue
            style = next((c for c in cols if re.search(r"estate\s+of|in\s+re", c, re.I)), "")
            if not style and len(cols) > 1:
                style = cols[1] if not CASE_NUMBER_RE.search(cols[1]) else ""
            decedent = _extract_decedent_from_chunk(style) or _clean_person_name(style)
            if decedent and PR_NAME_RE.search(decedent) and not re.search(r"estate\s+of", style, re.I):
                decedent = ""
            filing = next((c for c in cols if DATE_RE.search(c)), "")
            _upsert_case(case_m.group(1), decedent, filing, ln, source_rank=3)
            continue

        if CASE_NUMBER_RE.search(ln):
            case_m = CASE_NUMBER_RE.search(ln)
            decedent = _extract_decedent_from_chunk(ln)
            if not decedent:
                parts = re.split(r"[,|\t;]+", ln)
                for part in parts:
                    p = part.strip()
                    if CASE_NUMBER_RE.search(p) or DATE_RE.search(p) or JUNK_WORDS_RE.search(p):
                        continue
                    if re.search(r"estate\s+of|in\s+re", p, re.I):
                        decedent = _extract_decedent_from_chunk(p) or _clean_person_name(p)
                        break
                    if _is_valid_decedent(_clean_person_name(p)):
                        decedent = _clean_person_name(p)
                        break
            filing_m = DATE_RE.search(ln)
            filing = filing_m.group(0) if filing_m else ""
            _upsert_case(case_m.group(1), decedent, filing, ln, source_rank=3)

    # Second pass: attach orphan POC / address lines to preceding case
    last_key = None
    for ln in data_lines:
        if _is_caselink_junk_line(ln):
            continue
        m = CASE_NUMBER_RE.search(ln)
        if m:
            last_key = _normalize_case_number(m.group(1))
            continue
        if not last_key or last_key not in cases:
            continue
        addr_only = _extract_address_from_text(ln)
        if addr_only and not cases[last_key].get("address"):
            cases[last_key]["address"] = _normalize_address(addr_only, ln)
            continue
        poc_only = _extract_poc_hint(ln)
        if poc_only and poc_only != "POC TBD" and not cases[last_key].get("poc_hint"):
            cases[last_key]["poc_hint"] = poc_only

    # Section pass: full CaseLink page blocks (highest fidelity for POC + address)
    for section in _split_caselink_sections(raw):
        labeled = _parse_labeled_section(section)
        case_no = labeled.get("case_number") or ""
        if not case_no:
            continue
        dec = labeled.get("decedent") or _extract_decedent_from_chunk(section)
        filing = labeled.get("filing_date") or ""
        poc = labeled.get("poc_hint") or ""
        addr = labeled.get("address") or ""
        _upsert_case(case_no, dec, filing, section, source_rank=4)
        key = _normalize_case_number(case_no)
        if key in cases:
            if poc and poc != "POC TBD":
                cases[key]["poc_hint"] = poc
            if addr:
                cases[key]["address"] = _normalize_address(addr, section)

    for m in CASE_NUMBER_RE.finditer(raw):
        pos = m.start()
        window = 380
        start = max(0, pos - window)
        end = min(len(raw), pos + window)
        chunk = raw[start:end]
        decedent = _extract_decedent_from_chunk(chunk)
        if not decedent:
            line_start = raw.rfind("\n", 0, pos) + 1
            line_end = raw.find("\n", pos)
            if line_end == -1:
                line_end = len(raw)
            line = raw[line_start:line_end]
            before = line[: line.upper().find(m.group(1).upper())].strip(" ,;|.\t>-")
            after = line[line.upper().find(m.group(1).upper()) + len(m.group(1)) :].strip(" ,;|.\t>-")
            for candidate in (before, after):
                if re.search(r"estate\s+of|in\s+re", candidate, re.I):
                    decedent = _extract_decedent_from_chunk(candidate)
                else:
                    decedent = _clean_person_name(candidate)
                if _is_valid_decedent(decedent):
                    break
                decedent = ""
        filing = _nearest_date_in_text(raw, pos)
        _upsert_case(m.group(1), decedent, filing, chunk, source_rank=1)

    for m in DECEDENT_INLINE_RE.finditer(raw):
        decedent = m.group(1)
        pos = m.start()
        window = 420
        start = max(0, pos - window)
        end = min(len(raw), pos + window)
        chunk = raw[start:end]
        case_matches = list(CASE_NUMBER_RE.finditer(chunk))
        if not case_matches:
            continue
        rel_pos = pos - start
        best_case = min(case_matches, key=lambda cm: abs(cm.start() - rel_pos))
        filing = _nearest_date_in_text(raw, pos)
        _upsert_case(best_case.group(1), decedent, filing, chunk, source_rank=2)

    return cases


def _case_record_to_block(rec: dict, default_county: str) -> str:
    block = _block_from_minimal_fields(
        rec.get("decedent", "Unknown Decedent"),
        rec.get("case_number", ""),
        rec.get("filing_date", ""),
        rec.get("county", default_county),
    )
    if rec.get("poc_hint"):
        block += f"\n{rec['poc_hint']}, Personal Representative"
    if rec.get("address"):
        block += f"\n{rec['address']}"
    if rec.get("source_line"):
        block = rec["source_line"] + "\n" + block
    return block


def extract_caselink_case_records(raw: str, default_county: str = "Davidson County") -> list:
    """Structured case list from messy CaseLink / tncrtinfo paste."""
    cases = _caselink_cases_from_raw(raw, default_county)
    records = sorted(
        cases.values(),
        key=lambda r: (
            r.get("filing_dt", "") or "",
            r.get("case_number", ""),
        ),
        reverse=True,
    )
    return records


def smart_parse_messy_paste(raw: str, default_county: str = "Davidson County") -> list:
    """Return parse blocks for legacy bulk pipeline."""
    return [
        _case_record_to_block(rec, default_county)
        for rec in extract_caselink_case_records(raw, default_county)
    ]


def split_court_export(raw: str, default_county: str = "Davidson County") -> list:
    return smart_parse_messy_paste(raw, default_county=default_county)


def score_court_lead(parsed: dict) -> tuple:
    score = 0
    flags = []
    text = parsed.get("raw", "")

    if parsed.get("decedent", "") != "Unknown Decedent":
        score += 18
        flags.append("✓ Estate of [decedent]")
    if re.search(r"Estate of", text, re.I):
        score += 7
        flags.append("✓ Estate filing")

    role = parsed.get("contact_role", "") or ""
    contact = parsed.get("contact_name", "") or parsed.get("heirs", "")
    if contact and contact != "Contact TBD":
        score += 18
        flags.append(f"✓ Contact: {contact[:30]}")
    if re.search(r"Administratrix|Executrix", text, re.I):
        score += 12
        flags.append("✓ Administratrix/Executrix")
    if re.search(r"PR of the Estate|Personal Representative", text, re.I):
        score += 8
        flags.append("✓ PR role")

    filing_dt = None
    if parsed.get("filing_dt"):
        try:
            filing_dt = datetime.fromisoformat(parsed["filing_dt"])
        except ValueError:
            filing_dt = parse_filing_date_obj(parsed.get("filing_date", ""))
    else:
        filing_dt = parse_filing_date_obj(parsed.get("filing_date", "") or text)

    recency_days, recency_tier, recency_bonus, is_recent_30 = compute_recency(filing_dt)
    parsed["recency_days"] = recency_days
    parsed["recency_tier"] = recency_tier
    parsed["is_recent_30"] = is_recent_30

    if is_recent_30:
        score += recency_bonus
        flags.append(f"✓ Recent filing ({recency_days}d ago) — HIGH")
    elif recency_tier == "medium":
        score += recency_bonus
        flags.append(f"✓ Filing {recency_days}d ago")
    elif recency_tier == "low":
        score += recency_bonus
        flags.append(f"✓ Filing {recency_days}d ago — aging")
    elif recency_tier == "stale":
        flags.append("✗ Stale filing — low priority")

    year = parsed.get("filing_year") or _extract_filing_year(text)
    if year in (2025, 2026) and not is_recent_30:
        score += 10
        flags.append(f"✓ Filing year {year}")

    if parsed.get("court_status") == "Open" or OPEN_RE.search(text):
        score += 14
        flags.append("✓ Open status")
    elif parsed.get("court_status") == "Closed":
        flags.append("✗ Closed — lower priority")

    if parsed.get("has_real_estate") or parsed.get("address", "") != "Address TBD":
        score += 18
        flags.append("✓ Has real estate")
    elif REAL_ESTATE_RE.search(text):
        score += 10
        flags.append("○ Property mention — confirm in assessor")

    if parsed.get("case_number"):
        score += 5
        flags.append(f"✓ Case {parsed['case_number']}")

    if "Sumner" in parsed.get("county", ""):
        score += 4
        flags.append("✓ Sumner County")

    parsed["branton_hot"] = False

    if score >= 55:
        status = "Qualified"
    elif score >= 30:
        status = "Needs Review"
    else:
        status = "Low Priority"

    return min(score, 100), status, flags


def upsert_court_lead(parsed: dict, score: int, status: str, flags: list) -> dict:
    case_id = parsed.get("case_number", "")
    existing = None
    if case_id:
        for lead in st.session_state.leads:
            if lead.get("case_number") == case_id:
                existing = lead
                break

    if existing:
        existing.update({
            "score": score,
            "decedent": parsed.get("decedent", existing.get("decedent")),
            "address": parsed.get("address", existing.get("address")),
            "county": parsed.get("county", existing.get("county")),
            "heirs": parsed.get("heirs", existing.get("heirs")),
            "filing_date": parsed.get("filing_date", ""),
            "recency_days": parsed.get("recency_days"),
            "recency_tier": parsed.get("recency_tier", ""),
            "has_real_estate": existing.get("has_real_estate") or parsed.get("has_real_estate", False),
            "assessor_url": assessor_search_url(
                parsed.get("county", ""),
                parsed.get("decedent", ""),
                parsed.get("address", ""),
            ),
        })
        lead = existing
    else:
        lead = build_lead(
            parsed,
            pipeline_stage="Cold",
            status="New",
            score=score,
            source="ftc_batch",
            follow_up_days=2,
            assigned_to_branton=False,
        )
        lead["case_number"] = case_id
        lead["filing_date"] = parsed.get("filing_date", "")
        lead["court_status"] = parsed.get("court_status", "")
        lead["contact_name"] = parsed.get("contact_name", "")
        lead["contact_role"] = parsed.get("contact_role", "")
        lead["has_real_estate"] = parsed.get("has_real_estate", False)
        lead["recency_days"] = parsed.get("recency_days")
        lead["recency_tier"] = parsed.get("recency_tier", "")
        lead["branton_hot"] = False
        lead["branton_stage"] = "New"
        lead["phone"] = parsed.get("phone") or PHONE_PLACEHOLDER
        poc = _sanitize_poc_name(parsed.get("contact_name", "") or parsed.get("heirs", ""))
        lead["contact_name"] = poc
        lead["heirs"] = poc
        lead["assessor_url"] = assessor_search_url(
            parsed.get("county", ""),
            parsed.get("decedent", ""),
            parsed.get("address", ""),
        )
        note = f"CaseLink import · {status} · Score {score} · " + ", ".join(flags[:5])
        lead["notes"] = [{"ts": datetime.now().isoformat(), "text": note, "by": PARTNER_NAME}]
        st.session_state.leads.insert(0, lead)

    parsed["lead_id"] = lead["id"]
    parsed["stored_status"] = lead.get("status", "New")
    return lead


def mark_lead_real_estate(lead_id: str, has_re: bool = True) -> None:
    lead = find_lead(lead_id)
    if not lead:
        return
    lead["has_real_estate"] = has_re
    lead["assessor_checked"] = True
    is_hot = has_re and lead.get("recency_tier") == "high"
    lead["branton_hot"] = is_hot
    if is_hot:
        lead["status"] = "Qualified"
        lead["assigned_to_branton"] = True
        lead["assigned_to"] = PARTNER_NAME
        lead["pipeline_stage"] = "Warm"
        lead["follow_up_iso"] = follow_up_iso(0)
        lead["follow_up"] = follow_up_date(0)
    elif not has_re:
        lead["branton_hot"] = False
        lead["assigned_to_branton"] = False
        lead["assigned_to"] = ""
        if lead.get("status") in ("Qualified", ASSIGN_STATUS, "Hot"):
            lead["status"] = "New"
        lead["pipeline_stage"] = "Cold"
    if is_hot:
        lead["branton_stage"] = "Attempted"
    lead["activity"].insert(0, {
        "ts": datetime.now().isoformat(),
        "type": "assessor",
        "detail": "Has real estate ✓" if has_re else "No real estate ✗",
    })
    for row in st.session_state.get("ftc_batch_results", []):
        if row.get("lead_id") == lead_id:
            row["has_real_estate"] = has_re
            row["branton_hot"] = is_hot
            row["ftc_ready"] = is_hot
            row["ftc_priority"] = is_hot
            row["stored_status"] = lead.get("status", "New")
    save_leads(st.session_state.leads)


def mark_all_has_real_estate(lead_ids: list) -> int:
    marked = 0
    for lead_id in lead_ids:
        if not lead_id or not find_lead(lead_id):
            continue
        mark_lead_real_estate(lead_id, True)
        marked += 1
    return marked


def advance_workflow_status(lead_id: str, new_status: str) -> None:
    lead = find_lead(lead_id)
    if not lead:
        return
    lead["status"] = new_status
    lead["pipeline_stage"] = STATUS_TO_PIPELINE.get(new_status, lead.get("pipeline_stage", "Cold"))
    stage_map = {
        "New": "New", "Qualified": "Attempted", "Contacted": "Contacted",
        "Interested": "Interested", "Appt": "Appt Set", "Listed": "Listed",
    }
    if new_status in stage_map:
        lead["branton_stage"] = stage_map[new_status]
        if lead["branton_stage"] in DRIP_STOP_STAGES:
            lead["drip_paused"] = True
    if new_status == "Contacted":
        lead["calls"] = lead.get("calls", 0) + 1
        lead["activity"].insert(0, {
            "ts": datetime.now().isoformat(),
            "type": "call",
            "detail": f"Status → Contacted (call #{lead['calls']})",
        })
    else:
        lead["activity"].insert(0, {
            "ts": datetime.now().isoformat(),
            "type": "status",
            "detail": f"Status → {new_status}",
        })
    save_leads(st.session_state.leads)


def clear_all_leads_database() -> None:
    """Wipe every lead from memory + disk — empty queue instantly."""
    st.session_state.leads = []
    save_leads_raw([])
    wipe_keys = (
        "bw_paste_leads",
        "branton_last_added_id",
        "branton_queue_flash",
        "branton_quick_add_msg",
        "branton_db_cleared",
    )
    for key in wipe_keys:
        st.session_state.pop(key, None)
    for key, empty in (
        ("ftc_batch_results", []),
        ("bulk_results", []),
        ("bulk_re_results", []),
        ("ftc_batch_raw", ""),
        ("branton_caselink_raw", ""),
        ("branton_batch_raw", ""),
        ("branton_bulk_quick_add", ""),
        ("branton_caselink_preview", []),
        ("bulk_data", ""),
    ):
        st.session_state[key] = empty


def _on_clear_demo_leads() -> None:
    clear_all_leads_database()
    st.session_state.branton_queue_flash = "✅ Queue cleared — paste new leads above."


def delete_lead(lead_id: str) -> bool:
    """Remove one lead permanently from CRM."""
    if not lead_id:
        return False
    before = len(st.session_state.leads)
    st.session_state.leads = [l for l in st.session_state.leads if l.get("id") != lead_id]
    if len(st.session_state.leads) == before:
        return False
    save_leads(st.session_state.leads)
    st.session_state.queue_version = st.session_state.get("queue_version", 0) + 1
    return True


def _sanitize_poc_name(name: str) -> str:
    name = (name or "").strip()
    if not name or name in ("Contact TBD", "—", "POC TBD"):
        return "POC TBD"
    if name.startswith("PR20") or re.match(r"PR\d{4}-\d+", name):
        return "POC TBD"
    return name.split("—")[0].split(",")[0].strip() or "POC TBD"


def _split_poc_field(poc_raw: str) -> tuple:
    poc_raw = (poc_raw or "").strip()
    if not poc_raw:
        return "POC TBD", ""
    m = re.match(r"^(.+?)\s*[\(—–-]\s*(.+?)\)?\s*$", poc_raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if "," in poc_raw:
        name, rel = poc_raw.split(",", 1)
        return name.strip(), rel.strip()
    return poc_raw, ""


def _apply_confirmed_hot_fields(lead: dict, parsed: dict, notes: str = "") -> dict:
    filing_dt = parse_filing_date_obj(parsed.get("filing_date", ""))
    recency_days, recency_tier, _, _ = compute_recency(filing_dt)
    poc_name = parsed.get("contact_name", "POC TBD")
    poc_role = parsed.get("contact_role", "")
    poc_display = f"{poc_name} ({poc_role})" if poc_role else poc_name
    county = parsed.get("county", "Davidson County")
    decedent = parsed.get("decedent", "")
    address = parsed.get("address", "Address TBD")

    lead.update({
        "decedent": decedent,
        "address": address,
        "county": county,
        "heirs": poc_display or poc_name or "POC TBD",
        "contact_name": poc_name or poc_display or "POC TBD",
        "contact_role": poc_role,
        "phone": parsed.get("phone") or lead.get("phone") or PHONE_PLACEHOLDER,
        "email": parsed.get("email") or lead.get("email", ""),
        "case_number": parsed.get("case_number", lead.get("case_number", "")),
        "filing_date": parsed.get("filing_date", ""),
        "filing_dt": filing_dt.isoformat() if filing_dt else "",
        "recency_days": recency_days,
        "recency_tier": recency_tier if recency_tier != "unknown" else "high",
        "has_real_estate": True,
        "assessor_checked": True,
        "branton_hot": True,
        "hot_queued_at": datetime.now().isoformat(),
        "branton_stage": "New",
        "assigned_to_branton": True,
        "assigned_to": PARTNER_NAME,
        "pipeline_stage": "Warm",
        "status": "Qualified",
        "score": max(lead.get("score", 0), 95),
        "follow_up_iso": follow_up_iso(0),
        "follow_up": follow_up_date(0),
        "assessor_url": assessor_search_url(county, decedent, address),
        "raw": parsed.get("raw", lead.get("raw", "")),
        "source": "quick_add_confirmed",
        "drip_paused": False,
        "drip_touch_index": 0,
        "calls": 0,
    })
    if notes.strip():
        lead["notes"].insert(0, {
            "ts": datetime.now().isoformat(),
            "text": notes.strip(),
            "by": "Scott",
        })
    lead["activity"].insert(0, {
        "ts": datetime.now().isoformat(),
        "type": "quick_add",
        "detail": "Confirmed RE — added to HOT queue 🔥",
    })
    return normalize_lead(lead)


def add_confirmed_hot_lead(
    decedent: str,
    case_number: str = "",
    filing_date: str = "",
    poc_field: str = "",
    address: str = "",
    notes: str = "",
    county: str = "Davidson County",
) -> dict:
    decedent = decedent.strip()
    address = address.strip()
    poc_name, poc_role = _split_poc_field(poc_field)
    poc_display = f"{poc_name} ({poc_role})" if poc_role else poc_name
    raw = (
        f"Estate of {decedent}\n{case_number}\n{filing_date}\n"
        f"{poc_display}\n{address}\n{notes}"
    )
    parsed = {
        "decedent": decedent,
        "address": address,
        "county": county,
        "heirs": poc_display,
        "contact_name": poc_name,
        "contact_role": poc_role,
        "phone": PHONE_PLACEHOLDER,
        "case_number": case_number.strip(),
        "filing_date": filing_date.strip(),
        "raw": raw,
    }

    existing = find_lead_by_case(case_number.strip()) if case_number.strip() else None
    if existing:
        _apply_confirmed_hot_fields(existing, parsed, notes)
        _promote_lead_to_top(existing["id"])
        commit_leads_and_reload()
        lead = find_lead(existing["id"]) or existing
        _flash_hot_queue_add(lead)
        return lead

    lead = build_lead(
        parsed,
        pipeline_stage="Warm",
        status="Qualified",
        score=95,
        source="quick_add_confirmed",
        assigned_to_branton=True,
        follow_up_days=0,
    )
    _apply_confirmed_hot_fields(lead, parsed, notes)
    st.session_state.leads.insert(0, lead)
    commit_leads_and_reload()
    lead = find_lead(lead["id"]) or lead
    _flash_hot_queue_add(lead)
    return lead


CASE_NUMBER_BULK_RE = re.compile(
    r"^(PR\d{4}-\d+|26P\d+|20\d{2}P\d+|\d{1,2}P\d+).*$",
    re.I,
)


def _looks_like_case_number(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return False
    return bool(CASE_NUMBER_BULK_RE.match(v)) or bool(re.search(r"PR20\d{2}|26P\d+", v, re.I))


def _looks_like_filing_date(value: str) -> bool:
    return bool(re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", (value or "").strip()))


PHONE_BULK_RE = re.compile(r"\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}")
EMAIL_BULK_RE = re.compile(r"[\w\.\-]+@[\w\.\-]+\.\w+", re.I)


def _extract_phone_email_from_text(text: str) -> tuple:
    """Pull first phone + email from freeform notes or contact lines."""
    blob = (text or "").strip()
    if not blob:
        return "", ""
    phone = ""
    email = ""
    pm = PHONE_BULK_RE.search(blob)
    if pm:
        phone = pm.group(0).strip()
    em = EMAIL_BULK_RE.search(blob)
    if em:
        email = em.group(0).strip()
    return phone, email


def _bulk_notes_join(parts: list) -> str:
    return "\n\n".join(p.strip() for p in parts if (p or "").strip())


def _parse_delimited_bulk_row(parts: list):
    """Flexible columns: Name | Address | POC | Case | Notes (or classic court order)."""
    parts = [p.strip() for p in parts if p and str(p).strip()]
    if len(parts) < 2:
        return None

    decedent = parts[0].strip()
    if decedent.lower().startswith("estate of"):
        decedent = decedent[9:].strip()
    if not decedent:
        return None

    addr_idx = next((i for i, p in enumerate(parts) if _is_plausible_address(p)), None)
    if addr_idx is None:
        return None

    address = parts[addr_idx]
    case_no = ""
    filing = ""
    poc = ""
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

    notes = _bulk_notes_join(notes_parts)
    phone, email = _extract_phone_email_from_text(f"{poc}\n{notes}")

    return {
        "decedent": decedent,
        "case_number": case_no,
        "filing_date": filing,
        "poc_field": poc,
        "address": address,
        "notes": notes,
        "phone": phone,
        "email": email,
    }


def _parse_multiline_bulk_block(lines: list):
    """Block format — one lead per blank-line-separated chunk."""
    lines = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
    if len(lines) < 2:
        return None

    decedent = lines[0]
    if decedent.lower().startswith("estate of"):
        decedent = decedent[9:].strip()

    case_no = ""
    filing = ""
    poc = ""
    address = ""
    notes_lines = []
    after_address = False
    notes_marker = False

    for line in lines[1:]:
        if re.match(r"^NOTES:\s*", line, re.I):
            notes_marker = True
            after_address = True
            tail = re.sub(r"^NOTES:\s*", "", line, flags=re.I).strip()
            if tail:
                notes_lines.append(tail)
            continue
        if notes_marker or after_address:
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
        return None

    notes = _bulk_notes_join(notes_lines)
    phone, email = _extract_phone_email_from_text(f"{poc}\n{notes}")

    return {
        "decedent": decedent,
        "case_number": case_no,
        "filing_date": filing,
        "poc_field": poc,
        "address": address,
        "notes": notes,
        "phone": phone,
        "email": email,
    }


def _split_estate_chunks(text: str) -> list:
    """Split bulk paste into estates — single blank lines stay inside one record."""
    text = (text or "").strip()
    if not text:
        return []
    if re.search(r"^Estate of ", text, re.I | re.M):
        parts = re.split(r"(?=^Estate of )", text, flags=re.I | re.M)
        return [p.strip() for p in parts if p.strip()]
    triple = re.split(r"\n\s*\n\s*\n+", text)
    if len(triple) > 1:
        return [p.strip() for p in triple if p.strip()]
    return [text]


def parse_bulk_paste_all(text: str) -> list:
    """Parse any bulk paste: pipe/tab lines, multi-line blocks, or mixed."""
    text = (text or "").strip()
    if not text:
        return []

    rows: list = []
    seen: set = set()

    def _add_row(row) -> None:
        if not row or not row.get("decedent") or not row.get("address"):
            return
        key = (row["decedent"].lower(), row["address"].lower())
        if key in seen:
            return
        seen.add(key)
        rows.append(row)

    for block in _split_estate_chunks(text):
        lines = [l.strip() for l in block.splitlines() if l.strip() and not l.startswith("#")]
        if not lines:
            continue

        has_delimited = any("|" in ln or "\t" in ln for ln in lines)
        if not has_delimited and len(lines) >= 2:
            _add_row(_parse_multiline_bulk_block(lines))
            continue

        for line in lines:
            parts = _bulk_line_parts(line)
            if len(parts) >= 2:
                _add_row(_parse_delimited_bulk_row(parts))

    if not rows:
        all_lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
        if len(all_lines) >= 2:
            _add_row(_parse_multiline_bulk_block(all_lines))
        for line in all_lines:
            parts = _bulk_line_parts(line)
            if len(parts) >= 2:
                _add_row(_parse_delimited_bulk_row(parts))

    return rows


def _preview_row_to_bulk_row(row: dict) -> dict:
    addr = (row.get("address") or "").strip()
    if not row.get("decedent") or not addr or addr == "Address TBD":
        return {}
    poc = row.get("poc_hint", "") if row.get("poc_hint") != "—" else ""
    if not poc:
        poc = row.get("contact_name", "") or row.get("heirs", "")
    return {
        "decedent": row.get("decedent", ""),
        "case_number": row.get("case_number", ""),
        "filing_date": row.get("filing_date", ""),
        "poc_field": poc,
        "address": addr,
        "notes": " · ".join((row.get("flags") or row.get("re_signals") or [])[:3]),
        "recency_days": row.get("recency_days"),
    }


def _ingest_court_paste_rows(text: str, county: str) -> list:
    """Auto-detect CaseLink / tncrtinfo / raw court exports."""
    rows: list = []
    seen: set = set()
    for src in (
        process_caselink_preview(text, default_county=county),
        process_bulk_court_data(text, default_county=county, add_qualified=False),
    ):
        for row in src:
            bulk = _preview_row_to_bulk_row(row)
            if not bulk:
                continue
            key = (bulk["decedent"].lower(), bulk["address"].lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append(bulk)
        if rows:
            break
    return rows


def parse_bulk_quick_add_lines(text: str) -> list:
    return parse_bulk_paste_all(text)


def _freshness_sort_key(item: dict) -> tuple:
    """Lower = fresher = call first."""
    rd = item.get("recency_days")
    if rd is not None:
        return (0, rd)
    filing_dt = parse_filing_date_obj(item.get("filing_date", ""))
    if filing_dt:
        return (1, -filing_dt.timestamp())
    for iso_field in ("hot_queued_at", "created"):
        raw = item.get(iso_field, "")
        if raw:
            try:
                return (2, -datetime.fromisoformat(str(raw).replace("Z", "")).timestamp())
            except ValueError:
                pass
    return (3, 0)


def _prioritize_leads_freshest(leads: list) -> list:
    hot = [l for l in leads if l.get("branton_hot")]
    rest = [l for l in leads if not l.get("branton_hot")]
    hot.sort(key=_freshness_sort_key)
    return hot + rest


def _upsert_hot_lead_from_row(row: dict, county: str = "Davidson County") -> dict:
    """Create or update one HOT lead in session — no save/rerun."""
    decedent = row.get("decedent", "").strip()
    address = row.get("address", "").strip()
    poc_field = row.get("poc_field", "")
    case_number = row.get("case_number", "").strip()
    filing_date = row.get("filing_date", "").strip()
    notes = row.get("notes", "")

    poc_name, poc_role = _split_poc_field(poc_field)
    poc_display = f"{poc_name} ({poc_role})" if poc_role else poc_name
    phone = (row.get("phone") or "").strip()
    email = (row.get("email") or "").strip()
    if not phone or not email:
        bp, be = _extract_phone_email_from_text(f"{poc_field}\n{notes}")
        phone = phone or bp
        email = email or be
    raw = (
        f"Estate of {decedent}\n{case_number}\n{filing_date}\n"
        f"{poc_display}\n{address}\n{notes}"
    )
    parsed = {
        "decedent": decedent,
        "address": address,
        "county": county,
        "heirs": poc_display,
        "contact_name": poc_name,
        "contact_role": poc_role,
        "phone": phone or PHONE_PLACEHOLDER,
        "email": email,
        "case_number": case_number,
        "filing_date": filing_date,
        "raw": raw,
    }

    existing = find_lead_by_case(case_number) if case_number else None
    if not existing:
        for lead in st.session_state.leads:
            if (
                lead.get("decedent", "").lower() == decedent.lower()
                and lead.get("address", "").lower() == address.lower()
            ):
                existing = lead
                break

    if existing:
        _apply_confirmed_hot_fields(existing, parsed, notes)
        return existing

    lead = build_lead(
        parsed,
        pipeline_stage="Warm",
        status="Qualified",
        score=95,
        source="bulk_paste",
        assigned_to_branton=True,
        follow_up_days=0,
    )
    _apply_confirmed_hot_fields(lead, parsed, notes)
    st.session_state.leads.append(lead)
    return lead


def bulk_paste_to_hot_queue(raw: str, county: str = "Davidson County") -> int:
    """Unlimited bulk paste → HOT queue with unique IDs, persisted to disk."""
    global _lead_id_seq
    text = (raw or "").strip()
    if not text:
        return 0

    rows = parse_bulk_paste_all(text)
    if not rows:
        rows = _ingest_court_paste_rows(text, county)

    if not rows:
        return 0

    _lead_id_seq = 0
    rows.sort(key=_freshness_sort_key)
    touched: list = []
    for row in rows:
        lead = _upsert_hot_lead_from_row(row, county=county)
        touched.append(lead)

    if _ensure_unique_lead_ids(st.session_state.leads):
        pass

    touched_ids = {l["id"] for l in touched}
    rest = [l for l in st.session_state.leads if l["id"] not in touched_ids]
    st.session_state.leads = touched + _prioritize_leads_freshest(rest)
    save_leads(st.session_state.leads)
    st.session_state.queue_version = st.session_state.get("queue_version", 0) + 1

    if touched:
        st.session_state.branton_last_added_id = touched[0].get("id", "")
    return len(touched)


def bulk_add_confirmed_hot_leads(text: str, county: str = "Davidson County") -> int:
    return bulk_paste_to_hot_queue(text, county=county)


def _on_bulk_quick_add() -> None:
    raw = st.session_state.get("branton_bulk_quick_add", "")
    county = st.session_state.get("branton_quick_add_county", "Davidson County")
    n = bulk_add_confirmed_hot_leads(raw, county=county)
    st.session_state.branton_bulk_quick_add = ""
    if n:
        st.session_state.branton_queue_flash = (
            f"🔥 **{n}** confirmed leads added to HOT queue — open **Daily Call Queue**"
        )
        st.session_state.leads_need_reload = True
    else:
        st.session_state.branton_quick_add_msg = (
            "No leads added — each line needs **Decedent** + **Address** "
            "(pipe, tab, or comma separated)."
        )


def process_bulk_court_data(raw: str, default_county: str = "Sumner County", add_qualified: bool = True) -> list:
    blocks = split_court_export(raw, default_county=default_county)
    results = []
    for block in blocks:
        if not CASE_NUMBER_RE.search(block) and not re.search(
            r"Estate of|IN RE|Probate|PR20\d{2}|Administratrix|Executrix|Personal Representative",
            block,
            re.I,
        ):
            continue
        parsed = parse_court_row_block(block, default_county)
        score, status, flags = score_court_lead(parsed)
        parsed["score"] = score
        parsed["qual_status"] = status
        parsed["flags"] = flags
        lookups = lookup_urls(parsed.get("contact_name") or parsed.get("heirs", ""), parsed.get("address", ""), parsed.get("county", ""))
        parsed["lookups"] = lookups
        parsed["assessor_url"] = assessor_search_url(
            parsed.get("county", ""),
            parsed.get("decedent", ""),
            parsed.get("address", ""),
        )

        if add_qualified:
            upsert_court_lead(parsed, score, status, flags)

        results.append(parsed)

    if add_qualified:
        save_leads(st.session_state.leads)

    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results


def process_caselink_preview(raw: str, default_county: str = "Davidson County") -> list:
    """Parse CaseLink dump for preview — does NOT save to CRM until user marks + adds."""
    records = extract_caselink_case_records(raw, default_county)
    results = []
    seen_cases = set()
    for i, rec in enumerate(records):
        case_no = rec.get("case_number", "")
        key = _normalize_case_number(case_no)
        if not key or key in seen_cases:
            continue
        seen_cases.add(key)

        block = _case_record_to_block(rec, default_county)
        parsed = parse_court_row_block(block, default_county)

        decedent = rec.get("decedent", "")
        if decedent and decedent != "Unknown Decedent":
            parsed["decedent"] = decedent
        if rec.get("filing_date"):
            parsed["filing_date"] = rec["filing_date"]
            filing_dt = parse_filing_date_obj(rec["filing_date"])
            if filing_dt:
                parsed["filing_dt"] = filing_dt.isoformat()
                rd, rt, _, ir = compute_recency(filing_dt)
                parsed["recency_days"] = rd
                parsed["recency_tier"] = rt
                parsed["is_recent_30"] = ir
        if case_no:
            parsed["case_number"] = case_no

        poc = rec.get("poc_hint") or _extract_poc_hint(block)
        if poc and poc != "POC TBD":
            parsed["contact_name"] = poc
            parsed["heirs"] = poc
        parsed["poc_hint"] = poc if poc and poc != "POC TBD" else "—"

        clean_addr = _normalize_address(rec.get("address", ""), block)
        if not clean_addr:
            clean_addr = _normalize_address(parsed.get("address", ""), block)
        if clean_addr:
            parsed["address"] = clean_addr
            parsed["has_real_estate"] = True
        else:
            parsed["address"] = "Address TBD"
            parsed["has_real_estate"] = False

        score, status, flags = score_court_lead(parsed)
        parsed["score"] = score
        parsed["qual_status"] = status
        parsed["flags"] = flags
        parsed["assessor_url"] = assessor_search_url(
            parsed.get("county", default_county),
            parsed.get("decedent", ""),
            parsed.get("address", ""),
        )
        parsed["marked_re"] = bool(parsed.get("has_real_estate"))
        parsed["preview_id"] = case_no or f"preview_{i}"
        parsed["raw"] = block
        results.append(parsed)

    results.sort(
        key=lambda x: (
            x.get("is_recent_30", False),
            -(x.get("recency_days") if x.get("recency_days") is not None else 9999),
            -x.get("score", 0),
        ),
        reverse=True,
    )
    return results


def _preview_to_editor_rows(preview: list) -> list:
    rows = []
    for row in preview:
        rows.append({
            "Mark RE": bool(row.get("marked_re")),
            "Decedent": row.get("decedent", ""),
            "Case #": row.get("case_number", ""),
            "Filed": row.get("filing_date", "—"),
            "POC Hint": row.get("poc_hint", "—"),
            "Address": row.get("address", "Address TBD"),
            "Recency": _recency_label(row.get("recency_tier", "")),
            "Assessor": row.get("assessor_url", ""),
        })
    return rows


def _sync_editor_marks_to_preview(preview: list, edited: list) -> None:
    by_case = {r.get("case_number"): r for r in preview if r.get("case_number")}
    for er in edited or []:
        case = er.get("Case #")
        if case and case in by_case:
            by_case[case]["marked_re"] = bool(er.get("Mark RE"))


def promote_preview_row_to_hot(row: dict) -> dict:
    addr = row.get("address", "Address TBD")
    notes = "CaseLink bulk — CRS/assessor confirmed RE"
    if row.get("poc_hint") and row.get("poc_hint") != "—":
        notes += f" · POC: {row['poc_hint']}"
    return add_confirmed_hot_lead(
        decedent=row.get("decedent", ""),
        case_number=row.get("case_number", ""),
        filing_date=row.get("filing_date", ""),
        poc_field=row.get("poc_hint", "") if row.get("poc_hint") != "—" else "",
        address=addr if addr != "Address TBD" else "Address TBD",
        notes=notes,
        county=row.get("county", "Davidson County"),
    )


def add_marked_preview_to_hot_queue(preview: list) -> int:
    marked = [r for r in preview if r.get("marked_re") and r.get("decedent")]
    added = 0
    last_lead = None
    for row in reversed(marked):
        last_lead = promote_preview_row_to_hot(row)
        added += 1
    if last_lead and added == 1:
        _flash_hot_queue_add(last_lead)
    elif added > 1:
        st.session_state.branton_last_added_id = last_lead.get("id", "") if last_lead else ""
        st.session_state.branton_queue_flash = (
            f"🔥 **{added}** confirmed leads added to HOT queue — check **Daily Call Queue** tab"
        )
        st.session_state.leads_need_reload = True
    return added


def _sync_preview_from_editor() -> None:
    preview = st.session_state.get("branton_caselink_preview", [])
    edited = st.session_state.get("branton_preview_editor")
    if preview and edited is not None:
        _sync_editor_marks_to_preview(preview, edited)


def _on_mark_all_preview_re() -> None:
    preview = st.session_state.get("branton_caselink_preview", [])
    for row in preview:
        row["marked_re"] = True
    st.session_state.branton_preview_editor = _preview_to_editor_rows(preview)


def _on_add_marked_preview_hot() -> None:
    _sync_preview_from_editor()
    preview = st.session_state.get("branton_caselink_preview", [])
    n = add_marked_preview_to_hot_queue(preview)
    if n:
        st.session_state.branton_caselink_preview = []
        st.session_state.pop("branton_preview_editor", None)
        if not st.session_state.get("branton_queue_flash"):
            st.session_state.branton_queue_flash = (
                f"🔥 **{n}** confirmed RE leads added to HOT queue"
            )
            st.session_state.leads_need_reload = True
    else:
        st.session_state.branton_quick_add_msg = (
            "No leads added — check **Mark RE** on cases you confirmed in CRS/assessor first."
        )


def process_ftc_batch(raw: str, default_county: str = "Davidson County") -> list:
    results = process_bulk_court_data(raw, default_county=default_county, add_qualified=True)
    for row in results:
        row["branton_hot"] = False
        row["ftc_priority"] = False
        row["ftc_ready"] = False
        row["ftc_pending_assessor"] = not row.get("has_real_estate")
    results.sort(
        key=lambda x: (
            x.get("is_recent_30", False),
            -(x.get("recency_days") if x.get("recency_days") is not None else 9999),
            -x.get("score", 0),
        ),
        reverse=True,
    )
    return results


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
    stage = extra.get("pipeline_stage", "Warm" if branton else "Cold")
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
        if lead["id"] == lead_id:
            return lead
    return None


def find_lead_by_case(case_number: str):
    if not case_number:
        return None
    for lead in st.session_state.leads:
        if lead.get("case_number") == case_number:
            return lead
    return None


def set_branton_stage(lead_id: str, stage: str) -> None:
    lead = find_lead(lead_id)
    stage = BRANTON_STAGE_ALIASES.get(stage, stage)
    if not lead or stage not in BRANTON_STAGES:
        return
    lead["branton_stage"] = stage
    lead["status"] = BRANTON_TO_STATUS.get(stage, lead.get("status", "New"))
    lead["pipeline_stage"] = STATUS_TO_PIPELINE.get(lead["status"], lead.get("pipeline_stage", "Cold"))
    if stage in DRIP_STOP_STAGES:
        lead["drip_paused"] = True
    if stage == "Attempted" and lead.get("calls", 0) == 0:
        lead["calls"] = 1
    if stage in CRM_ACTIVE_STAGES and stage not in ("New", "Dead", "Nurture"):
        lead["assigned_to_branton"] = True
        lead["assigned_to"] = PARTNER_NAME
    if stage == "Closed Won":
        lead["pipeline_stage"] = "Closed"
        lead["status"] = "Closed"
    lead["activity"].insert(0, {
        "ts": datetime.now().isoformat(),
        "type": "branton_stage",
        "detail": f"Stage → {stage}",
    })
    save_leads(st.session_state.leads)


def advance_branton_stage(lead_id: str) -> None:
    lead = find_lead(lead_id)
    if not lead:
        return
    current = derive_branton_stage(lead)
    nxt = BRANTON_STAGE_NEXT.get(current, current)
    set_branton_stage(lead_id, nxt)
    lead = find_lead(lead_id)
    if lead:
        schedule_next_drip_touch(lead)
        save_leads(st.session_state.leads)


def _drip_aggressive_active(lead: dict) -> bool:
    return derive_branton_stage(lead) not in DRIP_STOP_STAGES and not lead.get("drip_paused")


def schedule_next_drip_touch(lead: dict) -> None:
    idx = lead.get("drip_touch_index", 0)
    if _drip_aggressive_active(lead) and idx < len(DRIP_AGGRESSIVE_SEQUENCE):
        touch = DRIP_AGGRESSIVE_SEQUENCE[idx]
        start = lead.get("drip_started_iso", datetime.now().strftime("%Y-%m-%d"))
        try:
            base = datetime.strptime(start, "%Y-%m-%d")
        except ValueError:
            base = datetime.now()
        next_day = touch["day"]
        if idx + 1 < len(DRIP_AGGRESSIVE_SEQUENCE):
            next_day = DRIP_AGGRESSIVE_SEQUENCE[idx + 1]["day"]
        due = (base + timedelta(days=next_day)).strftime("%Y-%m-%d")
        lead["follow_up_iso"] = due
        lead["follow_up"] = datetime.strptime(due, "%Y-%m-%d").strftime("%A, %B %d, %Y")
    elif lead.get("drip_paused") or derive_branton_stage(lead) in DRIP_STOP_STAGES:
        nidx = lead.get("drip_nurture_index", 0)
        if nidx < len(DRIP_NURTURE_SEQUENCE):
            nurture = DRIP_NURTURE_SEQUENCE[nidx]
            start = lead.get("drip_started_iso", datetime.now().strftime("%Y-%m-%d"))
            try:
                base = datetime.strptime(start, "%Y-%m-%d")
            except ValueError:
                base = datetime.now()
            due = (base + timedelta(days=nurture["day"])).strftime("%Y-%m-%d")
            if due <= datetime.now().strftime("%Y-%m-%d"):
                due = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
            lead["follow_up_iso"] = due
            lead["follow_up"] = datetime.strptime(due, "%Y-%m-%d").strftime("%A, %B %d, %Y")


def record_drip_touch(lead_id: str, touch_type: str, detail: str = "") -> None:
    lead = find_lead(lead_id)
    if not lead:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    lead["last_drip_touch_iso"] = today
    if _drip_aggressive_active(lead):
        lead["drip_touch_index"] = min(lead.get("drip_touch_index", 0) + 1, len(DRIP_AGGRESSIVE_SEQUENCE))
        if lead["drip_touch_index"] >= len(DRIP_AGGRESSIVE_SEQUENCE):
            lead["drip_paused"] = True
    else:
        lead["drip_nurture_index"] = min(lead.get("drip_nurture_index", 0) + 1, len(DRIP_NURTURE_SEQUENCE))
    schedule_next_drip_touch(lead)
    lead["activity"].insert(0, {
        "ts": datetime.now().isoformat(),
        "type": touch_type,
        "detail": detail or f"Drip touch logged ({touch_type})",
    })
    save_leads(st.session_state.leads)


def get_branton_pipeline_counts(leads: list) -> dict:
    counts = {s: 0 for s in BRANTON_STAGES}
    for lead in leads:
        stage = derive_branton_stage(lead)
        counts[stage] = counts.get(stage, 0) + 1
    return counts


def assess_re_likelihood(parsed: dict) -> dict:
    """Score how likely a probate case includes real estate (bulk RE finder)."""
    signals = []
    score = 0
    addr = (parsed.get("address") or "").strip()
    raw = parsed.get("raw", "")

    if addr and addr != "Address TBD" and _is_plausible_address(addr):
        score += 55
        signals.append("🏠 Street address detected")
    if parsed.get("has_real_estate"):
        score += 25
        signals.append("✓ Marked has RE")

    if REAL_ESTATE_RE.search(raw or ""):
        score += 20
        signals.append("📄 RE keywords in court filing")
    if re.search(r"residence|homestead|devised|real property|dwelling|parcel", raw or "", re.I):
        score += 12
        signals.append("📄 Property language in text")

    county = parsed.get("county", "")
    if county:
        score += 3
        signals.append(f"📍 {county}")

    if parsed.get("is_recent_30"):
        score += 10
        signals.append(f"🔥 Filed {parsed.get('recency_days', '?')}d ago")

    likely = score >= 45 or (addr and addr != "Address TBD")
    return {
        "re_score": min(score, 100),
        "re_signals": signals,
        "likely_re": likely,
        "needs_assessor": not parsed.get("has_real_estate") and likely,
    }


def process_bulk_re_scan(raw: str, default_county: str = "Davidson County") -> list:
    """Parse bulk dump and rank by real-estate likelihood — does NOT auto-save."""
    preview = process_caselink_preview(raw, default_county=default_county)
    for row in preview:
        re = assess_re_likelihood(row)
        row.update(re)
        if row.get("address") and row["address"] != "Address TBD":
            row["marked_re"] = row.get("marked_re") or re["likely_re"]
    preview.sort(
        key=lambda x: (
            x.get("likely_re", False),
            x.get("re_score", 0),
            x.get("is_recent_30", False),
            -(x.get("recency_days") if x.get("recency_days") is not None else 9999),
        ),
        reverse=True,
    )
    return preview


def compute_lead_gci(lead: dict) -> float:
    price = lead.get("deal_contract_price") or lead.get("deal_list_price") or 0
    pct = lead.get("deal_commission_pct", 3.0) or 3.0
    try:
        return round(float(price) * float(pct) / 100, 2)
    except (TypeError, ValueError):
        return 0.0


def update_lead_deal(lead_id: str, **fields) -> None:
    lead = find_lead(lead_id)
    if not lead:
        return
    for k, v in fields.items():
        if v is not None:
            lead[k] = v
    lead["deal_gci"] = compute_lead_gci(lead)
    save_leads(st.session_state.leads)


def get_crm_dashboard_stats(leads: list) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    stages = get_branton_pipeline_counts(leads)
    re_confirmed = sum(1 for l in leads if l.get("has_real_estate"))
    hot = sum(1 for l in leads if l.get("branton_hot"))
    in_deals = sum(1 for l in leads if derive_branton_stage(l) in CRM_DEAL_STAGES)
    pipeline_gci = sum(compute_lead_gci(l) for l in leads if derive_branton_stage(l) in CRM_DEAL_STAGES)
    closed_gci = sum(
        compute_lead_gci(l) for l in leads if derive_branton_stage(l) == "Closed Won"
    )
    calls_today = 0
    for lead in leads:
        for act in lead.get("activity", []):
            if act.get("type") == "call" and act.get("ts", "").startswith(today):
                calls_today += 1
    first_calls = stages.get("Attempted", 0) + stages.get("Contacted", 0)
    appts = stages.get("Appt Set", 0)
    closings = stages.get("Closed Won", 0)
    conv = round(closings / max(len(leads), 1) * 100, 1)
    return {
        "total": len(leads),
        "re_confirmed": re_confirmed,
        "hot": hot,
        "due_today": count_due_today(leads),
        "calls_today": calls_today,
        "in_deals": in_deals,
        "pipeline_gci": pipeline_gci,
        "closed_gci": closed_gci,
        "stages": stages,
        "first_calls": first_calls,
        "appts": appts,
        "closings": closings,
        "conv_pct": conv,
    }


def export_all_leads_csv(leads: list) -> str:
    buf = io.StringIO()
    fields = [
        "decedent", "case_number", "address", "county", "phone", "heirs",
        "branton_stage", "has_real_estate", "score", "follow_up_iso", "calls",
        "deal_list_price", "deal_contract_price", "deal_gci", "deal_close_date",
    ]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for lead in leads:
        row = dict(lead)
        row["branton_stage"] = derive_branton_stage(lead)
        writer.writerow(row)
    return buf.getvalue()


def get_queue_bucket(lead: dict, today: str) -> int:
    stage = derive_branton_stage(lead)
    if stage in ("Closed Won", "Dead", "Nurture"):
        return 99
    if lead.get("branton_hot"):
        return 0
    if lead.get("follow_up_iso", "9999-12-31") <= today:
        return 1
    if stage == "New":
        return 2
    return 3


def get_daily_prioritized_queue(leads: list, view_filter: str = "Priority Queue") -> list:
    today = datetime.now().strftime("%Y-%m-%d")
    seen_ids: set = set()
    unique_leads: list = []
    for lead in leads:
        lid = lead.get("id")
        if not lid or lid in seen_ids:
            continue
        seen_ids.add(lid)
        unique_leads.append(lead)
    inactive = {
        "Closed Won", "Dead", "Nurture", "Listed",
        "Listing Signed", "Under Contract", "Court Pending",
    }
    active = [l for l in unique_leads if derive_branton_stage(l) not in inactive]

    if view_filter == "Hot Today":
        active = [l for l in active if l.get("branton_hot")]
    elif view_filter == "Due Today":
        active = [l for l in active if l.get("follow_up_iso", "9999") <= today]
    elif view_filter == "Branton Only":
        active = [l for l in active if l.get("assigned_to_branton") or l.get("branton_hot")]
    elif view_filter == "Priority Queue":
        active = [l for l in active if get_queue_bucket(l, today) <= 3]

    def _hot_ts(iso: str) -> float:
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
        except (ValueError, TypeError):
            return 0.0

    def sort_key(lead: dict) -> tuple:
        bucket = get_queue_bucket(lead, today)
        recency = lead.get("recency_days") if lead.get("recency_days") is not None else 9999
        hot_at = lead.get("hot_queued_at") or lead.get("created") or ""
        if bucket == 0:
            return (0, -_hot_ts(hot_at), -lead.get("score", 0))
        return (bucket, lead.get("follow_up_iso", "9999-12-31"), recency, -lead.get("score", 0))

    return sorted(active, key=sort_key)


def count_due_today(leads: list) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    return sum(
        1 for l in leads
        if l.get("follow_up_iso", "9999") <= today and derive_branton_stage(l) not in {"Closed Won", "Dead", "Nurture"}
    )


def format_touch_history(lead: dict) -> str:
    idx = lead.get("drip_touch_index", 0)
    total = len(DRIP_AGGRESSIVE_SEQUENCE)
    markers = []
    for i in range(5):
        n = i + 1
        if i < idx:
            markers.append(f"✅{n}")
        elif i == idx and _drip_aggressive_active(lead):
            markers.append(f"🔥{n}")
        else:
            markers.append(f"○{n}")
    tail = f" …+{total - 5}" if total > 5 else ""
    return " ".join(markers) + tail


def format_touch_12345_html(lead: dict) -> str:
    idx = lead.get("drip_touch_index", 0)
    aggressive = _drip_aggressive_active(lead)
    parts = []
    for n in range(1, 6):
        if n <= idx:
            cls = "mm-touch-num done"
        elif n == idx + 1 and aggressive:
            cls = "mm-touch-num now"
        else:
            cls = "mm-touch-num"
        parts.append(f'<span class="{cls}">{n}</span>')
    return '<div class="mm-touch-track">' + "".join(parts) + "</div>"


def drip_progress_pct(lead: dict) -> float:
    if _drip_aggressive_active(lead):
        return lead.get("drip_touch_index", 0) / max(len(DRIP_AGGRESSIVE_SEQUENCE), 1)
    nidx = lead.get("drip_nurture_index", 0)
    return 0.75 + (nidx / max(len(DRIP_NURTURE_SEQUENCE), 1)) * 0.25


def next_drip_label(lead: dict) -> str:
    idx = lead.get("drip_touch_index", 0)
    if _drip_aggressive_active(lead) and idx < len(DRIP_AGGRESSIVE_SEQUENCE):
        return DRIP_AGGRESSIVE_SEQUENCE[idx]["label"]
    if lead.get("drip_paused") or derive_branton_stage(lead) in DRIP_STOP_STAGES:
        nidx = lead.get("drip_nurture_index", 0)
        if nidx < len(DRIP_NURTURE_SEQUENCE):
            return f"Nurture: {DRIP_NURTURE_SEQUENCE[nidx]['label']}"
        return "Nurture complete — quarterly check-in"
    return "Sequence complete"


def poc_display_name(lead: dict) -> str:
    for field in ("contact_name", "heirs"):
        name = (lead.get(field) or "").strip()
        if name and name not in ("Contact TBD", "—", "POC TBD"):
            if name.startswith("PR20"):
                continue
            return name.split("—")[0].split(",")[0].strip()
    raw = lead.get("raw", "")
    if raw:
        contact, _ = _extract_contact(raw)
        if contact:
            return contact
    for field in ("contact_name", "heirs"):
        name = (lead.get(field) or "").strip()
        if not name or name in ("Contact TBD", "—"):
            continue
        if name.startswith("PR20"):
            exec_m = re.search(
                r"(?:Executrix|Administratrix|Administrator|Executor):\s*([^,\n]+)",
                raw or name,
                re.I,
            )
            if exec_m:
                return exec_m.group(1).strip()
            continue
        if "," in name and re.match(r"PR\d{4}-\d+", name):
            continue
        return name.split("—")[0].split(",")[0].strip()
    return "POC TBD"


def clean_phone(phone: str) -> str:
    if not phone or phone == PHONE_PLACEHOLDER:
        return PHONE_PLACEHOLDER
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return phone or PHONE_PLACEHOLDER


def phone_tel_url(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return f"tel:+1{digits}" if len(digits) >= 10 else ""


def sms_url(phone: str, body: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) < 10:
        return ""
    return f"sms:+1{digits}?body={quote(body)}"


def mailto_url(email: str, subject: str, body: str) -> str:
    if not email:
        return ""
    return f"mailto:{email}?subject={quote(subject)}&body={quote(body)}"


def generate_branton_sms(lead: dict) -> str:
    poc = poc_display_name(lead).split(",")[0].split("—")[0].strip()
    decedent = lead.get("decedent", "your loved one").split("—")[0].strip()
    return (
        f"Hi {poc}, this is Branton Walker with eXp Realty. I'm sorry for your loss regarding "
        f"{decedent}. No pressure at all — I'm a local resource if property questions come up. "
        f"Reply STOP to opt out. — Branton 615-953-0758"
    )


def generate_branton_email(lead: dict) -> str:
    poc = poc_display_name(lead).split(",")[0].strip()
    decedent = lead.get("decedent", "").split("—")[0].strip()
    address = lead.get("address", "the property")
    return (
        f"Subject: A local resource for {decedent}'s estate — no obligation\n\n"
        f"Hi {poc},\n\n"
        f"My name is Branton Walker — I help Middle TN families navigate probate property "
        f"questions with compassion and clarity.\n\n"
        f"I noticed the filing for {decedent} ({address}). Whenever questions come up, I'd be "
        f"glad to send a free Equity Snapshot / Net Sheet — zero pressure.\n\n"
        f"May I suggest a brief 10-minute call this week?\n\n"
        f"Branton Walker · eXp Realty · 615-953-0758\n"
        f"Scott Hardesty partnership · Subject to court approval"
    )


def log_branton_call(lead_id: str) -> None:
    lead = find_lead(lead_id)
    if not lead:
        return
    was_new = derive_branton_stage(lead) == "New"
    log_call(lead_id)
    if was_new:
        set_branton_stage(lead_id, "Attempted")
    else:
        lead = find_lead(lead_id)
        if lead and derive_branton_stage(lead) == "Attempted":
            schedule_next_drip_touch(lead)
            save_leads(st.session_state.leads)
    record_drip_touch(lead_id, "call", "Call logged — drip advanced")


def export_branton_calls_today(leads: list) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for lead in leads:
        for act in lead.get("activity", []):
            ts = act.get("ts", "")
            if not ts.startswith(today):
                continue
            if act.get("type") in ("call", "text", "email", "branton_stage", "note"):
                rows.append({
                    "Time": ts[11:16] if len(ts) > 16 else ts,
                    "Decedent": lead.get("decedent", ""),
                    "POC": poc_display_name(lead),
                    "Phone": lead.get("phone", ""),
                    "Stage": derive_branton_stage(lead),
                    "Action": act.get("detail", act.get("type", "")),
                })
    if not rows:
        return "Time,Decedent,POC,Phone,Stage,Action\n(No calls logged today yet)\n"
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["Time", "Decedent", "POC", "Phone", "Stage", "Action"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def update_lead(lead_id: str, **fields) -> None:
    for lead in st.session_state.leads:
        if lead["id"] == lead_id:
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
            break
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
        save_leads(st.session_state.leads)


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
        save_leads(st.session_state.leads)


def get_lead_notes_full_text(lead: dict) -> str:
    """Full note body for card editor — no truncation."""
    notes = lead.get("notes") or []
    if not notes:
        return ""
    return "\n\n".join((n.get("text") or "").strip() for n in notes if (n.get("text") or "").strip())


def set_lead_notes_full_text(lead_id: str, text: str, author: str = None) -> None:
    """Persist entire note field instantly."""
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
    save_leads(st.session_state.leads)


def _on_card_note_saved(lead_id: str, widget_key: str) -> None:
    if not lead_id:
        return
    set_lead_notes_full_text(lead_id, st.session_state.get(widget_key, ""))


def _init_card_notes_widget(notes_key: str, lead: dict, real_lead_id: str) -> None:
    """Init notes widget state BEFORE st.text_area renders — avoids API exceptions."""
    sync_id_key = f"{notes_key}_lid"
    if st.session_state.get(sync_id_key) != real_lead_id:
        st.session_state[notes_key] = get_lead_notes_full_text(lead)
        st.session_state[sync_id_key] = real_lead_id


def _save_card_notes(lead_id: str, notes_key: str) -> None:
    if lead_id:
        set_lead_notes_full_text(lead_id, st.session_state.get(notes_key, ""))


def _append_quick_note(lead_id: str, notes_key: str) -> str:
    """Append timestamped line — only call from on_click (before widgets render)."""
    lead = find_lead(lead_id)
    if not lead:
        return ""
    base = st.session_state.get(notes_key, get_lead_notes_full_text(lead))
    stamp = datetime.now().strftime("%b %d, %Y %I:%M %p")
    line = f"[{stamp}] Call logged"
    new_text = f"{base}\n\n{line}".strip() if base.strip() else line
    set_lead_notes_full_text(lead_id, new_text)
    st.session_state[notes_key] = new_text
    lead = find_lead(lead_id)
    if lead:
        lead["activity"].insert(0, {
            "ts": datetime.now().isoformat(),
            "type": "note",
            "detail": line[:80],
        })
        save_leads(st.session_state.leads)
    return new_text


def _cb_quick_note(lead_id: str, notes_key: str) -> None:
    if not lead_id:
        return
    _append_quick_note(lead_id, notes_key)
    st.session_state.branton_note_saved_id = lead_id
    st.toast("Saved!")


def _cb_toggle_script(script_toggle_key: str) -> None:
    st.session_state[script_toggle_key] = not st.session_state.get(script_toggle_key, False)


def _cb_crm_stage(lead_id: str, stage: str, notes_key: str) -> None:
    if not lead_id:
        return
    apply_crm_stage_action(lead_id, stage, notes_key)
    st.toast("Saved!")


def _rebalance_lead_queue(lead: dict, stage: str) -> None:
    """Move lead in queue based on pipeline stage."""
    if stage in ("Listing Signed", "Listed", "Under Contract", "Court Pending", "Closed Won", "Dead"):
        lead["branton_hot"] = False
    if stage == "Contacted":
        lead["follow_up_iso"] = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        lead["follow_up"] = datetime.strptime(lead["follow_up_iso"], "%Y-%m-%d").strftime("%A, %B %d, %Y")
    elif stage == "Appt Set":
        lead["follow_up_iso"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        lead["follow_up"] = datetime.strptime(lead["follow_up_iso"], "%Y-%m-%d").strftime("%A, %B %d, %Y")
    elif stage in ("Listing Signed", "Closed Won"):
        lead["follow_up_iso"] = "9999-12-31"


def apply_crm_stage_action(lead_id: str, stage: str, notes_key: str = "") -> None:
    """Update stage, save notes, rebalance queue, persist."""
    if notes_key:
        _save_card_notes(lead_id, notes_key)
    set_branton_stage(lead_id, stage)
    lead = find_lead(lead_id)
    if lead:
        _rebalance_lead_queue(lead, stage)
        save_leads(st.session_state.leads)
    commit_leads_and_reload()
    st.session_state.branton_action_flash_id = lead_id
    st.session_state.branton_action_flash_msg = "Saved!"


def compute_analytics(leads: list) -> dict:
    total = len(leads)
    stages = {s: sum(1 for l in leads if l.get("pipeline_stage") == s) for s in PIPELINE_STAGES}
    total_calls = sum(l.get("calls", 0) for l in leads)
    branton_count = sum(1 for l in leads if l.get("assigned_to_branton"))
    today = datetime.now().strftime("%Y-%m-%d")
    due_today = sum(1 for l in leads if l.get("follow_up_iso", "") <= today and l.get("pipeline_stage") != "Closed")

    cold = stages["Cold"] or 1
    warm = stages["Warm"] or 0
    appt = stages["Appt"] or 0
    contract = stages["Contract"] or 0
    closed = stages["Closed"] or 0

    conv_warm = round((warm + appt + contract + closed) / cold * 100, 1) if cold else 0
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

    listings_won = sum(1 for l in leads if derive_branton_stage(l) == "Closed Won")

    return {
        "total": total,
        "stages": stages,
        "total_calls": total_calls,
        "branton_count": branton_count,
        "due_today": due_today,
        "listings_won": listings_won,
        "conv_warm": conv_warm,
        "conv_appt": conv_appt,
        "conv_close": conv_close,
        "top_counties": top_counties,
        "sources": sources,
        "avg_calls": round(total_calls / max(total, 1), 1),
    }


def import_leads_from_text(text: str, source: str = "import") -> int:
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    count = 0
    for block in blocks:
        parsed = parse_lead(block)
        score, qual_status, _ = score_lead(parsed)
        st.session_state.leads.insert(0, build_lead(
            parsed,
            pipeline_stage="Cold",
            source=source,
            score=score,
            status=qual_status if qual_status != "Qualified" else "Qualified",
        ))
        count += 1
    save_leads(st.session_state.leads)
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
        st.session_state.leads.insert(0, build_lead(parsed, pipeline_stage="Cold", source=source))
        count += 1
    save_leads(st.session_state.leads)
    return count


def pipeline_class(stage: str) -> str:
    return {
        "Cold": "pipe-cold",
        "Warm": "pipe-warm",
        "Appt": "pipe-appt",
        "Contract": "pipe-contract",
        "Closed": "pipe-closed",
    }.get(stage, "pipe-cold")


# ── Content generators ───────────────────────────────────────────────────────
def generate_phone_script(parsed: dict, lead: dict = None) -> str:
    lead = lead or {}
    decedent = parsed["decedent"]
    address = parsed["address"]
    county = parsed["county"]
    heir = poc_display_name(lead) if lead else (parsed["heirs"] or "[Heir Name]")
    heir = heir.split("(")[0].strip() or "[Heir Name]"
    role = (lead.get("contact_role") or "").strip()
    case_no = (lead.get("case_number") or "").strip() or "—"
    filing = (lead.get("filing_date") or "").strip() or "—"
    phone_raw = parsed.get("phone") or lead.get("phone", "")
    phone_disp = clean_phone(phone_raw) if phone_raw and phone_raw != PHONE_PLACEHOLDER else "—"
    email_disp = (parsed.get("email") or lead.get("email") or "").strip() or "—"
    notes_ctx = get_lead_notes_full_text(lead) if lead else ""
    recency = lead.get("recency_days")
    recency_line = ""
    if recency is not None and recency <= 45:
        recency_line = (
            f"Very recent filing ({recency} days) — lead with compassion; "
            f"acknowledge how fresh this loss may feel."
        )
    elif "recent" in notes_ctx.lower() or "died" in notes_ctx.lower():
        recency_line = "Notes mention a recent death — slow down, listen first, zero pressure."

    warm_custom = ""
    if notes_ctx:
        snippet = notes_ctx.replace("\n", " ")[:220]
        warm_custom = (
            f'\nCUSTOM OPENER (from your notes):\n'
            f'"I was reviewing the estate file for {decedent} — {snippet}…"\n'
            f'[Pause. Let them respond. Then: "Tell me more about that."]\n'
        )

    lead_brief = f"""═══════════════════════════════════════════════════════
  THIS LEAD — PERSONALIZED CALL BRIEF
  {decedent} · {case_no}
═══════════════════════════════════════════════════════
POC: {heir}{f" ({role})" if role else ""}
Phone: {phone_disp} · Email: {email_disp}
Property: {address}
County: {county} · Filed: {filing}
{recency_line}
"""
    if notes_ctx:
        lead_brief += f"""
YOUR FULL NOTES — READ BEFORE YOU DIAL:
─────────────────────────────────────────────
{notes_ctx}
"""
    if warm_custom:
        lead_brief += warm_custom

    return f"""{lead_brief}
═══════════════════════════════════════════════════════
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


if "ftc_outer_checklist" not in st.session_state:
    st.session_state.ftc_outer_checklist = {key: False for key, _ in OUTER_COUNTY_VISIT_CHECKLIST}
if "ftc_daily_checklist" not in st.session_state:
    st.session_state.ftc_daily_checklist = {key: False for key, _ in DAILY_ROUTINE_BRANTON}
if "ftc_batch_results" not in st.session_state:
    st.session_state.ftc_batch_results = []
if "ftc_assessor_mode" not in st.session_state:
    st.session_state.ftc_assessor_mode = False


def _recency_label(tier: str) -> str:
    return {
        "high": "🔥 HIGH",
        "medium": "🟡 MED",
        "low": "🟠 LOW",
        "stale": "⚫ STALE",
        "unknown": "❓ ?",
    }.get(tier or "", tier or "?")


def render_branton_caselink_preview(preview: list) -> None:
    if not preview:
        return

    marked_n = sum(1 for r in preview if r.get("marked_re"))
    recent_n = sum(1 for r in preview if r.get("is_recent_30"))
    st.markdown(
        f"**{len(preview)}** cases extracted · "
        f"**{recent_n}** recent · "
        f"**{marked_n}** marked Has RE · "
        f"ready for HOT queue"
    )

    editor_rows = st.session_state.get("branton_preview_editor")
    if not editor_rows or len(editor_rows) != len(preview):
        editor_rows = _preview_to_editor_rows(preview)

    preview_sig = len(editor_rows)
    edited = st.data_editor(
        editor_rows,
        editor_rows,
        column_config={
            "Mark RE": st.column_config.CheckboxColumn(
                "✅ Has RE",
                help="Check each case you confirmed in CRS / Davidson Assessor",
                default=False,
            ),
            "Assessor": st.column_config.LinkColumn(
                "🏠 Assessor",
                display_text="🏠 Search",
                help="One-tap Davidson Assessor search",
            ),
            "Decedent": st.column_config.TextColumn("Decedent", width="medium"),
            "Case #": st.column_config.TextColumn("Case #", width="small"),
            "POC Hint": st.column_config.TextColumn("POC Hint", width="medium"),
            "Address": st.column_config.TextColumn("Address", width="large"),
        },
        disabled=["Decedent", "Case #", "Filed", "POC Hint", "Address", "Recency"],
        hide_index=True,
        use_container_width=True,
        key=f"branton_preview_editor_{preview_sig}",
        num_rows="fixed",
    )
    _sync_editor_marks_to_preview(preview, edited)

    btn1, btn2, btn3 = st.columns([1, 1, 1])
    with btn1:
        st.button(
            "✅ Mark All Has Real Estate",
            use_container_width=True,
            type="secondary",
            key=f"branton_mark_all_preview_btn_{preview_sig}",
            on_click=_on_mark_all_preview_re,
        )
    with btn2:
        st.markdown('<div class="branton-quick-add-green-marker"></div>', unsafe_allow_html=True)
        st.button(
            f"🔥 Add All Marked to {PARTNER_NAME} HOT Queue",
            use_container_width=True,
            key=f"branton_add_marked_hot_btn_{preview_sig}",
            on_click=_on_add_marked_preview_hot,
        )
    with btn3:
        st.caption(
            "Workflow: paste → parse → open 🏠 Assessor links → check **Has RE** "
            "on confirmed addresses → **Add All Marked**."
        )

    with st.expander("Per-case Assessor quick links", expanded=False):
        for idx, row in enumerate(preview[:40]):
            url = row.get("assessor_url") or assessor_search_url(
                row.get("county", ""),
                row.get("decedent", ""),
                row.get("address", ""),
            )
            c1, c2 = st.columns([3, 1])
            c1.caption(
                f"{row.get('decedent', '')} · {row.get('case_number', '')} · "
                f"{row.get('address', 'Address TBD')[:50]}"
            )
            c2.markdown(f"[🏠 Assessor]({url})")
        if len(preview) > 40:
            st.caption(f"+ {len(preview) - 40} more in table Assessor column above")


def render_ftc_batch_results(results: list) -> None:
    if not results:
        return

    hot = [r for r in results if r.get("branton_hot")]
    recent = [r for r in results if r.get("is_recent_30")]
    st.markdown(
        f"**{len(results)}** cases extracted · "
        f"**{len(recent)}** filed in last {RECENCY_HIGH_DAYS}d · "
        f"**{len(hot)}** 🔥 in {PARTNER_NAME}'s HOT queue"
    )

    preview_rows = []
    for row in results:
        preview_rows.append({
            "Decedent": row.get("decedent", ""),
            "Case #": row.get("case_number", ""),
            "Filing Date": row.get("filing_date", "—"),
            "Days": row.get("recency_days", "—"),
            "Recency": _recency_label(row.get("recency_tier", "")),
            "Score": row.get("score", 0),
            "Has RE": "✅" if row.get("has_real_estate") else "—",
            "Status": "🔥 HOT" if row.get("branton_hot") else row.get("qual_status", "New"),
        })
    st.dataframe(preview_rows, use_container_width=True, hide_index=True)

    all_ids = [r.get("lead_id") for r in results if r.get("lead_id")]
    mark_col, info_col = st.columns([1, 2])
    with mark_col:
        if st.button(
            "✅ Mark All Has Real Estate",
            use_container_width=True,
            type="primary",
            key="ftc_mark_all_re",
        ):
            n = mark_all_has_real_estate(all_ids)
            hot_now = sum(1 for r in st.session_state.ftc_batch_results if r.get("branton_hot"))
            st.success(
                f"Marked **{n}** cases · **{hot_now}** recent + RE → 🔥 {PARTNER_NAME} HOT queue"
            )
            st.rerun()
    with info_col:
        st.caption(
            f"Open Assessor Search per row below. Only **marked** cases with recent filings "
            f"(≤{RECENCY_HIGH_DAYS}d) go HOT — nothing auto-queues on paste."
        )

    st.markdown("#### Per-case actions — Assessor + Mark RE")
    for idx, row in enumerate(results):
        lead_id = row.get("lead_id", "")
        decedent = row.get("decedent", "Unknown")
        hot_cls = "ftc-ready-green" if row.get("branton_hot") else "ftc-pending-row"
        hot_lbl = "🔥 HOT · Branton queue" if row.get("branton_hot") else _recency_label(row.get("recency_tier", ""))
        st.markdown(
            f'<div class="{hot_cls}">'
            f'<div class="ftc-ready-label">{hot_lbl}</div>'
            f"<strong>{decedent}</strong> · {row.get('case_number', '—')} · "
            f"Filed {row.get('filing_date', '—')} · Score {row.get('score', 0)}"
            f"</div>",
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        url = row.get("assessor_url") or assessor_search_url(
            row.get("county", ""), row.get("decedent", ""), row.get("address", "")
        )
        c1.link_button("🏠 Assessor Search", url, use_container_width=True)
        if lead_id:
            if c2.button("✅ Has RE", key=queue_widget_key("re_yes", lead_id, idx), use_container_width=True):
                mark_lead_real_estate(lead_id, True)
                st.rerun()
            if c3.button("✗ No RE", key=queue_widget_key("re_no", lead_id, idx), use_container_width=True):
                mark_lead_real_estate(lead_id, False)
                st.rerun()
            if row.get("branton_hot") and c4.button(
                "📞 Contacted",
                key=queue_widget_key("batch_contacted", lead_id, idx),
                use_container_width=True,
            ):
                advance_workflow_status(lead_id, "Contacted")
                st.rerun()
        st.caption(" · ".join(row.get("flags", [])[:5]))


def render_vendor_rolodex(key_prefix: str = "vnd_") -> None:
    st.caption("Up to 3 vendors per category + area notes. Auto-populates in every Guardian Kit.")
    for category in VENDOR_CATEGORIES:
        entry = st.session_state.vendors.get(category, _vendor_slot())
        with st.expander(f"**{category}**", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                entry["vendor_1"] = st.text_input(
                    "Vendor 1",
                    value=entry.get("vendor_1", ""),
                    key=f"{key_prefix}v1_{category}",
                )
                entry["vendor_2"] = st.text_input(
                    "Vendor 2",
                    value=entry.get("vendor_2", ""),
                    key=f"{key_prefix}v2_{category}",
                )
            with c2:
                entry["vendor_3"] = st.text_input(
                    "Vendor 3",
                    value=entry.get("vendor_3", ""),
                    key=f"{key_prefix}v3_{category}",
                )
                entry["area_notes"] = st.text_input(
                    "Area Notes",
                    value=entry.get("area_notes", ""),
                    placeholder="e.g., Wilson County preferred · Mount Juliet area",
                    key=f"{key_prefix}notes_{category}",
                )
        st.session_state.vendors[category] = entry
    if st.button("💾 Save Vendors", use_container_width=True, type="primary", key=f"{key_prefix}save"):
        st.success("✅ Vendor Rolodex saved — all Guardian Kits will reflect these contacts.")


CALL_QUEUE_KEY_NS = "cq"

SIMPLE_PIPELINE = {
    "All": None,
    "New": frozenset({"New", "Attempted"}),
    "Contacted": frozenset({"Contacted", "Interested"}),
    "Appt Set": frozenset({"Appt Set"}),
    "Listed": frozenset({"Listing Signed", "Listed", "Under Contract", "Court Pending"}),
    "Closed": frozenset({"Closed Won"}),
}

STAGE_PILL_MAP = {
    "New": ("bw-pill-new", "🆕 New"),
    "Attempted": ("bw-pill-new", "📞 Attempted"),
    "Contacted": ("bw-pill-contacted", "✅ Contacted"),
    "Interested": ("bw-pill-contacted", "💬 Interested"),
    "Appt Set": ("bw-pill-appt", "📍 Appt Set"),
    "Listing Signed": ("bw-pill-listed", "🏠 Listed"),
    "Listed": ("bw-pill-listed", "🏠 Listed"),
    "Under Contract": ("bw-pill-listed", "📝 Under Contract"),
    "Court Pending": ("bw-pill-listed", "⚖️ Court Pending"),
    "Closed Won": ("bw-pill-closed", "💰 Closed"),
    "Nurture": ("bw-pill-closed", "🌱 Nurture"),
    "Dead": ("bw-pill-closed", "✗ Dead"),
}


def get_simple_pipeline_counts(leads: list) -> dict:
    counts = {k: 0 for k in SIMPLE_PIPELINE if k != "All"}
    for lead in leads:
        stage = derive_branton_stage(lead)
        for pill, stages in SIMPLE_PIPELINE.items():
            if pill == "All" or not stages:
                continue
            if stage in stages:
                counts[pill] += 1
                break
    return counts


def _stage_pill_html(stage: str) -> str:
    css, label = STAGE_PILL_MAP.get(stage, ("bw-pill-new", stage))
    return f'<span class="bw-status-pill {css}">{label}</span>'


def _lead_matches_pipeline_filter(lead: dict, filt: str) -> bool:
    if filt == "All":
        return True
    stages = SIMPLE_PIPELINE.get(filt)
    if not stages:
        return True
    return derive_branton_stage(lead) in stages


def paste_auto_add_leads(raw: str, county: str = "Davidson County") -> int:
    """One paste → bulk add + auto-prioritize freshest first."""
    return bulk_paste_to_hot_queue(raw, county=county)


def _sanitize_widget_id(raw: str) -> str:
    """Safe token for Streamlit widget keys — strips chars that break key parsing."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", str(raw or "unknown"))


def queue_widget_key(widget: str, lead_id: str, idx: int) -> str:
    """Permanent unique widget key: cq_{widget}_{lead_id}_{idx}"""
    return f"{CALL_QUEUE_KEY_NS}_{widget}_{_sanitize_widget_id(lead_id)}_{idx}"


def _queue_lead_id(lead: dict, idx: int) -> str:
    """Stable lead id for widget keys — never collides with widget prefix 'card'."""
    return str(lead.get("id") or lead.get("lead_id") or f"slot_{idx}")


def _dedupe_queue_for_cards(queue: list, limit: int = 0) -> list:
    """One card per lead id — prevents duplicate Streamlit widget keys. limit=0 → unlimited."""
    seen: set = set()
    cards: list = []
    for lead in queue:
        if limit and len(cards) >= limit:
            break
        lead_id = _queue_lead_id(lead, len(cards))
        if lead_id in seen:
            continue
        seen.add(lead_id)
        cards.append(lead)
    return cards


def _prepare_queue_card_slots(cards: list) -> list:
    """Assign monotonic slot index per card — keys never reuse idx 0 across dup renders."""
    slots = []
    for slot_idx, lead in enumerate(cards):
        lid = _queue_lead_id(lead, slot_idx)
        slots.append((slot_idx, lid, lead))
    return slots


def _render_call_queue_card(
    lead: dict,
    idx: int,
    today: str,
    lead_id: str,
    highlight: bool = False,
) -> None:
    i = idx
    real_lead_id = lead.get("id") or lead.get("lead_id")
    notes_key = queue_widget_key("notes", lead_id, i)
    script_toggle_key = queue_widget_key("script_open", lead_id, i)
    _init_card_notes_widget(notes_key, lead, real_lead_id)

    bucket = get_queue_bucket(lead, today)
    card_class = "bw-card hot" if (highlight or bucket == 0 or lead.get("branton_hot")) else "bw-card"

    decedent = lead.get("decedent", "Unknown").split("—")[0].strip()
    poc = poc_display_name(lead)
    phone = lead.get("phone", "")
    address = lead.get("address", "Address TBD")
    stage = derive_branton_stage(lead)
    tel = phone_tel_url(phone)
    parsed = lead_to_parsed(lead)
    script_text = generate_phone_script(parsed, lead)

    hot_badge = ""
    if bucket == 0 or lead.get("branton_hot"):
        hot_badge = '<span class="bw-status-pill bw-pill-hot">🔥 CALL FIRST</span> '

    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
    badge_col, del_col = st.columns([6, 1])
    with badge_col:
        st.markdown(f"{hot_badge}{_stage_pill_html(stage)}", unsafe_allow_html=True)
    with del_col:
        st.markdown('<div class="bw-delete-btn-marker"></div>', unsafe_allow_html=True)
        if st.button(
            "🗑️",
            key=queue_widget_key("btn_delete", lead_id, i),
            help="Delete this lead",
            use_container_width=True,
        ):
            if real_lead_id and delete_lead(real_lead_id):
                st.toast(f"🗑️ Removed — {decedent}")
                st.rerun()
    st.markdown(f'<div class="bw-card-name">{decedent}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="bw-card-addr">🏠 {address}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="bw-card-poc">POC: <strong>{poc}</strong> · {lead.get("case_number", "—")}</div>',
        unsafe_allow_html=True,
    )
    if tel:
        st.markdown(
            f'<a class="mm-phone-tap" href="{tel}">📞 Tap to Call {clean_phone(phone)}</a>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="bw-script-btn-marker"></div>', unsafe_allow_html=True)
    st.button(
        "📞 Call Script",
        key=queue_widget_key("btn_script", lead_id, i),
        use_container_width=True,
        type="primary",
        on_click=_cb_toggle_script,
        args=(script_toggle_key,),
    )

    if st.session_state.get(script_toggle_key):
        st.markdown(
            f'<div class="bw-script-box">{html.escape(script_text)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="bw-notes-label">📝 Notes</div>', unsafe_allow_html=True)
    st.markdown('<div class="bw-notes-marker"></div>', unsafe_allow_html=True)
    st.text_area(
        "Lead notes",
        height=200,
        key=notes_key,
        on_change=_on_card_note_saved,
        args=(real_lead_id, notes_key),
        label_visibility="collapsed",
    )

    if st.session_state.get("branton_note_saved_id") == real_lead_id:
        st.markdown('<div class="bw-card-flash">✓ Saved!</div>', unsafe_allow_html=True)
    if st.session_state.get("branton_action_flash_id") == real_lead_id:
        msg = st.session_state.get("branton_action_flash_msg", "Saved!")
        st.markdown(f'<div class="bw-card-flash">✓ {msg}</div>', unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        st.markdown('<div class="bw-action-green-marker"></div>', unsafe_allow_html=True)
        st.button(
            "📝 Quick Note",
            key=queue_widget_key("btn_note", lead_id, i),
            use_container_width=True,
            on_click=_cb_quick_note,
            args=(real_lead_id, notes_key),
        )
    with g2:
        st.markdown('<div class="bw-action-green-marker"></div>', unsafe_allow_html=True)
        st.button(
            "✅ Contacted",
            key=queue_widget_key("btn_contacted", lead_id, i),
            use_container_width=True,
            on_click=_cb_crm_stage,
            args=(real_lead_id, "Contacted", notes_key),
        )

    g3, g4 = st.columns(2)
    with g3:
        st.markdown('<div class="bw-action-green-marker"></div>', unsafe_allow_html=True)
        st.button(
            "📍 Appt Set",
            key=queue_widget_key("btn_appt", lead_id, i),
            use_container_width=True,
            on_click=_cb_crm_stage,
            args=(real_lead_id, "Appt Set", notes_key),
        )
    with g4:
        st.markdown('<div class="bw-action-green-marker"></div>', unsafe_allow_html=True)
        st.button(
            "🏠 Listed",
            key=queue_widget_key("btn_listed", lead_id, i),
            use_container_width=True,
            on_click=_cb_crm_stage,
            args=(real_lead_id, "Listing Signed", notes_key),
        )

    st.markdown('<div class="bw-action-closed-marker"></div>', unsafe_allow_html=True)
    st.button(
        "💰 Closed",
        key=queue_widget_key("btn_closed", lead_id, i),
        use_container_width=True,
        on_click=_cb_crm_stage,
        args=(real_lead_id, "Closed Won", notes_key),
    )

    with st.expander(f"📘 Guardian Kit — {decedent[:32]}", expanded=False):
        st.markdown(generate_guardian_kit(parsed, st.session_state.vendors))

    st.markdown("</div>", unsafe_allow_html=True)


# Public aliases for CRM module imports
render_crm_call_queue_card = _render_call_queue_card
pg_render_call_queue_card = _render_call_queue_card
pg_queue_widget_key = queue_widget_key


def render_crm_call_queue(leads: list) -> None:
    """Branton mobile money machine — open app, see hot list, one-tap actions."""
    run_serial = st.session_state.get("_run_serial", 0)
    if st.session_state.get("_cq_done_serial") == run_serial:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    last_added = st.session_state.pop("branton_last_added_id", None)
    due_today = count_due_today(leads)
    pipe_counts = get_simple_pipeline_counts(leads)

    st.markdown('<div class="bw-bulk-paste-zone">', unsafe_allow_html=True)
    st.markdown(
        '<div class="bw-bulk-paste-title">🚀 Paste New Leads (Bulk)</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="bw-bulk-paste-hint">'
        "Unlimited capacity · auto-detects <strong>any format</strong> · unique IDs · saves to disk instantly"
        "</div>",
        unsafe_allow_html=True,
    )
    paste_raw = st.text_area(
        "Bulk paste leads",
        height=280,
        key="bw_paste_leads",
        label_visibility="collapsed",
        placeholder=(
            "Paste unlimited leads — any format:\n"
            "• One line: Name | Address | POC | Case | Notes\n"
            "• Multi-line court blocks (blank line between estates)\n"
            "• Full CaseLink / tncrtinfo dump"
        ),
    )
    paste_county = st.selectbox(
        "County",
        list(MIDDLE_TN_COUNTY_LINKS.keys()),
        index=1,
        key="bw_paste_county",
    )
    st.markdown('<div class="bw-bulk-btn-marker"></div>', unsafe_allow_html=True)
    if st.button(
        "Add All to HOT Queue + Auto-Prioritize (freshest first)",
        use_container_width=True,
        type="primary",
        key="bw_paste_add",
    ):
        if not paste_raw.strip():
            st.warning("Paste your leads first.")
        else:
            n = bulk_paste_to_hot_queue(paste_raw, county=paste_county)
            if n:
                st.session_state.pop("bw_paste_leads", None)
                st.session_state.branton_queue_flash = (
                    f"🔥 **{n} leads** added to HOT queue — freshest first. Smash the top card!"
                )
                st.rerun()
            else:
                st.warning(
                    "No leads parsed — each row needs **Name + Address**. "
                    "Use pipe (|), tab, or multi-line blocks."
                )
    st.markdown("</div>", unsafe_allow_html=True)

    flash = st.session_state.pop("branton_queue_flash", None)
    if flash:
        st.success(flash)
    msg = st.session_state.pop("branton_quick_add_msg", None)
    if msg:
        st.success(msg)

    st.markdown(
        f'<div class="bw-hero">🔥 Branton\'s HOT Queue – Call These First ({due_today} due today)</div>',
        unsafe_allow_html=True,
    )

    pill_labels = ["All"] + [k for k in SIMPLE_PIPELINE if k != "All"]

    def _pill_label(pill: str) -> str:
        if pill == "All":
            return f"All ({len(leads)})"
        return f"{pill} ({pipe_counts.get(pill, 0)})"

    filt_key = st.radio(
        "Pipeline",
        pill_labels,
        horizontal=True,
        key="bw_pipeline_filter",
        format_func=_pill_label,
        label_visibility="collapsed",
    )

    queue = get_daily_prioritized_queue(leads, "Priority Queue")
    if filt_key != "All":
        queue = [l for l in queue if _lead_matches_pipeline_filter(l, filt_key)]

    if not queue:
        st.info("Your call queue is empty. Paste leads above to build Branton's HOT list.")
    else:
        card_leads = _dedupe_queue_for_cards(queue)
        card_slots = _prepare_queue_card_slots(card_leads)
        for slot_idx, lid, lead in card_slots:
            _render_call_queue_card(
                lead,
                slot_idx,
                today,
                lid,
                highlight=(last_added and lead.get("id") == last_added),
            )

    st.session_state["_cq_done_serial"] = run_serial
    st.session_state.pop("branton_note_saved_id", None)
    st.session_state.pop("branton_action_flash_id", None)
    st.session_state.pop("branton_action_flash_msg", None)

    with st.expander("⚙️ More tools", expanded=False):
        tool1, tool2 = st.columns(2)
        with tool1:
            st.download_button(
                "📤 Export Calls CSV",
                data=export_branton_calls_today(leads),
                file_name=f"branton_calls_{today}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"btn_crm_queue_{today}_export",
            )
        with tool2:
            st.button(
                "🗑️ Clear All",
                use_container_width=True,
                key=f"btn_crm_queue_{today}_clear",
                on_click=_on_clear_demo_leads,
            )
        render_vendor_rolodex(key_prefix="bw_vnd_")


def _training_yt(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"


def _render_training_links(items: list, key_prefix: str) -> None:
    st.markdown('<div class="train-zone">', unsafe_allow_html=True)
    for label, url in items:
        safe_url = url.replace('"', "%22")
        st.markdown(
            f'<a class="train-link-btn" href="{safe_url}" target="_blank" rel="noopener">{label}</a>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def render_training_hub() -> None:
    st.markdown(
        '<div class="train-hero">'
        "<h2>🎥 Tennessee Probate Training Hub</h2>"
        "<p>The richest probate playbook in Middle TN — study before every call.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="train-cheat">'
        "<h3>🎙️ Opener · Listen · Close — Cheat Sheet</h3>"
        "<p><strong>OPENER (Aaron):</strong></p>"
        "<blockquote>"
        "\"I realize I may be reaching out a little early… very respectfully. "
        "Nothing needs to happen today. I'm not calling with an agenda.\""
        "</blockquote>"
        "<p><strong>LISTEN (Aaron + Rick) — use 2–3× per call:</strong></p>"
        "<blockquote>\"Tell me more about that.\"</blockquote>"
        "<blockquote>\"Help me understand — walk me through where things stand with the estate.\"</blockquote>"
        "<p><strong>HONEST EXPECTATIONS:</strong></p>"
        "<blockquote>"
        "\"More likely than not the goal will be to sell — but that might be months from now.\""
        "</blockquote>"
        "<p><strong>CLOSE (Aaron):</strong></p>"
        "<blockquote>"
        "\"May I make a suggestion?\" → 10–15 min call → free Equity Snapshot + Net Sheet"
        "</blockquote>"
        "<p><strong>ALWAYS SAY:</strong> <em>Subject to court approval</em> — every timeline, offer, and close.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="train-section">', unsafe_allow_html=True)
    st.markdown('<p class="train-section-title">⭐ Aaron Novello — Role-Play · Family Home · Close</p>', unsafe_allow_html=True)
    _render_training_links([
        ("▶ Probate Role-Play (Live Call Breakdown)", _training_yt("aaron novello probate role play phone call")),
        ("▶ Family Home & Heir Dynamics", _training_yt("aaron novello probate family home heirs")),
        ("▶ \"May I Make a Suggestion?\" Close", _training_yt("aaron novello may i make a suggestion probate")),
        ("▶ Empathy-First Early Outreach", _training_yt("aaron novello empathy first probate call")),
        ("▶ Probate Real Estate 101", _training_yt("aaron novello probate real estate 101")),
        ("▶ Listing Presentation (Options, Not Pressure)", _training_yt("aaron novello probate listing presentation")),
        ("▶ Follow-Up System (3-Touch Minimum)", _training_yt("aaron novello probate follow up system")),
    ], "train_aaron")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="train-section">', unsafe_allow_html=True)
    st.markdown('<p class="train-section-title">🎯 Rick Yen — Conversation · Anchoring · Objections</p>', unsafe_allow_html=True)
    _render_training_links([
        ("▶ Probate Conversation & Discovery", _training_yt("rick yen probate real estate conversation")),
        ("▶ Collaborative Scripts & Price Anchoring", _training_yt("rick yen probate scripts anchoring")),
        ("▶ Objection Handling (Not Ready / Have Attorney)", _training_yt("rick yen probate objections handling")),
        ("▶ Net Sheet & Equity Snapshot Delivery", _training_yt("rick yen net sheet probate real estate")),
    ], "train_rick")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="train-section">', unsafe_allow_html=True)
    st.markdown('<p class="train-section-title">🏆 High-Volume & Elite Operators</p>', unsafe_allow_html=True)
    _render_training_links([
        ("▶ Andrew Becker — Probate Systems & Scale", _training_yt("andrew becker probate real estate")),
        ("▶ 140 Listings/Year Probate Agent Playbook", _training_yt("probate real estate agent 140 listings high volume")),
        ("▶ Mike — Attorney Alignment & Realtor Partnership", _training_yt("probate attorney realtor alignment partnership")),
        ("▶ Tangy Cousins — Probate Lead Conversion", _training_yt("tangy cousins probate real estate")),
        ("▶ Jose — Attorney Referral & Coordinator Model", _training_yt("jose probate attorney referral project coordinator")),
    ], "train_ops")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="train-section">', unsafe_allow_html=True)
    st.markdown('<p class="train-section-title">📘 Guardian Kit · Concierge · Heavy Lifting</p>', unsafe_allow_html=True)
    _render_training_links([
        ("▶ Bruce & Heath — Concierge / Heavy Lifting Model", _training_yt("bruce heath probate concierge real estate")),
        ("▶ Estate Sale · Cleanout · Vendor Coordination", _training_yt("bruce heath estate sale cleanout probate")),
        ("▶ Project Coordinator Positioning (Jose)", _training_yt("probate project coordinator ancillary services")),
        ("▶ Guardian Kit Walkthrough — Appointment Prep", _training_yt("probate guardian kit listing appointment real estate")),
    ], "train_concierge")
    with st.expander("📖 Guardian Kit Talking Points (memorize)", expanded=False):
        st.markdown(
            """
            - **You focus on family. We handle the heavy lifting** — estate sale, cleanout, lockbox, utilities, lawn.
            - Bring printed kit to every appointment — **Express Offers section first**.
            - Present **four options**: Express Offers · Traditional + Funded Repairs · Muniment of Title · Off-Market
            - **Project Coordinator** — not a pushy listing pitch; coordinate attorneys, vendors, title, court timelines
            - Free **Equity Snapshot + Net Sheet** within 48 hours of first meaningful call
            """
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="train-section">', unsafe_allow_html=True)
    st.markdown('<p class="train-section-title">🚀 Express Offers · Muniment of Title · TN Law</p>', unsafe_allow_html=True)
    _render_training_links([
        ("▶ Express Offers — Competing Cash Buyers (eXp)", "https://www.exprealty.com"),
        ("▶ Express Offers Probate Pitch Training", _training_yt("express offers probate real estate exp")),
        ("▶ Muniment of Title — Tennessee Overview", _training_yt("muniment of title tennessee probate")),
        ("▶ TN Statute Search — T.C.A. Title 30", "https://www.tn.gov/content/tn/tcas/search.html"),
        ("▶ When to Use Muniment vs. Full Administration", _training_yt("muniment of title vs probate administration tennessee")),
    ], "train_legal")
    with st.expander("📖 Express Offers — 30-Second Pitch", expanded=False):
        st.markdown(
            """
            When speed and certainty matter more than squeezing every dollar, **Express Offers**
            gives your family **competing cash offers** — as-is, no repairs, no showings,
            close **subject to court approval**.

            *"It's not giving up — it's choosing peace of mind while the estate settles."*
            """
        )
    with st.expander("📖 Muniment of Title — Plain Language", expanded=False):
        st.markdown(
            """
            **Muniment of Title** (T.C.A. § 30-2-712) can transfer property **without listing or selling**
            when the estate qualifies — often no unpaid debts, will devises the home, all heirs aligned.

            - File in county Chancery Court · court approval required
            - Often **4–10 weeks** — faster than full administration in many cases
            - Scott coordinates valuation + vendors; **attorney handles legal path**
            - Defer every legal question to their office — make their job easier
            """
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="train-section">', unsafe_allow_html=True)
    st.markdown('<p class="train-section-title">⚖️ Attorney Outreach & Family Probes</p>', unsafe_allow_html=True)
    _render_training_links([
        ("▶ Attorney Partnership — Never Market Before Authority", _training_yt("probate attorney realtor when can sell property")),
        ("▶ Sibling / Heir Dynamics Questions", _training_yt("probate heirs disagreement sell inherited house")),
        ("▶ Out-of-State Heir Coordination", _training_yt("probate out of state heirs inherited property")),
    ], "train_attorney")
    st.markdown(
        """
        **Family probes (every call):**
        - How many heirs? Everyone on the same page?
        - Anyone want to buy out the others?
        - Anyone out of state? Property vacant or occupied?
        - Estate debts, mortgage, or liens?
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="train-stuck">'
        '<a class="train-link-btn train-stuck-btn" href="tel:6159530758">'
        "📞 Stuck? Call Scott 615-953-0758"
        "</a></div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Escalate immediately: sibling disputes · buyout math · competing agent · attorney conflicts · $500K+"
    )


def render_first_to_call_middle_tn(leads: list) -> None:
    """Mobile-first command center — one tap to dominate fresh Middle TN probate leads."""
    run_serial = st.session_state.get("_run_serial", 0)
    if st.session_state.get("_ftc_done_serial") == run_serial:
        return

    st.markdown(
        '<div class="ftc-hero">🚀 First-to-Call Middle TN · One tap = fastest caller in the region<br>'
        f'<span style="font-size:0.92rem;font-weight:500;">{PARTNER_NAME} on phone · Scott on CaseLink · '
        '50/50 on every close</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="ftc-role-split">{WIN_NOTE}</div>', unsafe_allow_html=True)

    schedule = get_courthouse_run_schedule()
    st.markdown(
        f'<div class="ftc-section"><strong>Week {schedule["week"]}</strong> · '
        f'Rotate: <span style="color:#58a6ff;">{schedule["rotation"]}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="ftc-zone-label">🏙️ Davidson — Online Speed</p>', unsafe_allow_html=True)
    davidson = MIDDLE_TN_COUNTY_LINKS["Davidson County"]
    d1, d2, d3, d4 = st.columns(4)
    d1.link_button("Probate Lookup", davidson["probate_lookup"], use_container_width=True)
    d2.link_button("Dockets", davidson["dockets"], use_container_width=True)
    d3.link_button("CaseLink", davidson["caselink"], use_container_width=True)
    d4.link_button("Assessor", davidson["assessor"], use_container_width=True)

    st.markdown('<p class="ftc-zone-label">🏛️ Outer Counties — Courthouse Sweat Equity</p>', unsafe_allow_html=True)
    outer_cols = st.columns(len(MIDDLE_TN_COUNTY_LINKS) - 1)
    outer_counties = [c for c in MIDDLE_TN_COUNTY_LINKS if c != "Davidson County"]
    for col, county in zip(outer_cols, outer_counties):
        info = MIDDLE_TN_COUNTY_LINKS[county]
        with col:
            st.markdown(f"**{info['emoji']} {county.replace(' County', '')}**")
            st.link_button("tncrtinfo", info["tncrtinfo"], use_container_width=True)
            st.link_button("Chancery", info["chancery"], use_container_width=True)
            st.link_button("Assessor", info["assessor"], use_container_width=True)
            if info.get("maps"):
                st.link_button("Maps", info["maps"], use_container_width=True)

    st.markdown("#### 🕊️ Obituary Search Templates")
    obit_cols = st.columns(3)
    obit_urls = obituary_search_urls(county="Davidson County")
    for col, (label, url) in zip(obit_cols, list(obit_urls.items())[:3]):
        col.link_button(label, url, use_container_width=True)

    st.markdown('<div class="ftc-paste-hero"><strong>📋 Paste New Batch</strong> — '
                'auto-scores real estate + recent filing → Branton HOT queue</div>', unsafe_allow_html=True)
    batch_raw = st.text_area(
        "Paste court export",
        value=st.session_state.get("ftc_batch_raw", ""),
        height=200,
        key="ftc_batch_paste",
        label_visibility="collapsed",
        placeholder="Paste tncrtinfo export, CaseLink dump, or courthouse notes…",
    )
    b1, b2 = st.columns([2, 1])
    with b2:
        batch_county = st.selectbox(
            "County",
            list(MIDDLE_TN_COUNTY_LINKS.keys()),
            index=1,
            key="ftc_batch_county",
        )
    with b1:
        st.markdown('<div class="ftc-btn-red-marker"></div>', unsafe_allow_html=True)
        if st.button("🔥 Parse & Score Batch", use_container_width=True, type="primary", key="ftc_batch_parse"):
            if not batch_raw.strip():
                st.warning("Paste court data first.")
            else:
                st.session_state.ftc_batch_raw = batch_raw
                st.session_state.ftc_batch_results = process_ftc_batch(batch_raw, default_county=batch_county)
                st.success(f"✅ {len(st.session_state.ftc_batch_results)} cases parsed — mark RE below")
                st.rerun()

    if st.session_state.get("ftc_batch_results"):
        render_ftc_batch_results(st.session_state.ftc_batch_results)

    st.markdown("---")
    st.markdown("#### 📞 Branton Call Queue")
    render_crm_call_queue(leads)

    with st.expander("📅 Daily Routine Checklist", expanded=False):
        for key, label in DAILY_ROUTINE_BRANTON:
            st.session_state.ftc_daily_checklist[key] = st.checkbox(
                label,
                value=st.session_state.ftc_daily_checklist.get(key, False),
                key=f"ftc_daily_{key}",
            )

    with st.expander("🏛️ Courthouse Visit Checklist", expanded=False):
        for key, label in OUTER_COUNTY_VISIT_CHECKLIST:
            st.session_state.ftc_outer_checklist[key] = st.checkbox(
                label,
                value=st.session_state.ftc_outer_checklist.get(key, False),
                key=f"ftc_outer_{key}",
            )
        st.markdown("**Weekly schedule**")
        for day, county, note in schedule["days"]:
            st.markdown(f"- **{day}** · {county} — {note}")

    with st.expander("🎯 Weekly Targets", expanded=False):
        for emoji_lbl, detail in WEEKLY_TARGETS:
            st.markdown(f"- {emoji_lbl}: {detail}")

    st.session_state["_ftc_done_serial"] = run_serial


_MAIN_SECTIONS = [
    "📞 Call Queue",
    "🚀 First-to-Call",
    "🤖 AI Agent Lead Harvester • Small Counties",
    "🎥 Training",
]


def _render_app_shell() -> None:
    st.markdown(
        '<div style="text-align:center;padding:0.35rem 0 0.5rem 0;">'
        '<span style="color:#8b949e;font-size:0.82rem;font-weight:700;">'
        'ProbateGuardian · Scott Hardesty · '
        '<a href="tel:6159530758" style="color:#3fb950;text-decoration:none;">615-953-0758</a>'
        '</span></div>',
        unsafe_allow_html=True,
    )

    if "main_nav_radio" not in st.session_state:
        st.session_state.main_nav_radio = _MAIN_SECTIONS[0]

    main_view = st.radio(
        "App section",
        _MAIN_SECTIONS,
        horizontal=True,
        key="main_nav_radio",
        label_visibility="collapsed",
    )

    if main_view == _MAIN_SECTIONS[0]:
        from probate_crm import render_probate_crm

        render_probate_crm()
    elif main_view == _MAIN_SECTIONS[1]:
        render_first_to_call_middle_tn(st.session_state.leads)
    elif main_view == _MAIN_SECTIONS[2]:
        from agent_harvester import render_ai_agent_lead_harvester

        render_ai_agent_lead_harvester(st.session_state.leads)
    else:
        render_training_hub()


def _maybe_render_app_shell() -> None:
    """Single UI entry — blocks duplicate render when app module is resolved twice."""
    run_serial = st.session_state.get("_run_serial", 0) + 1
    st.session_state["_run_serial"] = run_serial
    if st.session_state.get("_shell_entry_serial") == run_serial:
        return
    st.session_state["_shell_entry_serial"] = run_serial
    _render_app_shell()


_maybe_render_app_shell()
