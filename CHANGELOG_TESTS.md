# STARBLOOD.OS — lokale Bereinigung, 04.11.2026

## Freigegebenes Animationsupdate

Die spätere Bongo-Cat-Vorschau wurde zur Veröffentlichung freigegeben: kompakte Pixel-Art mit zwei abwechselnd tippenden Pfoten, 59 Frames und 4,96 Sekunden pro Loop. Statisches Poster und lokale Vorschauen wurden angepasst. Der Generator verwendet die mitgelieferte Grundpose und eine pfotenfreie Hintergrundebene; keine Bildgenerierung oder externen Quellen sind beim Neubau erforderlich. Die Animationstests prüfen jetzt Pfotenbewegung, unveränderte übrige Bildbereiche, Timings, identische Endpunkte und bytegleichen Neubau der ausgelieferten GIF-Datei. Die folgenden Abschnitte dokumentieren die ursprüngliche Bereinigung vor diesem Update.

Das Original in Downloads blieb unverändert. Dieses Paket wurde lokal mit dem bereits vorhandenen Ponytail-Workflow überarbeitet. Auf GitHub wurde nichts angelegt, geändert oder ausgeführt. Es wurden keine neuen Motive oder KI-Assets erzeugt.

## Änderungen

- **GIF:** Ursprünglich 8 Frames mit unregelmäßigen Haltezeiten (3,72 s), abrupten Höhenwechseln und unpassender Ersetzung der Augenglyphen. Jetzt 9 Frames / 4 s, abgestufter Augenaufschlag, gemeinsame Palette, ruhiger Körper und Cursor sowie pixelgleiche Start-/Endframes. Timing in ms: `2100, 30, 30, 30, 70, 40, 40, 40, 1620`. Größe: 301.187 → 46.902 Bytes. Die vorhandene Rasterzeichnung bleibt als `source/idle_base.png` erhalten; Augenkoordinaten sind bewusst auf dieses Portrait abgestimmt.
- **Statistikgenerator:** Fehlende Repository-/Sprachdaten, falsche Zähler, ungültige/mehrfache Daten und kaputte Pagination werden abgewiesen. Sprachabfrage von 10 auf 100 Sprachen pro Repository erweitert; weitere Seiten führen zu einem klaren Fehler statt stiller Unterzählung. API-Fehlermeldungen übernehmen keine beliebigen Antworttexte in Logs. Token bleiben ausschließlich in Umgebungsvariablen.
- **SVG-Renderer:** Eingaben und vollständige XML-Ausgaben werden vor dem Schreiben geprüft. Leere Live-Sprachdaten werden korrekt von „pending“ unterschieden. Tage außerhalb der gelieferten Kalenderdaten erscheinen nicht mehr als erfundene Nulltage. Mobile Sprachkarte trägt ebenfalls den Demo-/Live-Hinweis. Leerzeichen in Terminalbeispielen bleiben beim Browserrendern erhalten.
- **GitHub Actions:** Bestehende Hauptversionen auf verifizierte Commit-Hashes fixiert, Schreibrecht auf den ausführenden Job begrenzt, Standardbranch explizit gewählt und Offline-Tests vor Abruf/Commit ergänzt. Kein Force-Push, keine zusätzlichen Trigger, unverändert nur sieben generierte Dateien im Commit.
- **README und Vorschau:** Statisches Poster bei reduzierter Bewegung vorgesehen. Mobile HTML-Vorschau verwendet nun tatsächlich die mobilen Statistikgrafiken. Demo-Kennzeichnung bleibt auch auf schmalen Geräten sichtbar. Desktop-, Mobile- und Header-PNGs sind neue Screenshots des tatsächlichen HTML-Layouts.
- **Struktur:** Separaten Pillow/CairoSVG-Vorschauaufbau durch einen kleineren Browser-Capture ersetzt; dadurch entfallen doppelte Layouts und CairoSVG. Node/Playwright/Chrome werden nur zum Neuerstellen der Screenshots gebraucht. Keine Installation war für diese Überarbeitung nötig. Originalillustrationen und Referenzbild bleiben enthalten; Cachedateien und lokale Abhängigkeiten sind nicht im ZIP.

## Prüfungen

- **21 Offline-Tests bestanden**, einschließlich GIF-Neubau mit Pillow: Loop, Timings, Frameanzahl, identische Endpunkte und unveränderte Pixel außerhalb der Augen.
- **Ohne Pillow:** 20 Tests bestanden, 1 optionaler Animationstest gezielt übersprungen. Der tägliche Statistikworkflow benötigt weiterhin nur die Python-Standardbibliothek.
- API-Antworten wurden gemockt: mehrere Repositoryseiten, falscher Benutzer, fehlende/cyclische Pagination, unvollständige Sprachdaten, HTTP-/Netzwerk-/GraphQL-Fehler, fehlender Token und Erhalt vorhandener Dateien bei Fehlschlag.
- Renderer: ungültige Eingaben werden vor Dateischreibvorgängen abgelehnt; XML-Escaping einschließlich bösartiger Sprachbezeichnungen geprüft. Pending-Ausgaben enthalten keine Demo-Zähler.
- **20 SVG-Dateien:** XML gültig, keine Scripts/externen Bildreferenzen; zusätzlich im lokalen Chrome auf Text außerhalb des Bildbereichs geprüft — keine gefunden. README-/HTML-Bildpfade lösen innerhalb des Pakets auf.
- **Chrome bei 320, 390, 640 und 1280 px:** alle sieben Bilder geladen, passende mobile Statistikquelle gewählt, Demo-Hinweis sichtbar, kein horizontaler Überlauf. Poster bei reduzierter Bewegung und GIF bei normaler Bewegung ausgewählt. Externe HTTP-Anfragen während des Vorschautests blockiert.
- Desktop- und Mobile-Screenshots sowie offene/geschlossene GIF-Frames visuell geprüft. ZIP abschließend auf Integrität und enthaltene Dateien geprüft.

## Grenzen

Kein authentifizierter Live-API-Abruf, kein GitHub-Actions-Lauf und keine Prüfung im tatsächlichen GitHub-README-Renderer. Die Workflow-Prüfung erfolgte statisch, ohne Actionlint. Lokale Python-Tests liefen unter Windows mit Python 3.11.0 und 3.12.14; der Linux-Runner wurde nicht ausgeführt. Produktionsstatistiken bleiben bewusst „pending“, Vorschauwerte bleiben Demo. Das Verhalten von `prefers-reduced-motion` im veröffentlichten GitHub-README hängt zusätzlich von dessen Renderer ab. Die bestehenden Hinweise zu den Rechten am Sanrio-Charakter bleiben in SETUP.md enthalten.

Technische Referenzen: [GitHub zu Action-Pins und Tokenrechten](https://docs.github.com/en/actions/reference/security/secure-use), [verifizierter Checkout-Commit](https://github.com/actions/checkout/commit/11bd71901bbe5b1630ceea73d27597364c9af683), [verifizierter Setup-Python-Commit](https://github.com/actions/setup-python/commit/a26af69be951a213d495a4c3e4e4022e16d87065), [Pillow-GIF-Optionen](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif).
