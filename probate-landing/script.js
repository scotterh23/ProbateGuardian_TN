(function () {
  var yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  var pdfBtn = document.getElementById("roadmap-pdf-btn");
  if (pdfBtn) {
    pdfBtn.addEventListener("click", function () {
      window.print();
    });
  }

  var shareBtn = document.getElementById("roadmap-share-btn");
  var shareNote = document.getElementById("roadmap-share-note");
  if (shareBtn) {
    shareBtn.addEventListener("click", function () {
      var url = window.location.href;
      var title = "Probate Family Roadmap – Probate Guardians TN";
      var text = "7 simple steps to make probate season easier — free guide for Middle Tennessee families.";
      function showNote(msg) {
        if (shareNote) {
          shareNote.textContent = msg;
          shareNote.hidden = false;
        }
      }
      if (navigator.share) {
        navigator.share({ title: title, text: text, url: url }).catch(function () {});
      } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () {
          showNote("Link copied — paste into a text or email for family.");
        }).catch(function () {
          showNote("Copy this link: " + url);
        });
      } else {
        showNote("Copy this link: " + url);
      }
    });
  }

  var modal = document.getElementById("guardian-kit-modal");
  if (!modal) {
    return;
  }

  var formPanel = document.getElementById("gk-modal-form-panel");
  var successPanel = document.getElementById("gk-modal-success-panel");
  var modalForm = document.getElementById("guardian-kit-modal-form");
  var modalError = document.getElementById("gk-modal-error");
  var triggers = document.querySelectorAll(".js-guardian-kit-trigger");
  var closeEls = modal.querySelectorAll("[data-gk-close]");
  var copyCrmBtn = document.getElementById("gk-copy-crm-btn");
  var copyFeedback = document.getElementById("gk-copy-feedback");
  var lastFocus = null;
  var lastLead = null;

  function showError(message) {
    if (!modalError) return;
    modalError.textContent = message;
    modalError.classList.remove("hidden");
  }

  function clearError() {
    if (!modalError) return;
    modalError.textContent = "";
    modalError.classList.add("hidden");
  }

  function resetModal() {
    if (formPanel) formPanel.classList.remove("hidden");
    if (successPanel) successPanel.classList.add("hidden");
    clearError();
    if (modalForm) modalForm.reset();
  }

  function openModal() {
    lastFocus = document.activeElement;
    resetModal();
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("gk-modal-open");
    var firstInput = document.getElementById("gk-full-name");
    if (firstInput) {
      window.setTimeout(function () {
        firstInput.focus();
      }, 50);
    }
  }

  function closeModal() {
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("gk-modal-open");
    if (lastFocus && lastFocus.focus) {
      lastFocus.focus();
    }
  }

  function buildCrmCopy(lead) {
    var lines = [
      "Guardian Kit Lead — probateguardians.com",
      "Name: " + lead.fullName,
      "Email: " + lead.email,
      "Phone: " + (lead.phone || "—"),
      "County: " + lead.county,
      "Lead added to system — status: Kit Downloaded 🔥",
    ];
    return lines.join("\n");
  }

  function showSuccess(lead) {
    lastLead = lead;
    if (formPanel) formPanel.classList.add("hidden");
    if (successPanel) successPanel.classList.remove("hidden");
    if (copyFeedback) copyFeedback.classList.add("hidden");
    clearError();
    var downloadBtn = successPanel && successPanel.querySelector(".gk-modal-download");
    if (downloadBtn) {
      window.setTimeout(function () {
        downloadBtn.focus();
      }, 50);
    }
  }

  if (copyCrmBtn) {
    copyCrmBtn.addEventListener("click", function () {
      if (!lastLead) return;
      var text = buildCrmCopy(lastLead);
      function onCopied() {
        if (copyFeedback) {
          copyFeedback.classList.remove("hidden");
          window.setTimeout(function () {
            copyFeedback.classList.add("hidden");
          }, 2500);
        }
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(onCopied).catch(function () {
          window.prompt("Copy lead info:", text);
        });
      } else {
        window.prompt("Copy lead info:", text);
        onCopied();
      }
    });
  }

  triggers.forEach(function (trigger) {
    trigger.addEventListener("click", function (e) {
      e.preventDefault();
      openModal();
    });
  });

  closeEls.forEach(function (el) {
    el.addEventListener("click", closeModal);
  });

  document.addEventListener("keydown", function (e) {
    if (modal.hidden) return;
    if (e.key === "Escape") {
      closeModal();
    }
  });

  if (modalForm) {
    modalForm.addEventListener("submit", function (e) {
      e.preventDefault();
      clearError();

      if (!modalForm.reportValidity()) {
        return;
      }

      var data = new FormData(modalForm);
      var lead = {
        fullName: data.get("full-name") || "",
        email: data.get("email") || "",
        phone: data.get("phone") || "",
        county: data.get("county") || "",
      };
      var params = new URLSearchParams();
      params.append("form-name", "guardian-kit-lead");
      data.forEach(function (value, key) {
        if (key !== "bot-field" || value) {
          params.append(key, value);
        }
      });

      var submitBtn = modalForm.querySelector(".gk-modal-submit");
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Sending…";
      }

      fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params.toString(),
      })
        .then(function (res) {
          if (!res.ok) {
            throw new Error("submit failed");
          }
          showSuccess(lead);
        })
        .catch(function () {
          showError("Something went wrong. Please call or text (615) 669-7075 and we'll send your kit.");
        })
        .finally(function () {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = "Get your free Guardian Kit";
          }
        });
    });
  }

  var legacyForm = document.getElementById("guide-form");
  if (legacyForm) {
    legacyForm.addEventListener("submit", function (e) {
      e.preventDefault();
      openModal();
    });
  }
})();