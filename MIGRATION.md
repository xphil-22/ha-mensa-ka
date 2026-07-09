# Migrating from `ha-mensa-ka`

Version `1.0.0` renames this project from `ha-mensa-ka` (domain `mensa_ka`, Karlsruhe-only) to `ha-mensa` (domain `mensa`, provider-based). This is an intentional breaking change, not an in-place upgrade — old entities, automations, and dashboards do not carry over automatically.

## What changes

- Integration domain: `mensa_ka` → `mensa`. Entity ids like `sensor.mensa_ka_*` are gone; new entities use the `mensa` domain's naming (e.g. `sensor.mensa_adenauerring_meal_plan`, unchanged if you already had a canteen named "Mensa Adenauerring").
- Lovelace card type: `custom:mensa-ka-card` → `custom:mensa-card`.
- Config flow: setup now starts with a "data source" step (currently only Studierendenwerk Karlsruhe) before the canteen picker.
- `single_config_entry` is gone: you can now add the integration multiple times (e.g. once per provider, once you have more than one).

## Steps

1. Update HACS: remove the old `ha-mensa-ka` custom repository and add `https://github.com/xphil-22/ha-mensa` instead (or update the repository URL if HACS offers that directly).
2. In Home Assistant, go to `Settings -> Devices & Services`, remove the old `Karlsruher Mensen` integration entry.
3. Edit any dashboards using the old card: change `type: custom:mensa-ka-card` to `type: custom:mensa-card` for each card.
4. Update any automations/scripts/templates referencing old entity ids (`sensor.mensa_ka_*`, `calendar.mensa_ka_*`, or `integration_entities('mensa_ka')`) to the new `mensa` equivalents.
5. Re-add the integration: `Settings -> Devices & Services -> Add Integration -> Mensa`, pick "Studierendenwerk Karlsruhe" as the data source, and reselect your canteens.

Canteen device/sensor names stay the same (they're derived from the canteen name, not the domain), so most dashboard cards only need the card `type` updated, not the `entity` id.
