# KIT Mensa for Home Assistant

[![Validate](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/validate.yml/badge.svg)](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/validate.yml)
[![Test](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/test.yml/badge.svg)](https://github.com/xphil-22/ha-mensa-ka/actions/workflows/test.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Home Assistant integration for meal plans from the canteens and cafeterias of Studierendenwerk Karlsruhe (KIT). It uses the public GraphQL API from [kronos-et-al/MensaApp](https://github.com/kronos-et-al/MensaApp) (`api.mensa-ka.de`).

For each selected canteen, the integration creates one **calendar entity** with a daily event whenever meals are offered. The event contains all meals for that day, grouped by serving line, including price, meal type (vegan, vegetarian, and so on), allergens, and additives.

The integration exposes an additional **sensor entity** per canteen as the primary dashboard-friendly representation. The calendar entity remains available for multi-day and agenda-style use.

## Features

- Config Flow setup directly in Home Assistant
- Support for multiple canteens and cafeterias in a single integration
- Calendar entities with daily meals, prices, allergens, and additives
- Sensor entities with structured meal attributes for dashboard rendering
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
3. A device with both a calendar entity and a sensor entity is created for each selected canteen, for example `calendar.mensa_adenauerring` and `sensor.mensa_adenauerring_meal_plan`.

You can change the selected canteens at any time through the integration options.

## Dashboard View

The calendar entity is useful for agenda and multi-day navigation, but it is not ideal for a polished dashboard presentation because Home Assistant renders the event description as a large text block.

The sensor entity is designed to solve that:

- The calendar entity stays available for users who want an agenda-style overview.
- The sensor entity becomes the preferred dashboard-oriented view.
- The sensor state stays compact and automation-friendly.
- Structured attributes provide grouped meal data for custom cards, markdown cards, or template-based Lovelace layouts.

The intended sensor model per canteen is:

- State: number of meals for today, or the next available day with meals
- Attributes:
  - `day`
  - `lines`
  - each meal entry containing name, diet label, diet icon, prices, allergens, additives, and image URLs

This keeps the dashboard representation clean while preserving the richer multi-day browsing experience in the calendar entity.

## Example Dashboard

The following Markdown card is intended for the `v1.1` sensor entity. It renders the structured `lines` attribute into a layout that is closer to the official MensaApp presentation.

A more complete paste-ready Lovelace example is available in [examples/dashboard/mensa_dashboard.yaml](examples/dashboard/mensa_dashboard.yaml).

Assumption:
- your entity id is similar to `sensor.mensa_adenauerring_meal_plan`

```yaml
type: markdown
title: KIT Mensa
content: >
  {% set entity = 'sensor.mensa_adenauerring_meal_plan' %}
  {% set day = state_attr(entity, 'day') %}
  {% set lines = state_attr(entity, 'lines') or [] %}

  {% if not lines %}
  No meals available.
  {% else %}
  **{{ day }}**

  {% for line in lines %}
  ### {{ line.line }}
  {% for meal in line.meals %}
  - {{ meal.diet_icon }} **{{ meal.name }}**
    {% if meal.diet_label %}({{ meal.diet_label }}){% endif %}
    {% if meal.image_url %}
    ![{{ meal.name }}]({{ meal.image_url }})
    {% endif %}
    - Student: {{ '%.2f'|format(meal.price_student) }} EUR
    {% if meal.allergens %}
    - Allergens: {{ meal.allergens | join(', ') }}
    {% endif %}
    {% if meal.additives %}
    - Additives: {{ meal.additives | join(', ') }}
    {% endif %}
  {% endfor %}

  {% endfor %}
  {% endif %}
```

You can duplicate the card for multiple canteens by changing the entity id, or use a more advanced template/dashboard layout once the sensor data model is in place.

## Manual QA Checklist

For manual verification of the `v1.1` sensor implementation:

1. Restart the local Home Assistant dev container:
   `docker compose -f docker-compose.dev.yml up -d`
2. Open `http://localhost:8123`.
3. Verify that the integration now exposes a sensor entity in addition to the calendar entity.
4. Inspect the sensor attributes in Developer Tools and confirm that `day` and `lines` are populated as expected.
5. Paste the example Markdown card into a test dashboard.
6. Compare the resulting presentation with the current calendar-based popup and confirm that the sensor-based layout is easier to scan.

## Roadmap

- Improved dashboard examples and Lovelace presets for the sensor-based view
- Dedicated Lovelace custom card for a richer native MensaApp-like frontend
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
