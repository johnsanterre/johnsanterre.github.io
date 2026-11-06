// BiGi Data: the knowledge check. A click on an option marks it right or wrong, shows that
// option's feedback, reveals the right option, and counts the set's score. The score lives in
// the open page only; nothing is saved and nothing is sent. The markup carries English and
// Dutch twins (lang="en" / lang="nl"); lang.js shows one, so this file holds no words.
(function () {
  function tally(set) {
    var items = set.querySelectorAll(".kc-item");
    var done = 0, right = 0;
    items.forEach(function (it) {
      if (it.classList.contains("is-done")) {
        done += 1;
        if (it.classList.contains("is-right")) right += 1;
      }
    });
    set.querySelectorAll(".kc-right").forEach(function (e) { e.textContent = right; });
    set.querySelectorAll(".kc-done").forEach(function (e) { e.textContent = done; });
    set.classList.toggle("is-complete", items.length > 0 && done === items.length);
  }

  function answer(set, item, chosen) {
    if (item.classList.contains("is-done")) return;
    var isRight = chosen.dataset.right === "1";
    item.classList.add("is-done", isRight ? "is-right" : "is-wrong");
    item.querySelectorAll(".kc-opt").forEach(function (opt) {
      var btn = opt.querySelector(".kc-option");
      btn.setAttribute("aria-disabled", "true");
      btn.tabIndex = -1;
      if (opt === chosen) {
        opt.classList.add("is-chosen", isRight ? "is-right" : "is-wrong");
        btn.setAttribute("aria-pressed", "true");
      }
      if (opt.dataset.right === "1") opt.classList.add("is-answer");
      // The chosen option's feedback always shows; a wrong pick also opens the right option's.
      if (opt === chosen || (!isRight && opt.dataset.right === "1")) opt.classList.add("is-open");
    });
    tally(set);
  }

  function reset(set) {
    set.querySelectorAll(".kc-item").forEach(function (item) {
      item.classList.remove("is-done", "is-right", "is-wrong");
      item.querySelectorAll(".kc-opt").forEach(function (opt) {
        opt.classList.remove("is-chosen", "is-right", "is-wrong", "is-answer", "is-open");
        var btn = opt.querySelector(".kc-option");
        btn.removeAttribute("aria-disabled");
        btn.removeAttribute("aria-pressed");
        btn.tabIndex = 0;
      });
    });
    tally(set);
  }

  function init() {
    document.querySelectorAll(".kc-set").forEach(function (set) {
      set.addEventListener("click", function (ev) {
        var btn = ev.target.closest(".kc-option");
        if (btn && set.contains(btn)) {
          var item = btn.closest(".kc-item");
          if (item && !item.classList.contains("is-done")) answer(set, item, btn.closest(".kc-opt"));
          return;
        }
        if (ev.target.closest(".kc-reset")) reset(set);
      });
      tally(set);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
