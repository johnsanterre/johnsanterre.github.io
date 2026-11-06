// BiGi Data: English and Dutch on every written page. The choice is kept in the browser.
(function () {
  var KEY = "bigi-lang";
  var root = document.documentElement;
  function apply(lang) {
    root.setAttribute("data-lang", lang);
    root.setAttribute("lang", lang);
    var t = document.querySelector("title");
    if (t && t.dataset[lang]) document.title = t.dataset[lang];
    var b = document.getElementById("lang-btn");
    if (b) b.textContent = lang === "nl" ? "English" : "Nederlands";
  }
  var saved = "en";
  try { saved = localStorage.getItem(KEY) || "en"; } catch (e) {}
  apply(saved);
  document.addEventListener("DOMContentLoaded", function () {
    apply(root.getAttribute("data-lang") || "en");
    var b = document.getElementById("lang-btn");
    if (!b) return;
    b.addEventListener("click", function () {
      var next = root.getAttribute("data-lang") === "nl" ? "en" : "nl";
      try { localStorage.setItem(KEY, next); } catch (e) {}
      apply(next);
    });
  });
})();
