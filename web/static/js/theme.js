// Theme management script - lightweight version for immediate theme application
(function () {
    'use strict';

    // Apply theme immediately to prevent flash
    function applyTheme() {
        const savedTheme = localStorage.getItem('theme');
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const theme = savedTheme ? JSON.parse(savedTheme) : systemTheme;

        document.body.setAttribute('data-theme', theme);
        document.body.className = `theme-${theme}`;
    }

    // Apply theme immediately
    applyTheme();

    // Listen for storage changes (theme changes in other tabs)
    window.addEventListener('storage', function (e) {
        if (e.key === 'theme') {
            applyTheme();
        }
    });
})();