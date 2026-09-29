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

  // ---------------- Temperature ----------------
  function initTemperature() {
    var valueEl = document.getElementById("temp-value");
    var unitEl = document.getElementById("temp-unit");
    if (!valueEl) return;

    function update() {
      var v = parseFloat(valueEl.value);
      var container = document.getElementById("temp-result");
      if (isNaN(v)) { container.innerHTML = ""; return; }
      var c;
      if (unitEl.value === "C") c = v;
      else if (unitEl.value === "F") c = (v - 32) * 5 / 9;
      else c = v - 273.15;
      var f = c * 9 / 5 + 32;
      var k = c + 273.15;
      container.innerHTML =
        row("Celsius (°C)", fmt(c, 2)) + row("Fahrenheit (°F)", fmt(f, 2)) + row("Kelvin (K)", fmt(k, 2));
    }
    valueEl.addEventListener("input", update);
    unitEl.addEventListener("change", update);
    update();
  }

  // ---------------- Capacity (base unit: kW) ----------------
  var CAPACITY_UNITS = {
    w: { label: "Watt (W)", factor: 0.001 },
    kw: { label: "Kilowatt (kW)", factor: 1 },
    btu: { label: "BTU/hr", factor: 1 / 3412.142 },
    kcal: { label: "kcal/hr", factor: 1 / 860.421 },
    tr: { label: "Ton of Refrigeration (TR)", factor: 3.51685 },
  };

  function initCapacity() {
    var valueEl = document.getElementById("cap-value");
    var unitEl = document.getElementById("cap-unit");
    if (!valueEl) return;

    function update() {
      var v = parseFloat(valueEl.value);
      if (isNaN(v)) { document.getElementById("cap-result").innerHTML = ""; return; }
      var base = v * CAPACITY_UNITS[unitEl.value].factor;
      renderUnitList("cap-result", base, CAPACITY_UNITS, 3);
    }
    valueEl.addEventListener("input", update);
    unitEl.addEventListener("change", update);
    update();
  }

  // ---------------- Salary ----------------
  function initSalary() {
    var ids = ["sal-monthly", "sal-workdays", "sal-hours", "sal-ot-normal", "sal-holiday", "sal-ot-holiday"];
    var els = {};
    ids.forEach(function (id) { els[id] = document.getElementById(id); });
    if (!els["sal-monthly"]) return;

    function update() {
      var monthly = parseFloat(els["sal-monthly"].value) || 0;
      var workdays = parseFloat(els["sal-workdays"].value) || 0;
      var hoursPerDay = parseFloat(els["sal-hours"].value) || 0;
      var otNormal = parseFloat(els["sal-ot-normal"].value) || 0;
      var holidayHours = parseFloat(els["sal-holiday"].value) || 0;
      var otHoliday = parseFloat(els["sal-ot-holiday"].value) || 0;

      var daily = workdays > 0 ? monthly / workdays : 0;
      var hourly = hoursPerDay > 0 ? daily / hoursPerDay : 0;
      var otNormalPay = hourly * 1.5 * otNormal;
      var holidayPay = hourly * 1.0 * holidayHours;
      var otHolidayPay = hourly * 3.0 * otHoliday;

      document.getElementById("sal-result").innerHTML =
        row("อัตรารายวัน", fmt(daily, 2) + " บาท") +
        row("อัตรารายชั่วโมง", fmt(hourly, 2) + " บาท") +
        row("ค่า OT วันทำงาน (×1.5)", fmt(otNormalPay, 2) + " บาท") +
        row("ค่าทำงานวันหยุด (×1.0)", fmt(holidayPay, 2) + " บาท") +
        row("ค่า OT วันหยุด (×3.0)", fmt(otHolidayPay, 2) + " บาท") +
        row("รวมเงินพิเศษ", fmt(otNormalPay + holidayPay + otHolidayPay, 2) + " บาท");
    }
    ids.forEach(function (id) { els[id].addEventListener("input", update); });
    update();
  }

  // ---------------- Unit Converter ----------------
  var UNIT_CATEGORIES = {
    length: {
      units: {
        mm: { label: "มิลลิเมตร (mm)", factor: 0.001 },
        cm: { label: "เซนติเมตร (cm)", factor: 0.01 },
        m: { label: "เมตร (m)", factor: 1 },
        km: { label: "กิโลเมตร (km)", factor: 1000 },
        inch: { label: "นิ้ว (in)", factor: 0.0254 },
        ft: { label: "ฟุต (ft)", factor: 0.3048 },
        yard: { label: "หลา (yd)", factor: 0.9144 },
        mile: { label: "ไมล์ (mi)", factor: 1609.344 },
      },
    },
    weight: {
      units: {
        g: { label: "กรัม (g)", factor: 0.001 },
        kg: { label: "กิโลกรัม (kg)", factor: 1 },
        lb: { label: "ปอนด์ (lb)", factor: 0.453592 },
        oz: { label: "ออนซ์ (oz)", factor: 0.0283495 },
        ton: { label: "ตัน (metric ton)", factor: 1000 },
      },
    },
    volume: {
      units: {
        ml: { label: "มิลลิลิตร (mL)", factor: 0.001 },
        l: { label: "ลิตร (L)", factor: 1 },
        m3: { label: "ลูกบาศก์เมตร (m³)", factor: 1000 },
        gallon: { label: "แกลลอน (US gal)", factor: 3.785412 },
        ft3: { label: "ลูกบาศก์ฟุต (ft³)", factor: 28.316846 },
      },
    },
    area: {
      units: {
        cm2: { label: "ตารางเซนติเมตร (cm²)", factor: 0.0001 },
        m2: { label: "ตารางเมตร (m²)", factor: 1 },
        rai: { label: "ไร่", factor: 1600 },
        km2: { label: "ตารางกิโลเมตร (km²)", factor: 1000000 },
        acre: { label: "เอเคอร์ (acre)", factor: 4046.8564 },
      },
    },
  };

  function initUnitConverter() {
    var categoryEl = document.getElementById("unit-category");
    var valueEl = document.getElementById("unit-value");
    var fromEl = document.getElementById("unit-from");
    if (!categoryEl) return;

    function populateUnits() {
      var units = UNIT_CATEGORIES[categoryEl.value].units;
      fromEl.innerHTML = "";
      Object.keys(units).forEach(function (key) {
        var opt = document.createElement("option");
        opt.value = key;
        opt.textContent = units[key].label;
        fromEl.appendChild(opt);
      });
    }

    function update() {
      var units = UNIT_CATEGORIES[categoryEl.value].units;
      var v = parseFloat(valueEl.value);
      if (isNaN(v) || !fromEl.value) { document.getElementById("unit-result").innerHTML = ""; return; }
      var base = v * units[fromEl.value].factor;
      renderUnitList("unit-result", base, units, 4);
    }

    categoryEl.addEventListener("change", function () { populateUnits(); update(); });
    valueEl.addEventListener("input", update);
    fromEl.addEventListener("change", update);

    populateUnits();
    update();
  }

  // ---------------- Percentage ----------------
  function initPercentage() {
    function bind(xId, yId, resultId, calc) {
      var xEl = document.getElementById(xId), yEl = document.getElementById(yId), resEl = document.getElementById(resultId);
      if (!xEl) return;
      function update() {
        var r = calc(parseFloat(xEl.value), parseFloat(yEl.value));
        resEl.textContent = r === null ? "—" : r;
      }
      xEl.addEventListener("input", update);
      yEl.addEventListener("input", update);
      update();
    }

    bind("pct1-x", "pct1-y", "pct1-result", function (x, y) {
      if (isNaN(x) || isNaN(y) || y === 0) return null;
      return fmt((x / y) * 100, 2) + "%";
    });
    bind("pct2-pct", "pct2-x", "pct2-result", function (p, x) {
      if (isNaN(p) || isNaN(x)) return null;
      return fmt((p / 100) * x, 2);
    });
    bind("pct3-x", "pct3-y", "pct3-result", function (x, y) {
      if (isNaN(x) || isNaN(y) || x === 0) return null;
      var change = ((y - x) / x) * 100;
      return (change > 0 ? "+" : "") + fmt(change, 2) + "%";
    });
  }

  // ---------------- Date & Time ----------------
  function parseLocalDate(str) {
    if (!str) return null;
    var parts = str.split("-");
    return new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
  }

  function todayStr() {
    var t = new Date();
    return t.getFullYear() + "-" + String(t.getMonth() + 1).padStart(2, "0") + "-" + String(t.getDate()).padStart(2, "0");
  }

  function initDateTime() {
    var startEl = document.getElementById("dt1-start");
    var endEl = document.getElementById("dt1-end");
    var resEl = document.getElementById("dt1-result");
    if (!startEl) return;

    function updateDiff() {
      var d1 = parseLocalDate(startEl.value), d2 = parseLocalDate(endEl.value);
      if (!d1 || !d2) { resEl.textContent = "—"; return; }
      var days = Math.round((d2 - d1) / 86400000);
      var abs = Math.abs(days);
      var years = Math.floor(abs / 365.25);
      var months = Math.floor((abs % 365.25) / 30.44);
      resEl.textContent = (days < 0 ? "-" : "") + abs + " วัน (~" + years + " ปี " + months + " เดือน)";
    }
    startEl.addEventListener("change", updateDiff);
    endEl.addEventListener("change", updateDiff);

    var baseEl = document.getElementById("dt2-start");
    var daysEl = document.getElementById("dt2-days");
    var resultEl = document.getElementById("dt2-result");

    function updateAdd() {
      var base = parseLocalDate(baseEl.value);
      var n = parseInt(daysEl.value, 10);
      if (!base || isNaN(n)) { resultEl.textContent = "—"; return; }
      var result = new Date(base);
      result.setDate(result.getDate() + n);
      resultEl.textContent =
        String(result.getDate()).padStart(2, "0") + "/" +
        String(result.getMonth() + 1).padStart(2, "0") + "/" +
        result.getFullYear();
    }
    baseEl.addEventListener("change", updateAdd);
    daysEl.addEventListener("input", updateAdd);

    var t = todayStr();
    startEl.value = t;
    endEl.value = t;
    baseEl.value = t;
    updateDiff();
    updateAdd();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTemperature();
    initCapacity();
    initSalary();
    initUnitConverter();
    initPercentage();
    initDateTime();
  });
})();
