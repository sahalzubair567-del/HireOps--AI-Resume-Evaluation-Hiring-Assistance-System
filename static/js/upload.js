// upload.js
// Handles drag & drop resume upload and progress UI

(function () {
  const form = document.querySelector("[data-upload-form]");
  if (!form) return;

  const dropzone = form.querySelector("[data-dropzone]");
  const browseButton = form.querySelector("[data-browse-button]");
  const input = document.getElementById("resumes-input");
  const fileListEl = form.querySelector("[data-file-list]");
  const fileCountEl = form.querySelector("[data-file-count]");
  const progressSection = form.querySelector("[data-progress-section]");
  const progressBar = form.querySelector("[data-progress-bar]");
  const progressCount = form.querySelector("[data-progress-count]");
  const progressTotal = form.querySelector("[data-progress-total]");
  const progressItems = form.querySelector("[data-progress-items]");
  const progressComplete = form.querySelector("[data-progress-complete]");

  let files = [];

  function updateFileList() {
    fileListEl.innerHTML = "";
    files.forEach((file, index) => {
      const li = document.createElement("li");
      li.className = "flex items-center justify-between py-1";
      li.innerHTML = `
        <div class="flex flex-col">
          <span class="text-slate-800">${file.name}</span>
          <span class="text-[0.65rem] text-slate-500">${(file.size / 1024).toFixed(1)} KB</span>
        </div>
        <button type="button" class="text-[0.7rem] text-rose-500 hover:text-rose-600" data-remove-index="${index}">
          Remove
        </button>
      `;
      fileListEl.appendChild(li);
    });
    fileCountEl.textContent = `${files.length} files selected`;
  }

  function addFiles(newFiles) {
    const maxFiles = 20;
    for (const f of newFiles) {
      const ext = (f.name.split(".").pop() || "").toLowerCase();
      if (!["pdf", "docx"].includes(ext)) {
        alert("Only PDF and DOCX files are allowed.");
        continue;
      }
      if (files.length >= maxFiles) {
        alert("You can upload a maximum of 20 files at a time.");
        break;
      }
      files.push(f);
    }
    updateFileList();
  }

  if (browseButton && input) {
    browseButton.addEventListener("click", () => input.click());
    input.addEventListener("change", (e) => {
      const target = e.target;
      if (!(target instanceof HTMLInputElement) || !target.files) return;
      addFiles(Array.from(target.files));
      target.value = "";
    });
  }

  if (dropzone) {
    ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    ["dragenter", "dragover"].forEach((eventName) => {
      dropzone.addEventListener(eventName, () => {
        dropzone.classList.add("border-indigo-400", "bg-indigo-50/40");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropzone.addEventListener(eventName, () => {
        dropzone.classList.remove("border-indigo-400", "bg-indigo-50/40");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      if (!dt || !dt.files) return;
      addFiles(Array.from(dt.files));
    });
  }

  fileListEl.addEventListener("click", (e) => {
    const target = e.target;
    if (target instanceof HTMLElement && target.hasAttribute("data-remove-index")) {
      const idx = parseInt(target.getAttribute("data-remove-index") || "0", 10);
      files.splice(idx, 1);
      updateFileList();
    }
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    if (!files.length) {
      alert("Please select at least one resume file.");
      return;
    }

    const customEndpoint = form.getAttribute("data-upload-endpoint");
    let endpoint = customEndpoint || "";

    if (!endpoint) {
      // Authenticated recruiter upload path uses job_id from the dashboard page.
      const jobId = document
        .querySelector("[data-job-id]")
        ?.getAttribute("data-job-id");
      if (!jobId) {
        alert("Missing job ID.");
        return;
      }
      endpoint = `/candidates/upload/${jobId}`;
    }

    progressSection.classList.remove("hidden");
    progressItems.innerHTML = "";
    progressCount.textContent = "0";
    progressTotal.textContent = String(files.length);
    progressBar.style.width = "0%";
    progressComplete.classList.add("hidden");

    const formData = new FormData();
    files.forEach((file) => formData.append("resumes", file));

    fetch(endpoint, {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) {
          alert(data.error || "Upload failed.");
          return;
        }

        let processed = 0;
        files.forEach((file) => {
          const li = document.createElement("li");
          li.className = "flex items-center justify-between";
          li.innerHTML = `
            <span>${file.name}</span>
            <span class="text-[0.65rem] text-emerald-600">Done</span>
          `;
          progressItems.appendChild(li);
          processed += 1;
        });

        progressCount.textContent = String(processed);
        const pct = (processed / files.length) * 100;
        progressBar.style.width = `${pct}%`;
        progressComplete.classList.remove("hidden");
      })
      .catch(() => {
        alert("Upload failed.");
      });
  });
})();

