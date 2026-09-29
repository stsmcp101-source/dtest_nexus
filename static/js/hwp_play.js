/* Daily play-limit helper shared by the Happy Workplace score games. */
window.HwpPlay = (function () {
  function note(state) {
    if (state.limit === 0) return "เล่นได้ไม่จำกัดจำนวนครั้ง";
    if (state.remaining <= 0) return "วันนี้คุณเล่นครบ " + state.limit + " ครั้งแล้ว กลับมาเล่นใหม่ได้พรุ่งนี้";
    return "วันนี้เล่นได้อีก " + state.remaining + " จาก " + state.limit + " ครั้ง";
  }
  function exhausted(state) {
    return state.limit > 0 && state.remaining <= 0;
  }
  // Counts a round on the server. Resolves {ok, limit, remaining}; ok=false when the limit is reached.
  function start(url, csrf) {
    return fetch(url, {method: "POST", headers: {"X-CSRFToken": csrf}}).then(function (resp) {
      if (resp.status !== 200 && resp.status !== 403) throw new Error("play start failed");
      return resp.json();
    });
  }
  return {note: note, exhausted: exhausted, start: start};
})();
