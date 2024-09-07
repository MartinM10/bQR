document.addEventListener("DOMContentLoaded", (event) => {
    const darkModeToggle = document.getElementById("darkModeToggle");
    const html = document.documentElement;

    // Verificar si hay una preferencia guardada
    const isDarkMode = localStorage.getItem("darkMode") === "true";

    // Aplicar el modo guardado o el predeterminado
    html.setAttribute("data-bs-theme", isDarkMode ? "dark" : "light");
    updateToggleButton(isDarkMode);

    darkModeToggle.addEventListener("click", () => {
        const isDark = html.getAttribute("data-bs-theme") === "dark";
        html.setAttribute("data-bs-theme", isDark ? "light" : "dark");
        localStorage.setItem("darkMode", !isDark);
        updateToggleButton(!isDark);
    });

    function updateToggleButton(isDark) {
        const icon = darkModeToggle.querySelector("i");
        icon.className = isDark ? "bi bi-sun" : "bi bi-moon";
    }
});
