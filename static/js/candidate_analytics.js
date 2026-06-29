(function () {
  const page = document.querySelector("[data-public-analytics-page]");
  if (!page) return;

  function esc(s) {
    if (s == null || s === undefined) return "";
    s = String(s);
    return s.replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;");
  }

  function get(path) {
    return fetch(path, { credentials: "same-origin" }).then((r) => r.json());
  }
  function post(path, body) {
    return fetch(path, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    }).then((r) => r.json());
  }

  const roleSelect = document.getElementById("ca-job-role");
  const listEl = document.getElementById("ca-list");
  const countEl = document.getElementById("ca-count");
  const runBtn = document.getElementById("ca-run");
  const linkInput = document.getElementById("ca-public-link");
  const copyBtn = document.getElementById("ca-copy-link");
  const tableBody = document.getElementById("ca-public-table");

  const statTotal = document.getElementById("ca-stat-total");
  const statAvg = document.getElementById("ca-stat-avg");
  const statShort = document.getElementById("ca-stat-shortlisted");
  const statLast = document.getElementById("ca-stat-last");

  function setCount(n) {
    if (countEl) countEl.textContent = String(n || 0);
  }

  function buildPublicLink(jobId) {
    if (!jobId) return "";
    const origin = window.location.origin.replace(/\/+$/, "");
    return `${origin}/candidates/apply/${encodeURIComponent(jobId)}`;
  }

  function loadRoles() {
    if (!roleSelect) return;
    roleSelect.innerHTML = '<option value="">Loading…</option>';
    get("/api/candidate-analytics/job-roles")
      .then((data) => {
        const roles = (data && data.data) ? data.data : [];
        roleSelect.innerHTML = "";
        const opt0 = document.createElement("option");
        opt0.value = "";
        opt0.textContent = roles.length ? "Select a job role" : "No job roles found";
        roleSelect.appendChild(opt0);
        roles.forEach((r) => {
          const opt = document.createElement("option");
          opt.value = r.id;
          opt.textContent = (r.title || "Job Role") + (r.location ? " • " + r.location : "");
          roleSelect.appendChild(opt);
        });
      })
      .catch(() => {
        roleSelect.innerHTML = '<option value="">Failed to load job roles</option>';
      });
  }

  function renderPublicCandidates(rows) {
    if (!tableBody) return;
    if (!rows || !rows.length) {
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="py-4 px-4 text-xs text-slate-500">
            No public submissions yet. Share the public link for this job so candidates can upload their resumes.
          </td>
        </tr>
      `;
      setCount(0);
      return;
    }

    setCount(rows.length);
    tableBody.innerHTML = "";

    rows.forEach((c) => {
      const tr = document.createElement("tr");
      tr.className = "border-b border-slate-50";
      const viewUrl = c.id ? `/candidates/${encodeURIComponent(c.id)}` : "";
      tr.innerHTML = `
        <td class="py-2 px-4 text-xs text-slate-900">${esc(c.full_name || "Candidate")}</td>
        <td class="py-2 px-4 text-xs text-slate-600">${esc(c.email || "")}</td>
        <td class="py-2 px-4 text-xs">${c.ai_score != null ? esc(String(c.ai_score)) : "—"}</td>
        <td class="py-2 px-4 text-xs">${esc((c.status || "").toString().charAt(0).toUpperCase() + (c.status || "").toString().slice(1))}</td>
        <td class="py-2 px-4 text-xs text-slate-500">${esc(c.upload_date || "")}</td>
        <td class="py-2 px-4 text-right text-xs">
          ${
            viewUrl
              ? `<a href="${esc(viewUrl)}" class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-2 py-1 text-[0.7rem] text-slate-700 hover:bg-slate-50">View</a>`
              : ""
          }
        </td>
      `;
      tableBody.appendChild(tr);
    });
  }

  function updateSummary(jobRoleId) {
    if (!jobRoleId) {
      if (statTotal) statTotal.textContent = "0";
      if (statAvg) statAvg.textContent = "0";
      if (statShort) statShort.textContent = "0";
      if (statLast) statLast.textContent = "—";
      renderPublicCandidates([]);
      if (listEl) {
        listEl.innerHTML = "<p class=\"text-slate-500 text-sm\">Select a job role and click “Run AI analysis & rank”.</p>";
      }
      return;
    }

    // Public stats
    get(`/api/candidate-analytics/public-summary?job_role_id=${encodeURIComponent(jobRoleId)}`)
      .then((res) => {
        if (!res || res.error) return;
        if (statTotal) statTotal.textContent = String(res.total_public || 0);
        if (statAvg) statAvg.textContent = String(Math.round(res.average_score_public || 0));
        if (statShort) statShort.textContent = String(res.shortlisted_public || 0);
        if (statLast) statLast.textContent = res.last_upload_at || "—";
      })
      .catch(() => {});

    // Public candidate list
    get(`/api/candidate-analytics/public-candidates?job_role_id=${encodeURIComponent(jobRoleId)}`)
      .then((res) => {
        const rows = (res && res.data) ? res.data : [];
        renderPublicCandidates(rows);
      })
      .catch(() => {
        renderPublicCandidates([]);
      });
  }

  function loadLatestRanking(jobRoleId) {
    if (!listEl || !jobRoleId) return;
    listEl.innerHTML = '<p class="text-slate-500 text-sm">Loading latest analysis…</p>';
    const q = `?job_role_id=${encodeURIComponent(jobRoleId)}`;
    get(`/api/candidate-analytics/latest${q}`)
      .then((data) => {
        const items = (data && data.data) ? data.data : [];
        renderRanking(items);
      })
      .catch(() => {
        listEl.innerHTML = '<p class="text-rose-600 text-sm">Failed to load latest analysis.</p>';
      });
  }

  function renderRanking(items) {
    if (!listEl) return;
    if (!items || !items.length) {
      listEl.innerHTML =
        '<p class="text-slate-500 text-sm">No analysis yet for this job role. Click “Run AI analysis & rank”.</p>';
      return;
    }

    let html = '<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">';
    items.forEach((it) => {
      const rank = it.rank || "";
      const score =
        it.ai_score != null && it.ai_score !== undefined ? it.ai_score : "";
      const viewUrl = it.candidate_id
        ? `/candidates/${encodeURIComponent(it.candidate_id)}`
        : "";

      html += '<div class="border border-slate-200 rounded-xl p-5 bg-white">';
      html += '<div class="flex items-start justify-between gap-3">';
      html += '<div class="min-w-0">';
      html += `<p class="text-sm font-semibold text-slate-900 truncate">${esc(
        it.full_name || "Candidate"
      )}</p>`;
      html += `<p class="text-sm text-slate-500 truncate">${esc(
        it.email || ""
      )}</p>`;
      html += "</div>";
      html += '<div class="flex flex-col items-end gap-2">';
      if (viewUrl) {
        html += `<a href="${esc(
          viewUrl
        )}" class="rounded-lg border border-indigo-500 px-3 py-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50">View candidate</a>`;
      }
      html += "</div>";
      html += "</div>";

      html += '<div class="mt-4">';
      html += '<div class="flex items-center justify-between">';
      html += `<p class="text-sm font-semibold text-slate-900">Rank ${esc(
        String(rank || "")
      )}</p>`;
      html += `<p class="text-sm text-slate-700">Score: <span class="font-semibold">${esc(
        String(score || "")
      )}</span></p>`;
      html += "</div>";
      if (it.ai_summary) {
        html += `<p class="text-sm text-slate-600 mt-2">${esc(
          it.ai_summary
        )}</p>`;
      }
      html += "</div>";

      html += "</div>";
    });
    html += "</div>";
    listEl.innerHTML = html;
  }

  function onRoleChange() {
    const jobRoleId = roleSelect ? roleSelect.value : "";
    if (!jobRoleId) {
      if (linkInput) {
        linkInput.value = "Select a job role to generate the link.";
      }
      if (copyBtn) copyBtn.disabled = true;
      updateSummary("");
      return;
    }

    const link = buildPublicLink(jobRoleId);
    if (linkInput) linkInput.value = link;
    if (copyBtn) copyBtn.disabled = false;

    updateSummary(jobRoleId);
    loadLatestRanking(jobRoleId);
  }

  function runAnalysis() {
    if (!roleSelect) return;
    const jobRoleId = roleSelect.value;
    if (!jobRoleId) {
      alert("Please select a job role first.");
      return;
    }
    if (runBtn) {
      runBtn.disabled = true;
      runBtn.textContent = "Running…";
    }
    post("/api/candidate-analytics/analyze", {
      job_role_id: jobRoleId,
      public_only: true,
    })
      .then((res) => {
        if (res && res.error) {
          alert(res.error);
        } else {
          loadLatestRanking(jobRoleId);
        }
      })
      .catch(() => {
        alert("Failed to analyze. Please try again.");
      })
      .finally(() => {
        if (runBtn) {
          runBtn.disabled = false;
          runBtn.textContent = "Run AI analysis & rank";
        }
      });
  }

  if (roleSelect) roleSelect.addEventListener("change", onRoleChange);
  if (runBtn) runBtn.addEventListener("click", runAnalysis);

  if (copyBtn && linkInput) {
    copyBtn.addEventListener("click", () => {
      const val = linkInput.value || "";
      if (!val) return;
      navigator.clipboard
        .writeText(val)
        .then(() => {
          copyBtn.textContent = "Copied!";
          setTimeout(() => {
            copyBtn.textContent = "Copy link";
          }, 1200);
        })
        .catch(() => {});
    });
  }

  loadRoles();
})();

