import { useMemo, useState } from "react";
import {
  getIngredientStats,
  getReasonStats,
  getRestaurantStats,
  getRestaurants,
  getSummary,
  getTrend,
} from "../api";
import IngredientChart from "../components/IngredientChart";
import Panel from "../components/Panel";
import ReasonChart from "../components/ReasonChart";
import RestaurantChart from "../components/RestaurantChart";
import StatCard from "../components/StatCard";
import TrendChart from "../components/TrendChart";
import { useAsync } from "../hooks/useAsync";
import { CHART_COLORS, daysAgoISO, formatKg, formatMoney, todayISO } from "../utils";

function Toggle({ options, value, onChange }) {
  return (
    <div className="segmented">
      {options.map(([key, label]) => (
        <button type="button" key={key} className={value === key ? "seg active" : "seg"} onClick={() => onChange(key)}>
          {label}
        </button>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [days, setDays] = useState(30);
  const [restaurantId, setRestaurantId] = useState("");
  const [comparison, setComparison] = useState("total");
  const [ingredientSort, setIngredientSort] = useState("cost");

  const range = { date_from: daysAgoISO(days - 1), date_to: todayISO() };
  const filter = { ...range, restaurant_id: restaurantId };
  const interval = days <= 31 ? "day" : "week";

  const restaurants = useAsync(getRestaurants, []);
  const summary = useAsync(() => getSummary(filter), [days, restaurantId]);
  const comparisonData = useAsync(() => getRestaurantStats(range), [days]);
  const ingredients = useAsync(
    () => getIngredientStats({ ...filter, sort_by: ingredientSort, limit: 10 }),
    [days, restaurantId, ingredientSort]
  );
  const reasons = useAsync(() => getReasonStats(filter), [days, restaurantId]);
  const trend = useAsync(() => getTrend({ ...filter, interval }), [days, restaurantId]);

  // Each restaurant keeps the same color in every chart
  const colorOf = useMemo(() => {
    const ids = (restaurants.data ?? []).map((r) => r.id).sort((a, b) => a - b);
    return (id) => CHART_COLORS[Math.max(0, ids.indexOf(id)) % CHART_COLORS.length];
  }, [restaurants.data]);

  if (restaurants.error) return <p className="banner error">{restaurants.error}</p>;
  if (!restaurants.data) return <p className="muted">Loading...</p>;

  const s = summary.data;
  const change = s?.change_pct;
  const changeText = change === null || change === undefined ? "-" : `${change > 0 ? "+" : ""}${change}%`;
  // Less waste than before is good
  const changeTone = change === null || change === undefined ? undefined : change > 0 ? "bad" : "good";
  const scope = restaurantId
    ? restaurants.data.find((r) => r.id === Number(restaurantId))?.name
    : "All restaurants";

  return (
    <div className="dashboard">
      <div className="dash-header">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">
            {scope}
            {s ? ` · ${s.date_from} to ${s.date_to}` : ""}
          </p>
        </div>
        <div className="filters">
          <Toggle
            options={[
              [7, "7 days"],
              [30, "30 days"],
              [90, "90 days"],
            ]}
            value={days}
            onChange={setDays}
          />
          <select className="input filter-select" value={restaurantId} onChange={(e) => setRestaurantId(e.target.value)}>
            <option value="">All restaurants</option>
            {restaurants.data.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {summary.error && <p className="banner error">{summary.error}</p>}
      <div className="stat-grid">
        <StatCard label="Waste cost" value={s ? formatMoney(s.total_cost) : "..."} />
        <StatCard label="Weight" value={s ? formatKg(s.total_kg) : "..."} />
        <StatCard
          label="Vs previous period"
          value={changeText}
          tone={changeTone}
          hint={s ? `previous: ${formatMoney(s.previous_cost)}` : undefined}
        />
        <StatCard label="Entries" value={s ? s.entries : "..."} />
      </div>

      <Panel
        title="Restaurant comparison"
        subtitle="Always shows all restaurants. Per customer is the fairest way to compare a busy and a quiet one."
        state={comparisonData}
        controls={
          <Toggle
            options={[
              ["total", "Total"],
              ["perCover", "Per customer"],
            ]}
            value={comparison}
            onChange={setComparison}
          />
        }
      >
        {(rows) => <RestaurantChart rows={rows} metric={comparison} colorOf={colorOf} />}
      </Panel>

      <div className="two-col">
        <Panel
          title="Most wasted ingredients"
          state={ingredients}
          controls={
            <Toggle
              options={[
                ["cost", "By cost"],
                ["kg", "By weight"],
              ]}
              value={ingredientSort}
              onChange={setIngredientSort}
            />
          }
        >
          {(rows) => <IngredientChart rows={rows} sortBy={ingredientSort} />}
        </Panel>

        <Panel title="Why food gets wasted" state={reasons}>
          {(rows) => <ReasonChart rows={rows} />}
        </Panel>
      </div>

      <Panel
        title="Trend"
        subtitle={
          interval === "week"
            ? "Weekly totals. The first and last week may be partial."
            : "Daily totals."
        }
        state={trend}
      >
        {(points) => <TrendChart points={points} interval={interval} colorOf={colorOf} />}
      </Panel>
    </div>
  );
}