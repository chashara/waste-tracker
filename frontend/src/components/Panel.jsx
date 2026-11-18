export default function Panel({ title, subtitle, controls, state, children }) {
  return (
    <section className="card">
      <div className="card-header">
        <div>
          <h2>{title}</h2>
          {subtitle && <p className="muted">{subtitle}</p>}
        </div>
        {controls}
      </div>

      {state.error ? (
        <p className="banner error">{state.error}</p>
      ) : !state.data ? (
        <p className="muted">Loading...</p>
      ) : (
        <div className={state.loading ? "panel-body dim" : "panel-body"}>{children(state.data)}</div>
      )}
    </section>
  );
}