// BiGi Data: a student marks stages done; the choice stays in this browser under bigi-week-NN.
(function () {
  var m = location.pathname.match(/week-(\d\d)\//);
  if (!m) return;
  var KEY = "bigi-week-" + m[1];
  var done = {};
  try { done = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
  var boxes = document.querySelectorAll("input[data-stage]");
  var nav = document.querySelector(".stages");
  function paint() {
    boxes.forEach(function (b) {
      b.checked = !!done[b.dataset.stage];
      b.closest("section").classList.toggle("is-done", b.checked);
      var a = nav && nav.querySelector('a[href="#seg-' + b.dataset.stage + '"]');
      if (a) a.classList.toggle("is-done", b.checked);
    });
  }
  boxes.forEach(function (b) {
    b.addEventListener("change", function () {
      done[b.dataset.stage] = b.checked;
      try { localStorage.setItem(KEY, JSON.stringify(done)); } catch (e) {}
      paint();
    });
  });
  paint();
})();
