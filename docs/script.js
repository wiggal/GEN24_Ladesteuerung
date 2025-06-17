document.addEventListener('DOMContentLoaded', () => {
    const burger = document.getElementById('burger');
    const navLinks = document.getElementById('navLinks');
    const navItems = navLinks.querySelectorAll('li a'); // Alle Links in der Navigation
    const contentContainer = document.getElementById('content-container');
    const logo = document.querySelector('.logo'); // Das Logo-Element

    // Initialer Logo-Text (z.B. der Standard-Titel deiner Seite)
    const defaultLogoText = logo.textContent; 

    // Funktion zum Umschalten des Navigationsmenüs
    const toggleNav = () => {
        navLinks.classList.toggle('nav-active');
        burger.classList.toggle('toggle');
        
        // Accessibility: aria-expanded Attribut aktualisieren
        const isExpanded = burger.classList.contains('toggle');
        burger.setAttribute('aria-expanded', isExpanded);

        // Animation der Links nur, wenn das Menü geöffnet wird
        navItems.forEach((link, index) => {
            if (navLinks.classList.contains('nav-active')) {
                link.style.animation = `navLinkFade 0.5s ease forwards ${index / 7 + 0.3}s`;
            } else {
                link.style.animation = 'none'; // Animation zurücksetzen beim Schließen
            }
        });
    };

    // Event Listener für den Hamburger-Button
    burger.addEventListener('click', toggleNav);

    // Funktion zum Laden von Inhalten und Aktualisieren des Logos
    const loadContent = async (path, isMarkdown, newLogoText) => {
        try {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(`HTTP-Fehler! Status: ${response.status}`);
            }
            let content = await response.text();

            if (isMarkdown) {
                // Konvertiere Markdown zu HTML
                content = marked.parse(content);
            }

            contentContainer.innerHTML = content;

            // *** NEU: Logo-Text aktualisieren ***
            // Überprüfen, ob ein spezifischer Text für das Logo übergeben wurde
            if (newLogoText) {
                logo.textContent = newLogoText;
            } else {
                // Falls kein spezifischer Text, den Linktext verwenden
                // Dies wird normalerweise für die normalen Links verwendet
                logo.textContent = newLogoText;
            }

            // Menü schließen, wenn ein Link angeklickt wird
            if (navLinks.classList.contains('nav-active')) {
                toggleNav();
            }

            // Scroll zum Seitenanfang
            window.scrollTo(0, 0);

        } catch (error) {
            console.error("Fehler beim Laden des Inhalts:", error);
            contentContainer.innerHTML = `<p>Entschuldigung, der Inhalt konnte nicht geladen werden: ${error.message}</p>`;
            logo.textContent = "Fehler!"; // Logo-Text bei Fehler ändern
        }
    };

    // Event Listener für Navigationslinks
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault(); // Standard-Link-Verhalten verhindern

            const path = item.dataset.path;
            const isMarkdown = item.dataset.isMarkdown === 'true';
            // *** NEU: Den Text des angeklickten Links als neuen Logo-Text übergeben ***
            const newLogoText = item.textContent; 
            
            loadContent(path, isMarkdown, newLogoText);

            // Optional: Aktiven Zustand des Links hervorheben (falls gewünscht)
            navItems.forEach(link => link.classList.remove('active'));
            item.classList.add('active');
        });
    });

    // Initialen Inhalt laden (z.B. README.md beim ersten Laden der Seite)
    // Wenn du möchtest, dass beim ersten Laden das Logo den Titel des Startinhalts anzeigt,
    // musst du hier auch den neuenLogoText übergeben.
    // Beispiel: loadContent('README.md', true, 'README');
    
    // Für den Startzustand, wenn keine spezifische Seite geladen ist, das Standardlogo anzeigen.
    // Wenn du eine Startseite hast, die geladen wird, z.B. "README.md",
    // und du möchtest, dass deren Titel im Logo steht, dann ändere diese Zeile:
    loadContent('README.md', true, 'README'); // Lädt README.md und setzt Logo auf 'README'
});
