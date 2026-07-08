# KIT Mensa für Home Assistant

[![Validate](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/validate.yml/badge.svg)](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/validate.yml)
[![Test](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/test.yml/badge.svg)](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/test.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home-Assistant-Integration für die Speisepläne der Mensen und Cafeterien des Studierendenwerks Karlsruhe (KIT). Nutzt die öffentliche GraphQL-API von [kronos-et-al/MensaApp](https://github.com/kronos-et-al/MensaApp) (`api.mensa-ka.de`).

Für jede ausgewählte Mensa wird eine **Kalender-Entity** angelegt, mit einem Termin pro Tag, an dem die Mensa Essen anbietet. Der Termin enthält alle Gerichte dieses Tages (gruppiert nach Ausgabe/Linie) inklusive Preis, Ernährungstyp (vegan/vegetarisch/...), Allergenen und Zusatzstoffen.

## Umfang (v1)

Die Integration ist **read-only**: Es werden nur Speisepläne gelesen. Mutationen wie das Abgeben von Bewertungen oder das Hochladen von Bildern benötigen laut [`ApiAuth.md`](https://github.com/kronos-et-al/MensaApp/blob/main/doc/ApiAuth.md) der Upstream-API einen signierten Request mit einem API-Key, dessen Bezugsprozess dort selbst noch nicht dokumentiert ist. Deshalb sind diese Funktionen (noch) nicht implementiert.

## Installation

### Über HACS (empfohlen)

1. HACS → Integrationen → Menü (⋮) → *Benutzerdefinierte Repositories*.
2. Repository-URL `https://github.com/xphil-22/ha-mensa-ka` mit Kategorie *Integration* hinzufügen.
3. "KIT Mensa" installieren und Home Assistant neu starten.

### Manuell

Den Ordner `custom_components/mensa_ka` in das `custom_components`-Verzeichnis deiner Home-Assistant-Konfiguration kopieren und Home Assistant neu starten.

## Einrichtung

1. Einstellungen → Geräte & Dienste → Integration hinzufügen → "KIT Mensa" suchen.
2. Die gewünschten Mensen/Cafeterien aus der Liste auswählen und die Anzahl der Tage festlegen, die im Voraus abgerufen werden sollen.
3. Für jede ausgewählte Mensa wird ein Gerät mit einer Kalender-Entity angelegt (z. B. `calendar.mensa_adenauerring`).

Die Auswahl der Mensen kann jederzeit über die Optionen der Integration angepasst werden.

## Roadmap

- Zusätzliche Sensor-Entity ("heutige Gerichte") als Ergänzung zur Kalender-Entity.
- Bewertungen abgeben, sobald der API-Key-Beschaffungsprozess upstream geklärt ist.
- Aufnahme in [home-assistant/brands](https://github.com/home-assistant/brands) für ein eigenes Icon.

## Entwicklung

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
ruff check custom_components tests
pytest tests/ -v
```

## Browser-Test in lokaler Home-Assistant-Instanz

Fuer einen echten UI-Test der Integration gibt es eine lokale Dev-Umgebung mit Docker:

```bash
docker compose -f docker-compose.dev.yml up -d
```

Danach `http://localhost:8123` im Browser oeffnen und den Home-Assistant-Onboarding-Flow einmal abschliessen, falls beim ersten Start noch kein Benutzer existiert. Anschliessend unter `Einstellungen -> Geraete & Dienste -> Integration hinzufuegen` nach `KIT Mensa` suchen und den Config Flow durchklicken.

Logs:

```bash
docker logs --tail 120 ha-mensa-ka-dev
```

## Lizenz

MIT, siehe [LICENSE](LICENSE). Die Daten stammen vom [Studierendenwerk Karlsruhe](https://www.sw-ka.de/) über die API von [kronos-et-al/MensaApp](https://github.com/kronos-et-al/MensaApp).
