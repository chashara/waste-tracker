import { useMemo, useState } from "react";
import { formatMoney } from "../utils";

export default function IngredientPicker({ ingredients, selected, onSelect }) {
  const [query, setQuery] = useState("");

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    return ingredients.filter((i) => i.name.toLowerCase().includes(q)).slice(0, 8);
  }, [ingredients, query]);

  const choose = (ingredient) => {
    onSelect(ingredient);
    setQuery("");
  };

  if (selected) {
    return (
      <div className="selected-ingredient">
        <div>
          <strong>{selected.name}</strong>
          <span className="muted">
            {" "}
            {selected.category} · {formatMoney(selected.price_per_kg)}/kg
          </span>
        </div>
        <button type="button" className="btn-ghost" onClick={() => onSelect(null)}>
          Change
        </button>
      </div>
    );
  }

  return (
    <div className="picker">
      <input
        className="input"
        type="search"
        placeholder="Search ingredient..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && matches[0]) {
            e.preventDefault();
            choose(matches[0]);
          }
        }}
        autoComplete="off"
        autoFocus
      />
      {query.trim() && (
        <ul className="picker-list">
          {matches.length === 0 && <li className="picker-empty">No ingredient found</li>}
          {matches.map((i) => (
            <li key={i.id}>
              <button type="button" onClick={() => choose(i)}>
                <span>{i.name}</span>
                <span className="muted">
                  {i.category} · {formatMoney(i.price_per_kg)}/kg
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}