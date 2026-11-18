import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatKg, formatMoney } from "../utils";

export default function RestaurantChart({ rows, colorOf }) {
  const data = rows.map((r) => ({ id: r.restaurant_id, name: r.restaurant_name, value: r.total_cost }));

  return (
    <>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" />
            <YAxis tickFormatter={(v) => `€${v}`} width={64} />
            <Tooltip formatter={(v) => [formatMoney(v), "Waste cost"]} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((d) => (
                <Cell key={d.id} fill={colorOf(d.id)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Restaurant</th>
              <th>Waste cost</th>
              <th>Weight</th>
              <th>Entries</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.restaurant_id}>
                <td>{r.restaurant_name}</td>
                <td>{formatMoney(r.total_cost)}</td>
                <td>{formatKg(r.total_kg)}</td>
                <td>{r.entries}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}