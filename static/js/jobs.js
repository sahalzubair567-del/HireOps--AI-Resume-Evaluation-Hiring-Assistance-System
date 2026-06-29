// jobs.js
// Handles job list filters and job form skill interactions + preview

(function () {
  // List filters
  const table = document.querySelector("[data-jobs-table]");
  if (table) {
    const rows = Array.from(table.querySelectorAll("[data-job-row]"));
    const searchInput = document.querySelector("[data-jobs-search]");
    const statusFilter = document.querySelector("[data-filter-status]");
    const deptFilter = document.querySelector("[data-filter-department]");

    function applyFilters() {
      const term = (searchInput && searchInput.value.toLowerCase()) || "";
      const status = (statusFilter && statusFilter.value) || "";
      const dept = (deptFilter && deptFilter.value) || "";

      rows.forEach((row) => {
        const titleCell = row.querySelector("td");
        const text = titleCell ? titleCell.textContent.toLowerCase() : "";
        const rowStatus = row.getAttribute("data-job-status") || "";
        const rowDept = row.getAttribute("data-job-department") || "";

        const matchesTerm = !term || text.includes(term);
        const matchesStatus = !status || rowStatus === status;
        const matchesDept = !dept || rowDept === dept;

        row.classList.toggle("hidden", !(matchesTerm && matchesStatus && matchesDept));
      });
    }

    [searchInput, statusFilter, deptFilter].forEach((el) => {
      if (!el) return;
      el.addEventListener("input", applyFilters);
      el.addEventListener("change", applyFilters);
    });
  }

  // Job form dynamic skills + preview
  const form = document.querySelector("[data-job-form]");
  if (!form) return;

  const skillList = form.querySelector("[data-skill-list]");
  const addSkillBtn = form.querySelector("[data-add-skill]");
  const previewTitle = form.querySelector("[data-preview-title]");
  const previewDept = form.querySelector("[data-preview-dept]");
  const previewDesc = form.querySelector("[data-preview-desc]");
  const previewSkills = form.querySelector("[data-preview-skills]");

  function createSkillRow(name = "", weight = 1) {
    const div = document.createElement("div");
    div.className = "flex items-center gap-2";
    div.setAttribute("data-skill-row", "");
    div.innerHTML = `
      <input
        type="text"
        name="skill_name[]"
        class="flex-1 rounded-lg border border-slate-200 bg-slate-50 px-2 py-1.5 text-[0.7rem] focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        placeholder="Skill name"
        value="${name}"
      />
      <button
        type="button"
        class="p-1 rounded-full text-slate-400 hover:text-rose-500 hover:bg-rose-50"
        data-remove-skill
      >
        <i data-lucide="x" class="h-3 w-3"></i>
      </button>
    `;
    return div;
  }

  function refreshPreviewSkills() {
    if (!previewSkills) return;
    previewSkills.innerHTML = "";
    const rows = skillList.querySelectorAll("[data-skill-row]");
    rows.forEach((row) => {
      const input = row.querySelector('input[name="skill_name[]"]');
      if (!input || !input.value) return;
      const pill = document.createElement("span");
      pill.className =
        "inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[0.65rem] text-slate-700";
      pill.textContent = input.value;
      previewSkills.appendChild(pill);
    });
  }

  // (weights removed) keep UI simple

  if (addSkillBtn && skillList) {
    addSkillBtn.addEventListener("click", () => {
      const row = createSkillRow();
      skillList.appendChild(row);
      if (window.lucide) window.lucide.createIcons();
    });
  }

  if (skillList) {
    skillList.addEventListener("click", (e) => {
      const target = e.target;
      if (!(target instanceof HTMLElement)) return;

      if (target.matches("[data-remove-skill]") || target.closest("[data-remove-skill]")) {
        const btn = target.closest("[data-remove-skill]");
        const row = btn.closest("[data-skill-row]");
        if (row && skillList.children.length > 1) {
          row.remove();
          refreshPreviewSkills();
        }
        return;
      }

    });

    skillList.addEventListener("input", (e) => {
      const target = e.target;
      if (target instanceof HTMLInputElement && target.name === "skill_name[]") {
        refreshPreviewSkills();
      }
    });

    refreshPreviewSkills();
  }

  // Live job preview text
  function bindPreview(inputSelector, previewEl) {
    const input = form.querySelector(inputSelector);
    if (!input || !previewEl) return;
    input.addEventListener("input", () => {
      previewEl.textContent = input.value || previewEl.dataset.placeholder || previewEl.textContent;
    });
  }

  if (previewTitle && previewDept && previewDesc) {
    bindPreview('input[name="title"]', previewTitle);
    bindPreview('input[name="location"]', previewDept);
    const descInput = form.querySelector('textarea[name="description"]');
    if (descInput) {
      descInput.addEventListener("input", () => {
        previewDesc.textContent = descInput.value || "Short summary of the role will appear here.";
      });
    }
  }
})();

