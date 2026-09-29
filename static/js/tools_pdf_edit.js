(function () {
  "use strict";

  var script = document.currentScript;
  var URLS = {
    pageCount: script.getAttribute("data-page-count-url"),
    merge: script.getAttribute("data-merge-url"),
    split: script.getAttribute("data-split-url"),
    del: script.getAttribute("data-delete-url"),
    insert: script.getAttribute("data-insert-url"),
    lock: script.getAttribute("data-lock-url"),
    unlock: script.getAttribute("data-unlock-url"),
  };

  var csrfToken = document.querySelector('#pdf-csrf-form [name="csrfmiddlewaretoken"]').value;

  var FILE_ICON_SVG =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">' +
    '<path d="M6 2h9l5 5v15H6z"/><path d="M15 2v5h5"/></svg>';

  // ---------------- generic helpers ----------------
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function isPdf(file) {
    return file && (file.type === "application/pdf" || /\.pdf$/i.test(file.name));
  }

  function parseFilename(disposition, fallback) {
    if (!disposition) return fallback;
    var m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition);
    return m ? decodeURIComponent(m[1]) : fallback;
  }

  function downloadBlob(blob, filename) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }

  function setStatus(prefix, state, text) {
    var dot = document.getElementById(prefix + "-status-dot");
    var label = document.getElementById(prefix + "-status-text");
    if (dot) dot.className = "pdf-status-dot" + (state ? " " + state : "");
    if (label) label.textContent = text;
  }

  function setProgress(prefix, pct) {
    var fill = document.getElementById(prefix + "-progress-fill");
    if (fill) fill.style.width = pct + "%";
  }

  // Multipart POST with an upload-progress bar; on success triggers a
  // file download, on failure surfaces the server's JSON {error} text.
  function submitOperation(prefix, opts) {
    setStatus(prefix, "busy", opts.busyText);
    setProgress(prefix, 0);
    var submitBtn = document.getElementById(prefix + "-submit-btn");
    if (submitBtn) submitBtn.disabled = true;

    var xhr = new XMLHttpRequest();
    xhr.open("POST", opts.url, true);
    xhr.responseType = "blob";
    xhr.setRequestHeader("X-CSRFToken", csrfToken);

    xhr.upload.addEventListener("progress", function (e) {
      if (e.lengthComputable) {
        setProgress(prefix, Math.round((e.loaded / e.total) * 90));
      }
    });

    xhr.addEventListener("load", function () {
      if (xhr.status >= 200 && xhr.status < 300) {
        setProgress(prefix, 100);
        var filename = parseFilename(xhr.getResponseHeader("Content-Disposition"), opts.fallbackFilename);
        setStatus(prefix, "ok", "ดำเนินการเสร็จแล้ว — กรุณาตั้งชื่อไฟล์เพื่อบันทึก");
        openSaveModal(xhr.response, filename, {
          onSaved: function () {
            setStatus(prefix, "ok", opts.successText);
            if (opts.onDone) opts.onDone();
          },
          onCancelled: function () {
            setStatus(prefix, "", "ยกเลิกการบันทึกไฟล์ — ผลลัพธ์ยังไม่ได้บันทึก");
            setProgress(prefix, 0);
          },
        });
      } else {
        readErrorBlob(xhr.response, function (message) { setStatus(prefix, "err", message); });
        setProgress(prefix, 0);
      }
      if (submitBtn) submitBtn.disabled = false;
    });
    xhr.addEventListener("error", function () {
      setStatus(prefix, "err", "เกิดข้อผิดพลาดในการเชื่อมต่อ — กรุณาลองใหม่อีกครั้ง");
      setProgress(prefix, 0);
      if (submitBtn) submitBtn.disabled = false;
    });
    xhr.send(opts.formData);
  }

  function readErrorBlob(blob, cb) {
    var fallback = "เกิดข้อผิดพลาด — กรุณาลองใหม่อีกครั้ง";
    if (!blob) { cb(fallback); return; }
    var reader = new FileReader();
    reader.onload = function () {
      try {
        var data = JSON.parse(reader.result);
        cb(data.error || fallback);
      } catch (e) {
        cb(fallback);
      }
    };
    reader.onerror = function () { cb(fallback); };
    reader.readAsText(blob);
  }

  function fetchPageCount(file, onSuccess, onError) {
    var fd = new FormData();
    fd.append("csrfmiddlewaretoken", csrfToken);
    fd.append("file", file);
    fetch(URLS.pageCount, { method: "POST", body: fd })
      .then(function (r) {
        return r.json().then(function (data) { return { ok: r.ok, data: data }; });
      })
      .then(function (res) {
        if (res.ok) onSuccess(res.data.pages);
        else onError(res.data.error || "ไม่สามารถอ่านไฟล์ได้");
      })
      .catch(function () { onError("เกิดข้อผิดพลาดในการเชื่อมต่อ"); });
  }

  function populatePageList(selectEl, pages) {
    selectEl.innerHTML = "";
    for (var i = 1; i <= pages; i++) {
      var opt = document.createElement("option");
      opt.value = String(i);
      opt.textContent = "หน้า " + i;
      selectEl.appendChild(opt);
    }
    selectEl.disabled = pages === 0;
  }

  // ---------------- single-file picker (button + drag&drop target) ----------------
  function bindSingleFilePicker(btn, input, nameEl, clearBtn, placeholder, onSelect) {
    var current = null;

    function setFile(file) {
      current = file || null;
      if (!current) {
        nameEl.textContent = placeholder;
        nameEl.classList.remove("has-file");
        if (clearBtn) clearBtn.hidden = true;
      } else {
        nameEl.textContent = current.name + " (" + formatSize(current.size) + ")";
        nameEl.classList.add("has-file");
        if (clearBtn) clearBtn.hidden = false;
      }
      if (onSelect) onSelect(current);
    }

    btn.addEventListener("click", function () {
      input.value = "";
      input.click();
    });
    input.addEventListener("change", function () {
      setFile(input.files[0] || null);
    });
    nameEl.addEventListener("dragover", function (e) {
      e.preventDefault();
      nameEl.classList.add("dragover-hint");
    });
    nameEl.addEventListener("dragleave", function () {
      nameEl.classList.remove("dragover-hint");
    });
    nameEl.addEventListener("drop", function (e) {
      e.preventDefault();
      nameEl.classList.remove("dragover-hint");
      var f = e.dataTransfer.files && e.dataTransfer.files[0];
      if (isPdf(f)) setFile(f);
    });
    if (clearBtn) {
      clearBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        input.value = "";
        setFile(null);
      });
    }

    return {
      getFile: function () { return current; },
      clear: function () { input.value = ""; setFile(null); },
    };
  }

  // ---------------- save-location modal (shown after every successful op) ----------------
  function guessSaveType(filename) {
    if (/\.zip$/i.test(filename)) {
      return { description: "ZIP archive", accept: { "application/zip": [".zip"] } };
    }
    return { description: "PDF document", accept: { "application/pdf": [".pdf"] } };
  }

  // Writes the blob via the native OS save dialog (File System Access API)
  // when available, letting the user rename it and pick the folder;
  // otherwise falls back to a normal browser download with the chosen
  // name. Returns false only when the user cancelled the OS dialog.
  async function saveBlob(blob, filename) {
    if (window.showSaveFilePicker) {
      try {
        var handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [guessSaveType(filename)],
        });
        var writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        return true;
      } catch (err) {
        if (err && err.name === "AbortError") return false;
        // Any other failure (e.g. API present but blocked) — fall back below.
      }
    }
    downloadBlob(blob, filename);
    return true;
  }

  function openSaveModal(blob, suggestedName, callbacks) {
    var modal = document.getElementById("pdf-save-modal");
    var input = document.getElementById("pdf-save-modal-filename");
    var saveBtn = document.getElementById("pdf-save-modal-save");
    var cancelBtn = document.getElementById("pdf-save-modal-cancel");
    var backdrop = document.getElementById("pdf-save-modal-backdrop");

    input.value = suggestedName;
    modal.hidden = false;
    input.focus();
    input.select();

    function cleanup() {
      modal.hidden = true;
      saveBtn.removeEventListener("click", onSave);
      cancelBtn.removeEventListener("click", onCancel);
      backdrop.removeEventListener("click", onCancel);
      input.removeEventListener("keydown", onKeydown);
    }
    function onCancel() {
      cleanup();
      if (callbacks.onCancelled) callbacks.onCancelled();
    }
    function onSave() {
      var name = (input.value || suggestedName).trim();
      if (!name) { input.focus(); return; }
      cleanup();
      saveBlob(blob, name).then(function (saved) {
        if (saved && callbacks.onSaved) callbacks.onSaved(name);
        else if (!saved && callbacks.onCancelled) callbacks.onCancelled();
      });
    }
    function onKeydown(e) {
      if (e.key === "Enter") onSave();
      else if (e.key === "Escape") onCancel();
    }

    saveBtn.addEventListener("click", onSave);
    cancelBtn.addEventListener("click", onCancel);
    backdrop.addEventListener("click", onCancel);
    input.addEventListener("keydown", onKeydown);
  }

  // ---------------- ordered multi-file list (merge / insert) ----------------
  function createFileListManager(cfg) {
    // cfg: { listbox, emptyEl, input, addBtn, removeBtn, clearBtn, upBtn, downBtn, topBtn, bottomBtn, onChange }
    var files = [];
    var selected = {};
    var lastClickIndex = null;

    function selectedIndexes() {
      return Object.keys(selected).map(Number).sort(function (a, b) { return a - b; });
    }

    function render() {
      cfg.listbox.querySelectorAll(".pdf-list-row").forEach(function (el) { el.remove(); });
      cfg.emptyEl.style.display = files.length ? "none" : "flex";
      files.forEach(function (file, i) {
        var row = document.createElement("div");
        row.className = "pdf-list-row" + (selected[i] ? " selected" : "");
        row.draggable = true;
        row.dataset.index = String(i);
        row.innerHTML =
          '<span class="p-idx">' + (i + 1) + "</span>" +
          '<span class="p-icn">' + FILE_ICON_SVG + "</span>" +
          '<span class="p-name">' + escapeHtml(file.name) + "</span>" +
          '<span class="p-size">' + formatSize(file.size) + "</span>" +
          '<button type="button" class="p-remove" title="นำออก">&times;</button>';
        cfg.listbox.appendChild(row);
      });
      if (cfg.onChange) cfg.onChange(files.slice());
    }

    function addFiles(fileList) {
      Array.prototype.forEach.call(fileList, function (f) {
        if (isPdf(f)) files.push(f);
      });
      render();
    }

    function moveSelection(where) {
      var idxs = selectedIndexes();
      if (!idxs.length) return;
      var block = idxs.map(function (i) { return files[i]; });
      var rest = files.filter(function (_, i) { return !selected[i]; });
      var insertAt;
      if (where === "top") insertAt = 0;
      else if (where === "bottom") insertAt = rest.length;
      else if (where === -1) insertAt = Math.max(0, idxs[0] - 1);
      else insertAt = Math.min(rest.length, idxs[0] + 1);

      files = rest.slice(0, insertAt).concat(block, rest.slice(insertAt));
      selected = {};
      for (var k = 0; k < block.length; k++) selected[insertAt + k] = true;
      render();
    }

    cfg.listbox.addEventListener("click", function (e) {
      var removeBtn = e.target.closest(".p-remove");
      var row = e.target.closest(".pdf-list-row");
      if (!row) return;
      var idx = Number(row.dataset.index);
      if (removeBtn) {
        files.splice(idx, 1);
        selected = {};
        lastClickIndex = null;
        render();
        return;
      }
      if (e.shiftKey && lastClickIndex !== null) {
        var lo = Math.min(lastClickIndex, idx), hi = Math.max(lastClickIndex, idx);
        selected = {};
        for (var i = lo; i <= hi; i++) selected[i] = true;
      } else if (e.ctrlKey || e.metaKey) {
        if (selected[idx]) delete selected[idx]; else selected[idx] = true;
        lastClickIndex = idx;
      } else {
        selected = {};
        selected[idx] = true;
        lastClickIndex = idx;
      }
      render();
    });

    cfg.listbox.addEventListener("dragstart", function (e) {
      var row = e.target.closest(".pdf-list-row");
      if (!row) return;
      e.dataTransfer.setData("text/plain", row.dataset.index);
      e.dataTransfer.effectAllowed = "move";
      row.classList.add("dragging");
    });
    cfg.listbox.addEventListener("dragend", function (e) {
      var row = e.target.closest(".pdf-list-row");
      if (row) row.classList.remove("dragging");
    });
    cfg.listbox.addEventListener("dragover", function (e) {
      e.preventDefault();
      cfg.listbox.classList.add("dragover");
    });
    cfg.listbox.addEventListener("dragleave", function (e) {
      if (e.target === cfg.listbox) cfg.listbox.classList.remove("dragover");
    });
    cfg.listbox.addEventListener("drop", function (e) {
      e.preventDefault();
      cfg.listbox.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files.length) {
        addFiles(e.dataTransfer.files);
        return;
      }
      var fromIndex = Number(e.dataTransfer.getData("text/plain"));
      if (isNaN(fromIndex)) return;
      var targetRow = e.target.closest(".pdf-list-row");
      var toIndex = targetRow ? Number(targetRow.dataset.index) : files.length - 1;
      if (fromIndex === toIndex) return;
      var item = files.splice(fromIndex, 1)[0];
      var adjustedTo = toIndex > fromIndex ? toIndex - 1 : toIndex;
      files.splice(adjustedTo, 0, item);
      selected = {};
      selected[adjustedTo] = true;
      render();
    });

    cfg.addBtn.addEventListener("click", function () {
      cfg.input.value = "";
      cfg.input.click();
    });
    cfg.input.addEventListener("change", function () { addFiles(cfg.input.files); });
    cfg.removeBtn.addEventListener("click", function () {
      files = files.filter(function (_, i) { return !selected[i]; });
      selected = {};
      render();
    });
    cfg.clearBtn.addEventListener("click", function () {
      files = [];
      selected = {};
      render();
    });
    cfg.upBtn.addEventListener("click", function () { moveSelection(-1); });
    cfg.downBtn.addEventListener("click", function () { moveSelection(1); });
    cfg.topBtn.addEventListener("click", function () { moveSelection("top"); });
    cfg.bottomBtn.addEventListener("click", function () { moveSelection("bottom"); });

    render();
    return { getFiles: function () { return files.slice(); } };
  }

  // ==================== TABS ====================
  function initTabs() {
    var tabs = document.querySelectorAll(".pdf-tab");
    var panels = document.querySelectorAll(".pdf-panel");
    if (!tabs.length) return;

    function activate(name) {
      tabs.forEach(function (t) { t.classList.toggle("active", t.dataset.tab === name); });
      panels.forEach(function (p) { p.classList.toggle("active", p.dataset.panel === name); });
    }

    tabs.forEach(function (t) {
      t.addEventListener("click", function () {
        activate(t.dataset.tab);
        var url = new URL(window.location);
        url.searchParams.set("tab", t.dataset.tab);
        window.history.replaceState({}, "", url);
      });
    });

    var requested = new URLSearchParams(window.location.search).get("tab");
    var validTabs = Array.prototype.map.call(tabs, function (t) { return t.dataset.tab; });
    activate(validTabs.indexOf(requested) >= 0 ? requested : validTabs[0]);
  }

  // ==================== MERGE ====================
  function initMerge() {
    var manager = createFileListManager({
      listbox: document.getElementById("merge-listbox"),
      emptyEl: document.getElementById("merge-listbox-empty"),
      input: document.getElementById("merge-file-input"),
      addBtn: document.getElementById("merge-add-btn"),
      removeBtn: document.getElementById("merge-remove-btn"),
      clearBtn: document.getElementById("merge-clear-btn"),
      upBtn: document.getElementById("merge-up-btn"),
      downBtn: document.getElementById("merge-down-btn"),
      topBtn: document.getElementById("merge-top-btn"),
      bottomBtn: document.getElementById("merge-bottom-btn"),
      onChange: function (files) {
        var submitBtn = document.getElementById("merge-submit-btn");
        submitBtn.disabled = files.length < 2;
        if (!files.length) setStatus("merge", "", "ยังไม่มีไฟล์ที่เพิ่ม");
        else if (files.length === 1) setStatus("merge", "", "เพิ่มอีกอย่างน้อย 1 ไฟล์เพื่อรวม");
        else setStatus("merge", "", files.length + " ไฟล์ พร้อมรวม");
      },
    });

    document.getElementById("merge-submit-btn").addEventListener("click", function () {
      var files = manager.getFiles();
      if (files.length < 2) return;
      var fd = new FormData();
      files.forEach(function (f) { fd.append("files", f); });
      submitOperation("merge", {
        url: URLS.merge, formData: fd, fallbackFilename: "merged.pdf",
        busyText: "กำลังรวมไฟล์...", successText: "รวมไฟล์และบันทึกไฟล์เรียบร้อยแล้ว",
      });
    });
  }

  // ==================== SPLIT ====================
  function initSplit() {
    var pagelist = document.getElementById("split-pagelist");
    var rangesInput = document.getElementById("split-ranges-input");
    var chunkInput = document.getElementById("split-chunk-size");
    var submitBtn = document.getElementById("split-submit-btn");

    var picker = bindSingleFilePicker(
      document.getElementById("split-file-btn"),
      document.getElementById("split-file-input"),
      document.getElementById("split-file-name"),
      document.getElementById("split-file-clear"),
      "ยังไม่ได้เลือกไฟล์ (ลากไฟล์ PDF มาวางตรงนี้ได้)",
      function (file) {
        populatePageList(pagelist, 0);
        submitBtn.disabled = true;
        if (!file) { setStatus("split", "", "ยังไม่ได้เลือกไฟล์"); return; }
        setStatus("split", "busy", "กำลังอ่านจำนวนหน้า...");
        fetchPageCount(file, function (pages) {
          populatePageList(pagelist, pages);
          submitBtn.disabled = false;
          setStatus("split", "", "ไฟล์ '" + file.name + "' — " + pages + " หน้า");
        }, function (message) {
          setStatus("split", "err", message);
        });
      }
    );

    document.querySelectorAll('input[name="split-mode"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        chunkInput.disabled = document.querySelector('input[name="split-mode"]:checked').value !== "chunks";
      });
    });

    submitBtn.addEventListener("click", function () {
      var file = picker.getFile();
      if (!file) return;
      var mode = document.querySelector('input[name="split-mode"]:checked').value;
      var ranges = rangesInput.value.trim();
      var pages = Array.prototype.map.call(pagelist.selectedOptions, function (o) { return o.value; }).join(",");

      if (!ranges) {
        if ((mode === "selected_each" || mode === "selected_combined") && !pages) {
          setStatus("split", "err", "กรุณาเลือกหน้าที่ต้องการจากรายการ หรือระบุช่วงหน้าด้านขวา");
          return;
        }
        if (mode === "chunks" && (!chunkInput.value || Number(chunkInput.value) < 1)) {
          setStatus("split", "err", "กรุณาระบุจำนวนหน้าต่อไฟล์ให้ถูกต้อง");
          return;
        }
      }

      var fd = new FormData();
      fd.append("file", file);
      fd.append("mode", mode);
      fd.append("ranges", ranges);
      fd.append("pages", pages);
      fd.append("chunk_size", chunkInput.value || "");

      submitOperation("split", {
        url: URLS.split, formData: fd, fallbackFilename: "split.zip",
        busyText: "กำลังแยกไฟล์...", successText: "แยกไฟล์และบันทึกไฟล์เรียบร้อยแล้ว",
      });
    });
  }

  // ==================== DELETE PAGES ====================
  function initDelete() {
    var pagelist = document.getElementById("delete-pagelist");
    var pagesInput = document.getElementById("delete-pages-input");
    var submitBtn = document.getElementById("delete-submit-btn");

    function revalidate() {
      submitBtn.disabled = !(picker.getFile() && pagesInput.value.trim());
    }

    var picker = bindSingleFilePicker(
      document.getElementById("delete-file-btn"),
      document.getElementById("delete-file-input"),
      document.getElementById("delete-file-name"),
      document.getElementById("delete-file-clear"),
      "ยังไม่ได้เลือกไฟล์ (ลากไฟล์ PDF มาวางตรงนี้ได้)",
      function (file) {
        populatePageList(pagelist, 0);
        pagesInput.value = "";
        revalidate();
        if (!file) { setStatus("delete", "", "ยังไม่ได้เลือกไฟล์"); return; }
        setStatus("delete", "busy", "กำลังอ่านจำนวนหน้า...");
        fetchPageCount(file, function (pages) {
          populatePageList(pagelist, pages);
          setStatus("delete", "", "ไฟล์ '" + file.name + "' — " + pages + " หน้า");
        }, function (message) {
          setStatus("delete", "err", message);
        });
      }
    );

    pagelist.addEventListener("change", function () {
      var vals = Array.prototype.map.call(pagelist.selectedOptions, function (o) { return o.value; });
      pagesInput.value = vals.join(",");
      revalidate();
    });
    pagesInput.addEventListener("input", revalidate);

    submitBtn.addEventListener("click", function () {
      var file = picker.getFile();
      var pages = pagesInput.value.trim();
      if (!file || !pages) return;
      var fd = new FormData();
      fd.append("file", file);
      fd.append("pages", pages);
      submitOperation("delete", {
        url: URLS.del, formData: fd, fallbackFilename: "deleted.pdf",
        busyText: "กำลังลบหน้า...", successText: "ลบหน้าและบันทึกไฟล์เรียบร้อยแล้ว",
      });
    });
  }

  // ==================== INSERT ====================
  function initInsert() {
    var positionInput = document.getElementById("insert-position");
    var submitBtn = document.getElementById("insert-submit-btn");
    var currentBase = null;
    var manager;

    function revalidate() {
      var ready = currentBase && manager.getFiles().length > 0;
      submitBtn.disabled = !ready;
      if (!currentBase) setStatus("insert", "", "ยังไม่พร้อม — กรุณาเลือกไฟล์หลักและไฟล์ที่จะแทรก");
      else if (!manager.getFiles().length) setStatus("insert", "", "เลือกไฟล์หลักแล้ว — กรุณาเพิ่มไฟล์ที่จะแทรก");
      else setStatus("insert", "", "พร้อมแทรก " + manager.getFiles().length + " ไฟล์เข้าไปใน '" + currentBase.name + "'");
    }

    bindSingleFilePicker(
      document.getElementById("insert-base-btn"),
      document.getElementById("insert-base-input"),
      document.getElementById("insert-base-name"),
      document.getElementById("insert-base-clear"),
      "ยังไม่ได้เลือกไฟล์ (ลากไฟล์ PDF มาวางตรงนี้ได้)",
      function (file) { currentBase = file; revalidate(); }
    );

    manager = createFileListManager({
      listbox: document.getElementById("insert-listbox"),
      emptyEl: document.getElementById("insert-listbox-empty"),
      input: document.getElementById("insert-files-input"),
      addBtn: document.getElementById("insert-add-btn"),
      removeBtn: document.getElementById("insert-remove-btn"),
      clearBtn: document.getElementById("insert-clear-btn"),
      upBtn: document.getElementById("insert-up-btn"),
      downBtn: document.getElementById("insert-down-btn"),
      topBtn: document.getElementById("insert-top-btn"),
      bottomBtn: document.getElementById("insert-bottom-btn"),
      onChange: revalidate,
    });

    document.querySelectorAll('input[name="insert-mode"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        positionInput.disabled = document.querySelector('input[name="insert-mode"]:checked').value !== "custom";
      });
    });

    submitBtn.addEventListener("click", function () {
      var files = manager.getFiles();
      if (!currentBase || !files.length) return;
      var mode = document.querySelector('input[name="insert-mode"]:checked').value;

      var fd = new FormData();
      fd.append("base_file", currentBase);
      files.forEach(function (f) { fd.append("insert_files", f); });
      fd.append("mode", mode);
      fd.append("position", positionInput.value || "0");

      submitOperation("insert", {
        url: URLS.insert, formData: fd, fallbackFilename: "inserted.pdf",
        busyText: "กำลังแทรกไฟล์...", successText: "แทรกไฟล์และบันทึกไฟล์เรียบร้อยแล้ว",
      });
    });
  }

  // ==================== LOCK / UNLOCK ====================
  function initLockUnlock() {
    var lockFile = null;
    var lockSubmitBtn = document.getElementById("lock-submit-btn");
    var lockPassword = document.getElementById("lock-password");
    var lockOwnerPassword = document.getElementById("lock-owner-password");

    function revalidateLock() {
      lockSubmitBtn.disabled = !(lockFile && lockPassword.value.length >= 4);
    }

    bindSingleFilePicker(
      document.getElementById("lock-file-btn"),
      document.getElementById("lock-file-input"),
      document.getElementById("lock-file-name"),
      document.getElementById("lock-file-clear"),
      "ยังไม่ได้เลือกไฟล์ (ลากไฟล์ PDF มาวางตรงนี้ได้)",
      function (file) { lockFile = file; revalidateLock(); }
    );
    lockPassword.addEventListener("input", revalidateLock);

    document.getElementById("lock-show-password").addEventListener("change", function () {
      var type = this.checked ? "text" : "password";
      lockPassword.type = type;
      lockOwnerPassword.type = type;
    });

    lockSubmitBtn.addEventListener("click", function () {
      if (!lockFile || lockPassword.value.length < 4) return;
      var fd = new FormData();
      fd.append("file", lockFile);
      fd.append("password", lockPassword.value);
      fd.append("owner_password", lockOwnerPassword.value);
      submitOperation("lock", {
        url: URLS.lock, formData: fd, fallbackFilename: "encrypted.pdf",
        busyText: "กำลังล็อกไฟล์...", successText: "ล็อกไฟล์และบันทึกไฟล์เรียบร้อยแล้ว",
      });
    });

    var unlockFile = null;
    var unlockSubmitBtn = document.getElementById("unlock-submit-btn");
    var unlockPassword = document.getElementById("unlock-password");

    function revalidateUnlock() {
      unlockSubmitBtn.disabled = !(unlockFile && unlockPassword.value.length > 0);
    }

    bindSingleFilePicker(
      document.getElementById("unlock-file-btn"),
      document.getElementById("unlock-file-input"),
      document.getElementById("unlock-file-name"),
      document.getElementById("unlock-file-clear"),
      "ยังไม่ได้เลือกไฟล์ (ลากไฟล์ PDF มาวางตรงนี้ได้)",
      function (file) { unlockFile = file; revalidateUnlock(); }
    );
    unlockPassword.addEventListener("input", revalidateUnlock);

    document.getElementById("unlock-show-password").addEventListener("change", function () {
      unlockPassword.type = this.checked ? "text" : "password";
    });

    unlockSubmitBtn.addEventListener("click", function () {
      if (!unlockFile || !unlockPassword.value) return;
      var fd = new FormData();
      fd.append("file", unlockFile);
      fd.append("password", unlockPassword.value);
      submitOperation("unlock", {
        url: URLS.unlock, formData: fd, fallbackFilename: "decrypted.pdf",
        busyText: "กำลังปลดล็อกไฟล์...", successText: "ปลดล็อกและบันทึกไฟล์เรียบร้อยแล้ว",
      });
    });
  }

  initTabs();
  initMerge();
  initSplit();
  initDelete();
  initInsert();
  initLockUnlock();
})();
