(function () {
  "use strict";

  var script = document.currentScript;
  var tablesUrl = script.getAttribute("data-tables-url");
  var dataUrl = script.getAttribute("data-data-url");

  var sourceSel = document.getElementById("ds-source");
  var tableSel = document.getElementById("ds-table");
  var loadBtn = document.getElementById("ds-load-btn");
  var messageEl = document.getElementById("ds-message");
  var resultArea = document.getElementById("ds-result-area");

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function setMessage(text) {
    messageEl.textContent = text || "";
  }

  function loadTables() {
    tableSel.disabled = true;
    loadBtn.disabled = true;
    tableSel.innerHTML = '<option value="">กำลังโหลดรายชื่อตาราง...</option>';
    resultArea.innerHTML = "";
    setMessage("");

    fetch(tablesUrl + "?source=" + encodeURIComponent(sourceSel.value))
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.ok) {
          tableSel.innerHTML = '<option value="">-- ไม่สามารถโหลดรายชื่อตารางได้ --</option>';
          setMessage(data.message);
          return;
        }
        if (!data.tables.length) {
          tableSel.innerHTML = '<option value="">-- ไม่พบตารางในฐานข้อมูลนี้ --</option>';
          return;
        }
        tableSel.innerHTML = '<option value="">-- เลือกตาราง --</option>' +
          data.tables.map(function (t) { return '<option value="' + escapeHtml(t) + '">' + escapeHtml(t) + "</option>"; }).join("");
        tableSel.disabled = false;
      })
      .catch(function () {
        tableSel.innerHTML = '<option value="">-- เกิดข้อผิดพลาด --</option>';
        setMessage("เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์");
      });
  }

  function renderTable(data) {
    var head = "<tr>" + data.columns.map(function (c) { return "<th>" + escapeHtml(c) + "</th>"; }).join("") + "</tr>";
    var body = data.rows.map(function (row) {
      return "<tr>" + row.map(function (cell) {
        return "<td>" + (cell === null || cell === undefined ? '<span style="color:var(--slate-400);">NULL</span>' : escapeHtml(cell)) + "</td>";
      }).join("") + "</tr>";
    }).join("");

    var truncatedNote = data.truncated
      ? '<div class="pagination"><span class="info">แสดง ' + data.rows.length + ' แถวแรก (มีข้อมูลมากกว่านี้ — จำกัดไว้เพื่อความเร็ว)</span></div>'
      : '<div class="pagination"><span class="info">แสดงทั้งหมด ' + data.rows.length + ' แถว</span></div>';

    resultArea.innerHTML =
      '<div class="main-panel"><div class="table-scroll-x"><table class="doc-table"><thead>' + head +
      "</thead><tbody>" + (body || '<tr><td colspan="' + data.columns.length + '" class="table-empty">ไม่มีข้อมูล</td></tr>') +
      "</tbody></table></div>" + truncatedNote + "</div>";
  }

  loadBtn.addEventListener("click", function () {
    if (!tableSel.value) return;
    loadBtn.disabled = true;
    loadBtn.textContent = "กำลังโหลด...";
    setMessage("");
    resultArea.innerHTML = "";

    var params = new URLSearchParams({ source: sourceSel.value, table: tableSel.value });
    fetch(dataUrl + "?" + params.toString())
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (!data.ok) {
          setMessage(data.message);
          return;
        }
        renderTable(data);
      })
      .catch(function () {
        setMessage("เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์");
      })
      .finally(function () {
        loadBtn.disabled = false;
        loadBtn.textContent = "Load Data";
      });
  });

  tableSel.addEventListener("change", function () {
    loadBtn.disabled = !tableSel.value;
  });

  sourceSel.addEventListener("change", loadTables);

  loadTables();
})();
