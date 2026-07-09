# Contributing

Contributions are welcome.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
```

## Quality Checks

Run the local checks before opening a pull request:

```bash
ruff check custom_components tests
pytest tests/ -v
```

For a manual end-to-end UI test in Home Assistant:

```bash
docker compose -f docker-compose.dev.yml up -d
```

Then open `http://localhost:8123` and test the config flow via `Settings -> Devices & Services`.

## Adding a provider

A provider is a source of canteens and meal plans (e.g. one university's own API). To add one:

1. Add a new module under `custom_components/mensa/providers/` implementing the `Provider` protocol from `providers/base.py` (`async_get_canteens`, `async_get_meal_plans`, `display_name`). See `providers/karlsruhe.py` for a full example, or `providers/openmensa.py` for one dealing with missing prices, no discrete allergen codes, and per-canteen staleness.
2. Register it in `PROVIDERS` in `providers/__init__.py`.
3. Reuse the shared `Canteen`, `Price`, `Meal`, `MealDay` dataclasses from `providers/models.py` rather than inventing new ones — the config flow, coordinator, sensor, and calendar platforms are all written against those. `Price` fields and `Meal.notes` are optional/nullable specifically so a provider that doesn't report something isn't forced to invent a value.
4. If the catalog is too large for a plain multi-select (roughly: more than a few dozen canteens), set `requires_search = True` on the provider — the config flow then inserts a text-filter step before the canteen picker automatically.

No changes to the config flow, coordinator, or entity platforms are needed for a new provider with the same data shape.

## Pull Requests

- Keep changes focused and small where possible.
- Update tests and documentation when behavior changes.
- Do not mix unrelated refactors with feature work.
- Describe user-visible changes clearly in the pull request.
