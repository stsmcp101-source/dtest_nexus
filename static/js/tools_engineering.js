(function () {
  "use strict";

  function fmt(n, d) {
    if (n === null || n === undefined || !isFinite(n)) return "—";
    return Number(n.toFixed(d)).toLocaleString("en-US", { maximumFractionDigits: d });
  }

  function row(label, val) {
    return '<div class="unit-result-row"><span class="u-lbl">' + label + '</span><span class="u-val">' + val + "</span></div>";
  }

  function renderUnitList(containerId, valueInBase, unitDefs, decimals) {
    var container = document.getElementById(containerId);
    if (!container) return;
    var html = "";
    Object.keys(unitDefs).forEach(function (key) {
      var def = unitDefs[key];
      html += row(def.label, fmt(valueInBase / def.factor, decimals));
    });
    container.innerHTML = html;
  }

  // ---------------- OEE ----------------
  function initOEE() {
    var ids = ["oee-planned", "oee-downtime", "oee-ideal-cycle", "oee-total-count", "oee-good-count"];
    var els = {};
    ids.forEach(function (id) { els[id] = document.getElementById(id); });
    if (!els["oee-planned"]) return;

    function update() {
      var planned = parseFloat(els["oee-planned"].value) || 0;
      var downtime = parseFloat(els["oee-downtime"].value) || 0;
      var idealCycleSec = parseFloat(els["oee-ideal-cycle"].value) || 0;
      var total = parseFloat(els["oee-total-count"].value) || 0;
      var good = parseFloat(els["oee-good-count"].value) || 0;

      var runTime = Math.max(planned - downtime, 0);
      var availability = planned > 0 ? runTime / planned : 0;
      var performanceRaw = runTime > 0 ? ((idealCycleSec / 60) * total) / runTime : 0;
      var performance = Math.min(performanceRaw, 1);
      var quality = total > 0 ? good / total : 0;
      var oee = availability * performance * quality;

      document.getElementById("oee-result").textContent = fmt(oee * 100, 1) + "%";
      document.getElementById("oee-breakdown").innerHTML =
        row("Availability", fmt(availability * 100, 1) + "%") +
        row("Performance", fmt(performanceRaw * 100, 1) + "%") +
        row("Quality", fmt(quality * 100, 1) + "%");

      var pct = oee * 100;
      var cls = pct >= 85 ? "ok" : pct >= 60 ? "warn" : "bad";
      var text = pct >= 85 ? "World Class (≥85%)" : pct >= 60 ? "พอใช้ (60–85%)" : "ต้องปรับปรุง (<60%)";
      document.getElementById("oee-badge").innerHTML = '<span class="calc-badge ' + cls + '">' + text + "</span>";
    }
    ids.forEach(function (id) { els[id].addEventListener("input", update); });
    update();
  }

  // ---------------- Cycle Time ----------------
  function initCycle() {
    var timeEl = document.getElementById("cycle-time");
    var countEl = document.getElementById("cycle-count");
    var resEl = document.getElementById("cycle-result");
    if (!timeEl) return;

    function update() {
      var t = parseFloat(timeEl.value), c = parseFloat(countEl.value);
      if (!t || !c) { resEl.textContent = "—"; return; }
      var cycle = t / c;
      resEl.textContent = fmt(cycle, 2) + " นาที/ชิ้น (" + fmt(cycle * 60, 1) + " วินาที/ชิ้น)";
    }
    timeEl.addEventListener("input", update);
    countEl.addEventListener("input", update);
    update();
  }

  // ---------------- Power ----------------
  function initPower() {
    var phaseEl = document.getElementById("power-phase");
    var vEl = document.getElementById("power-v");
    var iEl = document.getElementById("power-i");
    var pfEl = document.getElementById("power-pf");
    if (!phaseEl) return;

    function update() {
      var v = parseFloat(vEl.value) || 0;
      var i = parseFloat(iEl.value) || 0;
      var pf = parseFloat(pfEl.value);
      if (isNaN(pf)) pf = 1;
      var watts = phaseEl.value === "3" ? Math.sqrt(3) * v * i * pf : v * i * pf;
      document.getElementById("power-result").innerHTML =
        row("กำลังไฟฟ้า (W)", fmt(watts, 2)) +
        row("กำลังไฟฟ้า (kW)", fmt(watts / 1000, 3)) +
        row("กำลังไฟฟ้า (HP)", fmt(watts / 745.7, 3));
    }
    [phaseEl, vEl, iEl, pfEl].forEach(function (el) {
      el.addEventListener("input", update);
      el.addEventListener("change", update);
    });
    update();
  }

  // ---------------- Pressure (base unit: atm) ----------------
  var PRESSURE_UNITS = {
    atm: { label: "Atmosphere (atm)", factor: 1 },
    pa: { label: "Pascal (Pa)", factor: 1 / 101325 },
    kpa: { label: "Kilopascal (kPa)", factor: 1 / 101.325 },
    bar: { label: "Bar", factor: 1 / 1.01325 },
    psi: { label: "PSI", factor: 1 / 14.6959 },
    kgfcm2: { label: "kgf/cm²", factor: 1 / 1.03323 },
    mmhg: { label: "mmHg", factor: 1 / 760 },
  };

  function initPressure() {
    var valueEl = document.getElementById("press-value");
    var unitEl = document.getElementById("press-unit");
    if (!valueEl) return;

    function update() {
      var v = parseFloat(valueEl.value);
      if (isNaN(v)) { document.getElementById("press-result").innerHTML = ""; return; }
      var base = v * PRESSURE_UNITS[unitEl.value].factor;
      renderUnitList("press-result", base, PRESSURE_UNITS, 5);
    }
    valueEl.addEventListener("input", update);
    unitEl.addEventListener("change", update);
    update();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initOEE();
    initCycle();
    initPower();
    initPressure();
  });
})();
