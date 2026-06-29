// analytics.js
// Renders charts and the job performance table on /analytics/ using /analytics/data

(function () {
  const page = document.querySelector("[data-analytics-page]");
  if (!page || typeof Chart === "undefined") return;

  function fetchAnalytics() {
    return fetch("/analytics/data", { credentials: "same-origin" })
      .then((r) => r.json())
      .then((json) => (json && json.data) || {});
  }

  function updateStats(data) {
    const total = document.getElementById("an-total-candidates");
    const avg = document.getElementById("an-avg-score");
    const rate = document.getElementById("an-hiring-rate");
    const job = document.getElementById("an-most-active-job");

    if (total) total.textContent = String(data.total_candidates || 0);
    if (avg) avg.textContent = String(Math.round(data.average_score || 0));
    if (rate) rate.textContent = `${Math.round(data.hiring_rate || 0)}%`;
    if (job) job.textContent = data.most_active_job || "N/A";
  }

  function makeTopSkillsChart(data) {
    const ctx = document.getElementById("an-top-skills");
    if (!ctx) return;
    const items = data.top_skills || [];
    if (!items.length) return;

    const labels = items.map((x) => x.skill);
    const values = items.map((x) => x.count);

    new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Candidates mentioning skill",
            data: values,
            backgroundColor: "rgba(56, 189, 248, 0.6)",
            borderColor: "rgb(56, 189, 248)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: { ticks: { font: { size: 10 } } },
          y: { beginAtZero: true, precision: 0 },
        },
      },
    });
  }

  function makeScoreDistributionChart(data) {
    const ctx = document.getElementById("an-score-distribution");
    if (!ctx) return;
    const dist = data.score_distribution || {};
    const labels = ["Poor", "Average", "Good", "Excellent"];
    const values = labels.map((k) => dist[k] || 0);

    if (!values.some((v) => v > 0)) return;

    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: ["#f97373", "#facc15", "#38bdf8", "#22c55e"],
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" },
        },
      },
    });
  }

  function makeCandidatesPerJobChart(data) {
    const ctx = document.getElementById("an-candidates-per-job");
    if (!ctx) return;
    const items = data.candidates_per_job || [];
    if (!items.length) return;

    const labels = items.map((x) => x.job_title || "Job");
    const values = items.map((x) => x.count || 0);

    new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: "Candidates",
            data: values,
            backgroundColor: "rgba(148, 163, 184, 0.7)",
            borderColor: "rgb(148, 163, 184)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: { beginAtZero: true, precision: 0 },
        },
      },
    });
  }

  fetchAnalytics()
    .then((data) => {
      updateStats(data);
      makeTopSkillsChart(data);
      makeScoreDistributionChart(data);
      makeCandidatesPerJobChart(data);
    })
    .catch(() => {
      // If analytics API fails, leave server-rendered numbers as-is and keep canvases empty.
    });
})();

