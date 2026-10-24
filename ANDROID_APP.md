# TeddyCloud Android – unabhängige MQTT-App

Die Android-App verbindet sich **direkt** mit dem MQTT-Broker von TeddyCloud und benötigt **keinen Home-Assistant-Server**.

## Android-App testen
1. Öffne unter **Actions** den Workflow **TeddyCloud Android APK**.
2. Starte ihn bei Bedarf über **Run workflow** auf dem Branch `feature/android-mqtt-app`.
3. Nach erfolgreichem Durchlauf wird das ZIP-Artefakt `TeddyCloud-Android-debug-APK` bereitgestellt.
4. Entpacke `app-debug.apk` und installiere sie auf Android 8.0 oder neuer.
5. Beim ersten Start MQTT-Host/IP, Port, Zugangsdaten und Präfix (`teddyCloud`) eingeben.

## Implementierte Funktionen
- MQTT (TCP / TLS) mit Wiederverbindung; Passwort lokal via Android Keystore geschützt
- Tonieboxen automatisch aus `<prefix>/box/+/+` erkennen, Box-ID alternativ manuell
- Mehrere Boxen verwalten, Namen und Farben auswählen
- Aktueller Titel, Audio-ID, gemeldeter Wiedergabestatus, Lautstärke und Ladestation
- Bilder und Laufzeiten optional über den Community-Katalog (exakter Audio-ID-Abgleich)
- Lautsprecher- und Kopfhörerlimits über MQTT `/set` auf 25/50/75/100 %
- LED aus/gedimmt/an über MQTT `/set`

## Technische Hinweise
Das Android-Projekt liegt auf diesem ersten Entwicklungszweig als `android-app-source.zip.b64`. Der Workflow dekodiert und entpackt es für den APK-Build. Eine normal entpackte Projektstruktur ist im bereitgestellten Android-Projekt-ZIP enthalten; der ZIP-Inhalt enthält auch eine ausführliche `README.md`.

**Stand:** erster Entwicklungsstand, keine Veröffentlichungsversion. Die MQTT-Zustandslogik ist lokal getestet. Der Android-Build über GitHub Actions (Gradle-Tests und Debug-APK) ist erfolgreich. Ein Praxistest mit einer echten Toniebox steht vor der Veröffentlichung noch aus.

**Einschränkungen:** Play/Pause, echte Wiedergabeposition, verlässlicher Akku-Prozentstand und die direkte Änderung der aktuellen Wiedergabelautstärke sind über die vorliegenden MQTT-Felder nicht verfügbar. Die Verbindung bleibt nur im App-Vordergrund aktiv.

## Sicherheit
MQTT ohne TLS nur im vertrauenswürdigen lokalen Netz oder über VPN einsetzen. Es werden keine TLS-Zertifikatsprüfungen deaktiviert. Keine Zugangsdaten in Issues oder Logs veröffentlichen.
