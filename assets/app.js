/* RFP Digest — static web mirror of the rfp-tracker daily email digest.
   Renders the same four sections, in the same order, as build_email_html() in rfp.py. */

const SECTIONS = [
  {
    type: "gov_federal",
    title: "Federal Advertising Contracts",
    color: "var(--c-federal)",
    badge: "APPLY ON SAM.GOV",
    linkText: "🔗 Apply on SAM.gov →",
    note: "US federal solicitations on SAM.gov — advertising & marketing contracts only. Click Apply on SAM.gov → to go directly to the listing and submit your proposal.",
  },
  {
    type: "state_local",
    title: "State & Local Government RFPs",
    color: "var(--c-state)",
    badge: "SUBMIT PROPOSAL",
    linkText: "📰 Read Article →",
    note: "US state & local government advertising RFPs — lotteries, tourism boards, transit authorities, universities, city/county agencies. Click Read Article → for the full solicitation.",
  },
  {
    type: "brand_lead",
    title: "Brand Agency Searches — US Only",
    color: "var(--c-brand)",
    badge: "OPEN SEARCH",
    linkText: "📰 Read Article →",
    note: "US brands actively seeking agencies. These are open searches, NOT award announcements. Click Read Article → to read the details, then contact the brand to respond.",
  },
  {
    type: "perplexity",
    title: "Perplexity AI Discoveries — Direct RFP Links",
    color: "var(--c-pplx)",
    badge: "DIRECT LINK",
    linkText: "🔗 View RFP →",
    note: "Found via real-time web search across procurement portals, SAM.gov, BidNet, state portals, and trade press. These links go directly to the RFP or source article — no redirects.",
  },
];

const state = { all: [], query: "" };
const $ = (s) => document.querySelector(s);

document.addEventListener("DOMContentLoaded", init);

async function init() {
  $("#search").addEventListener("input", (e) => {
    state.query = e.target.value.trim().toLowerCase();
    render();
  });
  try {
    const res = await fetch("data/rfps.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.all = (data.rfps || []).filter((r) => r && r.title);
    setHeader(data);
    render();
  } catch (err) {
    $("#sections").innerHTML =
      `<p class="empty">Couldn't load the data feed (${err.message}). ` +
      `If you opened the file directly, serve it over HTTP instead.</p>`;
    console.error(err);
  }
}

function setHeader(data) {
  const d = data.generated ? new Date(data.generated + "T00:00:00") : new Date();
  $("#headDate").textContent = d.toLocaleDateString("en-US", {
    month: "long", day: "numeric", year: "numeric",
  });

  const n = (t) => state.all.filter((r) => r.type === t).length;
  const parts = [
    `${n("gov_federal")} federal`,
    `${n("state_local")} state/local`,
    `${n("brand_lead")} brand searches`,
    `${n("perplexity")} AI-sourced`,
  ];
  $("#summary").innerHTML =
    parts.join('<span class="div">—</span>') +
    '<span class="div">|</span> All US-only · Active · Advertising-verified';

  if (data.generated) $("#footMeta").textContent =
    `RFP Tracker — advertising & marketing opportunities. Feed updated ${data.generated}.`;
}

function daysLeft(deadline) {
  if (!deadline) return null;
  const d = new Date(deadline + "T23:59:59");
  if (isNaN(d)) return null;
  return Math.ceil((d - new Date()) / 86400000);
}

function deadlinePill(deadline) {
  const dl = daysLeft(deadline);
  if (dl === null || dl < 0) return "";
  const cls = dl <= 7 ? "urgent" : dl <= 21 ? "soon" : "ok";
  const txt = dl === 0 ? "TODAY" : `${dl}d left`;
  return `<span class="deadline-pill ${cls}">${txt}</span>`;
}

function fmtDate(s) {
  if (!s) return "—";
  const d = new Date(s + "T00:00:00");
  if (isNaN(d)) return s;
  return d.toLocaleDateString("en-US", { year: "numeric", month: "2-digit", day: "2-digit" });
}

function matches(r) {
  if (!state.query) return true;
  return [r.title, r.issuer, r.description, r.source_domain]
    .filter(Boolean).join(" ").toLowerCase().includes(state.query);
}

function row(r, sec) {
  const domain = r.source_domain
    ? `<span class="domain">(${esc(r.source_domain.replace(/^https?:\/\//, "").replace(/\/$/, ""))})</span>`
    : "";
  const link = r.url
    ? `<a class="opp-link" href="${esc(r.url)}" target="_blank" rel="noopener">${sec.linkText}${domain}</a>`
    : "";
  const deadline = r.deadline || "";
  const dateShown = deadline || r.posted || "";
  return `
    <tr>
      <td class="col-opp">
        <a class="opp-title" href="${esc(r.url || "#")}" target="_blank" rel="noopener">${esc(r.title)}</a>
        ${link}
      </td>
      <td class="col-src">${esc(r.issuer || "—")}</td>
      <td class="col-date date-cell">
        <span class="${deadline ? "due" : ""}">${fmtDate(dateShown)}</span>
        ${deadlinePill(deadline)}
      </td>
      <td class="col-status"><span class="status-badge">new</span></td>
      <td class="col-assignee assignee">—</td>
    </tr>`;
}

function render() {
  const host = $("#sections");
  host.innerHTML = "";
  let shown = 0;

  for (const sec of SECTIONS) {
    const items = state.all.filter((r) => r.type === sec.type && matches(r));
    if (!items.length) continue;
    shown += items.length;
    const el = document.createElement("section");
    el.className = "section";
    el.innerHTML = `
      <h2>
        <span class="section-badge" style="background:${sec.color}">${sec.badge}</span>
        <span style="color:${sec.color}">${sec.title}</span>
        <span class="count">(${items.length} ${items.length === 1 ? "opportunity" : "opportunities"})</span>
      </h2>
      <p class="note">${esc(sec.note)}</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th class="col-opp">RFP / Opportunity</th>
              <th class="col-src">Source</th>
              <th class="col-date">Date</th>
              <th class="col-status">Status</th>
              <th class="col-assignee">Assignee</th>
            </tr>
          </thead>
          <tbody>${items.map((r) => row(r, sec)).join("")}</tbody>
        </table>
      </div>`;
    host.appendChild(el);
  }
  $("#empty").hidden = shown > 0;
}

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
