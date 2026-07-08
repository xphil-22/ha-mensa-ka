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

## Pull Requests

- Keep changes focused and small where possible.
- Update tests and documentation when behavior changes.
- Do not mix unrelated refactors with feature work.
- Describe user-visible changes clearly in the pull request.
