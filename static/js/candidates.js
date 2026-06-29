// candidates.js
// Handles candidate list filters, status updates, notes, compare bar, and confidence indicator

(function () {
  // Job detail candidate table interactions (status, compare bar, confidence, score animation)
  const jobDetail = document.querySelector("[data-candidates-table]");
  if (jobDetail) {
    const compareBar = document.querySelector("[data-compare-bar]");
    const compareCountEl = compareBar && compareBar.querySelector("[data-compare-count]");
    const compareGo = compareBar && compareBar.querySelector("[data-compare-go]");
    const jobContainer = document.querySelector("[data-job-id]");
    const jobId = jobContainer && jobContainer.getAttribute("data-job-id");

    function getSelectedCandidateIds() {
      const ids = [];
      const rows = jobDetail.querySelectorAll("[data-candidate-row]");
      rows.forEach((row) => {
        const checkbox = row.querySelector("[data-compare-checkbox]");
        if (checkbox instanceof HTMLInputElement && checkbox.checked) {
          const id = row.getAttribute("data-candidate-id");
          if (id) ids.push(id);
        }
      });
      return ids.slice(0, 3);
    }

    jobDetail.addEventListener("change", (e) => {
      const target = e.target;

      // Status dropdown change
      if (target instanceof HTMLSelectElement && target.matches("[data-status-select]")) {
        const row = target.closest("[data-candidate-row]");
        const candidateId = row && row.getAttribute("data-candidate-id");
        if (!candidateId) return;

        const formData = new FormData();
        formData.append("status", target.value);

        fetch(`/candidates/${candidateId}/status`, {
          method: "POST",
          body: formData,
        })
          .then((res) => res.json())
          .then((data) => {
            if (!data.success) {
              alert(data.error || "Failed to update status.");
            }
          })
          .catch(() => {
            alert("Failed to update status.");
          });
      }

      // Compare checkbox
      if (target instanceof HTMLInputElement && target.matches("[data-compare-checkbox]")) {
        const ids = getSelectedCandidateIds();
        if (!ids.length) {
          compareBar && compareBar.classList.add("hidden");
        } else {
          compareBar && compareBar.classList.remove("hidden");
          if (compareCountEl) {
            compareCountEl.textContent = `${ids.length} candidates selected for comparison`;
          }
        }
      }
    });

    if (compareGo) {
      compareGo.addEventListener("click", () => {
        const ids = getSelectedCandidateIds();
        if (!ids.length) return;
        const query = encodeURIComponent(ids.join(","));
        window.location.href = `/candidates/compare?ids=${query}`;
      });
    }

    // Confidence indicator based on resume text length
    jobDetail.querySelectorAll("[data-confidence]").forEach((el) => {
      const len = parseInt(el.getAttribute("data-confidence") || "0", 10);
      const labelEl = el.querySelector("[data-confidence-label]");
      const bar = el.querySelector("[data-confidence-bar]");
      let label = "Medium";
      let pct = 60;
      let color = "#f59e0b"; // amber

      if (len < 500) {
        label = "Low";
        pct = 35;
        color = "#f59e0b";
      } else if (len <= 1500) {
        label = "Medium";
        pct = 65;
        color = "#38bdf8"; // sky
      } else {
        label = "High";
        pct = 95;
        color = "#22c55e"; // green
      }

      if (labelEl) labelEl.textContent = label;
      if (bar instanceof HTMLElement) {
        bar.style.width = `${pct}%`;
        bar.style.backgroundColor = color;
      }
    });
  }

  // Candidate detail page interactions (status, notes, AI actions, email modal)
  const candidatePage = document.querySelector("[data-candidate-id]");
  if (candidatePage) {
    const candidateId = candidatePage.getAttribute("data-candidate-id");

    // Status change
    const statusSelect = candidatePage.querySelector("[data-status-select]");
    if (statusSelect instanceof HTMLSelectElement && candidateId) {
      statusSelect.addEventListener("change", () => {
        const formData = new FormData();
        formData.append("status", statusSelect.value);
        fetch(`/candidates/${candidateId}/status`, {
          method: "POST",
          body: formData,
        }).catch(() => {});
      });
    }

    // Notes
    const noteForm = candidatePage.querySelector("[data-note-form]");
    const notesList = candidatePage.querySelector("[data-notes-list]");
    if (noteForm && notesList && candidateId) {
      noteForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const textarea = noteForm.querySelector("textarea[name='note']");
        if (!(textarea instanceof HTMLTextAreaElement)) return;
        const text = textarea.value.trim();
        if (!text) return;

        const formData = new FormData();
        formData.append("note", text);
        fetch(`/candidates/${candidateId}/note`, {
          method: "POST",
          body: formData,
        })
          .then((res) => res.json())
          .then((data) => {
            if (!data.success || !data.note) {
              alert(data.error || "Failed to add note.");
              return;
            }
            const n = data.note;
            const div = document.createElement("div");
            div.className = "border border-slate-100 rounded-lg px-3 py-2";
            div.innerHTML = `
              <div class="flex items-center justify-between mb-1">
                <span class="font-medium text-slate-800">${n.recruiter_name}</span>
                <span class="text-[0.6rem] text-slate-400">${n.created_at || ""}</span>
              </div>
              <p class="text-slate-700 whitespace-pre-line">${n.note}</p>
            `;
            notesList.prepend(div);
            textarea.value = "";
          })
          .catch(() => {
            alert("Failed to add note.");
          });
      });
    }

    // Score ring animation on candidate detail
    candidatePage.querySelectorAll("[data-score-ring]").forEach((circle) => {
      const score = parseFloat(circle.getAttribute("data-score-ring") || "0");
      const maxDash = parseFloat(circle.getAttribute("stroke-dasharray") || "151");
      const targetOffset = maxDash * (1 - Math.min(Math.max(score, 0), 100) / 100);
      setTimeout(() => {
        circle.style.strokeDashoffset = String(targetOffset);
      }, 100);
    });

    // Confidence indicator on detail page
    candidatePage.querySelectorAll("[data-confidence]").forEach((el) => {
      const len = parseInt(el.getAttribute("data-confidence") || "0", 10);
      const labelEl = el.querySelector("[data-confidence-label]");
      const bar = el.querySelector("[data-confidence-bar]");
      let label = "Medium";
      let pct = 60;
      let color = "#f59e0b";

      if (len < 500) {
        label = "Low";
        pct = 35;
        color = "#f59e0b";
      } else if (len <= 1500) {
        label = "Medium";
        pct = 65;
        color = "#38bdf8";
      } else {
        label = "High";
        pct = 95;
        color = "#22c55e";
      }

      if (labelEl) labelEl.textContent = label;
      if (bar instanceof HTMLElement) {
        bar.style.width = `${pct}%`;
        bar.style.backgroundColor = color;
      }
    });

    // Generate interview questions
    const genQuestionsBtn = candidatePage.querySelector("[data-generate-questions]");
    const questionsList = candidatePage.querySelector("[data-question-list]");
    if (genQuestionsBtn && questionsList && candidateId) {
      // Preserve the original button content so we can restore after loading.
      if (!genQuestionsBtn.dataset.originalContent) {
        genQuestionsBtn.dataset.originalContent = genQuestionsBtn.innerHTML;
      }

      genQuestionsBtn.addEventListener("click", () => {
        const originalHtml = genQuestionsBtn.dataset.originalContent || genQuestionsBtn.innerHTML;

        // Show a clear loading state so recruiters know it's working.
        genQuestionsBtn.disabled = true;
        genQuestionsBtn.classList.add("opacity-60", "cursor-wait");
        genQuestionsBtn.innerHTML = `
          <span class="inline-flex items-center gap-1">
            <span class="inline-block h-3 w-3 rounded-full border-2 border-sky-100 border-t-white animate-spin"></span>
            <span>Generating questions...</span>
          </span>
        `;

        fetch(`/ai/generate-questions/${candidateId}`, {
          method: "POST",
        })
          .then((res) => res.json())
          .then((data) => {
            if (!data.success) {
              alert(data.error || "Failed to generate questions.");
              return;
            }
            questionsList.innerHTML = "";
            (data.questions || []).forEach((q) => {
              const div = document.createElement("div");
              div.className =
                "border border-slate-100 rounded-lg px-3 py-2 flex flex-col gap-1";
              div.setAttribute("data-question-item", "");
              div.setAttribute("data-category", q.category || "Technical");
              div.innerHTML = `
                <p class="text-slate-800">${q.question}</p>
                <div class="flex items-center gap-2 text-[0.6rem]">
                  <span class="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-slate-700">
                    ${q.category}
                  </span>
                  <span class="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-slate-700">
                    ${q.difficulty}
                  </span>
                </div>
              `;
              questionsList.appendChild(div);
            });
          })
          .catch(() => {
            alert("Failed to generate questions.");
          })
          .finally(() => {
            // Restore button so the user can click again if needed.
            genQuestionsBtn.disabled = false;
            genQuestionsBtn.classList.remove("opacity-60", "cursor-wait");
            genQuestionsBtn.innerHTML = originalHtml;
          });
      });
    }

    // Question filter tabs
    const filterGroup = candidatePage.querySelector("[data-question-filters]");
    if (filterGroup && questionsList) {
      filterGroup.addEventListener("click", (e) => {
        const target = e.target;
        if (!(target instanceof HTMLElement) || !target.hasAttribute("data-filter")) return;
        const filter = target.getAttribute("data-filter");
        Array.from(filterGroup.querySelectorAll("button")).forEach((btn) => {
          btn.classList.remove("bg-slate-900", "text-white");
        });
        target.classList.add("bg-slate-900", "text-white");

        questionsList.querySelectorAll("[data-question-item]").forEach((item) => {
          const cat = item.getAttribute("data-category");
          const show = filter === "All" || filter === cat;
          item.classList.toggle("hidden", !show);
        });
      });
    }

    // Email modal helpers
    const emailButtons = candidatePage.querySelectorAll("[data-generate-email]");
    const emailModal = document.querySelector("[data-email-modal]");
    const emailSubject = emailModal && emailModal.querySelector("[data-email-subject]");
    const emailBody = emailModal && emailModal.querySelector("[data-email-body]");
    const emailStatus = emailModal && emailModal.querySelector("[data-email-status]");
    const copyBtn = emailModal && emailModal.querySelector("[data-email-copy]");
    const tooltips = emailModal && emailModal.querySelectorAll("[data-tooltip]");
    const closeButtons = emailModal && emailModal.querySelectorAll("[data-modal-close]");

    function openModal() {
      if (!emailModal) return;
      emailModal.classList.remove("hidden");
      emailModal.classList.add("flex");
    }

    function closeModal() {
      if (!emailModal) return;
      emailModal.classList.add("hidden");
      emailModal.classList.remove("flex");
    }

    emailButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const type = btn.getAttribute("data-email-type") || "acceptance";
        if (!candidateId) return;

        const formData = new FormData();
        formData.append("type", type);

        if (emailStatus) emailStatus.textContent = "Generating email...";
        openModal();

        fetch(`/ai/generate-email/${candidateId}`, {
          method: "POST",
          body: formData,
        })
          .then((res) => res.json())
          .then((data) => {
            if (!data.success) {
              if (emailStatus) emailStatus.textContent = data.error || "Failed to generate email.";
              return;
            }
            if (emailSubject instanceof HTMLInputElement) {
              emailSubject.value = data.subject || "";
            }
            if (emailBody instanceof HTMLTextAreaElement) {
              emailBody.value = data.body || "";
            }
            if (emailStatus) emailStatus.textContent = "You can edit the email before sending.";
          })
          .catch(() => {
            if (emailStatus) emailStatus.textContent = "Failed to generate email.";
          });
      });
    });

    if (copyBtn && emailSubject && emailBody) {
      copyBtn.addEventListener("click", () => {
        const subject = emailSubject.value || "";
        const body = emailBody.value || "";
        const full = `Subject: ${subject}\n\n${body}`;
        if (window.copyToClipboard) {
          window.copyToClipboard(full, () => {
            tooltips &&
              tooltips.forEach((t) => {
                t.classList.add("visible");
                setTimeout(() => t.classList.remove("visible"), 1200);
              });
          });
        }
      });
    }

    if (closeButtons) {
      closeButtons.forEach((btn) => btn.addEventListener("click", closeModal));
    }
  }

  // Score ring animation in job list / tables
  document.querySelectorAll("[data-score-ring]").forEach((circle) => {
    const score = parseFloat(circle.getAttribute("data-score-ring") || "0");
    const maxDash = parseFloat(circle.getAttribute("stroke-dasharray") || "88");
    const targetOffset = maxDash * (1 - Math.min(Math.max(score, 0), 100) / 100);
    setTimeout(() => {
      circle.style.strokeDashoffset = String(targetOffset);
    }, 100);
  });
})();

