export default function StatCard({ label, value, hint, tone }) {
  return (
    <div className="stat-card">
      <span className="label">{label}</span>
      <strong className={tone ? `stat-value ${tone}` : "stat-value"}>{value}</strong>
      {hint && <span className="muted">{hint}</span>}
    </div>
  );
}