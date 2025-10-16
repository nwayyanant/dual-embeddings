const apiBaseEl = document.getElementById("apiBase");
apiBaseEl.textContent = typeof API_BASE !== "undefined" ? API_BASE : "(not set)";

const qEl      = document.getElementById("q");
const btnSearch= document.getElementById("btnSearch");
const btnAnswer= document.getElementById("btnAnswer");
const topkEl   = document.getElementById("topk");
const alphaEl  = document.getElementById("alpha");
const alphaVal = document.getElementById("alphaVal");
const langBadge= document.getElementById("langBadge");

const resultsEl   = document.getElementById("results");
const answerEl    = document.getElementById("answer");
const citationsEl = document.getElementById("citations");

alphaEl.addEventListener("input", () => {
  alphaVal.textContent = Number(alphaEl.value).toFixed(2);
});

async function search() {
  const query = qEl.value.trim();
  if (!query) return;
  resultsEl.innerHTML = `<div class="item"><div class="meta">Searching…</div></div>`;
  answerEl.textContent = "";
  citationsEl.innerHTML = "";

  const payload = {
    query,
    top_k: Number(topkEl.value),
    alpha: Number(alphaEl.value),
  };

  try {
    const resp = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    langBadge.textContent = `lang: ${data.query_lang || "—"} | α=${payload.alpha}`;
    renderResults(data.results || []);
  } catch (e) {
    resultsEl.innerHTML = `<div class="item"><div class="meta">Error</div><div>${e}</div></div>`;
  }
}

function renderResults(items) {
  if (!items.length) {
    resultsEl.innerHTML = `<div class="item"><div class="meta">No results</div></div>`;
    return;
  }
  resultsEl.innerHTML = "";
  for (const it of items) {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <div class="meta">[${it.book_id}:${it.para_id}] · doc=${it.doc_id}</div>
      <div class="snippet">${escapeHTML(it.snippet || "")}</div>
    `;
    resultsEl.appendChild(div);
  }
}

async function answer() {
  const query = qEl.value.trim();
  if (!query) return;
  answerEl.textContent = "Answering…";
  citationsEl.innerHTML = "";

  const payload = {
    query,
    top_k: Number(topkEl.value),
    alpha: Number(alphaEl.value),
  };

  try {
    const resp = await fetch(`${API_BASE}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    answerEl.textContent = data.answer || "";
    renderCitations(data.citations || []);
  } catch (e) {
    answerEl.textContent = `Error: ${e}`;
  }
}

function renderCitations(items) {
  if (!items.length) {
    citationsEl.innerHTML = `<div class="item"><div class="meta">No citations</div></div>`;
    return;
  }
  citationsEl.innerHTML = "";
  for (const it of items) {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `
      <div class="meta">[${it.book_id}:${it.para_id}]</div>
      <div class="snippet">${escapeHTML((it.pali_paragraph || "") + "\n" + (it.translation_paragraph || ""))}</div>
    `;
    citationsEl.appendChild(div);
  }
}

function escapeHTML(s) {
  return s.replace(/[&<>"']/g, ch => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[ch]
  ));
}

btnSearch.addEventListener("click", search);
btnAnswer.addEventListener("click", answer);

// Allow Enter to trigger search
qEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") search();
});