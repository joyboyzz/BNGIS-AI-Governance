/* ============================================================
   BNGIS — Frontend Application (vanilla JS, zero dependencies)
   Pages: Dashboard | Scheme Matching | Corruption Shield | Chain | About
   ============================================================ */

const API = {
  stats: "/api/stats",
  schemes: "/api/schemes",
  match: "/api/match",
  corruption: "/api/corruption/analyze",
  chain: "/api/chain",
  chainVerify: "/api/chain/verify",
};

const state = { lang: "en", statsCache: null, corrCache: null, lastMatch: null };

/* ------------------------- i18n (EN / TE) ------------------------- */
const I18N = {
  en: {
    brandSub: "Neuro-Governance AI",
    navDash: "Dashboard", navSchemes: "Scheme Matching", navResources: "Resource Finder",
    navDisaster: "Disaster Response", navVoice: "Citizen Voice AI",
    navCorruption: "Corruption Shield", navChain: "Transparency Chain", navAbout: "About Project",
    tDashboard: "📊 Command Dashboard", tSchemes: "🎯 Scheme Matching Engine",
    tResources: "🗺️ Resource Optimization Cortex", tCorruption: "🛡️ Corruption Detection Shield",
    tDisaster: "🌊 Disaster Response Neural Network", tVoice: "🗣️ Citizen Voice AI (Multilingual)",
    tChain: "⛓️ Transparency Blockchain", tAbout: "ℹ️ About the Project",
    heroTitle: "AI brain connecting every citizen to every government resource — in real time.",
    heroSub: "MVP of the Bharath Neuro-Governance Intelligence System: smart scheme matching, corruption detection (Benford's Law + anomaly AI), and a lightweight transparency blockchain.",
  },
  te: {
    brandSub: "న్యూరో-గవర్నెన్స్ AI",
    navDash: "డాష్‌బోర్డ్", navSchemes: "పథకాల మ్యాచింగ్", navResources: "వనరుల శోధన",
    navDisaster: "విపత్తు ప్రతిస్పందన", navVoice: "పౌర స్వరం AI",
    navCorruption: "అవినీతి డిటెక్షన్", navChain: "ట్రాన్స్‌పరెన్సీ చైన్", navAbout: "ప్రాజెక్ట్ గురించి",
    tDashboard: "📊 కమాండ్ డాష్‌బోర్డ్", tSchemes: "🎯 పథకాల మ్యాచింగ్ ఇంజన్",
    tResources: "🗺️ వనరుల ఆప్టిమైజేషన్ కార్టెక్స్", tCorruption: "🛡️ అవినీతి నిర్ధారణ కవచం",
    tDisaster: "🌊 విపత్తు ప్రతిస్పందన న్యూరల్ నెట్‌వర్క్", tVoice: "🗣️ పౌర స్వరం AI (బహుభాషా)",
    tChain: "⛓️ పారదర్శకత బ్లాక్‌చైన్", tAbout: "ℹ️ ప్రాజెక్ట్ సమాచారం",
    heroTitle: "ప్రతి పౌరుడినీ ప్రతి ప్రభుత్వ వనరుతో కలిపే AI బ్రెయిన్ — రియల్ టైమ్‌లో.",
    heroSub: "భారత్ న్యూరో-గవర్నెన్స్ ఇంటెలిజెన్స్ సిస్టమ్ MVP: స్మార్ట్ పథకాల మ్యాచింగ్, అవినీతి గుర్తింపు (బెన్‌ఫోర్డ్ లా + AI), పారదర్శకత బ్లాక్‌చైన్.",
  },
};
const t = (k) => I18N[state.lang][k] || k;

function applyI18n() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.getElementById("lang-btn").textContent =
    state.lang === "en" ? "తెలుగు" : "English";
  const route = location.hash.replace("#/", "") || "dashboard";
  document.getElementById("page-title").textContent = t("t" + route[0].toUpperCase() + route.slice(1));
}

/* ------------------------- API helper ------------------------- */
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) throw new Error("API " + res.status);
  return res.json();
}

/* ------------------------- Formatting ------------------------- */
const fmtIN = (n) => "₹" + Number(n).toLocaleString("en-IN");
const fmtCr = (n) => "₹" + Number(n).toLocaleString("en-IN") + " Cr";
const esc = (s) =>
  String(s).replace(/[&<>"']/g, (m) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));

/* ============================================================
   SVG CHARTS (hand-rolled, no libraries)
   ============================================================ */
function barChart(labels, values, { color = "#ff9933", h = 220, fmt = (v) => v } = {}) {
  const W = 640, H = h, pad = 26, bh = 26;
  const max = Math.max(...values, 1);
  const n = values.length;
  const slot = (W - pad * 2) / n;
  const bw = Math.min(slot * 0.62, 42);
  let bars = "";
  values.forEach((v, i) => {
    const x = pad + slot * i + (slot - bw) / 2;
    const bhActual = ((H - 54) * v) / max;
    const y = H - 30 - bhActual;
    bars += `<rect x="${x}" y="${y}" width="${bw}" height="${bhActual}" rx="5" fill="${color}" opacity="0.88">
      <title>${esc(labels[i])}: ${fmt(v)}</title></rect>`;
    if (n <= 14)
      bars += `<text x="${x + bw / 2}" y="${y - 6}" font-size="10.5" fill="#97a0bd" text-anchor="middle">${fmt(v)}</text>`;
    bars += `<text x="${x + bw / 2}" y="${H - 12}" font-size="${n > 8 ? 9 : 10.5}" fill="#97a0bd" text-anchor="middle">${esc(labels[i])}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%">${bars}</svg>`;
}

function groupedBarChart(labels, a, b, nameA, nameB, fmt = (v) => v) {
  const W = 640, H = 250, pad = 30;
  const max = Math.max(...a, ...b) * 1.12 || 1;
  const n = labels.length;
  const slot = (W - pad * 2) / n;
  const bw = Math.min(slot * 0.34, 26);
  let out = "";
  labels.forEach((l, i) => {
    const cx = pad + slot * i + slot / 2;
    const ha = ((H - 56) * a[i]) / max;
    const hb = ((H - 56) * b[i]) / max;
    out += `<rect x="${cx - bw - 2}" y="${H - 30 - ha}" width="${bw}" height="${ha}" rx="4" fill="#7c8cff" opacity="0.9"><title>${nameA} ${esc(l)}: ${fmt(a[i])}</title></rect>`;
    out += `<rect x="${cx + 2}" y="${H - 30 - hb}" width="${bw}" height="${hb}" rx="4" fill="#ff9933" opacity="0.9"><title>${nameB} ${esc(l)}: ${fmt(b[i])}</title></rect>`;
    out += `<text x="${cx}" y="${H - 12}" font-size="10" fill="#97a0bd" text-anchor="middle">${esc(l)}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%">${out}</svg>
    <div class="legend"><span><i style="background:#7c8cff"></i>${esc(nameA)}</span>
    <span><i style="background:#ff9933"></i>${esc(nameB)}</span></div>`;
}

function lineChart(labels, values, { color = "#38d6d0", h = 210 } = {}) {
  const W = 640, H = h, pad = 34;
  const max = Math.max(...values) * 1.1, min = Math.min(...values) * 0.85;
  const n = values.length;
  const x = (i) => pad + ((W - pad * 2) * i) / (n - 1);
  const y = (v) => H - 26 - ((H - 60) * (v - min)) / (max - min || 1);
  let path = "", dots = "", grid = "";
  values.forEach((v, i) => {
    path += (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1) + " ";
    dots += `<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="3.4" fill="${color}"><title>${esc(labels[i])}: ${v}</title></circle>`;
  });
  const area = `${path}L${x(n - 1)},${H - 26}L${x(0)},${H - 26}Z`;
  labels.forEach((l, i) => {
    if (i % 2 === 0)
      grid += `<text x="${x(i)}" y="${H - 8}" font-size="9.5" fill="#97a0bd" text-anchor="middle">${esc(l)}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%">
    <path d="${area}" fill="${color}" opacity="0.12"/>
    <path d="${path}" fill="none" stroke="${color}" stroke-width="2.6" stroke-linecap="round"/>
    ${dots}${grid}</svg>`;
}

function gauge(score, label = "Risk") {
  // score 0-100, semicircle gauge
  const cx = 110, cy = 105, r = 82;
  const theta = 180 - (score / 100) * 180;
  const pt = (deg) => [cx + r * Math.cos((deg * Math.PI) / 180), cy - r * Math.sin((deg * Math.PI) / 180)];
  const [sx, sy] = pt(180);
  const [ex, ey] = pt(theta);
  const color = score > 65 ? "#ff5c5c" : score > 50 ? "#ff9933" : score > 35 ? "#ffd666" : "#2eb872";
  return `<svg viewBox="0 0 220 125" style="width:190px">
    <path d="M ${sx} ${sy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="13" stroke-linecap="round"/>
    <path d="M ${sx} ${sy} A ${r} ${r} 0 0 1 ${ex.toFixed(1)} ${ey.toFixed(1)}" fill="none" stroke="${color}" stroke-width="13" stroke-linecap="round"/>
    <text x="${cx}" y="${cy - 12}" text-anchor="middle" font-size="27" font-weight="800" fill="${color}">${score}</text>
    <text x="${cx}" y="${cy + 8}" text-anchor="middle" font-size="10.5" fill="#97a0bd">${label}</text>
  </svg>`;
}

function progressRow(label, pct, note) {
  return `<div style="margin-bottom:13px">
    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px">
      <b>${esc(label)}</b><span class="muted">${pct}%</span></div>
    <div class="score-track"><div class="score-fill" style="width:${pct}%"></div></div>
    ${note ? `<div class="muted" style="font-size:11px;margin-top:4px">${esc(note)}</div>` : ""}
  </div>`;
}

/* ============================================================
   PAGE: DASHBOARD
   ============================================================ */
async function pageDashboard(view) {
  view.innerHTML = `<div class="card" style="text-align:center;padding:40px"><span class="spinner" style="width:26px;height:26px;border-color:rgba(255,255,255,0.15);border-top-color:#ff9933"></span><p class="muted" style="margin-top:12px">Loading AI core telemetry…</p></div>`;
  const s = await api(API.stats);
  state.statsCache = s;
  const k = s.kpi;

  view.innerHTML = `
    <div class="hero">
      <h1>${t("heroTitle")}</h1>
      <p>${t("heroSub")}</p>
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px">
        <a href="#/schemes" class="btn">🎯 ${state.lang === "te" ? "నా పథకాలు కనుగొనండి" : "Find My Schemes"}</a>
        <a href="#/resources" class="btn btn-ghost">🗺️ ${state.lang === "te" ? "వనరుల శోధన" : "Resource Finder"}</a>
        <a href="#/corruption" class="btn btn-ghost">🛡️ ${state.lang === "te" ? "ఆడిట్ రన్ చేయండి" : "Run Corruption Audit"}</a>
      </div>
    </div>

    <div class="grid g4">
      ${kpiCard("🗂️", k.schemes_indexed, "Schemes indexed", k.central_schemes + " central · " + k.state_schemes + " state")}
      ${kpiCard("👥", "12.8 L+", "Citizens matched", "+3.2% this month")}
      ${kpiCard("💰", fmtCr(k.benefits_routed_cr), "Benefits routed (yr)", "DBT — zero leakage")}
      ${kpiCard("🚨", k.ghosts_detected, "Ghost beneficiaries caught", "₹" + Math.round(k.leakage_detected_cr * 100).toLocaleString("en-IN") + " L leakage flagged")}
      ${kpiCard("⚡", k.grievance_resolution_days + " days", "Avg grievance time", "↓ from 21 days")}
      ${kpiCard("🏥", "71%", "Hospital bed utilization", "34% vacancy → re-routed")}
      ${kpiCard("💧", "64%", "Water supply efficiency", "leakage −9%")}
      ${kpiCard("⛓️", (s.dept_risk ? s.dept_risk.length : 5) + " depts", "Under corruption watch", "Benford + AI anomaly")}
    </div>

    <div class="section-title"><span class="bar"></span>Scheme applications & citizen satisfaction (12 months)</div>
    <div class="grid g2">
      <div class="card"><h3>📈 Applications processed</h3>${lineChart(s.monthly.labels, s.monthly.applications)}</div>
      <div class="card"><h3>😊 Satisfaction index</h3>${lineChart(s.monthly.labels, s.monthly.satisfaction, { color: "#2eb872" })}</div>
    </div>

    <div class="grid g2 mt">
      <div class="card"><h3>🗂️ Schemes by department</h3>
        ${barChart(Object.keys(s.schemes_by_dept).map(d => d.split(" ")[0]), Object.values(s.schemes_by_dept), { color: "#7c8cff" })}
      </div>
      <div class="card"><h3>🏗️ Public resource utilization</h3>
        ${s.resources.map(r => progressRow(r.name, r.utilization, r.note)).join("")}
      </div>
    </div>

    <div class="section-title"><span class="bar"></span>Department corruption risk (live from Detection Shield)</div>
    <div class="card tbl-wrap">
      <table class="tbl">
        <tr><th>Department</th><th>Risk score</th><th>Level</th></tr>
        ${s.dept_risk.map(d => `<tr>
          <td><b>${esc(d.department)}</b></td>
          <td style="min-width:160px"><div class="score-track"><div class="score-fill" style="width:${d.risk}%"></div></div><span class="muted" style="font-size:11px">${d.risk}/100</span></td>
          <td><span class="badge b-${d.level.toLowerCase()}">${d.level}</span></td>
        </tr>`).join("")}
      </table>
    </div>
    <p class="muted mt" style="font-size:12px">* Demo build: citizen/resource KPIs are simulated deterministically; department risk is computed live by the Corruption Detection Shield engine.</p>
  `;
}

function kpiCard(icon, value, label, sub) {
  return `<div class="card">
    <div class="kpi-icon">${icon}</div>
    <div class="kpi-value">${value}</div>
    <div class="kpi-label">${esc(label)}</div>
    <div class="kpi-sub">${esc(sub)}</div>
  </div>`;
}

/* ============================================================
   PAGE: SCHEME MATCHING
   ============================================================ */
const PERSONAS = [
  { icon: "👩‍🌾", name: "Lakshmi, 34", desc: "Rural daily-wage worker (SC)",
    data: { age: 34, gender: "F", state: "KA", area_type: "rural", income_annual: 96000,
            occupation: "daily_wage", caste: "sc", family_size: 4, land_hectares: 0,
            house_status: "kutcha", disability: "none", bank_account: true, is_pregnant: false,
            is_widow: false, has_girl_child: true, wants_business: false,
            is_family_head: true, is_minority: false } },
  { icon: "👨‍🌾", name: "Ramesh, 62", desc: "ST farmer with 1.2 ha land",
    data: { age: 62, gender: "M", state: "KA", area_type: "rural", income_annual: 80000,
            occupation: "farmer", caste: "st", family_size: 5, land_hectares: 1.2,
            house_status: "kutcha", disability: "none", bank_account: true, is_pregnant: false,
            is_widow: false, has_girl_child: false, wants_business: false,
            is_family_head: true, is_minority: false } },
  { icon: "👩‍🎓", name: "Ayesha, 20", desc: "Urban OBC minority student",
    data: { age: 20, gender: "F", state: "KA", area_type: "urban", income_annual: 180000,
            occupation: "student", caste: "obc", family_size: 4, land_hectares: 0,
            house_status: "rented", disability: "none", bank_account: true, is_pregnant: false,
            is_widow: false, has_girl_child: false, wants_business: false,
            is_family_head: false, is_minority: true } },
  { icon: "👵", name: "Savitri, 66", desc: "Widowed senior citizen",
    data: { age: 66, gender: "F", state: "KA", area_type: "rural", income_annual: 60000,
            occupation: "housewife", caste: "general", family_size: 2, land_hectares: 0,
            house_status: "kutcha", disability: "none", bank_account: true, is_pregnant: false,
            is_widow: true, has_girl_child: false, wants_business: false,
            is_family_head: true, is_minority: false } },
  { icon: "🧑‍💼", name: "Arun, 28", desc: "Aspiring entrepreneur (OBC)",
    data: { age: 28, gender: "M", state: "KA", area_type: "urban", income_annual: 240000,
            occupation: "self_employed", caste: "obc", family_size: 3, land_hectares: 0,
            house_status: "own_pucca", disability: "none", bank_account: true, is_pregnant: false,
            is_widow: false, has_girl_child: false, wants_business: true,
            is_family_head: true, is_minority: false } },
];

function fillPersona(p) {
  const form = document.getElementById("citizen-form");
  if (!form) return;
  const d = p.data;
  ["age", "gender", "state", "area_type", "income_annual", "occupation", "caste",
   "family_size", "land_hectares", "house_status", "disability"].forEach((k) => {
    if (d[k] !== undefined && form.elements[k]) form.elements[k].value = d[k];
  });
  ["bank_account", "is_pregnant", "is_widow", "has_girl_child", "wants_business",
   "is_family_head", "is_minority"].forEach((k) => {
    if (form.elements[k]) form.elements[k].checked = !!d[k];
  });
  document.querySelectorAll(".persona-btn").forEach((b) =>
    b.classList.toggle("active", b.dataset.persona === p.name));
}

function pageSchemes(view) {
  view.innerHTML = `
    <div class="card">
      <h3>⚡ One-click demo citizens <span class="badge b-low">try these first</span></h3>
      <div class="persona-row">
        ${PERSONAS.map((p, i) => `
          <button class="persona-btn ${i === 0 ? "active" : ""}" data-persona="${esc(p.name)}" data-idx="${i}">
            <span class="p-icon">${p.icon}</span>
            <span><b>${esc(p.name)}</b><small>${esc(p.desc)}</small></span>
          </button>`).join("")}
      </div>
    </div>
    <div class="card mt">
      <h3>👤 Citizen Neural Profile <span class="badge b-low" style="margin-left:6px">Module 1 + 3</span></h3>
      <p class="muted" style="margin-bottom:16px">The engine converts your profile into a 10-dimensional need vector, checks hard eligibility across all indexed schemes, ranks by priority score, then builds your optimal portfolio (knapsack optimization with conflict rules).</p>
      <form id="citizen-form" class="form-grid">
        <div class="fg"><label>Name (optional)</label><input name="name" placeholder="e.g. Lakshmi" /></div>
        <div class="fg"><label>Age</label><input name="age" type="number" value="34" min="0" max="110" required /></div>
        <div class="fg"><label>Gender</label><select name="gender">
          <option value="F">Female</option><option value="M">Male</option><option value="Other">Other</option></select></div>
        <div class="fg"><label>State</label><select name="state">
          <option value="KA">Karnataka</option><option value="AP">Andhra Pradesh</option>
          <option value="TG">Telangana</option><option value="TN">Tamil Nadu</option>
          <option value="MH">Maharashtra</option><option value="UP">Uttar Pradesh</option>
          <option value="BR">Bihar</option><option value="WB">West Bengal</option>
          <option value="DL">Delhi</option><option value="OT">Other</option></select></div>
        <div class="fg"><label>Area type</label><select name="area_type">
          <option value="rural">Rural</option><option value="tribal">Tribal</option>
          <option value="semi">Semi-urban</option><option value="urban">Urban</option></select></div>
        <div class="fg"><label>Annual family income (₹)</label><input name="income_annual" type="number" value="96000" min="0" step="1000" required /></div>
        <div class="fg"><label>Occupation</label><select name="occupation">
          <option value="farmer">Farmer</option><option value="daily_wage">Daily wage worker</option>
          <option value="labour">Labour</option><option value="student">Student</option>
          <option value="unemployed">Unemployed</option><option value="self_employed">Self-employed</option>
          <option value="salaried">Salaried</option><option value="housewife">Homemaker</option>
          <option value="retired">Retired</option></select></div>
        <div class="fg"><label>Caste category</label><select name="caste">
          <option value="general">General</option><option value="obc">OBC</option>
          <option value="sc">SC</option><option value="st">ST</option></select></div>
        <div class="fg"><label>Family size</label><input name="family_size" type="number" value="4" min="1" max="20" /></div>
        <div class="fg"><label>Agricultural land (hectares)</label><input name="land_hectares" type="number" value="0.5" min="0" step="0.1" /></div>
        <div class="fg"><label>House status</label><select name="house_status">
          <option value="kutcha">Kutcha (mud/temporary)</option><option value="none">Homeless</option>
          <option value="rented">Rented</option><option value="own_pucca">Own pucca house</option></select></div>
        <div class="fg"><label>Disability</label><select name="disability">
          <option value="none">None</option><option value="locomotor">Locomotor</option>
          <option value="visual">Visual</option><option value="hearing">Hearing</option>
          <option value="intellectual">Intellectual</option></select></div>
        <div class="fg" style="grid-column: span 3"><label>Special circumstances (improves matching)</label>
          <div class="check-row">
            <label class="check-pill"><input type="checkbox" name="bank_account" checked /> Has bank account</label>
            <label class="check-pill"><input type="checkbox" name="is_pregnant" /> Pregnant / new mother</label>
            <label class="check-pill"><input type="checkbox" name="is_widow" /> Widow</label>
            <label class="check-pill"><input type="checkbox" name="has_girl_child" /> Girl child below 10 in family</label>
            <label class="check-pill"><input type="checkbox" name="wants_business" /> Wants to start business</label>
            <label class="check-pill"><input type="checkbox" name="is_family_head" /> I am head of family</label>
            <label class="check-pill"><input type="checkbox" name="is_minority" /> Minority community</label>
          </div>
        </div>
        <div class="fg" style="grid-column: span 3">
          <button class="btn" id="match-btn" type="submit">⚡ Run AI Match — Find My Schemes</button>
        </div>
      </form>
    </div>
    <div id="match-results" class="mt"></div>
  `;

  // persona quick-fill
  document.querySelectorAll(".persona-btn").forEach((btn) => {
    btn.addEventListener("click", () => fillPersona(PERSONAS[+btn.dataset.idx]));
  });
  fillPersona(PERSONAS[0]); // prefill Lakshmi by default

  document.getElementById("citizen-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = {
      name: fd.get("name") || "",
      age: +fd.get("age"),
      gender: fd.get("gender"),
      state: fd.get("state"),
      area_type: fd.get("area_type"),
      income_annual: +fd.get("income_annual"),
      occupation: fd.get("occupation"),
      education: "10th",
      family_size: +fd.get("family_size"),
      land_hectares: +fd.get("land_hectares"),
      house_status: fd.get("house_status"),
      disability: fd.get("disability"),
      bank_account: fd.get("bank_account") === "on",
      is_pregnant: fd.get("is_pregnant") === "on",
      is_widow: fd.get("is_widow") === "on",
      has_girl_child: fd.get("has_girl_child") === "on",
      wants_business: fd.get("wants_business") === "on",
      is_family_head: fd.get("is_family_head") === "on",
      is_minority: fd.get("is_minority") === "on",
    };
    const btn = document.getElementById("match-btn");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> AI matching in progress…';
    try {
      const res = await api(API.match, { method: "POST", body: JSON.stringify(payload) });
      renderMatchResults(res, payload.name);
    } catch (err) {
      document.getElementById("match-results").innerHTML =
        `<div class="alert alert-bad">⚠️ Match failed: ${esc(err.message)}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = "⚡ Run AI Match — Find My Schemes";
    }
  });
}

function renderMatchResults(res, name) {
  const box = document.getElementById("match-results");
  const yearly = res.total_estimated_yearly_value;
  box.innerHTML = `
    <div class="grid g4">
      ${kpiCard("✅", res.eligible.length, "Schemes you qualify for", "out of 21 indexed")}
      ${kpiCard("🎒", res.portfolio.length, "In optimal portfolio", "effort budget " + res.effort_used + "/" + res.effort_budget)}
      ${kpiCard("💰", fmtIN(yearly), "Est. yearly value", "cash-type benefits")}
      ${kpiCard("⛓️", "#" + res.chain_block.index, "Recorded on chain", "match audit trail")}
    </div>

    <div class="section-title"><span class="bar"></span>🎒 Optimal Portfolio (auto-optimized)</div>
    <div class="grid g2">${res.portfolio.map(schemeCard).join("")}</div>

    <div class="section-title"><span class="bar"></span>📋 All eligible schemes (${res.eligible.length})</div>
    <div class="grid g2">${res.eligible.filter(s => !res.portfolio.find(p => p.id === s.id)).map(schemeCard).join("") || '<div class="card muted">All eligible schemes are already in the portfolio.</div>'}</div>

    <div class="section-title"><span class="bar"></span>🔍 Nearest misses (why not eligible)</div>
    ${res.missed.map(m => `
      <details class="acc">
        <summary>❌ ${esc(m.name)} <span class="muted" style="font-weight:400">(similarity ${(m.similarity * 100).toFixed(0)}%)</span></summary>
        <div class="inner">${m.blockers.map(b => "• " + esc(b)).join("<br/>")}</div>
      </details>`).join("")}
  `;
  box.scrollIntoView({ behavior: "smooth" });
}

function schemeCard(s) {
  return `<div class="card scheme-card">
    <span class="level-badge level-${s.level.toLowerCase()}">${s.level.toUpperCase()}</span>
    <div class="scheme-name">${esc(s.name)}</div>
    <div class="scheme-dept">${esc(s.department)} · decision in ~${s.avg_days} days</div>
    <div class="benefit-box">💰 ${esc(s.benefit_display)}</div>
    <div class="score-track"><div class="score-fill" style="width:${s.priority_score}%"></div></div>
    <div class="score-num"><span>Priority score</span><b>${s.priority_score}/100</b></div>
    <div class="chips">${s.reasons.slice(0, 3).map(r => `<span class="chip">✓ ${esc(r)}</span>`).join("")}</div>
    <div class="chips">${s.docs.map(d => `<span class="chip chip-doc">📄 ${esc(d)}</span>`).join("")}</div>
    <div class="breakdown">
      ${Object.entries(s.breakdown).map(([k2, v]) => `<div class="bd-item"><div class="bd-val">${v}</div><div class="bd-lbl">${esc(k2)}</div></div>`).join("")}
    </div>
    <div style="margin-top:12px"><a class="mini-link" href="${esc(s.url)}" target="_blank" rel="noopener">Official website ↗</a></div>
  </div>`;
}

/* ============================================================
   PAGE: RESOURCE FINDER (Module 2 — Optimization Cortex)
   ============================================================ */
const AREAS = {
  "Devaraja Mohalla": [12.3050, 76.6550],
  "Vijayanagar": [12.3110, 76.6420],
  "Gokulam 3rd Stage": [12.3180, 76.6530],
  "Kuvempunagar": [12.2890, 76.6340],
  "JP Nagar": [12.2820, 76.6240],
  "Saraswathipuram": [12.2950, 76.6350],
  "Hebbal": [12.3390, 76.6320],
  "Bannimantap": [12.3180, 76.6680],
  "Nanjangud (rural)": [12.1200, 76.6800],
  "T. Narsipur (rural)": [12.2300, 76.8900],
  "Hunsur (rural)": [12.3100, 76.2900],
};
const RTYPES = { hospital: "🏥 Hospitals", school: "🏫 Schools", water: "💧 Water Supply" };

async function pageResources(view) {
  view.innerHTML = `
    <div class="card">
      <h3>🗺️ Resource Optimization Cortex <span class="badge b-low">Module 2</span></h3>
      <p class="muted" style="line-height:1.65;margin-bottom:16px">
        Pick where you are and what you need — the engine maps every facility, computes distance
        (haversine), free capacity and quality, then builds a
        <b>BNGIS Allocation Score = 0.55·proximity + 0.30·availability + 0.15·quality</b>.
        When the nearest facility is overloaded (&gt;85%), the system issues a
        <b>reroute advisory</b> — this is how the full system would de-congest public resources
        (34% of hospital beds sit empty while the nearest hospital turns people away).</p>
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
        <div class="fg" style="min-width:230px"><label>Your area (Mysuru district demo)</label>
          <select id="area-select">
            ${Object.keys(AREAS).map((a) => `<option ${a === "Vijayanagar" ? "selected" : ""}>${esc(a)}</option>`).join("")}
          </select></div>
        <div class="fg" style="min-width:190px"><label>Resource type</label>
          <select id="type-select">
            ${Object.entries(RTYPES).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}
          </select></div>
        <button class="btn" id="res-btn" style="margin-top:18px">⚡ Find Best Facilities</button>
      </div>
    </div>
    <div id="res-results" class="mt"></div>
  `;
  const run = async () => {
    const area = document.getElementById("area-select").value;
    const type = document.getElementById("type-select").value;
    const [lat, lng] = AREAS[area];
    const box = document.getElementById("res-results");
    const btn = document.getElementById("res-btn");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Optimizing allocation…';
    box.innerHTML = `<div class="card" style="text-align:center;padding:40px">
      <span class="spinner" style="width:26px;height:26px;border-color:rgba(255,255,255,0.15);border-top-color:#ff9933"></span>
      <p class="muted" style="margin-top:12px">Mapping ${RTYPES[type].toLowerCase()} network around ${esc(area)}…</p></div>`;
    try {
      const r = await api(`/api/resources?lat=${lat}&lng=${lng}&type=${type}`);
      renderResources(r, area, box);
    } catch (e) {
      box.innerHTML = `<div class="alert alert-bad">⚠️ ${esc(e.message)}</div>`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = "⚡ Find Best Facilities";
    }
  };
  document.getElementById("res-btn").addEventListener("click", run);
  run(); // auto-run on page load
}

function resourceMap(r, topIds) {
  const pts = [{ lat: r.citizen.lat, lng: r.citizen.lng, citizen: true }, ...r.all_by_distance];
  const lats = pts.map((p) => p.lat), lngs = pts.map((p) => p.lng);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const W = 640, H = 320, P = 42;
  const spanLat = maxLat - minLat || 0.01, spanLng = maxLng - minLng || 0.01;
  const x = (lng) => P + ((W - 2 * P) * (lng - minLng)) / spanLng;
  const y = (lat) => H - P - ((H - 2 * P) * (lat - minLat)) / spanLat;
  const cx = x(r.citizen.lng), cy = y(r.citizen.lat);
  const pxKm = (H - 2 * P) / (spanLat * 111);

  let rings = "";
  [5, 10, 15].forEach((km) => {
    rings += `<circle cx="${cx}" cy="${cy}" r="${(km * pxKm).toFixed(0)}" fill="none"
      stroke="rgba(255,255,255,0.10)" stroke-dasharray="3 6"/>
      <text x="${cx}" y="${(cy - km * pxKm - 4).toFixed(0)}" font-size="9" fill="#5d6684" text-anchor="middle">${km} km</text>`;
  });

  const statusColor = (s) => s === "OVERLOADED" ? "#ff5c5c" : s === "STRAINED" ? "#ffb877" : "#2eb872";
  let dots = "", lines = "";
  r.all_by_distance.forEach((f) => {
    const fx = x(f.lng), fy = y(f.lat);
    const rr = 5 + Math.min(Math.sqrt(f.capacity) / 8, 8);
    const isTop = topIds.indexOf(f.id);
    if (isTop > -1) {
      lines += `<line x1="${cx}" y1="${cy}" x2="${fx}" y2="${fy}" stroke="#ff9933"
        stroke-width="1.6" stroke-dasharray="5 4" opacity="0.85"/>`;
      dots += `<circle cx="${fx}" cy="${fy - rr - 9}" r="9" fill="#ff9933"/>
        <text x="${fx}" y="${fy - rr - 5.5}" font-size="10" font-weight="800" fill="#1a1200" text-anchor="middle">${isTop + 1}</text>`;
    }
    dots += `<circle cx="${fx}" cy="${fy}" r="${rr}" fill="${statusColor(f.status)}" opacity="0.85" stroke="rgba(255,255,255,0.25)">
      <title>${esc(f.name)} — ${f.distance_km} km · ${f.util}% full · ${f.free} ${f.unit} free</title></circle>`;
  });
  const citizen = `<circle cx="${cx}" cy="${cy}" r="16" fill="none" stroke="#ff9933" stroke-width="1.5" opacity="0.6"/>
    <circle cx="${cx}" cy="${cy}" r="7" fill="#ff9933"/>
    <text x="${cx}" y="${cy + 26}" font-size="11" font-weight="700" fill="#ffce96" text-anchor="middle">📍 You</text>`;

  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;background:rgba(0,0,0,0.18);border-radius:12px">
    ${rings}${lines}${dots}${citizen}</svg>
    <div class="legend">
      <span><i style="background:#2eb872"></i>OK (&lt;75% full)</span>
      <span><i style="background:#ffb877"></i>Strained (75–85%)</span>
      <span><i style="background:#ff5c5c"></i>Overloaded (&gt;85%)</span>
      <span><i style="background:#ff9933;border-radius:50%"></i>You</span>
      <span style="color:#ff9933">- - → AI top picks</span>
    </div>`;
}

function renderResources(r, area, box) {
  const topIds = r.ranked.map((x) => x.id);
  const n = r.nearest;
  box.innerHTML = `
    ${r.advisory ? `
      <div class="alert alert-warn">🔀 <b>REROUTE ADVISORY:</b> ${esc(r.advisory.problem)}<br/>
      <b style="color:#ffc899">→ ${esc(r.advisory.action)}</b>
      ${r.advisory.saves_min > 0 ? ` <span class="badge b-low">saves ~${r.advisory.saves_min} min wait</span>` : ""}</div>
    ` : `<div class="alert alert-ok">✅ Nearest facility (${esc(n.name)}, ${n.distance_km} km) has healthy capacity — ${n.free} ${n.unit} free. No reroute needed.</div>`}

    <div class="grid g4">
      ${kpiCard(r.meta.icon, r.network.facilities, "Facilities mapped", r.meta.label.toLowerCase() + " network")}
      ${kpiCard("📊", r.network.avg_utilization + "%", "Network avg load", r.network.overloaded + " overloaded facilities")}
      ${kpiCard("🟢", r.network.free_total.toLocaleString("en-IN"), "Free " + r.meta.unit + " (network)", "total spare capacity")}
      ${kpiCard("📍", n.distance_km + " km", "Nearest facility", n.name.split("(")[0].trim())}
    </div>

    <div class="section-title"><span class="bar"></span>Live network map — ${esc(area)}</div>
    <div class="card">${resourceMap(r, topIds)}</div>

    <div class="section-title"><span class="bar"></span>AI-ranked recommendations</div>
    <div class="grid g2">
      ${r.ranked.map((f, i) => `
        <div class="card scheme-card">
          <span class="level-badge ${f.status === "OVERLOADED" ? "level-central" : "level-state"}" style="${f.status === "STRAINED" ? "background:rgba(255,184,119,.15);color:#ffb877;border-color:rgba(255,184,119,.4)" : ""}">${f.status}</span>
          <div style="font-size:22px">${i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : "·"} <b style="font-size:15.5px">${esc(f.name)}</b></div>
          <div class="scheme-dept">${f.distance_km} km away · ⭐ ${f.quality}/5 · ~${f.est_wait_min} min wait</div>
          <div class="benefit-box" style="margin:8px 0">🟢 ${f.free.toLocaleString("en-IN")} ${f.unit} free of ${f.capacity.toLocaleString("en-IN")}</div>
          <div class="score-track"><div class="score-fill" style="width:${f.allocation_score}%"></div></div>
          <div class="score-num"><span>Allocation score</span><b>${f.allocation_score}/100</b></div>
          <div class="chips">
            <span class="chip">📍 ${f.distance_km} km</span>
            <span class="chip">📊 ${f.util}% utilized</span>
            <span class="chip">⭐ quality ${f.quality}/5</span>
          </div>
        </div>`).join("")}
    </div>
    <p class="muted mt" style="font-size:12px">* Demo dataset: plausible Mysuru-area facilities with deterministic utilization. The allocation algorithm (proximity + availability + quality + reroute logic) is the real, production-shaped logic from the BNGIS specification.</p>
  `;
}

/* ============================================================
   PAGE: DISASTER RESPONSE (Module 5 — DRNN)
   ============================================================ */
function multiLineChart(labels, series, h = 260) {
  const W = 680, H = h, pad = 40;
  const all = series.flatMap((s) => s.values);
  const max = Math.max(...all) * 1.05 || 1;
  const n = labels.length;
  const x = (i) => pad + ((W - pad * 2) * i) / (n - 1);
  const y = (v) => H - 26 - ((H - 56) * v) / max;
  let out = "";
  series.forEach((s) => {
    let path = "";
    s.values.forEach((v, i) => { path += (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1) + " "; });
    out += `<path d="${path}" fill="none" stroke="${s.color}" stroke-width="2.4" stroke-dasharray="${s.dash || ""}" opacity="0.95"/>`;
  });
  let grid = "";
  [0, 0.25, 0.5, 0.75, 1].forEach((f) => {
    grid += `<line x1="${pad}" y1="${y(max * f)}" x2="${W - pad}" y2="${y(max * f)}" stroke="rgba(255,255,255,0.06)"/>
      <text x="${pad - 6}" y="${y(max * f) + 3}" font-size="9" fill="#5d6684" text-anchor="end">${Math.round(max * f / 1000)}k</text>`;
  });
  labels.forEach((l, i) => {
    if (i % 15 === 0) grid += `<text x="${x(i)}" y="${H - 8}" font-size="9.5" fill="#5d6684" text-anchor="middle">Day ${l}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%">${grid}${out}</svg>
    <div class="legend">${series.map((s) => `<span><i style="background:${s.color}"></i>${esc(s.name)}</span>`).join("")}</div>`;
}

async function pageDisaster(view) {
  view.innerHTML = `<div class="card" style="text-align:center;padding:40px"><span class="spinner" style="width:26px;height:26px;border-color:rgba(255,255,255,0.15);border-top-color:#ff9933"></span><p class="muted" style="margin-top:12px">Running SEIR epidemic model & flood risk scoring…</p></div>`;
  const [ep, fl] = await Promise.all([
    api("/api/disaster/epidemic"), api("/api/disaster/flood"),
  ]);
  const b = ep.base, s = b.summary, hi = ep.hospital_impact;
  const labels = Array.from({ length: b.days }, (_, i) => i + 1);
  const scenColors = ["#ff5c5c", "#ffb877", "#38d6d0", "#2eb872"];

  view.innerHTML = `
    <div class="alert alert-bad">🚨 <b>MONSOON WATCH:</b> ${fl.alerts.filter(a => a.level === "SEVERE").length} districts at SEVERE flood risk (48h window) — ${fl.total_displaced_estimate.toLocaleString("en-IN")} people potentially displaced. Response plans generated below & recorded on chain (block #${fl.chain_block.index}).</div>

    <div class="section-title"><span class="bar"></span>1️⃣ Epidemic Early Warning — SEIR Model (Module 5)</div>
    <div class="card">
      <h3>🦠 ${esc(ep.pathogen)} · population ${b.population.toLocaleString("en-IN")} · R₀ = ${b.r0}</h3>
      ${multiLineChart(labels, [
        { name: "Active infections (I)", color: "#ff5c5c", values: b.curves.I },
        { name: "Exposed (E)", color: "#ffb877", values: b.curves.E, dash: "5 4" },
        { name: "Recovered (R)", color: "#2eb872", values: b.curves.R },
      ])}
      <div class="grid g4 mt">
        <div class="bd-item"><div class="bd-val">${s.peak_infected.toLocaleString("en-IN")}</div><div class="bd-lbl">Peak concurrent cases</div></div>
        <div class="bd-item"><div class="bd-val">Day ${s.peak_day}</div><div class="bd-lbl">Peak arrival</div></div>
        <div class="bd-item"><div class="bd-val">${s.total_infected.toLocaleString("en-IN")}</div><div class="bd-lbl">Total infected (no action)</div></div>
        <div class="bd-item"><div class="bd-val">${s.attack_rate_pct}%</div><div class="bd-lbl">Attack rate</div></div>
      </div>
    </div>

    <div class="grid g2 mt">
      <div class="card">
        <h3>🧪 Intervention scenarios (what-if analysis)</h3>
        <div class="tbl-wrap"><table class="tbl">
          <tr><th>Scenario</th><th>Peak cases</th><th>Total infected</th><th>Attack rate</th></tr>
          ${ep.scenarios.map((sc, i) => `
            <tr><td><span style="color:${scenColors[i]}">●</span> ${esc(sc.name)}</td>
            <td><b>${sc.peak_infected.toLocaleString("en-IN")}</b></td>
            <td>${sc.total_infected.toLocaleString("en-IN")}</td>
            <td>${sc.attack_rate_pct}%</td></tr>`).join("")}
        </table></div>
        <div class="alert alert-ok mt" style="margin-bottom:0">💡 ${esc(ep.recommendation)}</div>
      </div>
      <div class="card">
        <h3>🏥 Hospital impact (Resource Cortex link)</h3>
        <div class="grid g2">
          <div class="bd-item"><div class="bd-val">${hi.beds_needed_at_peak.toLocaleString("en-IN")}</div><div class="bd-lbl">Beds needed at peak</div></div>
          <div class="bd-item"><div class="bd-val">${hi.region_beds.toLocaleString("en-IN")}</div><div class="bd-lbl">Network capacity</div></div>
        </div>
        <div class="alert ${hi.deficit ? "alert-bad" : "alert-warn"} mt">
          ${hi.deficit ? `⛔ <b>BED DEFICIT: ${hi.deficit.toLocaleString("en-IN")}</b> — ${esc(hi.verdict)}` : `⚠️ ${esc(hi.verdict)}`}
        </div>
        <p class="muted" style="font-size:12px">Cross-module integration: epidemic peak demand is checked against the same facility network used by the Resource Finder (Module 2 → Module 5).</p>
      </div>
    </div>

    <div class="section-title"><span class="bar"></span>2️⃣ Flood Risk — Karnataka districts (48h forecast)</div>
    <div class="card tbl-wrap">
      <table class="tbl">
        <tr><th>District</th><th>Rain 48h</th><th>River level</th><th>Terrain</th><th>Risk</th><th>Level</th><th>Est. displaced</th></tr>
        ${fl.districts.map((d) => `
          <tr>
            <td><b>${esc(d.district)}</b></td>
            <td>${d.rain48_mm} mm</td>
            <td>${d.river_level_pct}%</td>
            <td class="muted">${d.terrain_risk}</td>
            <td style="min-width:130px"><div class="score-track"><div class="score-fill" style="width:${d.risk_score}%"></div></div><span class="muted" style="font-size:11px">${d.risk_score}/100</span></td>
            <td><span class="badge b-${d.risk_level === "SEVERE" ? "critical" : d.risk_level === "HIGH" ? "high" : d.risk_level === "MODERATE" ? "medium" : "low"}">${d.risk_level}</span></td>
            <td>${d.est_displaced ? d.est_displaced.toLocaleString("en-IN") : "—"}</td>
          </tr>`).join("")}
      </table>
      <p class="muted mt" style="font-size:12px">Risk = 0.35·rainfall + 0.30·river level + 0.20·terrain + 0.15·historical exposure.</p>
    </div>

    <div class="section-title"><span class="bar"></span>3️⃣ AI response resource plans (top-risk districts)</div>
    <div class="grid g3">
      ${fl.response_plans.map((p) => `
        <div class="card">
          <h3>📍 ${esc(p.district)} <span class="badge b-critical">${p.risk}</span></h3>
          <ul class="tick-list">${p.actions.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>
        </div>`).join("")}
    </div>
  `;
}

/* ============================================================
   PAGE: CITIZEN VOICE AI (Module 8)
   ============================================================ */
const VOICE_SAMPLES = [
  { label: "🇬🇧 Water emergency (EN)", msg: "No water supply in our street for 3 days, please solve immediately!" },
  { label: "🇮🇳 రోడ్డు ప్రమాదం (TE)", msg: "రోడ్డు పై పెద్ద గుండు ఉంది, ప్రమాదం జరుగుతుంది, అత్యవసరంగా సరిచేయండి" },
  { label: "🇮🇳 रिश्वत शिकायत (HI)", msg: "राशन कार्ड में नाम जुड़ने के लिए दलाल 500 रुपये मांग रहा है" },
  { label: "🇮🇳 ಆಸ್ಪತ್ರೆ ತುರ್ತು (KN)", msg: "ಆಸ್ಪತ್ರೆಯಲ್ಲಿ ಔಷಧಿ ಇಲ್ಲ, ಜ್ವರ ಬಂದಿದೆ ತುರ್ತು ಸಹಾಯ ಬೇಕು" },
  { label: "😊 Appreciation (EN)", msg: "The PHC doctor was very kind and medicine was given quickly, thanks" },
];

async function pageVoice(view) {
  view.innerHTML = `
    <div class="card">
      <h3>🗣️ Multilingual grievance AI <span class="badge b-low">Module 8</span></h3>
      <p class="muted" style="line-height:1.65;margin-bottom:14px">
        Write a complaint in <b>English, हिंदी, తెలుగు, ಕನ್ನಡ</b> (or mixed). The AI detects the language,
        scores sentiment, classifies the issue into one of 9 categories, judges urgency, and
        auto-routes it to the right department with a priority ticket (P1–P4) — all recorded on the transparency chain.</p>
      <div class="check-row" style="margin-bottom:12px">
        ${VOICE_SAMPLES.map((s, i) => `<button class="check-pill vsample" data-i="${i}" style="cursor:pointer">${esc(s.label)}</button>`).join("")}
      </div>
      <textarea id="voice-input" rows="3" placeholder="Type your grievance here… / మీ ఫిర్యాదు ఇక్కడ రాయండి… / अपनी शिकायत यहाँ लिखें…" style="width:100%;background:rgba(0,0,0,0.3);border:1px solid var(--border);color:var(--text);border-radius:12px;padding:12px 14px;font-size:14.5px;outline:none;resize:vertical"></textarea>
      <button class="btn mt" id="voice-btn" style="margin-top:12px">🧠 Analyze Grievance</button>
    </div>
    <div id="voice-result" class="mt"></div>
    <div id="voice-feed"></div>
  `;

  const input = document.getElementById("voice-input");
  document.querySelectorAll(".vsample").forEach((btn) => {
    btn.addEventListener("click", () => { input.value = VOICE_SAMPLES[+btn.dataset.i].msg; });
  });

  const analyze = async () => {
    const msg = input.value.trim();
    const box = document.getElementById("voice-result");
    if (!msg) { box.innerHTML = '<div class="alert alert-warn">Please type or pick a sample grievance first.</div>'; return; }
    const btn = document.getElementById("voice-btn");
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Analyzing…';
    try {
      const r = await api("/api/voice", { method: "POST", body: JSON.stringify({ message: msg }) });
      const sentColor = r.sentiment <= -0.4 ? "#ff5c5c" : r.sentiment < 0 ? "#ffb877" : r.sentiment <= 0.05 ? "#97a0bd" : "#2eb872";
      const urgColor = r.urgency >= 0.65 ? "#ff5c5c" : r.urgency >= 0.4 ? "#ffb877" : "#2eb872";
      box.innerHTML = `
        <div class="card">
          <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;align-items:center">
            <h3 style="margin:0">🎫 Ticket ${esc(r.ticket)}</h3>
            <span class="badge ${r.priority.startsWith("P1") ? "b-critical" : r.priority.startsWith("P2") ? "b-high" : r.priority.startsWith("P3") ? "b-medium" : "b-low"}" style="font-size:13px;padding:7px 14px">${esc(r.priority)}</span>
          </div>
          <div class="grid g4 mt">
            <div class="bd-item"><div class="bd-val" style="font-size:15px">${esc(r.language_name)}</div><div class="bd-lbl">Detected language</div></div>
            <div class="bd-item"><div class="bd-val" style="color:${sentColor}">${r.sentiment >= 0 ? "+" : ""}${r.sentiment.toFixed ? r.sentiment.toFixed(2) : r.sentiment} ${esc(r.sentiment_label)}</div><div class="bd-lbl">Sentiment</div></div>
            <div class="bd-item"><div class="bd-val" style="text-transform:capitalize">${esc(r.category)}</div><div class="bd-lbl">Category</div></div>
            <div class="bd-item"><div class="bd-val" style="color:${urgColor}">${Math.round(r.urgency * 100)}%</div><div class="bd-lbl">Urgency</div></div>
          </div>
          <div class="grid g2 mt">
            <div>
              <div class="muted" style="font-size:12px;margin-bottom:4px"> routed to →</div>
              <div class="benefit-box">🏛️ ${esc(r.department)}</div>
              <div class="chips">${(r.matched_keywords || []).map((k) => `<span class="chip">✓ ${esc(k)}</span>`).join("") || '<span class="chip">general grievance</span>'}</div>
            </div>
            <div>
              <div class="muted" style="font-size:12px;margin-bottom:4px">Recommended action (SLA: ${r.sla_days} days)</div>
              <div class="alert alert-info" style="margin:0">⚡ ${esc(r.recommended_action)}</div>
              <p class="muted mt" style="font-size:11.5px">⛓️ Recorded on transparency chain — block #${r.chain_block.index}</p>
            </div>
          </div>
        </div>`;
      loadFeed();
    } catch (e) {
      box.innerHTML = `<div class="alert alert-bad">⚠️ ${esc(e.message)}</div>`;
    } finally {
      btn.disabled = false; btn.innerHTML = "🧠 Analyze Grievance";
    }
  };

  document.getElementById("voice-btn").addEventListener("click", analyze);

  async function loadFeed() {
    const f = await api("/api/voice/samples");
    const a = f.analytics;
    document.getElementById("voice-feed").innerHTML = `
      <div class="section-title"><span class="bar"></span>Live grievance feed & analytics (${a.total} samples, ${a.languages.length} languages)</div>
      <div class="grid g2-1">
        <div class="card tbl-wrap">
          <table class="tbl">
            <tr><th>Message</th><th>Lang</th><th>Category</th><th>Sentiment</th><th>Priority</th><th>Auto-routed department</th></tr>
            ${f.items.map((it) => `
              <tr>
                <td style="max-width:280px;font-size:12.5px">${esc(it.message.slice(0, 60))}${it.message.length > 60 ? "…" : ""}</td>
                <td><b>${esc(it.language)}</b></td>
                <td style="text-transform:capitalize">${esc(it.category)}</td>
                <td style="color:${it.sentiment < 0 ? "#ff8d8d" : it.sentiment > 0 ? "#8fe6b6" : "#97a0bd"}">${it.sentiment > 0 ? "+" : ""}${it.sentiment}</td>
                <td><span class="badge ${it.priority.startsWith("P1") ? "b-critical" : it.priority.startsWith("P2") ? "b-high" : "b-low"}">${esc(it.priority.split(" ")[0])}</span></td>
                <td style="font-size:12px">${esc(it.department.split("(")[0])}</td>
              </tr>`).join("")}
          </table>
        </div>
        <div class="card">
          <h3>📊 Category hotspots</h3>
          ${barChart(Object.keys(a.category_counts), Object.values(a.category_counts), { color: "#ff6b9d", h: 240 })}
          <div class="grid g2 mt">
            <div class="bd-item"><div class="bd-val">${a.avg_sentiment}</div><div class="bd-lbl">Avg sentiment</div></div>
            <div class="bd-item"><div class="bd-val" style="color:#ff8d8d">${a.p1_emergencies}</div><div class="bd-lbl">P1 emergencies</div></div>
          </div>
        </div>
      </div>`;
  }
  loadFeed();
}

/* ============================================================
   PAGE: CORRUPTION SHIELD
   ============================================================ */
async function pageCorruption(view) {
  view.innerHTML = `
    <div class="card">
      <h3>🛡️ Multi-layer anomaly analysis <span class="badge b-high">Module 4</span></h3>
      <p class="muted" style="line-height:1.65">The engine scans a seeded database of <b>1,250+ government transactions</b> across 5 departments using five layers:
      <b>① Benford's Law</b> (first-digit fraud test) · <b>② statistical outliers</b> (robust z-scores) ·
      <b>③ vendor concentration</b> (HHI index) · <b>④ temporal patterns</b> (threshold-splitting, weekend & fiscal-year spikes) ·
      <b>⑤ ghost beneficiary detection</b> (fuzzy name matching + address clustering). Fraud patterns were deliberately injected for this demo — see if the AI finds them.</p>
      <button class="btn mt" id="audit-btn">🚀 Run Full Audit</button>
    </div>
    <div id="audit-results" class="mt"></div>
  `;
  document.getElementById("audit-btn").addEventListener("click", runAudit);
}

async function runAudit() {
  const btn = document.getElementById("audit-btn");
  const box = document.getElementById("audit-results");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Scanning 1,250+ transactions…';
  box.innerHTML = `<div class="card" style="text-align:center;padding:40px">
    <span class="spinner" style="width:26px;height:26px;border-color:rgba(255,255,255,0.15);border-top-color:#ff9933"></span>
    <p class="muted" style="margin-top:12px">Layer 1: Benford's Law · Layer 2: Anomaly detection · Layer 3: Vendor network · Layer 4: Temporal · Layer 5: Ghosts…</p></div>`;
  try {
    const r = await api(API.corruption);
    state.corrCache = r;
    renderAudit(r, box);
  } catch (e) {
    box.innerHTML = `<div class="alert alert-bad">⚠️ ${esc(e.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = "🚀 Run Full Audit";
  }
}

function renderAudit(r, box) {
  const b = r.benford_overall;
  const digits = ["1","2","3","4","5","6","7","8","9"];
  const top = r.departments[0];

  box.innerHTML = `
    <div class="alert ${top.risk_level === "CRITICAL" || top.risk_level === "HIGH" ? "alert-bad" : "alert-warn"}">
      🚨 <b>${esc(top.department)}</b> flagged — risk ${top.risk_score}/100 (${top.risk_level}).
      ${r.flagged_transactions.length} suspicious transactions & ${r.ghosts.estimated_ghosts} ghost beneficiaries detected.
      Audit recorded on transparency chain block #${r.chain_block.index}.
    </div>

    <div class="section-title"><span class="bar"></span>Department risk ranking (weighted layers: 25/30/25/20)</div>
    <div class="grid g3">
      ${r.departments.map(d => `
        <div class="card" style="text-align:center">
          <div style="font-size:13.5px;font-weight:700;margin-bottom:4px">${esc(d.department)}</div>
          ${gauge(d.risk_score)}
          <span class="badge b-${d.risk_level.toLowerCase()}">${d.risk_level}</span>
          <div class="breakdown" style="grid-template-columns:repeat(4,1fr);margin-top:12px">
            <div class="bd-item"><div class="bd-val">${d.layers.benford}</div><div class="bd-lbl">Benford</div></div>
            <div class="bd-item"><div class="bd-val">${d.layers.anomaly}</div><div class="bd-lbl">Anomaly</div></div>
            <div class="bd-item"><div class="bd-val">${d.layers.vendor}</div><div class="bd-lbl">Vendor</div></div>
            <div class="bd-item"><div class="bd-val">${d.layers.temporal}</div><div class="bd-lbl">Temporal</div></div>
          </div>
        </div>`).join("")}
    </div>

    <div class="grid g2-1 mt">
      <div class="card">
        <h3>1️⃣ Benford's Law — first-digit distribution (all departments)</h3>
        ${groupedBarChart(digits, digits.map(d => b.expected[d]), digits.map(d => b.actual[d]),
          "Expected (Benford)", "Observed (actual)", (v) => (v * 100).toFixed(1) + "%")}
        <div class="grid g3 mt">
          <div class="bd-item"><div class="bd-val">${b.chi_square}</div><div class="bd-lbl">χ² (critical @1%: ${b.critical_value_1pct})</div></div>
          <div class="bd-item"><div class="bd-val">${b.mad}</div><div class="bd-lbl">Mean Abs Deviation</div></div>
          <div class="bd-item"><div class="bd-val" style="font-size:11.5px">${esc(b.conformity)}</div><div class="bd-lbl">Verdict</div></div>
        </div>
      </div>
      <div class="card">
        <h3>4️⃣ Temporal patterns</h3>
        ${barChart(r.temporal.monthly.map(m => m.month.slice(5)), r.temporal.monthly.map(m => m.total / 100000),
          { color: "#ff6b9d", fmt: (v) => v.toFixed(1) + "L" })}
        <ul class="tick-list">${r.temporal.patterns_found.map(p => `<li>${esc(p)}</li>`).join("") || "<li>No temporal anomalies</li>"}</ul>
        <p class="muted" style="font-size:11px;margin-top:6px">Monthly expenditure (₹ lakh)</p>
      </div>
    </div>

    <div class="section-title"><span class="bar"></span>2️⃣ Top flagged transactions</div>
    <div class="card tbl-wrap">
      <table class="tbl">
        <tr><th>Txn</th><th>Dept</th><th>Vendor</th><th>Amount</th><th>Date</th><th>Risk</th><th>AI flags</th></tr>
        ${r.flagged_transactions.slice(0, 12).map(t => `
          <tr>
            <td class="muted">#${t.id}</td>
            <td style="max-width:150px">${esc(t.dept.split(" ")[0])}</td>
            <td style="max-width:180px">${esc(t.vendor)}</td>
            <td><b>${fmtIN(t.amount)}</b></td>
            <td class="muted">${t.date}</td>
            <td><span class="badge ${t.risk > 0.8 ? "b-critical" : t.risk > 0.6 ? "b-high" : "b-medium"}">${Math.round(t.risk * 100)}%</span></td>
            <td style="max-width:260px"><span class="muted" style="font-size:11.5px">${t.flags.map(esc).join(" · ")}</span></td>
          </tr>`).join("")}
      </table>
    </div>

    <div class="grid g2 mt">
      <div class="card">
        <h3>3️⃣ Vendor concentration network</h3>
        <div class="tbl-wrap"><table class="tbl">
          <tr><th>Vendor</th><th>Txns</th><th>Total</th><th>Share</th></tr>
          ${r.vendor_analysis.vendors.map(v => `
            <tr><td>${esc(v.vendor)}${v.flagged ? ` <span class="badge b-critical">FLAGGED</span>` : ""}</td><td>${v.count}</td>
            <td>${fmtIN(v.total)}</td>
            <td><span class="badge ${v.share_pct > 15 ? "b-high" : "b-low"}">${v.share_pct}%</span></td></tr>`).join("")}
        </table></div>
        <p class="muted mt">HHI index: <b>${r.vendor_analysis.hhi}</b> — ${esc(r.vendor_analysis.verdict)}</p>
      </div>
      <div class="card">
        <h3>5️⃣ Ghost beneficiary detection</h3>
        <div class="grid g3">
          <div class="bd-item"><div class="bd-val">${r.ghosts.total_beneficiaries}</div><div class="bd-lbl">Sampled</div></div>
          <div class="bd-item"><div class="bd-val" style="color:#ff8d8d">${r.ghosts.duplicate_pairs.length}</div><div class="bd-lbl">Duplicate pairs</div></div>
          <div class="bd-item"><div class="bd-val" style="color:#ffb877">₹${r.ghosts.estimated_leakage_lakh}L</div><div class="bd-lbl">Est. leakage/yr</div></div>
        </div>
        <div class="tbl-wrap mt"><table class="tbl">
          <tr><th>Name A</th><th>Name B</th><th>Match</th><th>Area</th></tr>
          ${r.ghosts.duplicate_pairs.slice(0, 6).map(p => `
            <tr><td>${esc(p.a.name)}</td><td>${esc(p.b.name)}</td>
            <td><span class="badge b-high">${p.match_pct}%</span></td>
            <td class="muted">${esc(p.a.area)}</td></tr>`).join("")}
        </table></div>
        <p class="muted mt" style="font-size:12px">Fuzzy matching (SequenceMatcher ≥ 86%) + address clustering — e.g. "${esc(r.ghosts.duplicate_pairs[0]?.a.name || "")}" vs "${esc(r.ghosts.duplicate_pairs[0]?.b.name || "")}".</p>
      </div>
    </div>
  `;
}

/* ============================================================
   PAGE: TRANSPARENCY CHAIN
   ============================================================ */
async function pageChain(view) {
  view.innerHTML = `<div class="card" style="text-align:center;padding:40px"><span class="spinner" style="width:26px;height:26px;border-color:rgba(255,255,255,0.15);border-top-color:#ff9933"></span><p class="muted" style="margin-top:12px">Reading governance chain…</p></div>`;
  const data = await api(API.chain);
  const typeIcons = {
    GENESIS: "🌱", SERVICE_MATCH: "🎯", CORRUPTION_AUDIT: "🛡️",
    DECISION: "🏛️", EXPENDITURE: "💸", ASSET: "🏗️",
  };
  view.innerHTML = `
    <div class="card" style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;justify-content:space-between">
      <div>
        <h3 style="margin-bottom:6px">⛓️ Lightweight governance blockchain <span class="badge b-low">Module 7</span></h3>
        <p class="muted">SHA-256 hash chain — no mining, no cryptocurrency. Every AI action (scheme match, audit) is appended as an immutable block. ${data.total} blocks so far.</p>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap">
        <button class="btn" id="verify-btn">🔍 Verify Integrity</button>
        <button class="btn btn-ghost" id="tamper-btn">🧪 Simulate Hacker Attack</button>
        <button class="btn btn-ghost" id="repair-btn">🔧 Repair</button>
      </div>
    </div>
    <div id="verify-box" class="mt"></div>
    <div class="section-title"><span class="bar"></span>Block explorer (latest ${data.blocks.length})</div>
    <div class="chain-line">
      ${data.blocks.map(bl => `
        <div class="card block-card">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px">
            <b>${typeIcons[bl.type] || "📦"} Block #${bl.index} — ${esc(bl.type)}</b>
            <span class="muted" style="font-size:11.5px">${esc(bl.timestamp)}</span>
          </div>
          <pre class="hash" style="margin:8px 0;background:rgba(0,0,0,0.25);padding:9px 12px;border-radius:9px">${esc(JSON.stringify(bl.data, null, 1))}</pre>
          <div class="hash">prev: ${esc(bl.previous_hash.slice(0, 26))}… → hash: ${esc(bl.hash.slice(0, 26))}…</div>
        </div>`).join("")}
    </div>
  `;
  document.getElementById("verify-btn").addEventListener("click", async () => {
    const vb = document.getElementById("verify-box");
    vb.innerHTML = '<div class="alert alert-info">Recomputing SHA-256 hashes block by block…</div>';
    const v = await api(API.chainVerify);
    vb.innerHTML = v.valid
      ? `<div class="alert alert-ok">✅ ${esc(v.message)}</div>`
      : `<div class="alert alert-bad">⛔ ${esc(v.message)}</div>`;
  });
  document.getElementById("tamper-btn").addEventListener("click", async () => {
    const vb = document.getElementById("verify-box");
    const t = await api("/api/chain/tamper", { method: "POST" });
    const v = await api(API.chainVerify);
    vb.innerHTML = `
      <div class="alert alert-bad">🧪 <b>Attack simulated!</b> ${esc(t.message)} — an insider edited the recorded data (amount → ₹9,999,999) <i>after</i> it was signed.</div>
      ${v.valid
        ? '<div class="alert alert-ok">Chain still valid.</div>'
        : `<div class="alert alert-bad">⛔ <b>Verify caught it:</b> ${esc(v.message)}<br/>This is exactly why governance records need hash-chaining — the original hash no longer matches the data. Click 🔧 Repair to restore the authentic ledger.</div>`}
    `;
  });
  document.getElementById("repair-btn").addEventListener("click", async () => {
    const vb = document.getElementById("verify-box");
    const v = await api("/api/chain/repair", { method: "POST" });
    vb.innerHTML = v.valid
      ? `<div class="alert alert-ok">🔧 Ledger restored from the authentic chain. ${esc(v.message)}</div>`
      : `<div class="alert alert-bad">⛔ ${esc(v.message)}</div>`;
  });
}

/* ============================================================
   PAGE: ABOUT
   ============================================================ */
function pageAbout(view) {
  view.innerHTML = `
    <div class="hero">
      <h1>🇮🇳 Bharath Neuro-Governance Intelligence System</h1>
      <p>An AI brain that connects every citizen's need to every government resource in real time — eliminating corruption, delays and inefficiency automatically. This MVP implements Modules 1, 3, 4, 7 & 10 of the full specification as a working product.</p>
    </div>

    <div class="grid g2">
      <div class="card about-module">
        <h3>✅ Implemented in this MVP</h3>
        <ul class="tick-list">
          <li><b>Module 1 — Citizen Neural Profile:</b> privacy-first profile (no Aadhaar), 10-dim need vector, 5 ready demo personas</li>
          <li><b>Module 2 — Resource Optimization Cortex:</b> Mysuru network map (hospitals/schools/water), haversine distance, allocation score = 0.55·proximity + 0.30·availability + 0.15·quality, automatic reroute advisories for overloaded facilities</li>
          <li><b>Module 3 — Scheme Matching & Delivery Engine:</b> vector similarity + hard constraints + priority scoring (35/25/20/10/10 weights) + knapsack portfolio optimization with conflict rules, over 21 real schemes (incl. Karnataka state schemes)</li>
          <li><b>Module 4 — Corruption Detection Shield:</b> Benford's Law χ² test, robust z-score anomalies, vendor HHI concentration, temporal pattern detection, fuzzy ghost-beneficiary detection</li>
          <li><b>Module 7 — Transparency Blockchain:</b> SHA-256 hash chain with integrity verification + live hacker-attack simulation</li>
          <li><b>Module 10 — Public Dashboard:</b> real-time KPIs, live charts, EN/తెలుగు interface</li>
        </ul>
      </div>
      <div class="card about-module" style="border-left-color:#7c8cff">
        <h3>🚀 Roadmap (from full spec)</h3>
        <ul class="tick-list">
          <li><b>Module 5:</b> Disaster Response Neural Network (flood/epidemic early warning)</li>
          <li><b>Module 6:</b> Predictive Governance (LSTM + Prophet demand forecasting)</li>
          <li><b>Module 8:</b> Multi-language Citizen Voice NLP (12 Indian languages)</li>
          <li><b>Module 9:</b> Inter-department Coordination Brain</li>
          <li>PostgreSQL + PostGIS/pgvector, Kafka streaming, Airflow ETL, K3s deployment (₹0 cost)</li>
        </ul>
      </div>
    </div>

    <div class="grid g2 mt">
      <div class="card">
        <h3>💻 Technology stack (100% free & open source)</h3>
        <ul class="tick-list">
          <li><b>Backend:</b> Python 3.13 · FastAPI · Uvicorn</li>
          <li><b>AI engines:</b> pure-Python statistics, cosine-similarity matching, Benford χ², SequenceMatcher fuzzy matching, knapsack DP</li>
          <li><b>Frontend:</b> vanilla JS SPA · hand-rolled SVG charts · zero CDN dependencies</li>
          <li><b>Blockchain:</b> SHA-256 hash chain persisted to JSON (swap for PostgreSQL in prod)</li>
        </ul>
      </div>
      <div class="card">
        <h3>▶️ How to run</h3>
        <pre class="hash" style="background:rgba(0,0,0,0.3);padding:14px;border-radius:12px;font-size:12.5px;line-height:1.8">cd bngis
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# open http://localhost:8000</pre>
        <p class="muted mt">API docs (auto-generated): <a class="mini-link" href="/docs" target="_blank">/docs</a></p>
      </div>
    </div>

    <div class="card mt">
      <h3>📚 For the college report</h3>
      <p class="muted">Full documentation is in the project workspace: <b>README.md</b> (overview & API) and <b>docs/PROJECT_REPORT.md</b> (abstract, architecture, algorithms with formulas, testing, future scope).</p>
    </div>
  `;
}

/* ============================================================
   ROUTER
   ============================================================ */
const routes = {
  dashboard: pageDashboard,
  schemes: pageSchemes,
  resources: pageResources,
  disaster: pageDisaster,
  voice: pageVoice,
  corruption: pageCorruption,
  chain: pageChain,
  about: pageAbout,
};

async function render() {
  const route = location.hash.replace("#/", "") || "dashboard";
  const page = routes[route] || pageDashboard;
  document.querySelectorAll(".nav-item").forEach((a) =>
    a.classList.toggle("active", a.dataset.route === route));
  document.getElementById("page-title").textContent =
    t("t" + route[0].toUpperCase() + route.slice(1));
  document.getElementById("sidebar").classList.remove("open");
  const view = document.getElementById("view");
  view.classList.remove("fade-in");
  void view.offsetWidth; // restart animation
  view.classList.add("fade-in");
  try {
    await page(view);
  } catch (e) {
    view.innerHTML = `<div class="alert alert-bad">⚠️ Failed to load page: ${esc(e.message)} — is the backend running?</div>`;
  }
}

window.addEventListener("hashchange", render);
document.getElementById("lang-btn").addEventListener("click", () => {
  state.lang = state.lang === "en" ? "te" : "en";
  localStorage.setItem("bngis_lang", state.lang);
  applyI18n();
  if (["dashboard", "about", "schemes", "resources", "disaster", "voice", "corruption"].includes(location.hash.replace("#/", "") || "dashboard"))
    render();
});
document.getElementById("hamburger").addEventListener("click", () =>
  document.getElementById("sidebar").classList.toggle("open"));

state.lang = localStorage.getItem("bngis_lang") || "en";
applyI18n();
render();
