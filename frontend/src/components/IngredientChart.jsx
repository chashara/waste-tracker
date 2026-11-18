import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatKg, formatMoney } from "../utils";

export default function IngredientChart({ rows, sortBy }) {
  if (rows.length === 0) return <p className="muted">No waste entries in this period.</p>;

  const byCost = sortBy === "cost";
  const data = rows.map((r) => ({
    name: r.ingredient_name,
    value: byCost ? r.total_cost : r.total_kg,
  }));

  return (
    <div className="chart-box tall">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" tickFormatter={(v) => (byCost ? `€${v}` : `${v} kg`)} />
          <YAxis type="category" dataKey="name" width={120} />
          <Tooltip formatter={(v) => [byCost ? formatMoney(v) : formatKg(v), byCost ? "Waste cost" : "Weight"]} />
          <Bar dataKey="value" fill="#448699" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}