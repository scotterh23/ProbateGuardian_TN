(function () {
  var yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  var form = document.getElementById("guide-form");
  var success = document.getElementById("form-success");
  if (form && success) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      form.classList.add("hidden");
      success.classList.remove("hidden");
      success.scrollIntoView({ behavior: "smooth", block: "center" });
    });
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
})();