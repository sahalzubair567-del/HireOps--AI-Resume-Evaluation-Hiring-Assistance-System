// compare.js
// Handles score ring animation on compare page

(function () {
  document.querySelectorAll("[data-score-ring]").forEach((circle) => {
    const score = parseFloat(circle.getAttribute("data-score-ring") || "0");
    const maxDash = parseFloat(circle.getAttribute("stroke-dasharray") || "151");
    const targetOffset = maxDash * (1 - Math.min(Math.max(score, 0), 100) / 100);
    setTimeout(() => {
      circle.style.strokeDashoffset = String(targetOffset);
    }, 100);
  });
})();

