import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { REASON_COLORS, formatMoney, reasonLabel } from "../utils";

export default function ReasonChart({ rows }) {
  if (rows.length === 0) return <p className="muted">No waste entries in this period.</p>;

  const data = rows.map((r) => ({ key: r.reason, name: reasonLabel(r.reason), value: r.total_cost, share: r.share_pct }));

  return (
    <>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2}>
              {data.map((d) => (
                <Cell key={d.key} fill={REASON_COLORS[d.key] || "#9aa59d"} />
              ))}
            </Pie>
            <Tooltip formatter={(v, name) => [formatMoney(v), name]} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <ul className="legend-list">
        {data.map((d) => (
          <li key={d.key}>
            <span className="dot" style={{ background: REASON_COLORS[d.key] || "#9aa59d" }} />
            <span className="grow">{d.name}</span>
            <span className="muted">{d.share}%</span>
            <strong>{formatMoney(d.value)}</strong>
          </li>
        ))}
      </ul>
    </>
  );
}