# KIT Mensa for Home Assistant

[![Validate](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/validate.yml/badge.svg)](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/validate.yml)
[![Test](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/test.yml/badge.svg)](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/test.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for meal plans from the canteens and cafeterias of Studierendenwerk Karlsruhe (KIT). It uses the public GraphQL API from [kronos-et-al/MensaApp](https://github.com/kronos-et-al/MensaApp) (`api.mensa-ka.de`).

For each selected canteen, the integration creates one **calendar entity** with a daily event whenever meals are offered. The event contains all meals for that day, grouped by serving line, including price, meal type (vegan, vegetarian, and so on), allergens, and additives.

## Features

- Config Flow setup directly in Home Assistant
- Support for multiple canteens and cafeterias in a single integration
- Calendar entities with daily meals, prices, allergens, and additives
- HACS-compatible structure for simple installation
- Local Docker-based Home Assistant dev environment for UI testing

## Scope (v1)

The integration is **read-only**: it only fetches meal plans. According to the upstream API documentation in [`ApiAuth.md`](https://github.com/kronos-et-al/MensaApp/blob/main/doc/ApiAuth.md), mutations such as submitting ratings or uploading images require a signed request with an API key, and the process for obtaining that key is still not documented there. For that reason, these features are not implemented yet.

## Installation

### Via HACS (recommended)

1. In HACS, go to `Integrations -> Menu (⋮) -> Custom repositories`.
2. Add `https://github.com/xphil-22/ha-mensa-ka` as a repository with category `Integration`.
3. Install `KIT Mensa` and restart Home Assistant.

### Manual

Copy the `custom_components/mensa_ka` folder into the `custom_components` directory of your Home Assistant configuration and restart Home Assistant.

## Setup

1. Go to `Settings -> Devices & Services -> Add Integration` and search for `KIT Mensa`.
2. Select the canteens or cafeterias you want to track and choose how many days ahead should be fetched.
3. A device with a calendar entity is created for each selected canteen, for example `calendar.mensa_adenauerring`.

You can change the selected canteens at any time through the integration options.

## Roadmap

- Additional sensor entity for today's meals alongside the calendar entity
- Meal ratings once the upstream API key process is clarified
- Inclusion in [home-assistant/brands](https://github.com/home-assistant/brands) for a dedicated icon

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
ruff check custom_components tests
pytest tests/ -v
```

## Browser Test in a Local Home Assistant Instance

For a real UI test of the integration, a local Docker-based Home Assistant dev environment is included:

```bash
docker compose -f docker-compose.dev.yml up -d
```

Then open `http://localhost:8123` in your browser and complete the Home Assistant onboarding flow if no user exists yet. After that, go to `Settings -> Devices & Services -> Add Integration`, search for `KIT Mensa`, and walk through the Config Flow.

Logs:

```bash
docker logs --tail 120 ha-mensa-ka-dev
```

## Repository

- Issues: [GitHub Issues](https://github.com/xphil-22/ha-mensa-ka/issues)
- Contributing: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security: [SECURITY.md](SECURITY.md)

## License

MIT, see [LICENSE](LICENSE). The meal data originates from [Studierendenwerk Karlsruhe](https://www.sw-ka.de/) via the API from [kronos-et-al/MensaApp](https://github.com/kronos-et-al/MensaApp).
