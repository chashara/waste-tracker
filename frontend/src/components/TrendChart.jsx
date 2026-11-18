import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatMoney, periodLabel, periodTick } from "../utils";

export default function TrendChart({ points, interval, colorOf }) {
  if (points.length === 0) return <p className="muted">No waste entries in this period.</p>;

  // Turn the flat list into one row per period, with one column per restaurant
  const byPeriod = new Map();
  const series = new Map();
  for (const p of points) {
    series.set(p.restaurant_id, p.restaurant_name);
    const row = byPeriod.get(p.period) ?? { period: p.period };
    row[p.restaurant_name] = p.cost;
    byPeriod.set(p.period, row);
  }
  const rows = [...byPeriod.values()].sort((a, b) => a.period.localeCompare(b.period));
  const lines = [...series.entries()].sort((a, b) => a[0] - b[0]);

  return (
    <div className="chart-box tall">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="period" tickFormatter={(d) => periodTick(d, interval)} minTickGap={24} />
          <YAxis tickFormatter={(v) => `€${v}`} width={64} />
          <Tooltip labelFormatter={(d) => periodLabel(d, interval)} formatter={(v, name) => [formatMoney(v), name]} />
          <Legend />
          {lines.map(([id, name]) => (
            <Line key={id} type="monotone" dataKey={name} stroke={colorOf(id)} strokeWidth={2} dot={false} connectNulls />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}