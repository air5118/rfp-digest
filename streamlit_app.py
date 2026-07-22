"""
RFP Digest — Streamlit app.

A hosted mirror of the rfp-tracker daily digest email. Renders the same four
sections (Federal / State & Local / Brand Searches / AI-sourced) from data/rfps.json.
Deploy free on Streamlit Community Cloud: https://share.streamlit.io
"""
import json
import urllib.request
from datetime import datetime, date
from pathlib import Path
from html import escape

import streamlit as st

DATA_FILE = Path(__file__).parent / "data" / "rfps.json"
# Live feed URL — the app fetches this over HTTP so it reflects new data on its
# own (every ~5 min via the cache TTL below), WITHOUT waiting for a redeploy.
FEED_URL = "https://raw.githubusercontent.com/air5118/rfp-digest/main/data/rfps.json"

# Section definitions — mirror build_email_html() in rfp.py exactly.
SECTIONS = [
    {
        "type": "gov_federal",
        "title": "Federal Advertising Contracts",
        "color": "#1a73e8",
        "badge": "APPLY ON SAM.GOV",
        "link_text": "🔗 Apply on SAM.gov →",
        "note": "US federal solicitations on SAM.gov — advertising &amp; marketing contracts only. "
                "Click Apply on SAM.gov → to go directly to the listing and submit your proposal.",
    },
    {
        "type": "state_local",
        "title": "State &amp; Local Government RFPs",
        "color": "#f57c00",
        "badge": "SUBMIT PROPOSAL",
        "link_text": "📰 Read Article →",
        "note": "US state &amp; local government advertising RFPs — lotteries, tourism boards, transit "
                "authorities, universities, city/county agencies. Click Read Article → for the full solicitation.",
    },
    {
        "type": "brand_lead",
        "title": "Brand Agency Searches — US Only",
        "color": "#9c27b0",
        "badge": "OPEN SEARCH",
        "link_text": "📰 Read Article →",
        "note": "US brands actively seeking agencies. These are open searches, NOT award announcements. "
                "Click Read Article → to read the details, then contact the brand to respond.",
    },
    {
        "type": "perplexity",
        "title": "Perplexity AI Discoveries — Direct RFP Links",
        "color": "#00897b",
        "badge": "DIRECT LINK",
        "link_text": "🔗 View RFP →",
        "note": "Found via real-time web search across procurement portals, SAM.gov, BidNet, state portals, "
                "and trade press. These links go directly to the RFP or source article — no redirects.",
    },
]

st.set_page_config(page_title="RFP Digest", page_icon="📋", layout="wide")

CSS = """
<style>
  .block-container { max-width: 1000px; padding-top: 1.5rem; }
  #MainMenu, footer, header { visibility: hidden; }
  .digest-head {
    background: linear-gradient(135deg, #1a73e8, #9c27b0);
    color: #fff; padding: 24px 28px; border-radius: 12px;
    box-shadow: 0 8px 24px rgba(26,115,232,.18);
  }
  .digest-head h1 { margin: 0; font-size: 26px; font-weight: 800; }
  .digest-head .rfp { background: rgba(255,255,255,.22); padding: 1px 8px; border-radius: 5px; }
  .digest-head .summary { margin: 10px 0 0; font-size: 14px; opacity: .94; }
  .digest-head .div { opacity: .55; margin: 0 6px; }
  .sec-h2 { margin: 26px 0 3px; font-size: 17px; font-weight: 700; }
  .sec-badge { color:#fff; padding:3px 10px; border-radius:5px; font-size:11px; font-weight:700; }
  .sec-count { font-size:13px; color:#999; font-weight:500; }
  .sec-note { color:#666; font-size:13px; margin:0 0 12px; }
  table.rfp { width:100%; border-collapse:collapse; font-size:13px;
              background:#fff; border:1px solid #e9edf1; border-radius:12px; overflow:hidden; }
  table.rfp th { text-align:left; padding:11px 14px; background:#f4f6f8;
                 border-bottom:2px solid #dee2e6; font-size:12px; text-transform:uppercase;
                 letter-spacing:.04em; color:#666; }
  table.rfp td { padding:13px 14px; border-bottom:1px solid #eef1f4; vertical-align:top; color:#666; }
  table.rfp tr:last-child td { border-bottom:none; }
  .opp-title { color:#222; font-weight:600; font-size:13.5px; text-decoration:none; }
  .opp-title:hover { color:#1a73e8; }
  .opp-link { display:inline-block; margin-top:5px; font-size:11.5px; color:#1a73e8; text-decoration:none; }
  .domain { color:#999; margin-left:4px; }
  .due { font-weight:600; color:#222; }
  .pill { display:inline-block; margin-left:6px; font-size:10.5px; font-weight:600; padding:1px 7px; border-radius:10px; }
  .pill.urgent { background:rgba(220,53,69,.12); color:#dc3545; }
  .pill.soon { background:rgba(240,169,53,.14); color:#c67d00; }
  .pill.ok { background:rgba(40,167,69,.12); color:#1e7e34; }
  .status { display:inline-block; background:#17a2b8; color:#fff; padding:2px 9px; border-radius:10px; font-size:11px; font-weight:600; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_data():
    # Fetch the live feed over HTTP so the app auto-refreshes every ~5 min
    # (the cache TTL) with no redeploy/reboot needed. Fall back to the bundled
    # file only if the network read fails.
    try:
        req = urllib.request.Request(FEED_URL, headers={"User-Agent": "rfp-digest-app"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:  # noqa: BLE001
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)


def days_left(deadline):
    if not deadline:
        return None
    try:
        d = datetime.strptime(deadline[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    return (d - date.today()).days


def deadline_pill(deadline):
    dl = days_left(deadline)
    if dl is None or dl < 0:
        return ""
    cls = "urgent" if dl <= 7 else ("soon" if dl <= 21 else "ok")
    txt = "TODAY" if dl == 0 else f"{dl}d left"
    return f'<span class="pill {cls}">{txt}</span>'


def fmt_date(s):
    if not s:
        return "—"
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").strftime("%m/%d/%Y")
    except ValueError:
        return s


def row_html(r, sec):
    url = escape(r.get("url", "") or "")
    title = escape(r.get("title", "Untitled"))
    issuer = escape(r.get("issuer", "") or "—")
    sd = (r.get("source_domain") or "").replace("https://", "").replace("http://", "").rstrip("/")
    domain = f'<span class="domain">({escape(sd)})</span>' if sd else ""
    link = (f'<a class="opp-link" href="{url}" target="_blank">{sec["link_text"]}{domain}</a>'
            if url else "")
    deadline = r.get("deadline", "") or ""
    date_shown = deadline or r.get("posted", "") or ""
    date_cls = "due" if deadline else ""
    return f"""<tr>
      <td style="width:42%"><a class="opp-title" href="{url or '#'}" target="_blank">{title}</a><br>{link}</td>
      <td style="width:20%">{issuer}</td>
      <td style="width:14%"><span class="{date_cls}">{fmt_date(date_shown)}</span>{deadline_pill(deadline)}</td>
      <td style="width:11%"><span class="status">new</span></td>
      <td style="width:13%;color:#999">—</td>
    </tr>"""


def section_html(items, sec):
    rows = "".join(row_html(r, sec) for r in items)
    n = len(items)
    return f"""
    <div class="sec-h2">
      <span class="sec-badge" style="background:{sec['color']}">{sec['badge']}</span>
      <span style="color:{sec['color']}">&nbsp;{sec['title']}</span>
      <span class="sec-count">({n} {'opportunity' if n == 1 else 'opportunities'})</span>
    </div>
    <p class="sec-note">{sec['note']}</p>
    <table class="rfp">
      <thead><tr>
        <th>RFP / Opportunity</th><th>Source</th><th>Date</th><th>Status</th><th>Assignee</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def main():
    try:
        data = load_data()
    except Exception as e:  # noqa: BLE001
        st.error(f"Couldn't load data feed: {e}")
        return

    rfps = [r for r in data.get("rfps", []) if r.get("title")]
    gen = data.get("generated")
    head_date = (datetime.strptime(gen, "%Y-%m-%d") if gen else datetime.now()).strftime("%B %d, %Y")

    def count(t):
        return sum(1 for r in rfps if r.get("type") == t)

    summary = (
        f'{count("gov_federal")} federal<span class="div">—</span>'
        f'{count("state_local")} state/local<span class="div">—</span>'
        f'{count("brand_lead")} brand searches<span class="div">—</span>'
        f'{count("perplexity")} AI-sourced'
        '<span class="div">|</span> All US-only · Active · Advertising-verified'
    )
    st.markdown(
        f'<div class="digest-head"><h1>Daily <span class="rfp">RFP</span> Digest '
        f'— {head_date}</h1><div class="summary">{summary}</div></div>',
        unsafe_allow_html=True,
    )

    query = st.text_input("Filter", placeholder="Filter by title, issuer, or keyword…",
                          label_visibility="collapsed").strip().lower()

    def matches(r):
        if not query:
            return True
        hay = " ".join(str(r.get(k, "")) for k in ("title", "issuer", "description", "source_domain")).lower()
        return query in hay

    shown = 0
    for sec in SECTIONS:
        items = [r for r in rfps if r.get("type") == sec["type"] and matches(r)]
        if not items:
            continue
        shown += len(items)
        st.markdown(section_html(items, sec), unsafe_allow_html=True)

    if shown == 0:
        st.info("No opportunities match your filter.")

    foot = f"Feed updated {gen}." if gen else ""
    st.markdown(
        f'<p style="color:#aaa;font-size:12px;margin-top:36px;border-top:1px solid #eee;padding-top:14px;">'
        f'RFP Tracker — advertising &amp; marketing opportunities, refreshed daily. {foot} '
        f'Always verify details on the official posting before applying.</p>',
        unsafe_allow_html=True,
    )


main()
