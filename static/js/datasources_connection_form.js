(function () {
  "use strict";

  var script = document.currentScript;
  var testUrl = script.getAttribute("data-test-url");

  function getCookie(name) {
    var match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return match ? match.pop() : "";
  }

  var btn = document.getElementById("test-conn-btn");
  var resultEl = document.getElementById("test-conn-result");
  var pkInput = document.getElementById("conn-pk");

  btn.addEventListener("click", function () {
    var fd = new FormData();
    fd.append("server", document.getElementById("id_server").value.trim());
    fd.append("port", document.getElementById("id_port").value.trim());
    fd.append("database_name", document.getElementById("id_database_name").value.trim());
    fd.append("username", document.getElementById("id_username").value.trim());
    fd.append("password", document.getElementById("id_password").value);
    fd.append("driver", document.getElementById("id_driver").value.trim());
    if (pkInput) fd.append("pk", pkInput.value);

    btn.disabled = true;
    btn.textContent = "กำลังทดสอบ...";
    resultEl.innerHTML = "";

    fetch(testUrl, {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") },
      body: fd,
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        var cls = data.ok ? "ok" : "bad";
        resultEl.innerHTML = '<span class="calc-badge ' + cls + '">' + (data.ok ? "✓ " : "✗ ") + data.message + "</span>";
      })
      .catch(function () {
        resultEl.innerHTML = '<span class="calc-badge bad">เกิดข้อผิดพลาดในการเชื่อมต่อกับเซิร์ฟเวอร์</span>';
      })
      .finally(function () {
        btn.disabled = false;
        btn.textContent = "Test Connection";
      });
  });
})();
