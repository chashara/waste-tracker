import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatKg, formatMoney, formatPerCover } from "../utils";

export default function RestaurantChart({ rows, metric, colorOf }) {
  const perCover = metric === "perCover";
  const missingCovers = perCover && rows.every((r) => r.cost_per_cover === null);

  const data = rows
    .map((r) => ({
      id: r.restaurant_id,
      name: r.restaurant_name,
      value: perCover ? r.cost_per_cover : r.total_cost,
    }))
    .sort((a, b) => (b.value ?? -1) - (a.value ?? -1));

  return (
    <>
      {missingCovers ? (
        <p className="muted">No customer counts recorded for this period, so there is nothing to compare per customer.</p>
      ) : (
        <div className="chart-box">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(v) => (perCover ? `€${v.toFixed(2)}` : `€${v}`)} width={64} />
              <Tooltip
                formatter={(v) => [
                  perCover ? formatPerCover(v) : formatMoney(v),
                  perCover ? "Cost per customer" : "Waste cost",
                ]}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {data.map((d) => (
                  <Cell key={d.id} fill={colorOf(d.id)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Restaurant</th>
              <th>Waste cost</th>
              <th>Weight</th>
              <th>Customers</th>
              <th>Per customer</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.restaurant_id}>
                <td>{r.restaurant_name}</td>
                <td>{formatMoney(r.total_cost)}</td>
                <td>{formatKg(r.total_kg)}</td>
                <td>{r.covers || "-"}</td>
                <td>{r.cost_per_cover === null ? "-" : formatPerCover(r.cost_per_cover)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}