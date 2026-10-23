# TeddyCloud Home Assistant 🧸

**Community-Prototyp v0.1.5 für Home Assistant – lokale TeddyCloud-MQTT-Anzeige.**

Diese Integration ergänzt den bereits in Home Assistant konfigurierten MQTT-Broker um eine **lesende Media-Player-Entität pro Toniebox** sowie eine optionale Lovelace-Karte.

## Features

- Mehrere Boxen, jeweils eigener Name, MQTT-Prefix, Box-ID (CN) und Boxfarbe.
- Aktueller `ContentTitle`, `ContentAudioId`, `Playback`-Status, gemeldete Lautstärke und Ladestation.
- **Automatische Online-Figurensuche** anhand der exakten `ContentAudioId` aus der öffentlichen [tonies-json-Datenbank](https://github.com/toniebox-reverse-engineering/tonies-json); tägliche Aktualisierung während der Nutzung und Fallback auf das lokale TeddyCloud-Cover.
- Individueller Katalog je Box: `ContentAudioId` → `title`, `cover` und `duration_seconds`; optional Fallback-Cover.
- Dashboard-Karte für Titel, Cover, Farbe und **geschätzten** Wiedergabefortschritt.
- Kein eigener MQTT-Client und keine separaten MQTT-Zugangsdaten: die **bereits konfigurierte Home-Assistant-MQTT-Integration** wird verwendet.
- Keine Cloud-Anmeldung erforderlich.

## Wichtige technische Grenzen

TeddyCloud meldet über MQTT einen Wiedergabestatus (`Playback`: ON/OFF), Titel, Audio-ID und Cover-Entität. **Die tatsächliche Wiedergabeposition und eine garantierte Tracklänge liefert dieses MQTT-Schema nicht.** Fortschritt wird nur ab einem `Playback=ON`- oder neuen Audio-ID-Ereignis anhand der lokalen Uhr **geschätzt**. Bei Pausen, Puffern, Zeitsprüngen, Neustarts oder Kapitelwechseln ohne Audio-ID-Wechsel ist die Position ungenau. Die Leiste trägt deshalb ausdrücklich „geschätzt“. Ohne eigene Laufzeitangabe wird keine Zeit vorgetäuscht.

**Alle jemals veröffentlichten Tonies** gehören **nicht** zum Paket: Katalog, Bildrechte und Audio-ID-Zuordnung müssten aus einer lizenzierten Datenquelle ergänzt werden. Füge eigene Bilder/URLs und Laufzeiten im Katalog hinzu. Die Karte verwendet `ContentPicture` aus TeddyCloud-MQTT direkt. Das ist das **Cover des Inhalts**, nicht zwingend ein Foto der physischen Figur. Ein Figurenfoto erfordert eine separat gepflegte Bild-URL im Katalog.

TeddyCloud bietet über MQTT **keine echte Play/Pause-Fernsteuerung** der Toniebox 1. Diese Erweiterung zeigt Status an, behauptet aber keine Steuerung. Dokumentation: [TeddyCloud MQTT_CONTROL.md](https://github.com/toniebox-reverse-engineering/teddycloud/blob/master/MQTT_CONTROL.md).

**Hinweis zur Umbenennung:** Die Integrations-Domain wurde von `teddycloud_now_playing` auf `teddycloud_homeassistant` geändert. Wer den früheren Prototyp installiert hat, muss die alte Integration zunächst entfernen und danach die neue hinzufügen. Vorher Einstellungen und JSON-Katalog sichern.

## Installation (Entwicklerversion)

1. **MQTT-Integration** in Home Assistant einrichten, ggf. Mosquitto-Broker verbinden.
2. Den Ordner `custom_components/teddycloud_homeassistant` nach `/config/custom_components/` kopieren.
3. Home Assistant **neu starten**.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → TeddyCloud Home Assistant**.
5. Die **Box-ID** anhand der folgenden Anleitung ermitteln und eintragen. Das Prefix ist meist `teddyCloud`. Weitere Boxen als weitere Einträge hinzufügen.
6. Für die Karte `www/teddycloud-homeassistant-card.js` nach `/config/www/` kopieren.
7. **Einstellungen → Dashboards → Ressourcen**: `/local/teddycloud-homeassistant-card.js` als **JavaScript-Modul** hinzufügen. Danach Browser-Cache neu laden.
8. Manuelle Karte nach `examples/dashboard.yaml` hinzufügen. Die tatsächliche Media-Player-Entitäts-ID verwenden.

## Box-ID bei der Einrichtung finden

1. In Home Assistant **Einstellungen → Geräte & Dienste → MQTT → Konfigurieren** öffnen.
2. Im Bereich **Ein Topic abonnieren** ein bestehendes Abo ggf. mit **Abo beenden** stoppen.
3. Als Topic `teddyCloud/box/#` eingeben und **Abonnieren** wählen. Das Präfix `teddyCloud` bei Bedarf durch den eigenen TeddyCloud-MQTT-Topic-Präfix ersetzen.
4. Toniebox einschalten und eine Figur aufstellen, damit MQTT-Statusmeldungen erscheinen.
5. Ein Topic wie `teddyCloud/box/ABC123456/ContentTitle` oder `teddyCloud/box/ABC123456/Playback` suchen. **`ABC123456` ist die Box-ID.**
6. Im Einrichtungsdialog bei **Box-ID** ausschließlich `ABC123456` eintragen, bei **MQTT-Topic-Präfix** `teddyCloud`.

**Wichtig:** Im oberen Bereich **Ein Paket veröffentlichen** nichts eingeben oder veröffentlichen. `teddyCloud/status` mit der Nachricht `online` ist die Statusmeldung des Servers, **nicht** die Box-ID. Auch `teddyCloud/hass-id/status` bezeichnet den Server. Wenn unter `teddyCloud/box/#` nichts erscheint, zunächst unter `teddyCloud/#` prüfen, ob überhaupt Box-Ereignisse vorhanden sind.

## Optionen

In **Geräte & Dienste → TeddyCloud Home Assistant → Konfigurieren**:

- `box_color`: sechsstelliger Hexfarbwert (z. B. `#c991c5`).
- `fallback_cover`: URL zu einem Bild (optional; HTTPS oder `/local/...`).
- `catalog`: JSON-Zuordnung von **ContentAudioId** zu Bild, Titel und Dauer, siehe `examples/catalog.json`.

MQTT-Host, Port, TLS und Zugangsdaten werden zentral in **Einstellungen → Geräte & Dienste → MQTT → Neu konfigurieren** eingestellt. Hier absichtlich **kein zweiter Broker-Login**. Die Topic-Prefix- und Box-ID-Einstellungen werden beim Anlegen eines Eintrags festgelegt; zum Ändern in v0.1.0 Eintrag löschen und neu hinzufügen.

## Bekannte Grenzen / Entwicklungsstand

- Alpha/Prototyp: auf einer realen Home-Assistant-Installation **noch nicht getestet**. Bitte zuerst auf einem Testsystem oder mit Backup installieren.
- Nur Live-MQTT-Daten, keine automatische Historie oder robuste Rekonstruktion der Position nach HA-Neustart.
- Der Katalog wird zunächst manuell als JSON gepflegt (nicht als fertiger Figuren-Browser).
- Home Assistants bestehende TeddyCloud-MQTT-Discovery-Geräte bleiben unabhängig bestehen.
- Keine automatische Coverauflösung aus der TeddyCloud-Image-Entität und keine separate Auswahl einer Box-Farbpalette (Hex-Eingabe vorhanden).

## Contributing

Issues und Pull Requests willkommen. Für ein öffentliches Release: Tests mit mehreren TeddyCloud-/HA-Versionen, HACS-Validierung, UI-Optionen und Lizenzprüfung für mögliche Tonie-Cover-Datenbank ergänzen. **Keine privaten Zertifikate, MQTT-Passwörter oder persönlichen MQTT-Logs committen.**

## Lizenz

MIT (siehe LICENSE).

## Fehlerbehebung: „Leerlauf“ trotz Playback ON / „Unbekannter Tonie“

In v0.1.4 wurde die MQTT-Payload-Dekodierung korrigiert: `b"ON"` wird als `ON` interpretiert.
Die Integration hört auf `{prefix}/box/{box_id}/+` und unterstützt nun auch `ContentPicture`.
Überprüfe die **Box-ID** und das Topic-Präfix. Teste in MQTT → Konfigurieren mit `teddyCloud/box/#`.
Bei echten `Playback=ON` und `ContentTitle`-Meldungen aktualisiert sich der Player.
Home Assistant benötigt nach dem Austausch der Python-Dateien einen **Neustart**. Gegebenenfalls die Figur abnehmen und wieder aufsetzen, damit neue MQTT-Nachrichten entstehen; die Box-Nachrichten sind eventuell nicht retained.

### Coverbilder

TeddyCloud liefert beispielsweise `http://localhost/cache/BILD.png`. Das `localhost` meint den TeddyCloud-Server und ist aus Home Assistant nicht direkt erreichbar.
Unter **Einstellungen → Geräte & Dienste → TeddyCloud Home Assistant → Konfigurieren** `TeddyCloud-Adresse für Coverbilder` setzen, z. B. `http://192.168.180.81` (im eigenen Netzwerk anpassen).
Das Cover wird aus `ContentPicture` aufgelöst; ein eigener Katalogeintrag mit `cover` hat Vorrang.
**Achtung:** Die Bildadresse muss vom Browser, der das Dashboard anzeigt, erreichbar sein; bei Zugriff über HTTPS von außerhalb können HTTP-Bilder wegen Mixed Content blockiert werden. Diese Version ist ein lokaler Prototyp.
Die tatsächliche physische Tonie-Figur ist nicht automatisch als Bild im MQTT-Datensatz enthalten. Für Figurenfotos `cover` je `ContentAudioId` im Katalog hinterlegen.


## Neu in v0.1.4: Automatische Figurenbilder

Unter **TeddyCloud Home Assistant → Konfigurieren → Automatisch Figurenbilder online anhand der Audio-ID suchen** lässt sich die Funktion an- oder ausschalten (standardmäßig an).

1. TeddyCloud meldet `ContentAudioId`, z. B. `1725629281`.
2. Home Assistant lädt bei Bedarf einen öffentlichen JSON-Katalog von `toniebox-reverse-engineering/tonies-json` über HTTPS; eine heruntergeladene Tabelle wird im Arbeitsspeicher bis zu 24 Stunden wiederverwendet und bei Fehlern frühestens nach einer Stunde erneut versucht.
3. Nur eine **exakte Audio-ID-Übereinstimmung** zählt. Der Katalogeintrag liefert eine Bild-URL (`pic`), die vorrangig als Figurenbild verwendet wird.
4. Gibt es keinen Treffer, bleibt das von TeddyCloud veröffentlichte `ContentPicture` als Ersatz verfügbar. Ist auch dieses nicht erreichbar, folgt die eigene `fallback_cover`-URL.
5. Für ein bestimmtes Hörspiel kann im JSON-Katalog der Integration `"figure": "https://..."` gesetzt werden; das überschreibt den Online-Fund. Manuelle `cover`-URLs bleiben als sekundärer Fallback erhalten.

**Hinweis:** Die Bilddatenbank enthält öffentlich verlinkte Produktabbildungen. **Ein passender Audio-ID-Datensatz garantiert nicht, dass das verlinkte Bild exakt die physische Figur fotografisch zeigt**, beispielsweise bei Sondereditionen oder nachträglich bespielten Kreativ-Tonies. Bei benutzerdefinierten Audio-Dateien kann die Audio-ID in der Community-Datenbank fehlen. Es wird dann **nicht willkürlich ein ähnlich betiteltes Bild ausgewählt**.

**Datenschutz und Rechte:** Der Home-Assistant-Server kontaktiert `raw.githubusercontent.com`; der Browser lädt das gefundene Bild vom ursprünglichen Bildhost. Bildrechte verbleiben bei den Rechteinhabern. Keine Bilder werden mit diesem GitHub-Projekt ausgeliefert; für öffentliche Verbreitung oder lokales Caching fremder Bilder gesondert Rechte prüfen.

**Technische Grenze:** Bei Ausfall der Datenquelle gibt es weiterhin MQTT-Titel und Cover aus TeddyCloud. Die Karte zeigt die eigentliche Quelle in `image_source` an (`online_catalog`, `manual_figure`, `teddycloud_cover`). Nach Upgrade Home Assistant neu starten und Tonie neu aufsetzen, um ein frisches `ContentAudioId`-Ereignis zu erzeugen.


## Neu in v0.1.5: Box mit Figur wie auf einem Produktfoto

Die Lovelace-Karte stellt standardmäßig eine **stilisiert gezeichnete Toniebox in der gewählten Farbe** dar und legt das per Audio-ID gefundene Online-Bild **davor**. Bei passendem freigestelltem Figurenbild entsteht eine Ansicht ähnlich einer Toniebox mit aufgestellter Figur. **Es ist kein garantiert authentisches Kombinationsfoto**. Bilder aus der Datenbank können auch quadratische Cover oder weiße Hintergründe enthalten. Ein zuverlässiges Entfernen von Hintergründen ist in der Erweiterung nicht enthalten.

Mit `box_image: 'https://…'` kann eine **eigene zulässig genutzte Produktfoto-URL der Box** hinterlegt werden, oder mit `figure_image: 'https://…'` ein eigenes freigestelltes Figurenfoto. `color: '#e33d35'` legt die stilisierte Farbe fest. `composition: false` schaltet zurück auf die einfache Coveransicht. Die öffentliche Bildquelle ist nicht dauerhaft erreichbar garantiert.

Derzeit findet **keine frei formulierte Internet-Bildersuche** statt: aus Zuverlässigkeits- und Rechte-Gründen verwendet die Integration nur den bekannten Tonies-Metadatenkatalog mit **exaktem Audio-ID-Match**. Für echtes fotorealistisches Box+Figur-Rendering wären separate, lizenzierte und freigestellte Box- und Figurenbilder nötig.

Nach dem Aktualisieren `www/teddycloud-homeassistant-card.js` ersetzen und Browser-Cache hart aktualisieren. Python-Code gegenüber 0.1.4 ist unverändert, aber die Manifest-Version ist erhöht.


## Lautstärke aus Home Assistant einstellen

TeddyCloud erlaubt **keine direkte Fernsteuerung** der aktuellen Wiedergabelautstärke (0–16).
Stattdessen können die **maximalen Lautstärkegrenzen** für Lautsprecher und Kopfhörer
über MQTT gesetzt werden. Die Box übernimmt die Grenzen erst beim nächsten
*Freshness Check*. Die physische Lautstärke wird weiterhin über die Ohren eingestellt.

Diese Integration ergänzt pro Box folgende Entitäten:

- `number` **Lautsprecher-Lautstärkelimit**: 25 %, 50 %, 75 % oder 100 %
- `number` **Kopfhörer-Lautstärkelimit**: 25 %, 50 %, 75 % oder 100 %
- `sensor` **Aktuelle Lautstärke**: der von der Box gemeldete Rohwert (0–16)

Die `number`-Entitäten senden die Werte 0–3 über
`{prefix}/box/{box_id}/CmdVolLimitSpk/set` bzw.
`{prefix}/box/{box_id}/CmdVolLimitHdp/set`.
Der angezeigte Sollwert wird erst nach der entsprechenden MQTT-Statusmeldung
übernommen; beim ersten Start kann die Entität deshalb `unbekannt` anzeigen.
Die bereits vorhandenen TeddyCloud-MQTT-Discovery-Entitäten können dieselben
Einstellungen ebenfalls bereitstellen, sodass ggf. Duplikate entstehen.

**Voraussetzung:** Eine TeddyCloud-Version mit Unterstützung für
`CmdVolLimitSpk` und `CmdVolLimitHdp`.
Siehe [MQTT_CONTROL.md](https://github.com/toniebox-reverse-engineering/teddycloud/blob/master/MQTT_CONTROL.md).


## LED-Helligkeit einstellen

Pro Toniebox gibt es eine `number`-Entität **LED-Helligkeit** als Schieberegler, genau wie bei den Lautstärkelimits.

- **0 %** = Aus (MQTT-Wert `1`)
- **50 %** = Gedimmt (MQTT-Wert `2`)
- **100 %** = An (MQTT-Wert `0`)

Es sind nur diese drei Stufen möglich, keine stufenlose Helligkeit. Die Integration sendet den gewählten Modus an `{prefix}/box/{box_id}/CmdLed/set` und übernimmt Statusmeldungen von `{prefix}/box/{box_id}/CmdLed`. Die Toniebox setzt Änderungen erst beim nächsten Freshness Check um.


## Lovelace-Dashboard für den ersten Release

Die Karte `teddycloud-homeassistant-card` zeigt Figur/Box, Hörspieltitel,
Wiedergabestatus, geschätzten Fortschritt, Ladestation und drei Regler
(Lautsprecher-Limit, Kopfhörer-Limit und LED-Helligkeit).

```yaml
type: custom:teddycloud-homeassistant-card
entity: media_player.meine_toniebox_now_playing
composition: true
# Optional, falls mehrere Entitäten ähnliche Namen haben:
# speaker_entity: number.meine_toniebox_lautsprecher_lautstarkelimit
# headphone_entity: number.meine_toniebox_kopfhorer_lautstarkelimit
# led_entity: number.meine_toniebox_led_helligkeit
# color: '#c991c5'
```

Die Entity-IDs im Beispiel müssen an deine Home-Assistant-Installation angepasst werden.
Ohne optionale IDs sucht die Karte nach den passenden Entitäten anhand des
angezeigten Box-Namens. Ist der Zustand einer Entität unbekannt, wird der Regler
deaktiviert, statt einen Wert zu erfinden. Die Begrenzungen werden erst mit dem
nächsten Freshness Check der Box wirksam.

**Release-Status:** Entwicklungsversion; noch nicht mit echter Toniebox und
Home Assistant getestet. Vor einem stabilen Release MQTT-Befehle, Zuordnung
der Entitäten, Cache-Reload der JavaScript-Ressource sowie Mehrboxbetrieb prüfen.


## Vereinfachte Installation ab Version 0.2.0

1. In **HACS → Benutzerdefinierte Repositories** die Adresse
   `https://github.com/mirkohd1999/teddycloud-homeassistant` als **Integration** hinzufügen.
2. Integration herunterladen, Home Assistant neu starten.
3. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** TeddyCloud Home Assistant
   einrichten (MQTT muss bereits verbunden sein; Box-ID und Prefix angeben).
4. Im Dashboard **Bearbeiten → Karte hinzufügen → TeddyCloud Home Assistant** wählen,
   die richtige `media_player`-Entität auswählen und speichern.

Die Lovelace-Karte ist im Integrationsordner enthalten und wird in normalen
Lovelace-Dashboards mit **Speicherverwaltung (Storage-Modus)** automatisch als
JavaScript-Modul registriert. `/config/www`-Kopie und manuelle
Ressourcenregistrierung sind dabei nicht mehr notwendig. Falls der Eintrag im
Kartenkatalog nicht erscheint, Dashboard neu laden und die Browser-Cache-Version
prüfen. Bei **YAML-Ressourcenmodus** kann Home Assistant keine automatisch
gespeicherten Ressourcen hinzufügen; dort die Ressource
`/teddycloud-homeassistant/card.js?v=0.2.0` als Modul in YAML eintragen.

**Box-Erkennung:** Die automatische Erkennung und Auswahl verschiedener Boxen
ist noch nicht umgesetzt. Die Box-ID kann weiterhin über MQTT-Ereignisse
unter `teddyCloud/box/#` ermittelt werden.

**Teststatus:** Diese Änderungen sind noch nicht auf echter Hardware geprüft.


## Karteneditor auf Deutsch und ohne eingeschaltete Toniebox

In der mitgelieferten Dashboard-Karte stehen die Beschriftungen jetzt auf
Deutsch. Die Konfiguration ist auch dann möglich, wenn der Player
`unavailable` ist oder gerade keine MQTT-Ereignisse sendet. Die Auswahl
zeigt bestehende Media-Player-Entitäten; alternativ kann eine
`media_player.*`-ID manuell eingegeben werden. Ohne konfigurierte
Entität zeigt die Karte einen Platzhalter statt eines Konfigurationsfehlers.

**Achtung:** Dies gilt für die Karte mit dem Typ
`custom:teddycloud-homeassistant-card`. Andere Toniebox-Karten haben
einen eigenen Editor; das Einspielen dieser Integration verändert deren
englische Texte und Validierungen nicht.


## Saubere Deinstallation

**Reihenfolge:** In Home Assistant unter **Einstellungen → Geräte & Dienste →
TeddyCloud Home Assistant** die Box-Einträge entfernen, **erst danach** das
Repository aus HACS deinstallieren. Dadurch kann `async_remove_entry` ausgeführt
werden. Werden lediglich die Integrationsdateien über HACS entfernt, ohne vorher
die Einträge zu löschen, läuft die Bereinigungsroutine möglicherweise nicht.

Wenn die **letzte** TeddyCloud-Box entfernt wird, löscht die Integration
automatisch ihre eigene Lovelace-Ressource (nur Storage-Modus) und Bilder aus
`/config/www/teddycloud_homeassistant/figures`, die nach numerischer Audio-ID
und mit unterstützter Bilddateiendung benannt sind. Unbekannte und
selbst hinzugefügte Dateien bleiben bestehen. Home Assistant verwaltet und
entfernt beim Löschen des Eintrags die zugehörigen Entitäten und Geräte.

**Dashboard-Karten:** Manuell erstellte Dashboard-Karten sind Bestandteil
deiner eigenen Dashboard-Konfiguration. Sie werden aus Sicherheitsgründen
nicht ungefragt verändert oder gelöscht; entferne solche Karten vor der
Deinstallation über **Dashboard bearbeiten**. Die Integration kann weder
YAML-verwaltete Dashboards noch eigene externe Bildarchive sicher automatisch
löschen. Mehrere konfigurierte Boxen behalten gemeinsame Ressourcen, bis die
letzte Box entfernt wurde.

Hinweis: Die lokale Bildarchiv-Funktion wird separat entwickelt und ist
nicht in jedem bereits veröffentlichten Stand enthalten.
