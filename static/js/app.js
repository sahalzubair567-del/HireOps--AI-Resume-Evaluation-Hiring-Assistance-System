// Global JS utilities for HireOps

// Global confirm helper
window.confirmAction = function (message) {
  return window.confirm(message || "Are you sure?");
};

// Copy to clipboard utility
window.copyToClipboard = function (text, onSuccess) {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      if (typeof onSuccess === "function") onSuccess();
    })
    .catch(() => {
      // Fallback: do nothing for now
    });
};

// Loading spinner helpers
window.showLoading = function (id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("hidden");
};

window.hideLoading = function (id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("hidden");
};

// Avatar color initialization
window.initAvatars = function () {
  const avatars = document.querySelectorAll(".avatar-initials[data-name]");
  const colors = [
    "#4f46e5",
    "#0891b2",
    "#059669",
    "#d97706",
    "#dc2626",
    "#7c3aed",
    "#db2777",
    "#0284c7",
  ];

  avatars.forEach((avatarEl) => {
    const name = avatarEl.getAttribute("data-name") || "";
    if (!name) return;
    const idx = (name.charCodeAt(0) || 0) % colors.length;
    avatarEl.style.backgroundColor = colors[idx];
  });
};

// Auto-dismiss flash messages and init avatars
document.addEventListener("DOMContentLoaded", () => {
  const flashes = document.querySelectorAll("[data-flash]");
  if (flashes.length) {
    setTimeout(() => {
      flashes.forEach((el) => el.classList.add("opacity-0", "translate-y-2"));
      setTimeout(() => flashes.forEach((el) => el.remove()), 300);
    }, 4000);
  }

  if (typeof window.initAvatars === "function") {
    window.initAvatars();
  }
});

// Confirm dialog for delete actions
document.addEventListener("click", (event) => {
  const target = event.target;
  if (target instanceof HTMLElement && target.matches("[data-confirm]")) {
    const message = target.getAttribute("data-confirm") || "Are you sure?";
    if (!window.confirmAction(message)) {
      event.preventDefault();
    }
  }
});

// Keyboard shortcuts
document.addEventListener("keydown", (event) => {
  // "/" focuses search input on list pages
  if (event.key === "/" && !event.target.closest("input, textarea")) {
    const search = document.querySelector("[data-global-search]");
    if (search instanceof HTMLInputElement) {
      event.preventDefault();
      search.focus();
    }
  }

  // Escape closes any open modal with [data-modal]
  if (event.key === "Escape") {
    const openModal = document.querySelector("[data-modal].flex");
    if (openModal instanceof HTMLElement) {
      openModal.classList.add("hidden");
      openModal.classList.remove("flex");
    }
  }
});

