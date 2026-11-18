import { useCallback, useEffect, useState } from "react";
import { createWaste, deleteWaste, getIngredients, getReasons, getRestaurants, getWaste } from "../api";
import IngredientPicker from "../components/IngredientPicker";
import RecentEntries from "../components/RecentEntries";
import { MAX_ENTRY_KG, formatKg, formatMoney, reasonLabel, toKg, todayISO } from "../utils";

const RESTAURANT_KEY = "waste-tracker:restaurantId";
const QUICK_AMOUNTS = { kg: [0.5, 1, 2, 5], g: [100, 250, 500], pcs: [1, 5, 10] };

function savedRestaurantId() {
  try {
    return Number(localStorage.getItem(RESTAURANT_KEY)) || null;
  } catch {
    return null;
  }
}

export default function EntryPage() {
  const [restaurants, setRestaurants] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [reasons, setReasons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [restaurantId, setRestaurantId] = useState(null);
  const [ingredient, setIngredient] = useState(null);
  const [amount, setAmount] = useState("");
  const [unit, setUnit] = useState("kg");
  const [reason, setReason] = useState("");
  const [note, setNote] = useState("");
  const [date, setDate] = useState(todayISO());

  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [saved, setSaved] = useState(null); // { id, text } of the last saved entry
  const [entries, setEntries] = useState([]);

  // Load the lists the form needs
  useEffect(() => {
    Promise.all([getRestaurants(), getIngredients(), getReasons()])
      .then(([restaurantList, ingredientList, reasonList]) => {
        setRestaurants(restaurantList);
        setIngredients(ingredientList);
        setReasons(reasonList);
        const remembered = savedRestaurantId();
        const valid = restaurantList.some((r) => r.id === remembered);
        setRestaurantId(valid ? remembered : restaurantList[0]?.id ?? null);
      })
      .catch((err) => setLoadError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const refreshEntries = useCallback(async () => {
    if (!restaurantId) return;
    try {
      setEntries(await getWaste({ restaurant_id: restaurantId, date_from: date, date_to: date, limit: 100 }));
    } catch {
      // The list is a convenience; the form still works without it
    }
  }, [restaurantId, date]);

  useEffect(() => {
    refreshEntries();
  }, [refreshEntries]);

  const quantityKg = ingredient ? toKg(amount, unit, ingredient.grams_per_piece) : null;
  const cost = quantityKg !== null ? quantityKg * ingredient.price_per_kg : null;
  const tooLarge = quantityKg !== null && quantityKg > MAX_ENTRY_KG;
  const canSubmit = Boolean(restaurantId && ingredient && quantityKg !== null && !tooLarge && reason && !submitting);

  const handleRestaurantChange = (id) => {
    setRestaurantId(id);
    setSaved(null);
    try {
      localStorage.setItem(RESTAURANT_KEY, String(id));
    } catch {
      // ignore: remembering the restaurant is optional
    }
  };

  const handleIngredientSelect = (selected) => {
    setIngredient(selected);
    // Pieces only work for ingredients with a known piece weight
    if (selected && unit === "pcs" && !selected.grams_per_piece) setUnit("kg");
  };

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;

    setSubmitting(true);
    setFormError("");
    try {
      const entry = await createWaste({
        restaurant_id: restaurantId,
        ingredient_id: ingredient.id,
        amount: Number(amount),
        unit,
        reason,
        note: note.trim() || null,
        waste_date: date,
      });
      setSaved({
        id: entry.id,
        text: `${entry.ingredient_name}: ${formatKg(entry.quantity_kg)} = ${formatMoney(entry.cost)}`,
      });
      // Ready for the next entry: keep restaurant, date and unit
      setIngredient(null);
      setAmount("");
      setReason("");
      setNote("");
      await refreshEntries();
    } catch (err) {
      setSaved(null);
      setFormError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUndo() {
    if (!saved) return;
    try {
      await deleteWaste(saved.id);
      setSaved(null);
      await refreshEntries();
    } catch (err) {
      setFormError(err.message);
    }
  }

  async function handleDelete(entry) {
    if (!window.confirm(`Delete ${entry.ingredient_name} (${formatMoney(entry.cost)})?`)) return;
    try {
      await deleteWaste(entry.id);
      if (saved?.id === entry.id) setSaved(null);
      await refreshEntries();
    } catch (err) {
      setFormError(err.message);
    }
  }

  if (loading) return <p className="muted">Loading...</p>;
  if (loadError) return <p className="banner error">{loadError}</p>;

  return (
    <div className="entry-layout">
      <form className="card" onSubmit={handleSubmit}>
        <h1>Enter waste</h1>

        <label className="field">
          <span className="label">Restaurant</span>
          <select className="input" value={restaurantId ?? ""} onChange={(e) => handleRestaurantChange(Number(e.target.value))}>
            {restaurants.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </label>

        <div className="field">
          <span className="label">Ingredient</span>
          <IngredientPicker ingredients={ingredients} selected={ingredient} onSelect={handleIngredientSelect} />
        </div>

        <div className="field">
          <span className="label">Amount</span>
          <div className="amount-row">
            <input
              className="input amount-input"
              type="number"
              inputMode="decimal"
              min="0"
              step="any"
              placeholder="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            <div className="segmented">
              {["kg", "g", "pcs"].map((u) => (
                <button
                  type="button"
                  key={u}
                  className={unit === u ? "seg active" : "seg"}
                  disabled={u === "pcs" && !ingredient?.grams_per_piece}
                  onClick={() => setUnit(u)}
                >
                  {u}
                </button>
              ))}
            </div>
          </div>
          <div className="quick">
            {QUICK_AMOUNTS[unit].map((value) => (
              <button type="button" className="chip" key={value} onClick={() => setAmount(String(value))}>
                {value} {unit}
              </button>
            ))}
          </div>
        </div>

        {ingredient && quantityKg !== null && (
          <div className={tooLarge ? "preview warn" : "preview"}>
            {tooLarge ? (
              <>That's more than {MAX_ENTRY_KG} kg. Please check the amount.</>
            ) : (
              <>
                {formatKg(quantityKg)} × {formatMoney(ingredient.price_per_kg)}/kg = <strong>{formatMoney(cost)}</strong>
              </>
            )}
          </div>
        )}

        <div className="field">
          <span className="label">Reason</span>
          <div className="pills">
            {reasons.map((r) => (
              <button type="button" key={r} className={reason === r ? "pill active" : "pill"} onClick={() => setReason(r)}>
                {reasonLabel(r)}
              </button>
            ))}
          </div>
        </div>

        <div className="row">
          <label className="field">
            <span className="label">Date</span>
            <input
              className="input"
              type="date"
              max={todayISO()}
              value={date}
              onChange={(e) => setDate(e.target.value || todayISO())}
            />
          </label>
          <label className="field grow">
            <span className="label">Note (optional)</span>
            <input className="input" maxLength={200} value={note} onChange={(e) => setNote(e.target.value)} />
          </label>
        </div>

        {formError && <p className="banner error">{formError}</p>}
        {saved && (
          <p className="banner success">
            <span>Saved: {saved.text}</span>
            <button type="button" className="btn-ghost" onClick={handleUndo}>
              Undo
            </button>
          </p>
        )}

        <button type="submit" className="btn-primary" disabled={!canSubmit}>
          {submitting ? "Saving..." : "Save waste"}
        </button>
      </form>

      <RecentEntries entries={entries} onDelete={handleDelete} dateLabel={date === todayISO() ? "today" : date} />
    </div>
  );
}