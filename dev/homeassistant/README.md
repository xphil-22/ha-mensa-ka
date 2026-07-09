# Home Assistant Dev Environment

Local test instance for trying the integration in a browser.

## Start

```bash
docker compose -f docker-compose.dev.yml up -d
```

Then open `http://localhost:8123` in your browser.

## Test the Integration

1. If Home Assistant asks you to create a user on first startup, complete the onboarding flow once.
2. Go to `Settings -> Devices & Services -> Add Integration`.
3. Search for `Mensa` and go through the Config Flow.

## Logs

```bash
docker compose -f docker-compose.dev.yml logs -f homeassistant
```

## Reset

Persistent Home Assistant data is stored in `dev/homeassistant/config/.storage/`.
If you want to reset the instance completely, stop the container and delete that directory.
