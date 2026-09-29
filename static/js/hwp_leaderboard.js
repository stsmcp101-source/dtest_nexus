/* Shared leaderboard helpers for the Happy Workplace score games. */
window.HwpLeaderboard = (function () {
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c];
    });
  }
  function render(el, rows, detailLabel) {
    var head = '<div class="wd-lb-row wd-lb-head"><span>ลำดับ</span><span>ชื่อ</span><span>' +
      esc(detailLabel) + '</span><span>คะแนน</span></div>';
    if (!rows.length) {
      el.innerHTML = head + '<p class="hwp-empty">ยังไม่มีใครทำคะแนนไว้</p>';
      return;
    }
    el.innerHTML = head + rows.map(function (r, i) {
      return '<div class="wd-lb-row"><span class="wd-lb-rank">' + (i + 1) + '</span>' +
        '<span class="wd-lb-name">' + esc(r.name) + '</span>' +
        '<span class="wd-lb-words">' + esc(r.detail || "-") + '</span>' +
        '<span class="wd-lb-score">' + r.score.toLocaleString() + '</span></div>';
    }).join("");
  }
  function submit(url, csrf, payload) {
    return fetch(url, {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrf},
      body: JSON.stringify(payload)
    }).then(function (resp) {
      if (!resp.ok) throw new Error("save failed");
      return resp.json();
    });
  }
  return {render: render, submit: submit};
})();
