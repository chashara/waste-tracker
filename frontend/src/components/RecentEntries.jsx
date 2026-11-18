import { formatKg, formatMoney, reasonLabel } from "../utils";

export default function RecentEntries({ entries, onDelete, dateLabel }) {
  const total = entries.reduce((sum, e) => sum + e.cost, 0);

  return (
    <section className="card">
      <div className="card-header">
        <h2>Entries for {dateLabel}</h2>
        <span className="total">{formatMoney(total)}</span>
      </div>

      {entries.length === 0 ? (
        <p className="muted">Nothing entered yet.</p>
      ) : (
        <ul className="entry-list">
          {entries.map((e) => (
            <li key={e.id}>
              <div>
                <strong>{e.ingredient_name}</strong>
                <span className="muted">
                  {" "}
                  {formatKg(e.quantity_kg)} · {reasonLabel(e.reason)}
                </span>
              </div>
              <div className="entry-right">
                <span>{formatMoney(e.cost)}</span>
                <button type="button" className="icon-btn" onClick={() => onDelete(e)} aria-label="Delete entry">
                  ✕
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}