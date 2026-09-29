(function () {
  "use strict";

  var root = document.getElementById("spdb-root");
  var TX_URL = root.getAttribute("data-tx-url");
  var IMPORT_URL = root.getAttribute("data-import-url");
  var CAN_EDIT = root.getAttribute("data-can-edit") === "1";

  function getCookie(name) {
    var match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return match ? decodeURIComponent(match.pop()) : "";
  }
  var CSRF = getCookie("csrftoken");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c];
    });
  }

  var parts = JSON.parse(document.getElementById("sp-parts-data").textContent);
  var txLog = JSON.parse(document.getElementById("sp-txlog-data").textContent);
  var mode = "receive", curPart = null, logFilter = "all";
  var importedRows = [], importMode = "merge";

  function apiPost(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": CSRF},
      body: JSON.stringify(payload),
    }).then(function (resp) {
      return resp.json().then(function (data) { return {status: resp.status, data: data}; });
    });
  }

  // ═══════════════════════════════════
  //  STATUS (logic: cur/min ≥ 50% = OK)
  // ═══════════════════════════════════
  function getStatus(p) {
    if (!p.cur || p.cur <= 0) return "OUT OF STOCK";
    if (p.min > 0 && (p.cur / p.min) < 0.5) return "LOW STOCK";
    return "IN STOCK";
  }
  function getPct(p) {
    if (!p.min || p.min === 0) return p.cur > 0 ? 100 : 0;
    return Math.round((p.cur / p.min) * 100);
  }
  function statusBadge(s) {
    if (s === "OUT OF STOCK") return '<span class="sp-badge b-out">Out of Stock</span>';
    if (s === "LOW STOCK") return '<span class="sp-badge b-low">Low Stock</span>';
    return '<span class="sp-badge b-in">In Stock</span>';
  }

  // ═══════════════════════════════════
  //  RENDER
  // ═══════════════════════════════════
  function refresh() {
    var tot = parts.length;
    var inN = parts.filter(function (p) { return getStatus(p) === "IN STOCK"; }).length;
    var low = parts.filter(function (p) { return getStatus(p) === "LOW STOCK"; }).length;
    var out = parts.filter(function (p) { return getStatus(p) === "OUT OF STOCK"; }).length;
    var wd = txLog.filter(function (t) { return t.type === "withdraw"; }).length;

    document.getElementById("k-total").textContent = tot;
    document.getElementById("k-in").textContent = inN;
    document.getElementById("k-low").textContent = low;
    document.getElementById("k-out").textContent = out;
    document.getElementById("k-wd").textContent = wd;
    document.getElementById("alert-count").textContent = low + out;
    document.querySelectorAll(".spdb .nav-tab")[0].textContent = "📦 Parts List (" + tot + ")";

    renderAlerts(); renderCats(); renderTable(); renderLog();
  }

  function renderAlerts() {
    var el = document.getElementById("alert-list");
    var list = parts.filter(function (p) { return getStatus(p) !== "IN STOCK"; })
      .sort(function (a, b) { return getPct(a) - getPct(b); });
    if (!list.length) {
      el.innerHTML = '<div style="text-align:center;padding:24px;color:#9CA3AF;font-size:12px">✅ ทุกรายการสต็อกปกติ</div>';
      return;
    }
    el.innerHTML = list.map(function (p) {
      var s = getStatus(p), dot = s === "OUT OF STOCK" ? "red" : "amber", pct = getPct(p);
      return '<div class="alert-row">' +
        '<div class="adot ' + dot + '"></div>' +
        '<div class="ainfo">' +
        '<div class="aname">' + esc(p.pn) + " — " + esc(p.desc) + " " + esc(p.model) + '</div>' +
        '<div class="ameta">' + esc(p.sub) + " · " + esc(p.loc) + " · สต็อก: <b>" + p.cur + "</b>/" + p.min + " (" + pct + "%)</div>" +
        "</div>" + statusBadge(s) + "</div>";
    }).join("");
  }

  function renderCats() {
    var subs = Array.from(new Set(parts.map(function (p) { return p.sub; }).filter(Boolean))).sort();
    var el = document.getElementById("cat-list");
    var maxQ = Math.max.apply(null, subs.map(function (s) {
      return parts.filter(function (p) { return p.sub === s; }).reduce(function (a, p) { return a + p.cur; }, 0);
    }).concat([1]));
    el.innerHTML = subs.map(function (sub) {
      var sp = parts.filter(function (p) { return p.sub === sub; });
      var q = sp.reduce(function (a, p) { return a + p.cur; }, 0);
      var al = sp.filter(function (p) { return getStatus(p) !== "IN STOCK"; }).length;
      var pct = Math.round(q / maxQ * 100);
      return '<div class="cat-row"><div class="cat-lbl" title="' + esc(sub) + '">' + esc(sub) + '</div>' +
        '<div class="cat-bar-bg"><div class="cat-bar-fill" style="width:' + pct + '%"></div></div>' +
        '<div class="cat-num">' + sp.length + ' items</div>' +
        '<div class="cat-num">· ' + q + '</div>' +
        '<div class="cat-alert">' + (al ? '<span class="sp-badge b-low" title="รายการสต็อกต่ำหรือหมด">⚠' + al + '</span>' : '') + '</div></div>';
    }).join("");
  }

  function renderTable() {
    var q = document.getElementById("sq").value.toLowerCase();
    var cat = document.getElementById("scat").value;
    var sub = document.getElementById("ssub").value;
    var st = document.getElementById("sst").value;
    var list = parts.filter(function (p) {
      var mq = !q || (p.pn.toLowerCase().indexOf(q) >= 0 || p.desc.toLowerCase().indexOf(q) >= 0 || p.model.toLowerCase().indexOf(q) >= 0);
      var mc = !cat || p.cat === cat;
      var ms = !sub || p.sub === sub;
      var mst = !st || getStatus(p) === st;
      return mq && mc && ms && mst;
    });
    document.getElementById("tbl-count").textContent = "แสดง " + list.length + " จาก " + parts.length + " รายการ";
    var body = document.getElementById("tbl-body");
    if (!list.length) { body.innerHTML = '<tr><td colspan="12" style="text-align:center;padding:24px;color:#9CA3AF">ไม่พบรายการ</td></tr>'; return; }
    body.innerHTML = list.map(function (p) {
      var s = getStatus(p), pct = getPct(p);
      var cls = s === "OUT OF STOCK" ? "r-out" : s === "LOW STOCK" ? "r-low" : "";
      var fc = s === "OUT OF STOCK" ? "#DC2626" : s === "LOW STOCK" ? "#D97706" : "#16A34A";
      var barW = Math.min(pct, 100);
      var actions = CAN_EDIT ? (
        '<button class="sp-action-btn blue" data-act="receive" data-pn="' + esc(p.pn) + '" title="รับเข้า" style="margin-right:3px">+</button>' +
        '<button class="sp-action-btn" data-act="withdraw" data-pn="' + esc(p.pn) + '" title="เบิกออก" style="margin-right:3px">-</button>' +
        '<button class="sp-action-btn" data-act="update" data-pn="' + esc(p.pn) + '" title="แก้ไข">✏</button>'
      ) : "";
      return '<tr class="' + cls + '">' +
        '<td class="mono">' + esc(p.pn) + "</td>" +
        '<td style="font-weight:600;max-width:160px">' + esc(p.desc) + "</td>" +
        '<td style="font-size:11px;color:var(--sp-dgray)">' + esc(p.model) + "</td>" +
        '<td><span class="sp-badge b-cat" style="font-size:9px">' + esc(p.cat) + "</span></td>" +
        '<td><span class="sp-badge b-sub">' + esc(p.sub) + "</span></td>" +
        '<td style="font-size:11px">' + esc(p.mfr) + "</td>" +
        '<td style="text-align:center">' + p.min + "</td>" +
        '<td style="text-align:center;font-weight:800;font-size:15px;color:' + fc + '">' + p.cur + "</td>" +
        '<td><div class="pbar-wrap"><div class="pbar-bg"><div class="pbar-fill" style="width:' + barW + "%;background:" + fc + '"></div></div><span style="font-size:10px;color:var(--sp-dgray)">' + pct + "%</span></div></td>" +
        "<td>" + statusBadge(s) + "</td>" +
        '<td style="font-size:11px;color:var(--sp-dgray)">' + esc(p.loc) + "</td>" +
        '<td style="white-space:nowrap">' + actions + "</td></tr>";
    }).join("");
  }

  function renderLog() {
    var icons = {receive: "📦", withdraw: "📤", replace: "🔄", update: "✏️", new: "➕"};
    var cls = {receive: "li-r", withdraw: "li-w", replace: "li-p", update: "li-u", new: "li-n"};
    var lbl = {receive: "รับเข้า", withdraw: "เบิกออก", replace: "เปลี่ยน", update: "แก้ไข", new: "เพิ่มใหม่"};
    var list = logFilter === "all" ? txLog : txLog.filter(function (t) { return t.type === logFilter; });
    var el = document.getElementById("log-list");
    if (!list.length) { el.innerHTML = '<div style="text-align:center;padding:24px;color:#9CA3AF;font-size:12px">ยังไม่มี Transaction</div>'; return; }
    el.innerHTML = list.map(function (t) {
      var dc = t.delta > 0 ? "dp" : t.delta < 0 ? "dn" : "dz";
      var dt = t.delta > 0 ? "+" + t.delta : t.delta < 0 ? t.delta : (lbl[t.type] || "—");
      return '<div class="log-item"><div class="lic ' + (cls[t.type] || "li-u") + '">' + (icons[t.type] || "✏️") + "</div>" +
        "<div><div class=\"ltitle\">" + esc(t.pn) + " — " + esc(t.desc) + '</div><div class="lmeta">' + esc(lbl[t.type] || t.type) + " · " + esc(t.by) + " · " + esc(t.reason) + "</div></div>" +
        '<div style="text-align:right"><div class="ldelta ' + dc + '">' + esc(dt) + '</div><div class="ltime">' + esc(t.ts) + "</div></div></div>";
    }).join("");
  }

  // ═══════════════════════════════════
  //  FORM
  // ═══════════════════════════════════
  var mCfg = {
    receive: {hint: "กรอก Part No → ดึงข้อมูลอัตโนมัติ แล้วกรอกจำนวนที่รับเพิ่ม", ql: "จำนวนที่รับเข้า", bc: "sp-btn-blue", bt: "✓ บันทึกรับเข้า"},
    withdraw: {hint: "กรอก Part No → กรอกจำนวนที่เบิก (ระบบหักสต็อกอัตโนมัติ)", ql: "จำนวนที่เบิกออก", bc: "sp-btn-red", bt: "✓ บันทึกเบิกออก"},
    update: {hint: "ดึงข้อมูลมาแก้ไข — ประวัติเดิมยังเก็บไว้ครบ", ql: "Current Stock (แก้ไข)", bc: "sp-btn-green", bt: "✓ บันทึกแก้ไข"},
    replace: {hint: "พิมพ์ Part No เดิม → กรอกข้อมูลของใหม่ที่ทดแทน", ql: "สต็อกใหม่", bc: "sp-btn-amber", bt: "✓ บันทึกเปลี่ยน"},
    new: {hint: "กรอกข้อมูลอะไหล่ใหม่ที่ยังไม่มีในระบบ", ql: "จำนวนเริ่มต้น", bc: "sp-btn-blue", bt: "✓ เพิ่มรายการใหม่"},
  };

  function setMode(m, btn) {
    mode = m;
    document.querySelectorAll(".spdb .mtab").forEach(function (b) { b.className = "mtab" + (b === btn ? " m-" + m : ""); });
    var c = mCfg[m];
    document.getElementById("f-hint").textContent = c.hint;
    document.getElementById("qty-lbl").textContent = c.ql;
    var sb = document.getElementById("f-submit");
    sb.className = "sp-btn " + c.bc; sb.textContent = c.bt;
    document.getElementById("diff-wrap").style.display = "none";
    curPart = null;
  }

  function onPN(val) {
    var v = val.trim().toUpperCase();
    var tag = document.getElementById("pn-tag");
    var p = parts.find(function (x) { return x.pn.toUpperCase() === v; });
    curPart = p || null;
    if (!v) { tag.style.display = "none"; updateDiff(); return; }
    if (p) {
      tag.textContent = "พบ"; tag.className = "pn-tag tag-found"; tag.style.display = "block";
      autoFill(p);
    } else {
      tag.textContent = "ใหม่"; tag.className = "pn-tag tag-new"; tag.style.display = "block";
    }
    updateDiff();
  }

  function autoFill(p) {
    var map = [["f-desc", p.desc], ["f-model", p.model], ["f-cat", p.cat], ["f-sub", p.sub],
      ["f-mfr", p.mfr], ["f-unit", p.unit], ["f-price", p.price],
      ["f-min", p.min], ["f-loc", p.loc], ["f-lead", p.lead]];
    map.forEach(function (pair) {
      var el = document.getElementById(pair[0]);
      if (!el) return;
      el.value = pair[1];
      if (el.tagName === "INPUT") { el.classList.add("autofill"); setTimeout(function () { el.classList.remove("autofill"); }, 800); }
    });
    if (mode === "update") document.getElementById("f-qty").value = p.cur;
    else if (mode !== "new") document.getElementById("f-qty").value = "";
  }

  function updateDiff() {
    var w = document.getElementById("diff-wrap");
    if (!curPart) { w.style.display = "none"; return; }
    var qty = parseInt(document.getElementById("f-qty").value, 10) || 0;
    var before = curPart.cur;
    var delta, after;
    if (mode === "receive") { delta = +qty; after = before + qty; }
    else if (mode === "withdraw") { delta = -qty; after = before - qty; }
    else if (mode === "update") { after = qty; delta = qty - before; }
    else { w.style.display = "none"; return; }
    if (!qty && mode !== "update") { w.style.display = "none"; return; }
    w.style.display = "block";
    var av = Math.max(0, after);
    document.getElementById("d-before").textContent = before + " " + curPart.unit;
    var de = document.getElementById("d-delta");
    de.textContent = (delta >= 0 ? "+" : "") + delta;
    de.style.color = delta > 0 ? "#16A34A" : delta < 0 ? "#DC2626" : "#D97706";
    var ae = document.getElementById("d-after");
    ae.textContent = av + " " + curPart.unit;
    ae.style.color = av <= 0 ? "#DC2626" : (curPart.min > 0 && (av / curPart.min) < 0.5) ? "#D97706" : "#16A34A";
    var pct = curPart.min > 0 ? Math.round((av / curPart.min) * 100) : 0;
    document.getElementById("d-pct").textContent = pct + "%";
  }

  function getBy() {
    var by = document.getElementById("f-by").value.trim() || "—";
    var team = document.getElementById("f-team").value;
    return team ? by + " [" + team + "]" : by;
  }

  function upsertLocalPart(part) {
    var idx = parts.findIndex(function (x) { return x.pn === part.pn; });
    if (idx >= 0) parts[idx] = part; else parts.push(part);
    parts.sort(function (a, b) { return a.pn.localeCompare(b.pn); });
  }

  function submitForm() {
    var pn = document.getElementById("f-pn").value.trim().toUpperCase();
    var desc = document.getElementById("f-desc").value.trim();
    var qty = document.getElementById("f-qty").value;
    if (!pn) { toast("กรุณากรอก Part Number", "warn"); return; }
    if (!desc && mode === "new") { toast("กรุณากรอกชื่ออะไหล่", "warn"); return; }

    var payload = {
      mode: mode, pn: pn, desc: desc, qty: qty,
      model: document.getElementById("f-model").value.trim(),
      cat: document.getElementById("f-cat").value.trim(),
      sub: document.getElementById("f-sub").value.trim(),
      mfr: document.getElementById("f-mfr").value.trim(),
      unit: document.getElementById("f-unit").value.trim(),
      price: document.getElementById("f-price").value,
      min: document.getElementById("f-min").value,
      loc: document.getElementById("f-loc").value.trim(),
      lead: document.getElementById("f-lead").value.trim(),
      by: document.getElementById("f-by").value.trim(),
      team: document.getElementById("f-team").value.trim(),
      reason: document.getElementById("f-reason").value.trim(),
    };

    var submitBtn = document.getElementById("f-submit");
    submitBtn.disabled = true;
    apiPost(TX_URL, payload).then(function (res) {
      submitBtn.disabled = false;
      if (!res.data.ok) { toast(res.data.message || "เกิดข้อผิดพลาด", "warn"); return; }
      upsertLocalPart(res.data.part);
      txLog.unshift(res.data.tx);
      toast(res.data.message, "ok");
      clearForm(false); refresh(); updateDataLists(); syncStickyOffsets();
    }).catch(function () {
      submitBtn.disabled = false;
      toast("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้", "err");
    });
  }

  function clearForm(rm) {
    if (rm === undefined) rm = true;
    ["f-pn", "f-desc", "f-model", "f-cat", "f-sub", "f-mfr", "f-unit",
      "f-price", "f-min", "f-qty", "f-loc", "f-lead", "f-by", "f-team", "f-reason"]
      .forEach(function (id) { var el = document.getElementById(id); if (el) el.value = ""; });
    document.getElementById("f-unit").value = "EA";
    document.getElementById("pn-tag").style.display = "none";
    document.getElementById("diff-wrap").style.display = "none";
    curPart = null;
    if (rm) setMode("receive", document.getElementById("mt-receive"));
  }

  function qLoad(pn, m) {
    var p = parts.find(function (x) { return x.pn === pn; });
    if (!p) return;
    document.getElementById("f-pn").value = p.pn;
    onPN(p.pn);
    setMode(m, document.getElementById("mt-" + m));
    if (m === "update") document.getElementById("f-qty").value = p.cur;
    showTab("t-form", document.querySelectorAll(".spdb .nav-tab")[1]);
    document.getElementById("f-pn").scrollIntoView({behavior: "smooth", block: "nearest"});
  }

  // ═══════════════════════════════════
  //  IMPORT
  // ═══════════════════════════════════
  function openImportModal() { document.getElementById("import-modal").style.display = "flex"; resetImport(); }
  function closeImport() { document.getElementById("import-modal").style.display = "none"; }
  function resetImport() {
    importedRows = [];
    document.getElementById("drop-title").textContent = "ลากไฟล์ Excel มาวางที่นี่";
    document.getElementById("drop-sub").textContent = 'รองรับ .xlsx | Sheet: "📦 Master Parts List"';
    document.getElementById("import-opts").style.display = "none";
    document.getElementById("import-preview").style.display = "none";
    document.getElementById("do-import").style.display = "none";
    selOpt("merge");
  }
  function selOpt(v) {
    importMode = v;
    ["merge", "full", "reset"].forEach(function (k) {
      var el = document.getElementById("opt-" + k);
      if (el) el.classList.toggle("selected", k === v);
    });
  }
  function handleDrop(e) {
    e.preventDefault();
    document.getElementById("drop-zone").classList.remove("over");
    var f = e.dataTransfer.files[0];
    if (f && /\.xlsx?$/i.test(f.name)) readImport(f);
    else toast("กรุณาเลือกไฟล์ .xlsx", "warn");
  }
  function handleFileInput(inp) { if (inp.files[0]) readImport(inp.files[0]); inp.value = ""; }

  function readImport(file) {
    var reader = new FileReader();
    reader.onload = function (e) {
      try {
        var wb = XLSX.read(e.target.result, {type: "binary"});
        var sh = wb.SheetNames.find(function (n) { return n.indexOf("Master Parts List") >= 0; }) || wb.SheetNames[0];
        var rows = XLSX.utils.sheet_to_json(wb.Sheets[sh], {header: 1, defval: ""});
        importedRows = parseImportRows(rows);
        if (!importedRows.length) { toast("ไม่พบข้อมูลใน Sheet", "warn"); return; }
        document.getElementById("drop-title").textContent = "✅ " + file.name;
        document.getElementById("drop-sub").textContent = "พบ " + importedRows.length + " รายการ";
        document.getElementById("import-opts").style.display = "block";
        document.getElementById("import-preview").style.display = "block";
        document.getElementById("do-import").style.display = "inline-block";
        renderPreview(importedRows);
      } catch (err) { toast("อ่านไฟล์ไม่ได้: " + err.message, "warn"); }
    };
    reader.readAsBinaryString(file);
  }

  function parseImportRows(rows) {
    var result = [];
    var h = -1;
    for (var i = 0; i < Math.min(rows.length, 8); i++) {
      var r = rows[i].map(function (c) { return String(c).toLowerCase(); });
      if (r.some(function (c) { return c.indexOf("part number") >= 0 || c.indexOf("part no") >= 0; })) { h = i; break; }
    }
    if (h < 0) return [];
    var hdr = rows[h].map(function (c) { return String(c).toLowerCase().trim(); });
    var col = function (n) { return hdr.findIndex(function (x) { return x.indexOf(n) >= 0; }); };
    var ci = {
      pn: col("part number") >= 0 ? col("part number") : col("part no"),
      desc: col("description") >= 0 ? col("description") : 2,
      model: col("model") >= 0 ? col("model") : 3,
      cat: col("category") >= 0 ? col("category") : 4,
      sub: col("sub") >= 0 ? col("sub") : 5,
      mfr: col("manufacturer") >= 0 ? col("manufacturer") : 6,
      unit: col("unit") >= 0 ? col("unit") : 7,
      min: col("qty\nstock") >= 0 ? col("qty\nstock") : col("min stock") >= 0 ? col("min stock") : col("qty stock") >= 0 ? col("qty stock") : 8,
      cur: col("qty\ncurrent") >= 0 ? col("qty\ncurrent") : col("current stock") >= 0 ? col("current stock") : col("qty current") >= 0 ? col("qty current") : 9,
      price: col("unit price") >= 0 ? col("unit price") : 11,
      loc: col("location") >= 0 ? col("location") : 13,
      lead: col("lead") >= 0 ? col("lead") : 14,
      rem: col("remarks") >= 0 ? col("remarks") : 16,
    };
    for (var j = h + 1; j < rows.length; j++) {
      var row = rows[j];
      var pn = String(row[ci.pn] || "").trim();
      if (!pn || pn.indexOf("──") === 0) continue;
      result.push({
        pn: pn, desc: String(row[ci.desc] || ""),
        model: String(row[ci.model] || ""),
        cat: String(row[ci.cat] || ""), sub: String(row[ci.sub] || ""),
        mfr: String(row[ci.mfr] || ""), unit: String(row[ci.unit] || "EA"),
        price: parseFloat(row[ci.price]) || 0,
        min: parseInt(row[ci.min], 10) || 0, cur: parseInt(row[ci.cur], 10) || 0,
        loc: String(row[ci.loc] || ""), lead: String(row[ci.lead] || "7"), remarks: String(row[ci.rem] || ""),
      });
    }
    return result;
  }

  function renderPreview(data) {
    var s = data.slice(0, 6);
    var tbl = document.getElementById("prev-tbl");
    tbl.querySelector("thead").innerHTML = "<tr>" + ["Part No.", "Description", "Model", "Cat", "Sub", "Min", "Stock"].map(function (h) { return "<th>" + h + "</th>"; }).join("") + "</tr>";
    tbl.querySelector("tbody").innerHTML = s.map(function (p) {
      var st = p.cur <= 0 ? "OUT" : (p.min > 0 && (p.cur / p.min) < 0.5) ? "LOW" : "OK";
      var c = st === "OUT" ? "color:#DC2626" : st === "LOW" ? "color:#D97706" : "color:#16A34A";
      return "<tr><td style=\"font-family:monospace\">" + esc(p.pn) + "</td><td>" + esc(p.desc) + "</td><td>" + esc(p.model) + "</td><td>" + esc(p.cat) + "</td><td>" + esc(p.sub) + '</td><td style="text-align:center">' + p.min + '</td><td style="text-align:center;font-weight:700;' + c + '">' + p.cur + "</td></tr>";
    }).join("");
    var outN = data.filter(function (p) { return p.cur <= 0; }).length;
    var lowN = data.filter(function (p) { return p.cur > 0 && p.min > 0 && (p.cur / p.min) < 0.5; }).length;
    document.getElementById("prev-stat").innerHTML = "พบ <b>" + data.length + "</b> รายการ · <span style=\"color:#DC2626\">Out: " + outN + '</span> · <span style="color:#D97706">Low: ' + lowN + "</span>";
  }

  function doImport() {
    if (!importedRows.length) return;
    if (importMode !== "merge") {
      var warnMsg = importMode === "reset"
        ? "Full Reset จะลบข้อมูลอะไหล่และ Transaction Log เดิมทั้งหมด แล้วแทนที่ด้วยไฟล์นี้ — ยืนยันหรือไม่?"
        : "Full Replace จะแทนที่รายการอะไหล่ทั้งหมดด้วยไฟล์นี้ (Log เดิมยังอยู่) — ยืนยันหรือไม่?";
      if (!window.confirm(warnMsg)) return;
    }
    var btn = document.getElementById("do-import");
    btn.disabled = true;
    apiPost(IMPORT_URL, {import_mode: importMode, rows: importedRows}).then(function (res) {
      btn.disabled = false;
      if (!res.data.ok) { toast(res.data.message || "Import ไม่สำเร็จ", "warn"); return; }
      parts = res.data.parts;
      txLog = res.data.txlog;
      toast(res.data.message, "ok");
      refresh(); updateDataLists(); closeImport(); syncStickyOffsets();
    }).catch(function () {
      btn.disabled = false;
      toast("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้", "err");
    });
  }

  // ═══════════════════════════════════
  //  EXPORT
  // ═══════════════════════════════════
  function exportExcel() {
    var wb = XLSX.utils.book_new();
    var lbl = {receive: "รับเข้า", withdraw: "เบิกออก", replace: "เปลี่ยนทดแทน", update: "แก้ไข", new: "เพิ่มใหม่"};

    var ph = ["No.", "Part Number", "Description (EN)", "Model / Spec", "Category", "Sub-Category",
      "Manufacturer", "Unit", "Qty Stock (Min)", "Qty Current", "%", "Unit Price (THB)", "Total Value (THB)",
      "Location / Storage", "Lead Time (Days)", "Status", "Remarks"];
    var pr = parts.map(function (p, i) {
      var pct = p.min > 0 ? Math.round((p.cur / p.min) * 100) : 0;
      var st = p.cur <= 0 ? "OUT OF STOCK" : (p.min > 0 && (p.cur / p.min) < 0.5) ? "LOW STOCK" : "IN STOCK";
      return [i + 1, p.pn, p.desc, p.model, p.cat, p.sub, p.mfr, p.unit, p.min, p.cur, pct + "%",
        p.price, p.price * p.cur, p.loc, p.lead, st, p.remarks || ""];
    });
    var ws1 = XLSX.utils.aoa_to_sheet([ph].concat(pr));
    ws1["!cols"] = [5, 10, 22, 16, 14, 16, 14, 7, 10, 10, 7, 12, 13, 14, 8, 12, 20].map(function (w) { return {wch: w}; });
    XLSX.utils.book_append_sheet(wb, ws1, "Master Parts List");

    var th = ["No.", "Date", "Type", "Part Number", "Description", "Before", "Change", "After", "By", "Reason"];
    var tr = txLog.slice().reverse().map(function (t, i) { return [i + 1, t.ts, lbl[t.type] || t.type, t.pn, t.desc, t.before, t.delta, t.after, t.by, t.reason]; });
    var ws2 = XLSX.utils.aoa_to_sheet([th].concat(tr));
    ws2["!cols"] = [5, 16, 12, 10, 28, 8, 8, 8, 18, 28].map(function (w) { return {wch: w}; });
    XLSX.utils.book_append_sheet(wb, ws2, "Transaction Log");

    var wh = ["WD No.", "Date", "Part Number", "Description", "Model", "Qty", "Unit", "By", "Purpose"];
    var wr = txLog.filter(function (t) { return t.type === "withdraw"; }).slice().reverse().map(function (t, i) {
      var p = parts.find(function (x) { return x.pn === t.pn; });
      return ["WD-" + String(i + 1).padStart(3, "0"), t.ts, t.pn, t.desc, p ? p.model : "", Math.abs(t.delta), p ? p.unit : "EA", t.by, t.reason];
    });
    var ws3 = XLSX.utils.aoa_to_sheet([wh].concat(wr));
    ws3["!cols"] = [12, 16, 10, 22, 14, 8, 7, 18, 28].map(function (w) { return {wch: w}; });
    XLSX.utils.book_append_sheet(wb, ws3, "Withdrawal Log");

    var rh = ["Status", "Part Number", "Description", "Model", "Sub-Category", "Unit", "Current", "Min", "Order Qty", "Location"];
    var rr = parts.filter(function (p) { return p.cur <= 0 || (p.min > 0 && (p.cur / p.min) < 0.5); }).map(function (p) {
      var st = p.cur <= 0 ? "OUT OF STOCK" : "LOW STOCK";
      return [st, p.pn, p.desc, p.model, p.sub, p.unit, p.cur, p.min, Math.max(0, p.min - p.cur), p.loc];
    });
    var ws4 = XLSX.utils.aoa_to_sheet([rh].concat(rr));
    ws4["!cols"] = [12, 10, 22, 14, 16, 7, 8, 8, 10, 14].map(function (w) { return {wch: w}; });
    XLSX.utils.book_append_sheet(wb, ws4, "Reorder List");

    var dt = new Date().toLocaleDateString("th-TH").replace(/\//g, "-");
    XLSX.writeFile(wb, "SparePartsList_" + dt + ".xlsx");
    toast("Export Excel สำเร็จ!", "ok");
  }

  // ═══════════════════════════════════
  //  UI HELPERS
  // ═══════════════════════════════════
  function showTab(id, btn) {
    document.querySelectorAll(".spdb .tab-pane").forEach(function (p) { p.classList.remove("active"); });
    document.querySelectorAll(".spdb .nav-tab").forEach(function (b) { b.classList.remove("active"); });
    document.getElementById(id).classList.add("active");
    if (btn) btn.classList.add("active");
    syncStickyOffsets();
  }
  function filterLog(f, el) {
    logFilter = f;
    document.querySelectorAll(".spdb .lf").forEach(function (b) { b.classList.remove("active"); });
    el.classList.add("active");
    renderLog();
  }
  function toast(msg, type) {
    type = type || "ok";
    var wrap = document.getElementById("sp-toasts");
    var t = document.createElement("div");
    t.className = "sp-toast sp-t" + type;
    t.textContent = (type === "ok" ? "✅ " : type === "warn" ? "⚠️ " : "❌ ") + msg;
    wrap.appendChild(t);
    setTimeout(function () { t.style.opacity = "0"; t.style.transition = "opacity .3s"; setTimeout(function () { t.remove(); }, 300); }, 3000);
  }
  function updateDataLists() {
    var set = function (key) { return Array.from(new Set(parts.map(function (p) { return p[key]; }).filter(Boolean))).sort(); };
    var fill = function (id, vals) {
      var el = document.getElementById(id);
      if (el) el.innerHTML = vals.map(function (v) { return "<option>" + esc(v) + "</option>"; }).join("");
    };
    fill("dl-cat", set("cat"));
    fill("sub-list", set("sub"));
    fill("mfr-list", set("mfr"));
    fill("unit-list", set("unit"));
    fill("loc-list", set("loc"));
  }

  // ═══════════════════════════════════
  //  COLLAPSIBLE CARDS (Auto Alert / Sub-Category)
  // ═══════════════════════════════════
  function collapseStorageKey(key) { return "spdb_collapsed_" + key; }
  function setCardCollapsed(card, collapsed) {
    card.classList.toggle("is-collapsed", collapsed);
    var btn = card.querySelector("[data-collapse-toggle]");
    if (btn) btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
    var key = card.getAttribute("data-collapse-key");
    if (key) {
      try { localStorage.setItem(collapseStorageKey(key), collapsed ? "1" : "0"); } catch (e) {}
    }
    syncStickyOffsets();
  }
  // ═══════════════════════════════════
  //  STICKY OFFSETS (measured, not guessed — the app navbar's height
  //  varies with viewport width, and the locked-head's height varies
  //  with whether the Auto Alert / Sub-Category cards are collapsed).
  //  Search stays outside the table scrollport. Size the table using its
  //  actual document position, including wrapped filters and card spacing.
  // ═══════════════════════════════════
  function syncStickyOffsets() {
    var root = document.documentElement;
    var nav = document.querySelector("header.nav");
    if (nav) root.style.setProperty("--sp-nav-h", nav.offsetHeight + "px");
    var head = document.getElementById("sp-locked-head");
    if (head) root.style.setProperty("--sp-head-h", head.offsetHeight + "px");
    var sbar = document.getElementById("sp-sbar");
    if (sbar) root.style.setProperty("--sp-sbar-h", sbar.offsetHeight + "px");
    var footer = document.querySelector("footer.app-footer");
    if (footer) root.style.setProperty("--sp-footer-h", footer.offsetHeight + "px");
    var table = document.querySelector("#t-parts .tbl-wrap");
    var count = document.getElementById("tbl-count");
    if (table && table.getClientRects().length) {
      var top = table.getBoundingClientRect().top + window.scrollY;
      // Count margin, card padding/border, and the card's bottom margin.
      var bottom = (footer ? footer.offsetHeight : 0) + (count ? count.offsetHeight : 0) + 38;
      // On short/narrow screens allow the summary to leave the viewport,
      // rather than pinning a header taller than the screen over the table.
      if (head) head.classList.toggle("sp-head-scroll", window.innerHeight - top - bottom < 120);
      root.style.setProperty("--sp-table-h", Math.max(120, window.innerHeight - top - bottom) + "px");
    }
  }
  syncStickyOffsets();
  window.addEventListener("resize", syncStickyOffsets);
  // Heights also change once web fonts load (Thai labels wrap), after this runs.
  if (window.ResizeObserver) {
    var stickyObserver = new ResizeObserver(syncStickyOffsets);
    ["header.nav", "#sp-locked-head", "#sp-sbar", "#tbl-count", "footer.app-footer"].forEach(function (sel) {
      var el = document.querySelector(sel);
      if (el) stickyObserver.observe(el);
    });
  }

  document.querySelectorAll(".spdb .card[data-collapse-key]").forEach(function (card) {
    var key = card.getAttribute("data-collapse-key");
    var saved = "0";
    try { saved = localStorage.getItem(collapseStorageKey(key)) || "0"; } catch (e) {}
    setCardCollapsed(card, saved === "1");
    var btn = card.querySelector("[data-collapse-toggle]");
    if (btn) btn.addEventListener("click", function () { setCardCollapsed(card, !card.classList.contains("is-collapsed")); });
  });

  // ═══════════════════════════════════
  //  WIRE UP
  // ═══════════════════════════════════
  document.getElementById("sq").addEventListener("input", renderTable);
  document.getElementById("scat").addEventListener("change", renderTable);
  document.getElementById("ssub").addEventListener("change", renderTable);
  document.getElementById("sst").addEventListener("change", renderTable);
  if (CAN_EDIT) {
    document.getElementById("f-qty").addEventListener("input", updateDiff);
    document.getElementById("f-pn").addEventListener("input", function () { onPN(this.value); });
  }

  document.querySelectorAll(".spdb .nav-tab").forEach(function (btn) {
    btn.addEventListener("click", function () { showTab(btn.getAttribute("data-tab"), btn); });
  });
  document.querySelectorAll(".spdb .mtab").forEach(function (btn) {
    btn.addEventListener("click", function () { setMode(btn.getAttribute("data-mode"), btn); });
  });
  document.querySelectorAll(".spdb .lf").forEach(function (btn) {
    btn.addEventListener("click", function () { filterLog(btn.getAttribute("data-filter"), btn); });
  });
  document.getElementById("tbl-body").addEventListener("click", function (e) {
    var btn = e.target.closest("[data-act]");
    if (!btn) return;
    qLoad(btn.getAttribute("data-pn"), btn.getAttribute("data-act"));
  });
  var clearBtn = document.getElementById("sp-clear-btn");
  if (clearBtn) clearBtn.addEventListener("click", function () { clearForm(true); });
  var submitBtn = document.getElementById("f-submit");
  if (submitBtn) submitBtn.addEventListener("click", submitForm);

  var importOpenBtn = document.getElementById("sp-import-open");
  if (importOpenBtn) importOpenBtn.addEventListener("click", openImportModal);
  var exportBtn = document.getElementById("sp-export-btn");
  if (exportBtn) exportBtn.addEventListener("click", exportExcel);
  var importModal = document.getElementById("import-modal");
  if (importModal) {
    importModal.addEventListener("click", function (e) { if (e.target === importModal) closeImport(); });
    document.getElementById("sp-import-close").addEventListener("click", closeImport);
    document.getElementById("sp-import-cancel").addEventListener("click", closeImport);
    document.getElementById("do-import").addEventListener("click", doImport);
    var dropZone = document.getElementById("drop-zone");
    dropZone.addEventListener("click", function () { document.getElementById("xl-input").click(); });
    dropZone.addEventListener("dragover", function (e) { e.preventDefault(); dropZone.classList.add("over"); });
    dropZone.addEventListener("dragleave", function () { dropZone.classList.remove("over"); });
    dropZone.addEventListener("drop", handleDrop);
    document.getElementById("xl-input").addEventListener("change", function () { handleFileInput(this); });
    document.querySelectorAll(".spdb .iopt").forEach(function (opt) {
      opt.addEventListener("click", function () { selOpt(opt.getAttribute("data-opt")); });
    });
  }

  refresh();
  updateDataLists();
  if (CAN_EDIT) setMode("receive", document.getElementById("mt-receive"));
  syncStickyOffsets();
})();
