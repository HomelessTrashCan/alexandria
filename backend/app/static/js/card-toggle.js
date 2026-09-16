document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".card-toggle").forEach(function (toggle) {
    toggle.addEventListener("click", function () {
      var card = toggle.closest(".card");
      if (!card) return;
      
      var isCollapsed = card.classList.toggle("collapsed");
      toggle.setAttribute("aria-expanded", isCollapsed ? "false" : "true");
    });
  });
});
