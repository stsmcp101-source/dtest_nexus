(function () {
  "use strict";

  var root = document.getElementById("thdb-root");
  var CAN_EDIT = root.getAttribute("data-can-edit") === "1";
  var EMPLOYEE_CREATE_URL = root.getAttribute("data-employee-create-url");
  var EMPLOYEE_UPDATE_URL_TPL = root.getAttribute("data-employee-update-url-tpl");
  var EMPLOYEE_DELETE_URL_TPL = root.getAttribute("data-employee-delete-url-tpl");
  var TRAINING_CREATE_URL = root.getAttribute("data-training-create-url");
  var TRAINING_UPDATE_URL_TPL = root.getAttribute("data-training-update-url-tpl");
  var TRAINING_DELETE_URL_TPL = root.getAttribute("data-training-delete-url-tpl");
  function urlForPk(tpl, pk) { return tpl.replace(/\/0\//, "/" + pk + "/"); }

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

  function statusBadgeClass(emp) {
    return "rounded-full font-semibold " + (emp.statusCode === "resigned" ? "bg-red-100 text-red-800" : "bg-emerald-100 text-emerald-800");
  }

  var employees = JSON.parse(document.getElementById("th-employees-data").textContent);
  var trainings = JSON.parse(document.getElementById("th-trainings-data").textContent);
  var currentHistoryEmpId = employees.length ? employees[0].empId : null;

  // ═══════════════════════════════════
  //  TAB SWITCHING
  // ═══════════════════════════════════
  window.switchTab = function (tabKey) {
    ["history", "employees", "courses"].forEach(function (t) {
      document.getElementById("section-" + t).classList.add("hidden");
      var btn = document.getElementById("tab-btn-" + t);
      btn.classList.remove("active", "bg-blue-600", "text-white", "shadow-sm");
      btn.classList.add("text-slate-300");
    });
    document.getElementById("section-" + tabKey).classList.remove("hidden");
    var activeBtn = document.getElementById("tab-btn-" + tabKey);
    activeBtn.classList.add("active", "bg-blue-600", "text-white", "shadow-sm");
    activeBtn.classList.remove("text-slate-300");

    if (tabKey === "history") renderHistoryPage();
    else if (tabKey === "employees") renderEmployeesTable(employees);
    else if (tabKey === "courses") renderCoursesTable(trainings);

    if (window.lucide) lucide.createIcons();
  };

  // ═══════════════════════════════════
  //  SECTION 1: HISTORY
  // ═══════════════════════════════════
  function populateHistorySelect() {
    var select = document.getElementById("historyEmployeeSelect");
    var trainSelect = document.getElementById("trainEmployeeSelect");
    select.innerHTML = "";
    if (trainSelect) trainSelect.innerHTML = "";
    employees.forEach(function (emp) {
      var opt = document.createElement("option");
      opt.value = emp.empId;
      opt.textContent = "[" + emp.empId + "] " + emp.nameEn + " (" + emp.nameTh + ") - " + emp.group;
      select.appendChild(opt);
      if (trainSelect) {
        var tOpt = document.createElement("option");
        tOpt.value = emp.empId;
        tOpt.textContent = "[" + emp.empId + "] " + emp.nameEn + " (" + emp.nameTh + ")";
        trainSelect.appendChild(tOpt);
      }
    });
    if (currentHistoryEmpId) select.value = currentHistoryEmpId;
  }

  window.changeHistoryEmployee = function (empId) {
    currentHistoryEmpId = empId;
    renderHistoryPage();
  };

  window.viewEmployeeHistory = function (empId) {
    currentHistoryEmpId = empId;
    var select = document.getElementById("historyEmployeeSelect");
    if (select) select.value = empId;
    switchTab("history");
  };

  function renderHistoryPage() {
    var emp = employees.find(function (e) { return e.empId === currentHistoryEmpId; }) || employees[0];
    var photoImg = document.getElementById("doc-photo");
    var photoPlaceholder = document.getElementById("doc-photo-placeholder");
    if (!emp) {
      document.getElementById("doc-history-no").textContent = "—";
      ["doc-name-th", "doc-name-en", "doc-emp-id", "doc-working-group", "doc-position", "doc-education", "doc-work-start", "doc-working-years", "doc-birthday", "doc-age"].forEach(function (id) {
        document.getElementById(id).textContent = "";
      });
      document.getElementById("history-table-body").innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-400">ยังไม่มีข้อมูลพนักงาน</td></tr>';
      return;
    }

    document.getElementById("doc-history-no").textContent = emp.historyNo;
    document.getElementById("doc-name-th").textContent = emp.nameTh;
    document.getElementById("doc-name-en").textContent = emp.nameEn;
    document.getElementById("doc-emp-id").textContent = emp.empId;
    document.getElementById("doc-working-group").textContent = emp.group;
    document.getElementById("doc-position").textContent = emp.position;
    document.getElementById("doc-education").textContent = emp.education;
    document.getElementById("doc-work-start").textContent = emp.workStartDisplay || emp.workStart;
    document.getElementById("doc-working-years").textContent = (emp.workYears == null ? "—" : emp.workYears + " ปี");
    document.getElementById("doc-birthday").textContent = emp.birthdayDisplay || emp.birthday;
    document.getElementById("doc-age").textContent = (emp.age == null ? "—" : emp.age + " ปี");
    var docStatus = document.getElementById("doc-status");
    docStatus.textContent = emp.status;
    docStatus.className = "px-2.5 py-0.5 text-xs " + statusBadgeClass(emp);

    if (emp.photoUrl) {
      photoImg.src = emp.photoUrl;
      photoImg.classList.remove("hidden");
      photoPlaceholder.classList.add("hidden");
    } else {
      photoImg.classList.add("hidden");
      photoPlaceholder.classList.remove("hidden");
    }

    var empTrainings = trainings.filter(function (t) { return t.empId === emp.empId; });
    var tbody = document.getElementById("history-table-body");
    if (!empTrainings.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-400">ยังไม่มีบันทึกประวัติการฝึกอบรมสำหรับพนักงานท่านนี้</td></tr>';
    } else {
      tbody.innerHTML = empTrainings.map(function (item, index) {
        return '<tr class="hover:bg-slate-50 transition-colors">' +
          '<td class="border-r border-slate-300 py-2.5 px-2 text-center font-medium text-slate-700">' + (index + 1) + "</td>" +
          '<td class="border-r border-slate-300 py-2.5 px-3 font-medium text-slate-900">' + esc(item.courseName) + "</td>" +
          '<td class="border-r border-slate-300 py-2.5 px-2 text-center whitespace-nowrap text-slate-700 font-mono">' + esc(item.trainingDate) + "</td>" +
          '<td class="border-r border-slate-300 py-2.5 px-3 text-slate-800">' + esc(item.trainer) + "</td>" +
          '<td class="border-r border-slate-300 py-2.5 px-2 text-center whitespace-nowrap">' +
            '<button data-cert-id="' + item.id + '" class="th-view-cert text-blue-700 hover:text-blue-900 hover:underline font-semibold flex items-center justify-center gap-1 mx-auto">' +
            '<i data-lucide="file-check" class="w-3.5 h-3.5 text-emerald-600"></i><span>' + esc(item.evidence) + "</span></button></td>" +
          '<td class="border-r border-slate-300 py-2.5 px-2 text-center whitespace-nowrap text-slate-700">' + esc(item.recorder) + "</td>" +
          '<td class="py-2.5 px-2 text-center whitespace-nowrap text-slate-700 font-mono">' + esc(item.recordDate) + "</td></tr>";
      }).join("");
    }
    if (window.lucide) lucide.createIcons();
  }

  // ═══════════════════════════════════
  //  EXPORT PDF (history form only, A4 portrait)
  // ═══════════════════════════════════
  // The form is re-laid out at a fixed width so the PDF looks the same on any screen size.
  var PDF_RENDER_WIDTH = 900;
  var PDF_WINDOW_WIDTH = 1280;
  var PDF_MARGIN_MM = 10;

  function buildPdf(canvas, rowBottomsCss, renderMetrics, tableHeaderCanvas) {
    var pdf = new window.jspdf.jsPDF({unit: "mm", format: "a4", orientation: "portrait"});
    var contentW = pdf.internal.pageSize.getWidth() - PDF_MARGIN_MM * 2;
    var contentH = pdf.internal.pageSize.getHeight() - PDF_MARGIN_MM * 2;
    var pxPerCss = renderMetrics.height > 0 ? canvas.height / renderMetrics.height : canvas.width / PDF_RENDER_WIDTH;
    var horizontalPxPerCss = renderMetrics.width > 0 ? canvas.width / renderMetrics.width : pxPerCss;
    var mmPerPx = contentW / canvas.width;
    var pageHeightPx = Math.floor(contentH / mmPerPx);
    var cuts = rowBottomsCss.map(function (b) { return Math.round(b * pxPerCss); });
    var tableBodyTopPx = Math.round(renderMetrics.tableBodyTop * pxPerCss);
    var headerLeftPx = Math.max(0, Math.round(renderMetrics.headerLeft * horizontalPxPerCss));
    var headerWidthPx = Math.min(
      canvas.width - headerLeftPx,
      Math.round(renderMetrics.headerWidth * horizontalPxPerCss)
    );
    var headerHeightPx = tableHeaderCanvas && tableHeaderCanvas.width > 0
      ? Math.round(tableHeaderCanvas.height * (headerWidthPx / tableHeaderCanvas.width))
      : 0;

    var y = 0;
    while (y < canvas.height) {
      // Once the table continues onto another page, reserve space and copy its
      // heading row to the top so every page remains understandable on its own.
      var repeatHeader = y > 0 && y >= tableBodyTopPx && headerHeightPx > 0;
      var availableBodyHeightPx = pageHeightPx - (repeatHeader ? headerHeightPx : 0);
      var end = canvas.height;
      if (y + availableBodyHeightPx < canvas.height) {
        var fitting = cuts.filter(function (c) { return c > y && c <= y + availableBodyHeightPx; });
        end = fitting.length ? Math.max.apply(null, fitting) : y + availableBodyHeightPx;
        // Don't push a sliver of table border onto its own page.
        if (canvas.height - end < 4 * pxPerCss) end = canvas.height;
      }
      var slice = document.createElement("canvas");
      slice.width = canvas.width;
      slice.height = end - y + (repeatHeader ? headerHeightPx : 0);
      var ctx = slice.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, slice.width, slice.height);
      if (repeatHeader) {
        ctx.drawImage(tableHeaderCanvas, 0, 0, tableHeaderCanvas.width, tableHeaderCanvas.height,
          headerLeftPx, 0, headerWidthPx, headerHeightPx);
        ctx.strokeStyle = "#1e293b";
        ctx.lineWidth = Math.max(1, Math.round(horizontalPxPerCss));
        ctx.strokeRect(headerLeftPx, 0, headerWidthPx, headerHeightPx);
      }
      ctx.drawImage(canvas, 0, y, canvas.width, end - y,
        0, repeatHeader ? headerHeightPx : 0, canvas.width, end - y);
      if (y === 0 && end < canvas.height && headerWidthPx > 0) {
        // Close the table cleanly at the first page break. The normal row
        // divider is dotted, so draw a solid bottom edge for the page frame.
        ctx.strokeStyle = "#1e293b";
        ctx.lineWidth = Math.max(1, Math.round(horizontalPxPerCss));
        var firstPageBottomY = slice.height - ctx.lineWidth / 2;
        ctx.beginPath();
        ctx.moveTo(headerLeftPx, firstPageBottomY);
        ctx.lineTo(headerLeftPx + headerWidthPx, firstPageBottomY);
        ctx.stroke();
      }
      if (y > 0) pdf.addPage();
      pdf.addImage(slice.toDataURL("image/jpeg", 0.95), "JPEG", PDF_MARGIN_MM, PDF_MARGIN_MM, contentW, slice.height * mmPerPx);
      y = end;
    }
    return pdf;
  }

  window.exportHistoryPdf = function () {
    var emp = employees.find(function (e) { return e.empId === currentHistoryEmpId; }) || employees[0];
    if (!emp) return;
    if (!window.html2canvas || !window.jspdf) { alert("ยังโหลดตัวสร้าง PDF ไม่เสร็จ กรุณาลองใหม่อีกครั้ง"); return; }

    var btn = document.getElementById("exportPdfBtn");
    var label = btn.querySelector("span");
    var clone = document.querySelector("#section-history .print-container").cloneNode(true);
    clone.classList.remove("border", "rounded-xl", "shadow-sm", "p-6", "sm:p-8");
    clone.querySelectorAll("[id]").forEach(function (el) { el.removeAttribute("id"); });

    // Kept inside #thdb-root so the tool's scoped resets and fonts still apply.
    var wrapper = document.createElement("div");
    wrapper.style.cssText = "position:fixed;left:-10000px;top:0;background:#fff;width:" + PDF_RENDER_WIDTH + "px;";
    wrapper.appendChild(clone);
    root.appendChild(wrapper);

    btn.disabled = true;
    label.textContent = "กำลังสร้าง PDF...";
    var rowBottoms = [];
    var renderMetrics = {width: PDF_RENDER_WIDTH, height: 0, tableBodyTop: 0, headerLeft: 0, headerWidth: 0};
    var tableHeaderElement = wrapper.querySelector("[data-pdf-table-header], table thead");
    document.fonts.ready.then(function () {
      var mainRender = html2canvas(wrapper, {
        scale: 2, backgroundColor: "#ffffff", useCORS: true, logging: false,
        // The form's sm:/md: classes follow the window width, so render in a desktop-sized window.
        windowWidth: PDF_WINDOW_WIDTH,
        onclone: function (doc, el) {
          var rootRect = el.getBoundingClientRect();
          var top = rootRect.top;
          // Keep the tag selector as a fallback for pages that were rendered
          // before the data marker was added but load this newer JavaScript.
          var thead = el.querySelector("[data-pdf-table-header], table thead");
          var table = thead ? thead.closest("table") : null;
          var rows = table ? table.querySelectorAll("tbody tr") : el.querySelectorAll("tr");
          rowBottoms = Array.prototype.map.call(rows, function (tr) {
            return tr.getBoundingClientRect().bottom - top;
          });
          renderMetrics.width = rootRect.width;
          renderMetrics.height = rootRect.height;
          if (thead) {
            var headerRect = thead.getBoundingClientRect();
            var firstRow = rows.length ? rows[0].getBoundingClientRect() : headerRect;
            renderMetrics.tableBodyTop = firstRow.top - top;
            renderMetrics.headerLeft = headerRect.left - rootRect.left;
            renderMetrics.headerWidth = headerRect.width;
          }
        },
      });
      var headerRender = tableHeaderElement ? html2canvas(tableHeaderElement, {
        scale: 2, backgroundColor: "#e2e8f0", useCORS: true, logging: false,
        windowWidth: PDF_WINDOW_WIDTH,
      }) : Promise.resolve(null);
      return Promise.all([mainRender, headerRender]);
    }).then(function (rendered) {
      openPdfPreview(buildPdf(rendered[0], rowBottoms, renderMetrics, rendered[1]), "Training_History_" + emp.historyNo + "_" + emp.empId + ".pdf");
    }).catch(function () {
      alert("สร้างไฟล์ PDF ไม่สำเร็จ");
    }).then(function () {
      wrapper.remove();
      btn.disabled = false;
      label.textContent = "Export PDF";
    });
  };

  var pdfPreview = null;

  function openPdfPreview(pdf, filename) {
    var blob = pdf.output("blob");
    pdfPreview = {pdf: pdf, blob: blob, filename: filename, url: URL.createObjectURL(blob)};
    document.getElementById("pdf-preview-frame").src = pdfPreview.url + "#view=FitH";
    document.getElementById("pdf-preview-filename").textContent = filename;
    document.getElementById("pdf-preview-info").textContent =
      pdf.getNumberOfPages() + " หน้า · A4 แนวตั้ง · " + (blob.size / 1024).toFixed(0) + " KB";
    document.getElementById("modal-pdf-preview").classList.remove("hidden");
  }

  window.closePdfPreview = function () {
    document.getElementById("modal-pdf-preview").classList.add("hidden");
    document.getElementById("pdf-preview-frame").removeAttribute("src");
    if (pdfPreview) URL.revokeObjectURL(pdfPreview.url);
    pdfPreview = null;
  };

  window.savePreviewPdf = function () {
    if (!pdfPreview) return;
    var current = pdfPreview;
    // The native "Save As" picker only exists in Chromium browsers on a secure origin (https or localhost).
    if (!window.showSaveFilePicker) {
      current.pdf.save(current.filename);
      return;
    }
    var saveBtn = document.getElementById("pdfSaveBtn");
    window.showSaveFilePicker({
      suggestedName: current.filename,
      types: [{description: "PDF Document", accept: {"application/pdf": [".pdf"]}}],
    }).then(function (handle) {
      saveBtn.disabled = true;
      return handle.createWritable().then(function (writable) {
        return writable.write(current.blob).then(function () { return writable.close(); });
      }).then(function () {
        closePdfPreview();
        alert("บันทึกไฟล์ " + handle.name + " เรียบร้อยแล้ว");
      });
    }).catch(function (err) {
      if (err && err.name === "AbortError") return;
      alert("บันทึกไฟล์ไม่สำเร็จ");
    }).then(function () {
      saveBtn.disabled = false;
    });
  };

  // ═══════════════════════════════════
  //  SECTION 2: EMPLOYEES
  // ═══════════════════════════════════
  function renderEmployeesTable(data) {
    var tbody = document.getElementById("employees-table-body");
    document.getElementById("employee-count-badge").textContent = "แสดง " + data.length + " คน (จากทั้งหมด " + employees.length + " คน)";
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="12" class="py-8 text-center text-slate-400">ไม่พบข้อมูลพนักงานที่ตรงกับเงื่อนไข</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(function (emp) {
      var photoCell = emp.photoUrl
        ? '<img src="' + esc(emp.photoUrl) + '" alt="" class="w-8 h-8 rounded-full object-cover mx-auto border border-slate-200 shadow-sm">'
        : '<span class="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 mx-auto flex items-center justify-center text-slate-400"><i data-lucide="user" class="w-4 h-4"></i></span>';
      return '<tr class="hover:bg-slate-50 transition-colors">' +
        '<td class="py-2.5 px-3 text-center border-r border-slate-100">' + photoCell + "</td>" +
        '<td class="py-2.5 px-3 font-mono text-center border-r border-slate-100 text-slate-700 font-semibold">' + esc(emp.empId) + "</td>" +
        '<td class="py-2.5 px-3 font-medium text-slate-900 border-r border-slate-100 whitespace-nowrap">' + esc(emp.nameEn) + "</td>" +
        '<td class="py-2.5 px-3 text-center border-r border-slate-100"><span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">' + esc(emp.group) + "</span></td>" +
        '<td class="py-2.5 px-3 text-center border-r border-slate-100 font-mono text-slate-700 font-medium">' + esc(emp.position) + "</td>" +
        '<td class="py-2.5 px-3 text-slate-700 border-r border-slate-100 whitespace-nowrap">' + esc(emp.education) + "</td>" +
        '<td class="py-2.5 px-3 text-center font-mono border-r border-slate-100 whitespace-nowrap text-slate-600">' + esc(emp.workStartDisplay) + "</td>" +
        '<td class="py-2.5 px-2 text-center border-r border-slate-100 font-semibold text-slate-700">' + (emp.workYears == null ? "—" : emp.workYears) + "</td>" +
        '<td class="py-2.5 px-3 text-center font-mono border-r border-slate-100 whitespace-nowrap text-slate-600">' + esc(emp.birthdayDisplay) + "</td>" +
        '<td class="py-2.5 px-2 text-center border-r border-slate-100 font-semibold text-slate-700">' + (emp.age == null ? "—" : emp.age) + "</td>" +
        '<td class="py-2.5 px-3 text-center border-r border-slate-100"><span class="px-2 py-0.5 text-[11px] ' + statusBadgeClass(emp) + '">' + esc(emp.status) + "</span></td>" +
        '<td class="py-2.5 px-3 text-center whitespace-nowrap">' +
          '<button data-view-history="' + esc(emp.empId) + '" class="th-view-history px-2.5 py-1 text-[11px] bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white rounded border border-blue-200 transition-colors font-medium">ดูประวัติ</button>' +
          (CAN_EDIT ?
            ' <button data-edit-emp="' + emp.id + '" class="th-edit-emp px-2 py-1 text-[11px] bg-amber-50 text-amber-700 hover:bg-amber-600 hover:text-white rounded border border-amber-200 transition-colors font-medium">แก้ไข</button>' +
            ' <button data-del-emp="' + emp.id + '" data-del-emp-label="' + esc(emp.empId + " — " + emp.nameEn) + '" class="th-del-emp px-2 py-1 text-[11px] bg-red-50 text-red-700 hover:bg-red-600 hover:text-white rounded border border-red-200 transition-colors font-medium">ลบ</button>'
            : "") +
        "</td></tr>";
    }).join("");
    if (window.lucide) lucide.createIcons();
  }

  window.filterEmployees = function () {
    var q = (document.getElementById("employeeSearchInput").value || "").trim().toLowerCase();
    var group = document.getElementById("employeeGroupFilter").value;
    var filtered = employees.filter(function (emp) {
      var matchesQuery = emp.nameEn.toLowerCase().indexOf(q) >= 0 || emp.nameTh.toLowerCase().indexOf(q) >= 0 ||
        emp.empId.toLowerCase().indexOf(q) >= 0 || emp.group.toLowerCase().indexOf(q) >= 0;
      var matchesGroup = true;
      if (group === "All") matchesGroup = true;
      else if (group === "ISO") matchesGroup = emp.group.toUpperCase().indexOf("ISO") >= 0;
      else matchesGroup = emp.group.toUpperCase() === group.toUpperCase();
      return matchesQuery && matchesGroup;
    });
    renderEmployeesTable(filtered);
  };

  // ═══════════════════════════════════
  //  SECTION 3: TRAINING COURSES
  // ═══════════════════════════════════
  function renderCoursesTable(data) {
    var tbody = document.getElementById("courses-table-body");
    document.getElementById("courses-count-badge").textContent = "แสดง " + data.length + " รายการ (จากทั้งหมด " + trainings.length + " รายการ)";
    if (!data.length) {
      tbody.innerHTML = '<tr><td colspan="10" class="py-8 text-center text-slate-400">ไม่พบหลักสูตรการฝึกอบรมที่ค้นหา</td></tr>';
      return;
    }
    var counters = {};
    tbody.innerHTML = data.map(function (item) {
      counters[item.empId] = (counters[item.empId] || 0) + 1;
      return '<tr class="hover:bg-slate-50 transition-colors">' +
        '<td class="py-2.5 px-3 font-mono text-center border-r border-slate-100 text-blue-700 font-semibold">' +
          '<button data-view-history="' + esc(item.empId) + '" class="th-view-history hover:underline">' + esc(item.empId) + "</button></td>" +
        '<td class="py-2.5 px-2 text-center border-r border-slate-100 font-medium text-slate-600">' + counters[item.empId] + "</td>" +
        '<td class="py-2.5 px-4 font-medium text-slate-900 border-r border-slate-100">' + esc(item.courseName) + "</td>" +
        '<td class="py-2.5 px-3 text-center font-mono border-r border-slate-100 whitespace-nowrap text-slate-700">' + esc(item.trainingDate) + "</td>" +
        '<td class="py-2.5 px-4 text-slate-800 border-r border-slate-100">' + esc(item.trainer) + "</td>" +
        '<td class="py-2.5 px-3 text-center border-r border-slate-100 whitespace-nowrap"><span class="px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded font-medium border border-emerald-200">' + esc(item.evidence) + "</span></td>" +
        '<td class="py-2.5 px-3 text-center border-r border-slate-100 whitespace-nowrap text-slate-600">' + esc(item.recorder) + "</td>" +
        '<td class="py-2.5 px-3 text-center font-mono border-r border-slate-100 whitespace-nowrap text-slate-600">' + esc(item.recordDate) + "</td>" +
        '<td class="py-2.5 px-3 text-center border-r border-slate-100 whitespace-nowrap">' +
          '<button data-cert-id="' + item.id + '" class="th-view-cert inline-flex items-center gap-1.5 text-blue-600 hover:text-blue-800 hover:underline font-mono text-xs font-semibold whitespace-nowrap">' +
          '<i data-lucide="eye" class="w-3.5 h-3.5 text-blue-500 flex-shrink-0"></i><span class="whitespace-nowrap">' + esc(item.refId || "-") + "</span></button></td>" +
        '<td class="py-2.5 px-3 text-center whitespace-nowrap">' +
          '<button data-view-history="' + esc(item.empId) + '" class="th-view-history p-1 text-slate-400 hover:text-blue-600" title="ดูประวัติพนักงาน"><i data-lucide="external-link" class="w-4 h-4"></i></button>' +
          (CAN_EDIT ?
            ' <button data-edit-training="' + item.id + '" class="th-edit-training px-2 py-1 text-[11px] bg-amber-50 text-amber-700 hover:bg-amber-600 hover:text-white rounded border border-amber-200 transition-colors font-medium">แก้ไข</button>' +
            ' <button data-del-training="' + item.id + '" data-del-training-label="' + esc(item.courseName) + '" class="th-del-training px-2 py-1 text-[11px] bg-red-50 text-red-700 hover:bg-red-600 hover:text-white rounded border border-red-200 transition-colors font-medium">ลบ</button>'
            : "") +
        "</td></tr>";
    }).join("");
    if (window.lucide) lucide.createIcons();
  }

  window.filterCourses = function () {
    var q = (document.getElementById("courseSearchInput").value || "").trim().toLowerCase();
    var trainer = document.getElementById("courseTrainerFilter").value;
    var filtered = trainings.filter(function (item) {
      var matchesQuery = item.courseName.toLowerCase().indexOf(q) >= 0 || item.trainer.toLowerCase().indexOf(q) >= 0 ||
        (item.refId && item.refId.toLowerCase().indexOf(q) >= 0) || item.empId.toLowerCase().indexOf(q) >= 0;
      var matchesTrainer = (trainer === "All") || item.trainer.indexOf(trainer) >= 0;
      return matchesQuery && matchesTrainer;
    });
    renderCoursesTable(filtered);
  };

  // ═══════════════════════════════════
  //  PHOTO / DOC UPLOAD PREVIEWS
  // ═══════════════════════════════════
  window.handlePhotoUpload = function (event) {
    var file = event.target.files[0];
    if (!file) return;
    if (!file.type.match(/^image\//)) { alert("กรุณาเลือกไฟล์รูปภาพเท่านั้น"); return; }
    var reader = new FileReader();
    reader.onload = function (e) {
      var img = document.getElementById("newEmpPhotoPreview");
      img.src = e.target.result;
      img.classList.remove("hidden");
      document.getElementById("newEmpPhotoPlaceholder").classList.add("hidden");
      document.getElementById("uploadedPhotoName").textContent = file.name;
    };
    reader.readAsDataURL(file);
  };

  // Set when the user clicks "ล้างรูป" so saving an edit also deletes the stored photo.
  var removeExistingPhoto = false;

  window.clearPhotoUpload = function () {
    resetPhotoInput();
    removeExistingPhoto = true;
    var editPk = parseInt(document.getElementById("editEmpPk").value, 10);
    var emp = employees.find(function (e) { return e.id === editPk; });
    if (emp && emp.photoUrl) {
      document.getElementById("uploadedPhotoName").textContent = "รูปเดิมจะถูกลบเมื่อกด \"บันทึกการแก้ไข\"";
    }
  };

  function resetPhotoInput() {
    removeExistingPhoto = false;
    document.getElementById("newEmpPhotoFile").value = "";
    var img = document.getElementById("newEmpPhotoPreview");
    img.src = "";
    img.classList.add("hidden");
    document.getElementById("newEmpPhotoPlaceholder").classList.remove("hidden");
    document.getElementById("uploadedPhotoName").textContent = "";
  }

  window.handleTrainingDocUpload = function (event) {
    var file = event.target.files[0];
    if (!file) return;
    var isPdf = file.type === "application/pdf" || /\.pdf$/i.test(file.name);
    var isImg = file.type.match(/^image\//);
    if (!isPdf && !isImg) { alert("กรุณาเลือกไฟล์รูปภาพ (PNG, JPG) หรือไฟล์ PDF เท่านั้น"); return; }
    document.getElementById("uploadedTrainDocName").textContent = file.name + " (" + (file.size / 1024).toFixed(1) + " KB)";
    var previewBox = document.getElementById("trainFilePreviewBox");
    if (isPdf) {
      previewBox.innerHTML = '<div class="flex flex-col items-center justify-center text-red-600"><i data-lucide="file-text" class="w-7 h-7"></i><span class="text-[9px] font-bold mt-0.5">PDF</span></div>';
      if (window.lucide) lucide.createIcons();
    } else {
      var reader = new FileReader();
      reader.onload = function (e) { previewBox.innerHTML = '<img src="' + e.target.result + '" alt="Preview" class="w-full h-full object-cover">'; };
      reader.readAsDataURL(file);
    }
  };

  window.clearTrainingDocUpload = function () {
    document.getElementById("trainDocFile").value = "";
    document.getElementById("uploadedTrainDocName").textContent = "";
    var previewBox = document.getElementById("trainFilePreviewBox");
    previewBox.innerHTML = '<i data-lucide="file-text" class="w-7 h-7 text-slate-400"></i>';
    if (window.lucide) lucide.createIcons();
  };

  // ═══════════════════════════════════
  //  MODALS
  // ═══════════════════════════════════
  function setEmpModalMode(editing) {
    document.getElementById("empModalTitle").querySelector("span").textContent =
      editing ? "แก้ไขข้อมูลพนักงาน (Edit Employee)" : "เพิ่มข้อมูลพนักงานใหม่ (New Employee)";
    document.getElementById("empSubmitBtn").textContent = editing ? "บันทึกการแก้ไข" : "บันทึกพนักงาน";
    document.getElementById("newEmpId").disabled = editing;
    document.getElementById("newEmpHistoryNo").disabled = editing;
  }

  window.openAddEmployeeModal = function () {
    document.getElementById("modal-add-employee").classList.remove("hidden");
    document.getElementById("formAddEmployee").reset();
    document.getElementById("editEmpPk").value = "";
    setEmpModalMode(false);
    resetPhotoInput();
  };
  window.openEditEmployeeModal = function (pk) {
    var emp = employees.find(function (e) { return e.id === pk; });
    if (!emp) return;
    document.getElementById("formAddEmployee").reset();
    document.getElementById("editEmpPk").value = emp.id;
    document.getElementById("newEmpId").value = emp.empId;
    document.getElementById("newEmpHistoryNo").value = emp.historyNo;
    document.getElementById("newEmpNameTh").value = emp.nameTh;
    document.getElementById("newEmpNameEn").value = emp.nameEn;
    document.getElementById("newEmpGroup").value = emp.group;
    document.getElementById("newEmpPosition").value = emp.position;
    document.getElementById("newEmpEducation").value = emp.education;
    document.getElementById("newEmpStart").value = emp.workStart || "";
    document.getElementById("newEmpBirth").value = emp.birthday || "";
    document.getElementById("newEmpStatus").value = emp.statusCode || "active";
    resetPhotoInput();
    if (emp.photoUrl) {
      var img = document.getElementById("newEmpPhotoPreview");
      img.src = emp.photoUrl;
      img.classList.remove("hidden");
      document.getElementById("newEmpPhotoPlaceholder").classList.add("hidden");
      document.getElementById("uploadedPhotoName").textContent = "รูปปัจจุบัน — เลือกไฟล์ใหม่เพื่อเปลี่ยน";
    }
    setEmpModalMode(true);
    document.getElementById("modal-add-employee").classList.remove("hidden");
  };
  window.closeAddEmployeeModal = function () {
    document.getElementById("modal-add-employee").classList.add("hidden");
  };

  function setTrainingModalMode(editing) {
    document.getElementById("trainingModalTitle").querySelector("span").textContent =
      editing ? "แก้ไขข้อมูลการฝึกอบรม (Edit Training Record)" : "บันทึกข้อมูลการฝึกอบรม (Training Record)";
    document.getElementById("trainingSubmitBtn").textContent = editing ? "บันทึกการแก้ไข" : "บันทึกรายการ";
  }

  window.openAddTrainingModal = function () {
    document.getElementById("modal-add-training").classList.remove("hidden");
    document.getElementById("formAddTraining").reset();
    document.getElementById("editTrainingPk").value = "";
    setTrainingModalMode(false);
    clearTrainingDocUpload();
    var tSelect = document.getElementById("trainEmployeeSelect");
    if (tSelect && currentHistoryEmpId) tSelect.value = currentHistoryEmpId;
  };
  window.openEditTrainingModal = function (pk) {
    var item = trainings.find(function (t) { return t.id === pk; });
    if (!item) return;
    document.getElementById("formAddTraining").reset();
    document.getElementById("editTrainingPk").value = item.id;
    document.getElementById("trainEmployeeSelect").value = item.empId;
    document.getElementById("trainCourseName").value = item.courseName;
    document.getElementById("trainDate").value = item.trainingDate;
    document.getElementById("trainInstitute").value = item.trainer;
    document.getElementById("trainEvidence").value = item.evidence;
    document.getElementById("trainRefId").value = item.refId;
    document.getElementById("trainRecorder").value = item.recorder;
    document.getElementById("trainRecordDate").value = item.recordDate;
    clearTrainingDocUpload();
    if (item.docUrl) {
      document.getElementById("uploadedTrainDocName").textContent = "มีไฟล์แนบอยู่แล้ว — เลือกไฟล์ใหม่เพื่อเปลี่ยน";
      var previewBox = document.getElementById("trainFilePreviewBox");
      if (item.docType === "pdf") {
        previewBox.innerHTML = '<div class="flex flex-col items-center justify-center text-red-600"><i data-lucide="file-text" class="w-7 h-7"></i><span class="text-[9px] font-bold mt-0.5">PDF</span></div>';
      } else {
        previewBox.innerHTML = '<img src="' + esc(item.docUrl) + '" alt="Preview" class="w-full h-full object-cover">';
      }
      if (window.lucide) lucide.createIcons();
    }
    setTrainingModalMode(true);
    document.getElementById("modal-add-training").classList.remove("hidden");
  };
  window.closeAddTrainingModal = function () {
    document.getElementById("modal-add-training").classList.add("hidden");
  };

  function viewCertificate(trainingId) {
    var item = trainings.find(function (t) { return t.id === trainingId; });
    if (!item) return;
    document.getElementById("cert-modal-ref").textContent = "REF: " + (item.refId || "N/A");
    document.getElementById("cert-modal-title").textContent = "หลักฐานผ่านการฝึกอบรม (Certificate / Evidence)";
    var modalBody = document.getElementById("cert-modal-body");
    var fileInfoSpan = document.getElementById("cert-modal-file-info");

    if (item.docUrl) {
      fileInfoSpan.textContent = "เอกสารแนบ: " + (item.refId || "ไฟล์แนบ");
      if (item.docType === "pdf") {
        modalBody.innerHTML = '<div class="w-full h-[400px] flex flex-col items-center"><iframe src="' + esc(item.docUrl) + '" class="w-full h-full rounded border border-slate-300"></iframe></div>';
      } else {
        modalBody.innerHTML = '<div class="w-full flex flex-col items-center justify-center p-2">' +
          '<img src="' + esc(item.docUrl) + '" alt="Certificate" class="max-h-[380px] max-w-full rounded border border-slate-200 shadow object-contain mb-3">' +
          '<h4 class="font-bold text-slate-800 text-sm">' + esc(item.courseName) + '</h4>' +
          '<p class="text-xs text-slate-600 mt-0.5">ผู้ฝึกอบรม / สถาบัน: ' + esc(item.trainer) + "</p></div>";
      }
    } else {
      fileInfoSpan.textContent = "ไม่มีไฟล์แนบ";
      modalBody.innerHTML = '<div class="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mb-3"><i data-lucide="file-check-2" class="w-8 h-8"></i></div>' +
        '<h4 class="font-bold text-slate-800 text-sm max-w-md">' + esc(item.courseName) + '</h4>' +
        '<p class="text-xs text-slate-600 mt-1">ผู้ฝึกอบรม / สถาบัน: ' + esc(item.trainer) + '</p>' +
        '<span class="mt-4 px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-full flex items-center gap-1">' +
        '<i data-lucide="check-circle" class="w-3.5 h-3.5"></i>ผ่านการประเมินและได้รับ ' + esc(item.evidence) + " (REF: " + esc(item.refId || "-") + ")</span>";
    }
    document.getElementById("modal-cert-viewer").classList.remove("hidden");
    if (window.lucide) lucide.createIcons();
  }
  window.closeCertModal = function () {
    document.getElementById("modal-cert-viewer").classList.add("hidden");
  };

  document.addEventListener("click", function (e) {
    var certBtn = e.target.closest(".th-view-cert");
    if (certBtn) { viewCertificate(parseInt(certBtn.getAttribute("data-cert-id"), 10)); return; }
    var histBtn = e.target.closest(".th-view-history");
    if (histBtn) { viewEmployeeHistory(histBtn.getAttribute("data-view-history")); return; }
    var editEmpBtn = e.target.closest(".th-edit-emp");
    if (editEmpBtn) { openEditEmployeeModal(parseInt(editEmpBtn.getAttribute("data-edit-emp"), 10)); return; }
    var delEmpBtn = e.target.closest(".th-del-emp");
    if (delEmpBtn) {
      deleteEmployee(parseInt(delEmpBtn.getAttribute("data-del-emp"), 10), delEmpBtn.getAttribute("data-del-emp-label"));
      return;
    }
    var editTrainingBtn = e.target.closest(".th-edit-training");
    if (editTrainingBtn) { openEditTrainingModal(parseInt(editTrainingBtn.getAttribute("data-edit-training"), 10)); return; }
    var delTrainingBtn = e.target.closest(".th-del-training");
    if (delTrainingBtn) {
      deleteTraining(parseInt(delTrainingBtn.getAttribute("data-del-training"), 10), delTrainingBtn.getAttribute("data-del-training-label"));
    }
  });

  // ═══════════════════════════════════
  //  FORM SUBMISSION
  // ═══════════════════════════════════
  function apiPostForm(url, formData) {
    return fetch(url, {
      method: "POST",
      headers: {"X-CSRFToken": CSRF},
      body: formData,
    }).then(function (resp) {
      return resp.json().then(function (data) { return {status: resp.status, data: data}; });
    });
  }

  window.handleSaveEmployee = function (e) {
    e.preventDefault();
    var fd = new FormData();
    fd.append("empId", document.getElementById("newEmpId").value.trim());
    fd.append("historyNo", document.getElementById("newEmpHistoryNo").value.trim());
    fd.append("nameTh", document.getElementById("newEmpNameTh").value.trim());
    fd.append("nameEn", document.getElementById("newEmpNameEn").value.trim());
    fd.append("group", document.getElementById("newEmpGroup").value);
    fd.append("position", document.getElementById("newEmpPosition").value.trim());
    fd.append("education", document.getElementById("newEmpEducation").value.trim());
    fd.append("workStart", document.getElementById("newEmpStart").value);
    fd.append("birthday", document.getElementById("newEmpBirth").value);
    fd.append("status", document.getElementById("newEmpStatus").value);
    var photoFile = document.getElementById("newEmpPhotoFile").files[0];
    if (photoFile) fd.append("photo", photoFile);
    else if (removeExistingPhoto) fd.append("removePhoto", "1");

    var editPk = document.getElementById("editEmpPk").value;
    var isEdit = !!editPk;
    var url = isEdit ? urlForPk(EMPLOYEE_UPDATE_URL_TPL, editPk) : EMPLOYEE_CREATE_URL;

    var submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    apiPostForm(url, fd).then(function (res) {
      submitBtn.disabled = false;
      if (!res.data.ok) { alert(res.data.message || "บันทึกไม่สำเร็จ"); return; }
      if (isEdit) {
        var idx = employees.findIndex(function (e) { return e.id === res.data.employee.id; });
        if (idx !== -1) employees[idx] = res.data.employee;
      } else {
        employees.unshift(res.data.employee);
      }
      currentHistoryEmpId = res.data.employee.empId;
      populateHistorySelect();
      renderEmployeesTable(employees);
      renderCoursesTable(trainings);
      if (currentHistoryEmpId === res.data.employee.empId) renderHistoryPage();
      closeAddEmployeeModal();
      alert(isEdit ? "แก้ไขข้อมูลพนักงาน " + res.data.employee.nameEn + " เรียบร้อยแล้ว" : "บันทึกข้อมูลพนักงาน " + res.data.employee.nameEn + " เรียบร้อยแล้ว");
    }).catch(function () {
      submitBtn.disabled = false;
      alert("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้");
    });
  };

  window.deleteEmployee = function (pk, label) {
    if (!confirm("ยืนยันการลบพนักงาน \"" + label + "\" ?\nประวัติการอบรมทั้งหมดของพนักงานคนนี้จะถูกลบไปด้วย และไม่สามารถกู้คืนได้")) return;
    apiPostForm(urlForPk(EMPLOYEE_DELETE_URL_TPL, pk), new FormData()).then(function (res) {
      if (!res.data.ok) { alert(res.data.message || "ลบไม่สำเร็จ"); return; }
      employees = employees.filter(function (e) { return e.id !== pk; });
      trainings = trainings.filter(function (t) { return t.empId !== res.data.empId; });
      populateHistorySelect();
      renderEmployeesTable(employees);
      renderCoursesTable(trainings);
      if (currentHistoryEmpId === res.data.empId) {
        currentHistoryEmpId = employees.length ? employees[0].empId : null;
        renderHistoryPage();
      }
      alert("ลบข้อมูลพนักงานเรียบร้อยแล้ว");
    }).catch(function () {
      alert("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้");
    });
  };

  window.handleSaveTraining = function (e) {
    e.preventDefault();
    var fd = new FormData();
    fd.append("empId", document.getElementById("trainEmployeeSelect").value);
    fd.append("courseName", document.getElementById("trainCourseName").value.trim());
    fd.append("trainingDate", document.getElementById("trainDate").value.trim());
    fd.append("trainer", document.getElementById("trainInstitute").value.trim());
    fd.append("evidence", document.getElementById("trainEvidence").value.trim());
    fd.append("refId", document.getElementById("trainRefId").value.trim());
    fd.append("recorder", document.getElementById("trainRecorder").value.trim());
    fd.append("recordDate", document.getElementById("trainRecordDate").value.trim());
    var docFile = document.getElementById("trainDocFile").files[0];
    if (docFile) fd.append("docFile", docFile);

    var editPk = document.getElementById("editTrainingPk").value;
    var isEdit = !!editPk;
    var url = isEdit ? urlForPk(TRAINING_UPDATE_URL_TPL, editPk) : TRAINING_CREATE_URL;

    var submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    apiPostForm(url, fd).then(function (res) {
      submitBtn.disabled = false;
      if (!res.data.ok) { alert(res.data.message || "บันทึกไม่สำเร็จ"); return; }
      if (isEdit) {
        var idx = trainings.findIndex(function (t) { return t.id === res.data.training.id; });
        if (idx !== -1) trainings[idx] = res.data.training;
      } else {
        trainings.unshift(res.data.training);
      }
      closeAddTrainingModal();
      if (currentHistoryEmpId === res.data.training.empId) renderHistoryPage();
      renderCoursesTable(trainings);
      alert(isEdit ? "แก้ไขข้อมูลประวัติการอบรมเรียบร้อยแล้ว" : "บันทึกข้อมูลประวัติการอบรมเรียบร้อยแล้ว");
    }).catch(function () {
      submitBtn.disabled = false;
      alert("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้");
    });
  };

  window.deleteTraining = function (pk, label) {
    if (!confirm("ยืนยันการลบประวัติการอบรม \"" + label + "\" ?\nไม่สามารถกู้คืนได้")) return;
    apiPostForm(urlForPk(TRAINING_DELETE_URL_TPL, pk), new FormData()).then(function (res) {
      if (!res.data.ok) { alert(res.data.message || "ลบไม่สำเร็จ"); return; }
      var removed = trainings.find(function (t) { return t.id === pk; });
      trainings = trainings.filter(function (t) { return t.id !== pk; });
      renderCoursesTable(trainings);
      if (removed && currentHistoryEmpId === removed.empId) renderHistoryPage();
      alert("ลบข้อมูลประวัติการอบรมเรียบร้อยแล้ว");
    }).catch(function () {
      alert("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้");
    });
  };

  // ═══════════════════════════════════
  //  INIT
  // ═══════════════════════════════════
  var appNav = document.querySelector("header.nav");
  function syncNavHeight() {
    if (appNav) document.documentElement.style.setProperty("--th-nav-h", appNav.offsetHeight + "px");
  }
  syncNavHeight();
  // The navbar grows once its web font loads (Thai labels wrap), after this runs.
  if (appNav && window.ResizeObserver) new ResizeObserver(syncNavHeight).observe(appNav);
  else window.addEventListener("resize", syncNavHeight);

  populateHistorySelect();
  renderHistoryPage();
  renderEmployeesTable(employees);
  renderCoursesTable(trainings);
  if (window.lucide) lucide.createIcons();
})();
