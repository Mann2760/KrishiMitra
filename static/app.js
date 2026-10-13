const form = document.querySelector("#advisory-form");
const submitBtn = document.querySelector("#submit-btn");
const resultPanel = document.querySelector("#result-panel");
const advisoryText = document.querySelector("#advisory-text");
const resultMeta = document.querySelector("#result-meta");
const historyList = document.querySelector("#history-list");
const feedbackBtn = document.querySelector("#feedback-btn");
let currentAdvisoryId = null;

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

function showAdvisory(item) {
  currentAdvisoryId = item.id;
  advisoryText.textContent = item.advisory || "No advisory text returned.";
  resultMeta.textContent = `${item.crop} · ${item.location} · ${new Date(item.created_at).toLocaleString()} · ${item.generation_mode}`;
  resultPanel.classList.remove("hidden");
  document.querySelector("#feedback-status").textContent = "";
  resultPanel.scrollIntoView({behavior: "smooth", block: "start"});
}

async function loadHistory() {
  historyList.replaceChildren();
  try {
    const data = await api("/api/advisories?limit=10");
    if (!data.items.length) {
      historyList.innerHTML = '<p class="helper">No plans saved yet. Create your first one above.</p>';
      return;
    }
    data.items.forEach(item => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "history-item";
      const icon = document.createElement("span");
      icon.className = "history-icon";
      icon.textContent = "✳";
      const detail = document.createElement("span");
      detail.className = "history-detail";
      const title = document.createElement("span");
      title.className = "history-title";
      title.textContent = `${item.crop} · ${item.growth_stage}`;
      const sub = document.createElement("span");
      sub.className = "history-sub";
      sub.textContent = `${item.location} — ${item.symptoms}`;
      detail.append(title, document.createElement("br"), sub);
      const arrow = document.createElement("span");
      arrow.className = "history-arrow";
      arrow.textContent = "↗";
      button.append(icon, detail, arrow);
      button.addEventListener("click", async () => {
        try { showAdvisory(await api(`/api/advisories/${encodeURIComponent(item.id)}`)); }
        catch (error) { alert(error.message); }
      });
      historyList.append(button);
    });
  } catch (error) {
    historyList.textContent = `Could not load history: ${error.message}`;
  }
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  submitBtn.disabled = true;
  submitBtn.textContent = "Preparing your crop plan…";
  const payload = Object.fromEntries(new FormData(form).entries());
  try {
    const item = await api("/api/advisory", {method: "POST", body: JSON.stringify(payload)});
    showAdvisory(item);
    await loadHistory();
  } catch (error) {
    alert(`Could not create an advisory: ${error.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Create my crop plan <span>→</span>';
  }
});

document.querySelector("#refresh-history").addEventListener("click", loadHistory);

feedbackBtn.addEventListener("click", async () => {
  if (!currentAdvisoryId) {
    document.querySelector("#feedback-status").textContent = "Create or open a crop plan first.";
    return;
  }
  feedbackBtn.disabled = true;
  try {
    const result = await api("/api/feedback", {
      method: "POST",
      body: JSON.stringify({
        advisory_id: currentAdvisoryId,
        rating: Number(document.querySelector("#rating").value),
        comment: document.querySelector("#feedback-comment").value
      })
    });
    document.querySelector("#feedback-status").textContent = result.message;
    document.querySelector("#feedback-comment").value = "";
  } catch (error) {
    document.querySelector("#feedback-status").textContent = error.message;
  } finally {
    feedbackBtn.disabled = false;
  }
});

loadHistory();
