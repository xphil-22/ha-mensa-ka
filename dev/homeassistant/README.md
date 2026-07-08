# Home Assistant Dev-Umgebung

Lokale Testinstanz fuer die Integration im Browser.

## Start

```bash
docker compose -f docker-compose.dev.yml up -d
```

Danach im Browser `http://localhost:8123` oeffnen.

## Integration testen

1. Falls Home Assistant beim ersten Start einen Benutzer anlegen will, den Onboarding-Flow einmal abschliessen.
2. `Einstellungen -> Geraete & Dienste -> Integration hinzufuegen`.
3. Nach `KIT Mensa` suchen und den Config Flow durchklicken.

## Logs

```bash
docker compose -f docker-compose.dev.yml logs -f homeassistant
```

## Reset

Persistente HA-Daten liegen unter `dev/homeassistant/config/.storage/`.
Wenn du die Instanz komplett neu aufsetzen willst, den Container stoppen und diesen Ordner loeschen.
