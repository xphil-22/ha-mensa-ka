"""Constants for the Karlsruher Mensen integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "mensa_ka"
API_URL = "https://api.mensa-ka.de"

CONF_CANTEENS = "canteens"
CONF_FORECAST_DAYS = "forecast_days"

DEFAULT_UPDATE_INTERVAL = timedelta(hours=6)
DEFAULT_FORECAST_DAYS = 14
MIN_FORECAST_DAYS = 1
MAX_FORECAST_DAYS = 30

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]

# Served via `_async_register_frontend_card` in __init__.py. Bump CARD_VERSION
# whenever www/mensa-ka-card.js changes so browsers don't keep a stale cached
# copy of the module.
CARD_URL_PATH = "/mensa_ka-card/mensa-ka-card.js"
CARD_VERSION = "1"

# Labels are taken verbatim (only shortened) from the descriptions the API itself
# returns for these enum values, to avoid mistranslating allergen-relevant data.
# The two-/three-letter code is kept alongside the label so it can be cross-checked
# against the official Studierendenwerk Karlsruhe legend.
ALLERGEN_LABELS: dict[str, str] = {
    "CA": "Cashew nuts",
    "DI": "Spelt / gluten",
    "EI": "Eggs",
    "ER": "Peanuts",
    "FI": "Fish",
    "GE": "Barley / gluten",
    "HF": "Oat / gluten",
    "HA": "Hazelnuts",
    "KA": "Kamut / gluten",
    "KR": "Crustaceans",
    "LU": "Lupin",
    "MA": "Almonds",
    "ML": "Milk / lactose",
    "PA": "Brazil nuts",
    "PE": "Pecans",
    "PI": "Pistachios",
    "QU": "Macadamia nuts",
    "RO": "Rye / gluten",
    "SA": "Sesame",
    "SE": "Celery",
    "SF": "Sulphite",
    "SN": "Mustard",
    "SO": "Soya",
    "WA": "Walnuts",
    "WE": "Wheat / gluten",
    "WT": "Molluscs",
    "LA": "Animal rennet",
    "GL": "Gelatin",
}

ADDITIVE_LABELS: dict[str, str] = {
    "COLORANT": "Colorants",
    "PRESERVING_AGENTS": "Preserving agents",
    "ANTIOXIDANT_AGENTS": "Antioxidant agents",
    "FLAVOUR_ENHANCER": "Flavour enhancers",
    "PHOSPHATE": "Phosphate",
    "SURFACE_WAXED": "Surface waxed",
    "SULPHUR": "Sulphur",
    "ARTIFICIALLY_BLACKENED_OLIVES": "Artificially blackened olives",
    "SWEETENER": "Sweetener",
    "LAXATIVE_IF_OVERUSED": "Laxative if overused",
    "PHENYLALANINE": "Contains phenylalanine",
    "ALCOHOL": "May contain alcohol",
    "PRESSED_MEAT": "Pressed meat",
    "GLAZING_WITH_CACAO": "Glazed with cacao",
    "PRESSED_FISH": "Pressed fish",
}

FOOD_TYPE_LABELS: dict[str, str] = {
    "VEGAN": "Vegan",
    "VEGETARIAN": "Vegetarian",
    "BEEF": "Beef",
    "BEEF_AW": "Beef (regional husbandry)",
    "PORK": "Pork",
    "PORK_AW": "Pork (regional husbandry)",
    "FISH": "Fish",
    "POULTRY": "Poultry",
    "UNKNOWN": "Unknown",
}

FOOD_TYPE_ICONS: dict[str, str] = {
    "vegan": "\U0001f331",
    "vegetarian": "\U0001f955",
    "default": "\U0001f356",
}
