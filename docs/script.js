document.addEventListener('DOMContentLoaded', function() {
    const burger = document.getElementById('burger');
    const nav = document.getElementById('navLinks');
    const navLinks = document.querySelectorAll('.nav-links li a'); // Selektiert jetzt die Anker-Tags
    const contentContainer = document.getElementById('content-container');

    // Funktion zum Umschalten des Hamburgermenüs (wie zuvor)
    function toggleMenu() {
        nav.classList.toggle('nav-active');
        burger.classList.toggle('toggle');
        const isExpanded = burger.getAttribute('aria-expanded') === 'true';
        burger.setAttribute('aria-expanded', !isExpanded);
        navLinks.forEach((link, index) => {
            if (nav.classList.contains('nav-active')) {
                link.style.animation = `navLinkFade 0.5s ease forwards ${index / 7 + 0.3}s`;
            } else {
                link.style.animation = '';
            }
        });
    }

    // Burger-Button Klick-Event
    if (burger && nav && navLinks) {
        burger.addEventListener('click', toggleMenu);
    }

    // Klick außerhalb des Menüs schließen
    document.addEventListener('click', function(event) {
        if (nav.classList.contains('nav-active') &&
            !burger.contains(event.target) &&
            !nav.contains(event.target)) {
            toggleMenu();
        }
    });

    // Funktion zum Laden von Inhalten
    async function loadContent(path, isMarkdown = false) {
        if (!contentContainer) return;

        contentContainer.innerHTML = '<p>Lade Inhalt...</p>'; // Lade-Indikator
        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} for ${path}`);
            }
            let content = await response.text();

            if (isMarkdown) {
                if (typeof marked !== 'undefined') {
                    content = marked.parse(content);
                } else {
                    console.warn("marked.js ist nicht geladen, kann Markdown nicht parsen.");
                }
            }

            contentContainer.innerHTML = content;
        } catch (error) {
            console.error('Fehler beim Laden des Inhalts:', error);
            contentContainer.innerHTML = `<p style="color: red;">Fehler beim Laden des Inhalts von ${path}.</p>`;
        }
    }

    // Event-Listener für Navigationslinks
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();

            const path = this.dataset.path;
            const isMarkdown = this.dataset.isMarkdown === 'true';

            if (path) {
                loadContent(path, isMarkdown);
                if (nav.classList.contains('nav-active')) {
                    toggleMenu();
                }
            }
        });
    });

    // --- Geänderter Standard-Lade-Mechanismus ---
    // Standardinhalt beim Laden der Seite: Lade zuerst README.md
    const readmeNavLink = document.querySelector('a[data-path="README.md"]');
    
    if (readmeNavLink) {
        loadContent(readmeNavLink.dataset.path, readmeNavLink.dataset.isMarkdown === 'true');
    } else {
        // Fallback: Wenn kein README.md-Link existiert, lade den Home-Link
        const homeNavLink = document.querySelector('a[data-path="content/home.html"]');
        if (homeNavLink) {
            loadContent(homeNavLink.dataset.path, homeNavLink.dataset.isMarkdown === 'true');
        } else {
            // Letzter Fallback: Einfache Willkommensnachricht
            contentContainer.innerHTML = '<p>Willkommen auf unserer Seite!</p>';
        }
    }
});
