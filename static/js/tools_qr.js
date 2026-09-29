(function () {
  "use strict";

  var script = document.currentScript;
  var generateUrl = script.getAttribute("data-generate-url");

  var state = {
    type: "website",
    frame: "none",
    shape: "square",
    fg: "#000000",
    bg: "#ffffff",
  };

  var img = document.getElementById("qr-preview-img");
  var empty = document.getElementById("qr-preview-empty");
  var frameEl = document.getElementById("qr-preview-frame");
  var downloadBtn = document.getElementById("qr-download-btn");
  var downloadToggle = document.getElementById("qr-download-toggle");
  var downloadMenu = document.getElementById("qr-download-menu");
  var downloadLabel = document.getElementById("qr-download-label");

  var FRAME_CLASSES = [
    "frame-bottom", "frame-top-pointer", "frame-badge", "frame-shake", "frame-torn",
    "frame-cursive", "frame-cursive-arrow", "frame-bag", "frame-box", "frame-cup", "frame-scooter",
  ];

  function escapeVCard(s) {
    return (s || "").replace(/([\\;,])/g, "\\$1");
  }

  function buildData() {
    switch (state.type) {
      case "website": {
        var url = document.getElementById("qr-field-website").value.trim();
        if (!url) return "";
        if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(url)) url = "https://" + url;
        return url;
      }
      case "text":
        return document.getElementById("qr-field-text").value.trim();
      case "vcard": {
        var name = document.getElementById("qr-field-vcard-name").value.trim();
        if (!name) return "";
        var org = document.getElementById("qr-field-vcard-org").value.trim();
        var tel = document.getElementById("qr-field-vcard-tel").value.trim();
        var email = document.getElementById("qr-field-vcard-email").value.trim();
        var url2 = document.getElementById("qr-field-vcard-url").value.trim();
        var lines = ["BEGIN:VCARD", "VERSION:3.0", "FN:" + escapeVCard(name)];
        if (org) lines.push("ORG:" + escapeVCard(org));
        if (tel) lines.push("TEL:" + escapeVCard(tel));
        if (email) lines.push("EMAIL:" + escapeVCard(email));
        if (url2) lines.push("URL:" + escapeVCard(url2));
        lines.push("END:VCARD");
        return lines.join("\n");
      }
      default:
        return "";
    }
  }

  function buildUrl(download, format) {
    var params = new URLSearchParams({
      data: buildData(),
      fg: state.fg,
      bg: state.bg,
      shape: state.shape,
      format: format || "png",
    });
    if (download) params.set("download", "1");
    return generateUrl + "?" + params.toString();
  }

  function updatePreview() {
    var data = buildData();
    if (!data) {
      img.style.display = "none";
      empty.style.display = "block";
      downloadBtn.disabled = true;
      downloadToggle.disabled = true;
      return;
    }
    img.src = buildUrl(false, "png");
    img.style.display = "block";
    empty.style.display = "none";
    downloadBtn.disabled = false;
    downloadToggle.disabled = false;
  }

  function triggerDownload(format) {
    var a = document.createElement("a");
    a.href = buildUrl(true, format);
    document.body.appendChild(a);
    a.click();
    a.remove();
    downloadMenu.classList.remove("open");
  }

  // ---------------- Content type tabs ----------------
  var typeTabs = document.querySelectorAll(".qr-type-tab");
  var contentPanels = document.querySelectorAll(".qr-content-panel");
  typeTabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      typeTabs.forEach(function (t) { t.classList.toggle("active", t === tab); });
      contentPanels.forEach(function (p) { p.classList.toggle("active", p.dataset.content === tab.dataset.type); });
      state.type = tab.dataset.type;
      updatePreview();
    });
  });

  // ---------------- Collapsible sections ----------------
  document.querySelectorAll("[data-toggle-section]").forEach(function (head) {
    head.addEventListener("click", function () {
      head.closest(".qr-section").classList.toggle("collapsed");
    });
  });

  // ---------------- Design sub-tabs ----------------
  var subtabs = document.querySelectorAll(".qr-subtab");
  var subpanels = document.querySelectorAll(".qr-subpanel");
  subtabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
      subtabs.forEach(function (t) { t.classList.toggle("active", t === tab); });
      subpanels.forEach(function (p) { p.classList.toggle("active", p.dataset.subpanel === tab.dataset.subtab); });
    });
  });

  // ---------------- Frame picker ----------------
  var frameTiles = document.querySelectorAll(".qr-frame-tile");
  frameTiles.forEach(function (tile) {
    tile.addEventListener("click", function () {
      frameTiles.forEach(function (t) { t.classList.toggle("active", t === tile); });
      state.frame = tile.dataset.frame;
      FRAME_CLASSES.forEach(function (c) { frameEl.classList.remove(c); });
      if (state.frame !== "none") frameEl.classList.add("frame-" + state.frame);
    });
  });

  // ---------------- Shape picker ----------------
  var shapeOpts = document.querySelectorAll(".qr-shape-opt");
  shapeOpts.forEach(function (opt) {
    opt.addEventListener("click", function () {
      shapeOpts.forEach(function (o) { o.classList.toggle("active", o === opt); });
      state.shape = opt.dataset.shape;
      updatePreview();
    });
  });

  // ---------------- Colors ----------------
  var fgInput = document.getElementById("qr-fg-color");
  var bgInput = document.getElementById("qr-bg-color");
  var fgHex = document.getElementById("qr-fg-hex");
  var bgHex = document.getElementById("qr-bg-hex");
  fgInput.addEventListener("input", function () {
    state.fg = fgInput.value;
    fgHex.textContent = fgInput.value;
    updatePreview();
  });
  bgInput.addEventListener("input", function () {
    state.bg = bgInput.value;
    bgHex.textContent = bgInput.value;
    updatePreview();
  });

  // ---------------- Content field inputs (live preview) ----------------
  [
    "qr-field-website", "qr-field-text",
    "qr-field-vcard-name", "qr-field-vcard-org", "qr-field-vcard-tel", "qr-field-vcard-email", "qr-field-vcard-url",
  ].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("input", updatePreview);
  });

  // ---------------- Download button + dropdown ----------------
  downloadBtn.addEventListener("click", function () {
    triggerDownload(downloadLabel.textContent.trim().endsWith("JPG") ? "jpg" : "png");
  });
  downloadToggle.addEventListener("click", function (e) {
    e.stopPropagation();
    downloadMenu.classList.toggle("open");
  });
  downloadMenu.querySelectorAll("button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      downloadLabel.textContent = "ดาวน์โหลด " + btn.dataset.format.toUpperCase();
      triggerDownload(btn.dataset.format);
    });
  });
  document.addEventListener("click", function (e) {
    if (!downloadMenu.contains(e.target) && e.target !== downloadToggle) {
      downloadMenu.classList.remove("open");
    }
  });

  updatePreview();
})();
