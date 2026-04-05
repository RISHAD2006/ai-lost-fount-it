<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard – Campus Found-It AI</title>
  <link rel="stylesheet" href="/static/style.css">
  <style>
    /* ── LAYOUT ── */
    .dash-wrap { max-width: 1200px; margin: 0 auto; padding: 24px 16px 60px; }

    /* ── SEARCH BAR ── */
    .search-row { display:flex; gap:10px; margin-bottom:24px; }
    .search-row input { flex:1; padding:11px 16px; border-radius:10px;
      border:1px solid #cbd5e1; font-size:14px; outline:none; }
    .search-row input:focus { border-color:#6366f1; }
    .search-row .btn { padding:11px 22px; }

    /* ── UPLOAD CARD ── */
    .upload-card { background:white; border-radius:16px; padding:26px;
      box-shadow:0 4px 20px rgba(0,0,0,0.08); margin-bottom:30px; }
    .upload-card h3 { font-size:18px; margin-bottom:18px; color:#1e293b; }
    .form-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
    .form-grid.one { grid-template-columns:1fr; }
    .form-grid input, .form-grid textarea, .form-grid select {
      padding:10px 14px; border-radius:9px; border:1px solid #cbd5e1;
      font-size:14px; outline:none; width:100%; transition:border 0.2s;
      font-family:inherit; }
    .form-grid input:focus, .form-grid textarea:focus, .form-grid select:focus {
      border-color:#6366f1; }
    .form-grid textarea { resize:vertical; min-height:80px; }
    .upload-btn { margin-top:16px; width:100%; padding:13px;
      font-size:15px; font-weight:bold; }

    /* ── MATCH RESULT BOX ── */
    .match-result { display:none; margin-top:16px; padding:16px;
      background:#ede9fe; border:2px solid #a78bfa; border-radius:12px; }
    .match-result h4 { color:#5b21b6; margin-bottom:10px; font-size:15px; }
    .match-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:12px; margin-top:10px; }
    .match-card { background:white; border-radius:10px; overflow:hidden;
      box-shadow:0 2px 10px rgba(0,0,0,0.08); }
    .match-card img { width:100%; height:140px; object-fit:cover; }
    .match-card .no-img { width:100%; height:140px; background:#f1f5f9;
      display:flex; align-items:center; justify-content:center; font-size:36px; }
    .match-card .mc-body { padding:10px; }
    .match-card h5 { margin:0 0 4px; font-size:14px; }
    .match-card p  { margin:0; font-size:12px; color:#64748b; line-height:1.5; }
    .score-badge { display:inline-block; margin-top:6px; padding:3px 10px;
      background:#7c3aed; color:white; border-radius:20px; font-size:11px; font-weight:bold; }
    .contact-badge { display:inline-block; margin-top:5px; padding:3px 10px;
      background:#dcfce7; color:#166534; border-radius:20px; font-size:11px; font-weight:bold; }

    /* ── TABS ── */
    .tab-row { display:flex; gap:10px; margin-bottom:20px; flex-wrap:wrap; }
    .tab-btn { padding:9px 20px; border-radius:10px; border:2px solid #e2e8f0;
      background:white; color:#64748b; cursor:pointer; font-size:14px; font-weight:600;
      transition:0.2s; }
    .tab-btn.t-all   { border-color:#6366f1; background:#6366f1; color:white; }
    .tab-btn.t-lost  { border-color:#ef4444; background:#ef4444; color:white; }
    .tab-btn.t-found { border-color:#10b981; background:#10b981; color:white; }
    .tab-btn.t-mine  { border-color:#f59e0b; background:#f59e0b; color:white; }

    /* ── ITEMS GRID ── */
    .items-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:18px; }
    .item-card  { background:white; border-radius:14px; overflow:hidden;
      box-shadow:0 4px 16px rgba(0,0,0,0.07); transition:transform 0.2s; }
    .item-card:hover { transform:translateY(-3px); }
    .item-card img  { width:100%; height:180px; object-fit:cover; display:block; }
    .item-card .no-img { width:100%; height:180px; background:#f1f5f9;
      display:flex; align-items:center; justify-content:center; font-size:48px; }
    .item-body { padding:14px; }
    .item-body h4 { margin:0 0 6px; font-size:15px; }
    .item-body p  { margin:0 0 8px; font-size:12px; color:#64748b; line-height:1.5; }
    .pill-row { display:flex; flex-wrap:wrap; gap:6px; }
    .pill { padding:3px 10px; border-radius:20px; font-size:11px; font-weight:bold; }
    .p-lost    { background:#fee2e2; color:#b91c1c; }
    .p-found   { background:#dcfce7; color:#166534; }
    .p-matched { background:#ede9fe; color:#5b21b6; }
    .p-contact { background:#fef3c7; color:#92400e; }
    .del-btn { margin-top:8px; padding:5px 12px; background:#ef4444;
      color:white; border:none; border-radius:7px; font-size:12px; cursor:pointer; }

    .empty   { grid-column:1/-1; text-align:center; color:#94a3b8; padding:50px; }
    .loading { grid-column:1/-1; text-align:center; color:#6366f1; padding:30px; font-size:15px; }

    /* ── UPLOAD MSG ── */
    .up-msg { display:none; margin-top:10px; padding:11px 16px;
      border-radius:10px; font-size:14px; font-weight:500; }
    .up-ok    { background:#dcfce7; color:#166534; }
    .up-error { background:#fee2e2; color:#991b1b; }
    .up-match { background:#ede9fe; color:#5b21b6; }

    @media(max-width:600px) {
      .form-grid { grid-template-columns:1fr; }
      .search-row { flex-wrap:wrap; }
    }
  </style>
</head>
<body>

<!-- NAVBAR -->
<nav class="navbar">
  <div class="nav-brand">🤖 Campus Found-It AI</div>
  <div class="nav-right">
    <span class="nav-user" id="nav-user"></span>
    <button class="btn btn-red" onclick="logout()">Logout</button>
  </div>
</nav>

<div class="dash-wrap">

  <!-- SEARCH -->
  <div class="search-row">
    <input id="search-q" placeholder="Search items by name, colour, brand... (press Enter or click Search)">
    <button class="btn btn-purple" onclick="doSearch()">🔍 Search</button>
    <button class="btn btn-gray"   onclick="clearSearch()">✕ Clear</button>
  </div>

  <!-- UPLOAD CARD -->
  <div class="upload-card">
    <h3>📤 Report a Lost or Found Item</h3>

    <div class="form-grid">
      <input id="u-title"   placeholder="Item Name  e.g. Blue Water Bottle *">
      <input id="u-contact" placeholder="Your Phone / Email (for contact) *">
    </div>

    <div class="form-grid one" style="margin-top:12px;">
      <textarea id="u-desc" placeholder="Describe the item — colour, brand, size, any unique marks..."></textarea>
    </div>

    <div class="form-grid" style="margin-top:12px;">
      <input id="u-image"  placeholder="Image URL (paste a photo link) — optional">
      <select id="u-status">
        <option value="lost">🔴 I Lost this item</option>
        <option value="found">🟢 I Found this item</option>
      </select>
    </div>

    <button class="btn btn-purple upload-btn" onclick="uploadItem()">
      Upload &amp; Find Matches →
    </button>

    <div class="up-msg" id="up-msg"></div>

    <!-- MATCH RESULTS appear here after upload -->
    <div class="match-result" id="match-result">
      <h4 id="match-heading">🤖 Possible Matches Found!</h4>
      <div class="match-cards" id="match-cards"></div>
    </div>
  </div>

  <!-- TABS -->
  <div class="tab-row">
    <button class="tab-btn t-all"   id="tab-all"   onclick="switchTab('all')">📋 All Items</button>
    <button class="tab-btn"         id="tab-lost"  onclick="switchTab('lost')">🔴 Lost Items</button>
    <button class="tab-btn"         id="tab-found" onclick="switchTab('found')">🟢 Found Items</button>
    <button class="tab-btn"         id="tab-mine"  onclick="switchTab('mine')">👤 My Items</button>
  </div>

  <!-- ITEMS GRID -->
  <div class="items-grid" id="items-grid">
    <div class="loading">Loading items...</div>
  </div>

</div><!-- /dash-wrap -->

<script>
/* ── USER DATA ── */
const userId = localStorage.getItem("user_id");
const uName  = localStorage.getItem("name");
const uEmail = localStorage.getItem("email");

if (!userId) location.href = "/login";

document.getElementById("nav-user").textContent = uName + " | " + uEmail;

/* ── TABS ── */
let currentTab = "all";

function switchTab(tab) {
  currentTab = tab;
  // Reset all tab styles
  ["all","lost","found","mine"].forEach(t => {
    document.getElementById("tab-" + t).className = "tab-btn";
  });
  document.getElementById("tab-" + tab).className = "tab-btn t-" + tab;
  loadItems(tab);
}

/* ── LOAD ITEMS ── */
async function loadItems(tab) {
  const grid = document.getElementById("items-grid");
  grid.innerHTML = '<div class="loading">Loading...</div>';

  let url;
  if (tab === "mine")  url = "/api/my-items/" + userId;
  else if (tab === "lost")  url = "/api/items?status=lost";
  else if (tab === "found") url = "/api/items?status=found";
  else url = "/api/items";

  try {
    const res   = await fetch(url);
    const items = await res.json();
    renderItems(items, tab === "mine");
  } catch(e) {
    grid.innerHTML = '<div class="empty">⚠️ Failed to load items. Check connection.</div>';
  }
}

function renderItems(items, canDelete) {
  const grid = document.getElementById("items-grid");
  if (!items || !items.length) {
    grid.innerHTML = '<div class="empty">No items found here yet.</div>';
    return;
  }
  grid.innerHTML = items.map(item => cardHTML(item, canDelete)).join("");
}

function cardHTML(item, canDelete) {
  const imgPart = item.image_url
    ? `<img src="${item.image_url}" alt="item" onerror="this.parentElement.innerHTML='<div class=no-img>📦</div>'">`
    : `<div class="no-img">📦</div>`;

  const statusPill = item.status === "lost"
    ? `<span class="pill p-lost">🔴 Lost</span>`
    : `<span class="pill p-found">🟢 Found</span>`;

  const matchedPill = item.matched
    ? `<span class="pill p-matched">🤖 AI Matched</span>` : "";

  const contactPill = item.contact
    ? `<span class="pill p-contact">📞 ${esc(item.contact)}</span>` : "";

  const delBtn = canDelete
    ? `<button class="del-btn" onclick="deleteItem(${item.id})">🗑 Delete</button>` : "";

  return `
  <div class="item-card">
    ${imgPart}
    <div class="item-body">
      <h4>${esc(item.title)}</h4>
      <p>${esc(item.description || "No description provided")}</p>
      <div class="pill-row">
        ${statusPill} ${matchedPill}
      </div>
      ${contactPill ? `<div style="margin-top:6px">${contactPill}</div>` : ""}
      ${delBtn}
    </div>
  </div>`;
}

/* ── SEARCH ── */
async function doSearch() {
  const q = document.getElementById("search-q").value.trim();
  if (!q) { loadItems(currentTab); return; }

  const grid = document.getElementById("items-grid");
  grid.innerHTML = '<div class="loading">Searching...</div>';

  const res   = await fetch("/api/search?q=" + encodeURIComponent(q));
  const items = await res.json();

  if (!items.length) {
    grid.innerHTML = '<div class="empty">No matching items found for "<b>' + esc(q) + '</b>".</div>';
    return;
  }

  // Show score badge on each search result
  grid.innerHTML = items.map(item => {
    let card = cardHTML(item, false);
    // Inject score badge before closing item-body div
    const scoreHTML = `<span class="pill p-matched" style="margin-top:6px">🎯 ${item.score}% match</span>`;
    card = card.replace("</div>\n  </div>", scoreHTML + "\n</div>\n  </div>");
    return card;
  }).join("");
}

function clearSearch() {
  document.getElementById("search-q").value = "";
  loadItems(currentTab);
}

document.getElementById("search-q").addEventListener("keydown", e => {
  if (e.key === "Enter") doSearch();
});

/* ── UPLOAD ITEM ── */
async function uploadItem() {
  const title   = document.getElementById("u-title").value.trim();
  const desc    = document.getElementById("u-desc").value.trim();
  const status  = document.getElementById("u-status").value;
  const imageUrl= document.getElementById("u-image").value.trim();
  const contact = document.getElementById("u-contact").value.trim();

  if (!title) { showUpMsg("Please enter an item name.", "up-error"); return; }
  if (!contact){ showUpMsg("Please enter your contact info.", "up-error"); return; }

  showUpMsg("Uploading and running AI match...", "up-ok");

  // Hide any previous match result
  document.getElementById("match-result").style.display = "none";

  const res  = await fetch("/api/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId, title, description: desc,
      status, image_url: imageUrl, contact
    })
  });
  const data = await res.json();

  if (!res.ok) {
    showUpMsg(data.error || "Upload failed.", "up-error");
    return;
  }

  // Show success message
  showUpMsg("✅ Item uploaded successfully!", "up-ok");

  // Show match results if any
  if (data.matches && data.matches.length > 0) {
    showMatches(data.matches, status);
    showUpMsg(
      `✅ Uploaded! 🎉 ${data.matches.length} possible match(es) found! See below.`,
      "up-match"
    );
  }

  // Clear form
  document.getElementById("u-title").value   = "";
  document.getElementById("u-desc").value    = "";
  document.getElementById("u-image").value   = "";
  document.getElementById("u-contact").value = "";

  loadItems(currentTab);
}

function showMatches(matches, uploadedStatus) {
  const resultBox  = document.getElementById("match-result");
  const heading    = document.getElementById("match-heading");
  const cardsDiv   = document.getElementById("match-cards");

  heading.textContent = uploadedStatus === "lost"
    ? `🤖 Found items that might be yours! (${matches.length} match${matches.length > 1 ? "es" : ""})`
    : `🤖 Lost items that match what you found! (${matches.length} match${matches.length > 1 ? "es" : ""})`;

  cardsDiv.innerHTML = matches.map(m => `
    <div class="match-card">
      ${m.image_url
        ? `<img src="${m.image_url}" alt="match" onerror="this.parentElement.innerHTML='<div class=no-img>📦</div>'">`
        : `<div class="no-img">📦</div>`}
      <div class="mc-body">
        <h5>${esc(m.title)}</h5>
        <p>${esc(m.description || "No description")}</p>
        <div><span class="score-badge">🎯 Match Score: ${m.score}%</span></div>
        ${m.contact
          ? `<div><span class="contact-badge">📞 ${esc(m.contact)}</span></div>`
          : ""}
      </div>
    </div>
  `).join("");

  resultBox.style.display = "block";
  resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function showUpMsg(text, cls) {
  const el = document.getElementById("up-msg");
  el.textContent  = text;
  el.className    = "up-msg " + cls;
  el.style.display = "block";
}

/* ── DELETE ── */
async function deleteItem(id) {
  if (!confirm("Delete this item?")) return;
  await fetch("/api/delete/" + id, { method: "DELETE" });
  loadItems(currentTab);
}

/* ── LOGOUT ── */
function logout() {
  localStorage.clear();
  location.href = "/login";
}

/* ── HELPERS ── */
function esc(s) {
  const d = document.createElement("div");
  d.innerText = s || "";
  return d.innerHTML;
}

/* ── INITIAL LOAD ── */
loadItems("all");
</script>
</body>
</html>
