document.addEventListener("DOMContentLoaded", () => {
  const switchBtn = document.getElementById("switchLang");
  const currentLang = localStorage.getItem("lang") || "tr";

  function updateLanguage(lang) {
    document.querySelectorAll("[data-tr], [data-en]").forEach(el => {
      if (lang === 'en' && el.dataset.en) el.textContent = el.dataset.en;
      else if (lang === 'tr' && el.dataset.tr) el.textContent = el.dataset.tr;
    });

    switchBtn.innerHTML = lang === "tr" ? "🇬🇧 EN" : "🇹🇷 TR";
    localStorage.setItem("lang", lang);
  }

  updateLanguage(currentLang);

  switchBtn.addEventListener("click", () => {
    const nextLang = localStorage.getItem("lang") === "tr" ? "en" : "tr";
    updateLanguage(nextLang);
  });
});
