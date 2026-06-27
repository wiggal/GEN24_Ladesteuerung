document.addEventListener('DOMContentLoaded', () => {
    const burger = document.getElementById('burger');
    const navLinks = document.getElementById('navLinks');
    const navItems = navLinks.querySelectorAll('li a'); // Alle Links in der Navigation
    const contentContainer = document.getElementById('content-container');
    const logo = document.querySelector('.logo'); // Das Logo-Element (Link, enthält Icon + Text)
    const logoText = document.querySelector('.logo-text'); // Nur der Text-Teil des Logos

    const defaultLogoText = logoText.textContent; // Standard-Logo-Text

    // Funktion zum Umschalten des Navigationsmenüs
    const toggleNav = () => {
        navLinks.classList.toggle('nav-active');
        burger.classList.toggle('toggle');

        // Accessibility: aria-expanded Attribut aktualisieren
        const isExpanded = burger.classList.contains('toggle');
        burger.setAttribute('aria-expanded', isExpanded);

        // Animation der Links nur beim Öffnen
        navItems.forEach((link, index) => {
            if (navLinks.classList.contains('nav-active')) {
                link.style.animation = `navLinkFade 0.5s ease forwards ${index / 7 + 0.3}s`;
            } else {
                link.style.animation = 'none';
            }
        });
    };

    burger.addEventListener('click', toggleNav);

    // Funktion zum Laden von Inhalten und Aktualisieren des Logos
    // path darf eine Sprungmarke enthalten, z.B. "WIKI/EnergyController.html#abschnitt-x"
    const loadContent = async (path, isMarkdown, newLogoText) => {
        try {
            // Datei-Pfad und Sprungmarke (Hash) trennen, damit fetch() nur die echte Datei lädt
            const [filePath, hash] = path.split('#');

            const response = await fetch(filePath);
            if (!response.ok) {
                throw new Error(`HTTP-Fehler! Status: ${response.status}`);
            }
            let content = await response.text();

            if (isMarkdown) {
                const renderer = new marked.Renderer();

                renderer.heading = ({ text, depth }) => {
                    // 1. Bereinigung: Markdown-Links [Text](URL) zu "Text" reduzieren
                    // 2. Bereinigung: HTML-Tags entfernen
                    const cleanText = text
                        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Entfernt (URL), behält [Text]
                        .replace(/<[^>]*>/g, '');                // Entfernt HTML-Tags

                    // ID generieren (GitHub-Style)
                    const id = cleanText.toLowerCase()
                        .trim()
                        .replace(/[^\w\s-]/g, '')  // Entfernt Sonderzeichen/Emojis für die ID
                        .replace(/\s+/g, '-');     // Leerzeichen zu Bindestrichen

                    // Das 'text' Property enthält bereits das gerenderte HTML (mit Links),
                    // wir nutzen es für die Anzeige, aber unsere 'id' für den Anker.
                    return `<a name="${id}"></a><br><h${depth}>${cleanText}</h${depth}>`;
                };

                content = marked.parse(content, { renderer: renderer });
            }

            contentContainer.innerHTML = content;
            logoText.textContent = newLogoText || defaultLogoText;

            if (navLinks.classList.contains('nav-active')) {
                toggleNav();
            }

            // Zur Sprungmarke springen, falls vorhanden, sonst zum Seitenanfang
            if (hash) {
                // Scrollt manuell mit Offset, damit der fixierte Header das Zielelement nicht verdeckt
                const headerOffset = 70;
                const scrollToTarget = () => {
                    const target = contentContainer.querySelector(`[name="${hash}"]`)
                        || document.getElementById(hash);
                    if (target) {
                        const top = target.getBoundingClientRect().top + window.pageYOffset - headerOffset;
                        window.scrollTo({ top, behavior: 'auto' });
                        return true;
                    }
                    return false;
                };

                // Doppeltes requestAnimationFrame: wartet auf Layout/Reflow nach innerHTML-Änderung
                requestAnimationFrame(() => {
                    requestAnimationFrame(() => {
                        if (!scrollToTarget()) {
                            // Fallback: falls Bilder o.ä. das Layout noch verzögern, kurz erneut versuchen
                            setTimeout(() => {
                                if (!scrollToTarget()) {
                                    window.scrollTo(0, 0);
                                }
                            }, 150);
                        }
                    });
                });
            } else {
                window.scrollTo(0, 0);
            }

        } catch (error) {
            console.error("Fehler beim Laden des Inhalts:", error);
            contentContainer.innerHTML = `<p>Entschuldigung, der Inhalt konnte nicht geladen werden: ${error.message}</p>`;
            logoText.textContent = "Fehler!";
        }
    };

    // Event Listener für Navigationslinks
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const path = item.dataset.path;
            const isMarkdown = item.dataset.isMarkdown === 'true';
            const newLogoText = item.textContent;

            // Prüfen, ob es ein externer Link ist
            const isExternal = !path || path.trim() === '';

            if (isExternal) {
                // Externe Links normal öffnen (target="_blank" im HTML)
                return;
            }

            // Internen Link laden
            e.preventDefault();
            loadContent(path, isMarkdown, newLogoText);

            // Aktiven Zustand des Links aktualisieren
            navItems.forEach(link => link.classList.remove('active'));
            item.classList.add('active');
        });
    });

    // URL-Parameter auswerten
    const params = new URLSearchParams(window.location.search);
    const page = params.get("page");

    if (page) {
        // Dateinamen-Endung und Logo-Text sollen sich auf den Datei-Teil beziehen, nicht auf die Sprungmarke
        const pageFilePath = page.split('#')[0];
        const isMarkdown = pageFilePath.toLowerCase().endsWith(".md");

        // Dateiname als Logo verwenden
        const fileName = pageFilePath.split('/').pop().replace(/\.(md|html)$/i, '');

        loadContent(page, isMarkdown, fileName);
    } else {
        // Standardseite laden
        loadContent('README.md', true, 'README');
}
});

