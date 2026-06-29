// pipeline.js
// Handles HTML5 drag and drop across pipeline columns and status updates

(function () {
  const board = document.querySelector("[data-pipeline]");
  if (!board) return;

  const columns = board.querySelectorAll("[data-pipeline-column]");

  function refreshCounts() {
    columns.forEach((col) => {
      const status = col.getAttribute("data-status");
      const list = col.querySelector("[data-dropzone]");
      const countEl = col.querySelector("[data-column-count]");
      if (!list || !countEl) return;
      const cards = Array.from(list.querySelectorAll("[data-candidate-card]")).filter((el) => {
        return !(el instanceof HTMLElement) || !el.classList.contains("hidden");
      });
      countEl.textContent = String(cards.length);
    });
  }

  refreshCounts();

  // Filter by job
  const jobFilter = board.querySelector("[data-pipeline-job-filter]");
  if (jobFilter instanceof HTMLSelectElement) {
    jobFilter.addEventListener("change", () => {
      const jobId = jobFilter.value;
      const url = new URL(window.location.href);
      if (jobId) url.searchParams.set("job_id", jobId);
      else url.searchParams.delete("job_id");
      window.location.href = url.toString();
    });
  }

  let draggedId = null;

  board.addEventListener("dragstart", (e) => {
    const target = e.target;
    if (!(target instanceof HTMLElement) || !target.matches("[data-candidate-card]")) return;
    draggedId = target.getAttribute("data-candidate-id");
    e.dataTransfer?.setData("text/plain", draggedId || "");
    e.dataTransfer?.setDragImage(target, 50, 20);
  });

  board.addEventListener("dragover", (e) => {
    if (!(e.target instanceof HTMLElement)) return;
    if (!e.target.closest("[data-dropzone]")) return;
    e.preventDefault();
    const col = e.target.closest("[data-pipeline-column]");
    if (col) col.classList.add("ring-2", "ring-indigo-300");
  });

  board.addEventListener("dragleave", (e) => {
    if (!(e.target instanceof HTMLElement)) return;
    const col = e.target.closest("[data-pipeline-column]");
    if (col) col.classList.remove("ring-2", "ring-indigo-300");
  });

  board.addEventListener("drop", (e) => {
    if (!(e.target instanceof HTMLElement)) return;
    const dropzone = e.target.closest("[data-dropzone]");
    const col = e.target.closest("[data-pipeline-column]");
    if (!dropzone || !col) return;
    e.preventDefault();
    col.classList.remove("ring-2", "ring-indigo-300");

    const status = col.getAttribute("data-status");
    const id = draggedId || e.dataTransfer?.getData("text/plain");
    if (!id || !status) return;

    const card = board.querySelector(
      `[data-candidate-card][data-candidate-id="${id}"]`
    );
    if (!card) return;

    dropzone.appendChild(card);
    refreshCounts();

    const formData = new FormData();
    formData.append("status", status);

    fetch(`/candidates/${id}/status`, {
      method: "POST",
      body: formData,
    }).catch(() => {});
  });
})();

