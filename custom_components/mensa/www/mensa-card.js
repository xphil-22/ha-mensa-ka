/**
 * Lovelace card for the Mensa integration.
 *
 * Renders one canteen's meal plan (one card per `sensor.<canteen>_meal_plan`
 * entity) with real CSS - unlike a markdown card, whose sanitizer strips
 * every `style` attribute from embedded HTML, this card owns its DOM and
 * shadow root directly, so layout and styling actually render as designed.
 */

function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [key, value] of Object.entries(attrs)) {
      if (value == null) continue;
      if (key === "class") el.className = value;
      else if (key === "style") el.setAttribute("style", value);
      else if (key.startsWith("on") && typeof value === "function") {
        el.addEventListener(key.slice(2), value);
      } else {
        el.setAttribute(key, value);
      }
    }
  }
  for (const child of children.flat()) {
    if (child == null) continue;
    el.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return el;
}

const CARD_STYLE = `
  :host { display: block; }
  ha-card { padding: 16px; }
  .header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
    margin-bottom: 12px;
  }
  .header .title {
    font-size: 1.2em;
    font-weight: 600;
    color: var(--primary-text-color);
  }
  .header .day {
    font-size: 0.9em;
    color: var(--secondary-text-color);
    white-space: nowrap;
  }
  .empty {
    color: var(--secondary-text-color);
    font-style: italic;
  }
  .error {
    color: var(--error-color, #db4437);
  }
  details.line {
    border: 1px solid var(--divider-color);
    border-radius: 12px;
    margin-bottom: 10px;
    overflow: hidden;
  }
  details.line:last-child { margin-bottom: 0; }
  details.line[open] summary { border-bottom: 1px solid var(--divider-color); }
  summary {
    cursor: pointer;
    padding: 10px 14px;
    font-weight: 600;
    color: var(--primary-text-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    list-style: none;
  }
  summary::-webkit-details-marker { display: none; }
  summary::after {
    content: "\\25BE";
    margin-left: auto;
    padding-left: 8px;
    transition: transform 0.15s ease;
    color: var(--secondary-text-color);
  }
  details.line[open] summary::after { transform: rotate(180deg); }
  .line-count {
    font-weight: 400;
    font-size: 0.8em;
    color: var(--secondary-text-color);
    white-space: nowrap;
  }
  .meals {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 12px 14px;
  }
  .meal { display: flex; gap: 12px; align-items: flex-start; }
  .thumb {
    width: 64px;
    height: 64px;
    min-width: 64px;
    border-radius: 10px;
    overflow: hidden;
    background: var(--secondary-background-color);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
  }
  .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .meal-info { min-width: 0; flex: 1; }
  .meal-name { font-weight: 600; color: var(--primary-text-color); }
  .meal-diet {
    font-size: 0.85em;
    color: var(--secondary-text-color);
    margin-top: 2px;
  }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .chip {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 0.78em;
    line-height: 1.5;
  }
  .chip.price { background: var(--secondary-background-color); font-weight: 600; }
  .chip.allergen { background: rgba(255, 152, 0, 0.22); }
  .chip.additive { background: var(--secondary-background-color); }
`;

class MensaCard extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
    this._lastRenderKey = null;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error("Set 'entity' to a Mensa meal plan sensor.");
    }
    this._config = config;
    this._lastRenderKey = null;
    this._renderShell();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  getCardSize() {
    return 6;
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states).find(
      (entityId) =>
        entityId.startsWith("sensor.") && hass.states[entityId].attributes.lines !== undefined
    );
    return { entity: entity || "" };
  }

  _renderShell() {
    this._root.innerHTML = "";
    const style = document.createElement("style");
    style.textContent = CARD_STYLE;
    this._card = h("ha-card");
    this._content = h("div", { class: "content" });
    this._card.appendChild(this._content);
    this._root.appendChild(style);
    this._root.appendChild(this._card);
  }

  _update() {
    if (!this._hass || !this._config) return;
    const stateObj = this._hass.states[this._config.entity];
    const renderKey = stateObj
      ? `${stateObj.state}|${stateObj.last_changed}|${JSON.stringify(stateObj.attributes)}`
      : "missing";
    if (renderKey === this._lastRenderKey) return;
    this._lastRenderKey = renderKey;
    this._render(stateObj);
  }

  _render(stateObj) {
    if (!this._content) this._renderShell();
    this._content.innerHTML = "";

    if (!stateObj) {
      this._content.appendChild(
        h(
          "div",
          { class: "error" },
          `Entity not found: ${this._config.entity}`
        )
      );
      return;
    }

    const attrs = stateObj.attributes;
    const lines = attrs.lines || [];
    const title = attrs.friendly_name || this._config.entity;

    const header = h(
      "div",
      { class: "header" },
      h("div", { class: "title" }, title),
      attrs.day ? h("div", { class: "day" }, attrs.day) : null
    );
    this._content.appendChild(header);

    if (!lines.length) {
      this._content.appendChild(h("div", { class: "empty" }, "No meals available."));
      return;
    }

    for (const line of lines) {
      this._content.appendChild(this._renderLine(line));
    }
  }

  _renderLine(line) {
    const meals = line.meals || [];
    const mealLabel = meals.length === 1 ? "1 meal" : `${meals.length} meals`;

    const summary = h(
      "summary",
      null,
      h("span", null, line.line),
      h("span", { class: "line-count" }, mealLabel)
    );
    const mealsEl = h("div", { class: "meals" }, ...meals.map((meal) => this._renderMeal(meal)));
    return h("details", { class: "line", open: "" }, summary, mealsEl);
  }

  _renderMeal(meal) {
    const thumb = h("div", { class: "thumb" });
    if (meal.image_url) {
      thumb.appendChild(h("img", { src: meal.image_url, alt: meal.name, loading: "lazy" }));
    } else {
      thumb.textContent = meal.diet_icon || "\u{1F37D}️";
    }

    const chips = [
      h(
        "span",
        { class: "chip price" },
        `Student ${Number(meal.price_student).toFixed(2)} €`
      ),
    ];
    if (meal.price_employee != null) {
      chips.push(
        h(
          "span",
          { class: "chip price" },
          `Employee ${Number(meal.price_employee).toFixed(2)} €`
        )
      );
    }
    for (const allergen of meal.allergens || []) {
      chips.push(h("span", { class: "chip allergen" }, allergen));
    }
    for (const additive of meal.additives || []) {
      chips.push(h("span", { class: "chip additive" }, additive));
    }

    const info = h(
      "div",
      { class: "meal-info" },
      h("div", { class: "meal-name" }, `${meal.diet_icon ? meal.diet_icon + " " : ""}${meal.name}`),
      meal.diet_label ? h("div", { class: "meal-diet" }, meal.diet_label) : null,
      h("div", { class: "chips" }, ...chips)
    );

    return h("div", { class: "meal" }, thumb, info);
  }
}

customElements.define("mensa-card", MensaCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "mensa-card",
  name: "Mensa",
  description: "Meal plan card for one Mensa canteen sensor.",
});
