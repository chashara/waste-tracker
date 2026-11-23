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
import {
  CHART_COLORS,
  daysAgoISO,
  formatKg,
  formatMoney,
  monthRange,
  previousMonthRange,
  recentMonths,
  todayISO,
} from "../utils";

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

const MONTHS = recentMonths(24);

export default function DashboardPage() {
  const [mode, setMode] = useState(30); // 7, 30, 90 or "month"
  const [month, setMonth] = useState(MONTHS[0].value);
  const [restaurantId, setRestaurantId] = useState("");
  const [ingredientSort, setIngredientSort] = useState("cost");

  const isMonth = mode === "month";
  const range = isMonth ? monthRange(month) : { date_from: daysAgoISO(mode - 1), date_to: todayISO() };
  const compare = isMonth ? previousMonthRange(month, range.date_to) : {};
  const filter = { ...range, restaurant_id: restaurantId };
  const interval = mode === 90 ? "week" : "day";
  const rangeDeps = [range.date_from, range.date_to];

  const restaurants = useAsync(getRestaurants, []);
  const summary = useAsync(() => getSummary({ ...filter, ...compare }), [...rangeDeps, restaurantId]);
  const comparisonData = useAsync(() => getRestaurantStats(range), rangeDeps);
  const ingredients = useAsync(
    () => getIngredientStats({ ...filter, sort_by: ingredientSort, limit: 10 }),
    [...rangeDeps, restaurantId, ingredientSort]
  );
  const reasons = useAsync(() => getReasonStats(filter), [...rangeDeps, restaurantId]);
  const trend = useAsync(() => getTrend({ ...filter, interval }), [...rangeDeps, restaurantId]);

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
              ["month", "Month"],
            ]}
            value={mode}
            onChange={setMode}
          />
          {isMonth && (
            <select className="input filter-select" value={month} onChange={(e) => setMonth(e.target.value)}>
              {MONTHS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          )}
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
          label={isMonth ? "Vs previous month" : "Vs previous period"}
          value={changeText}
          tone={changeTone}
          hint={s ? `previous: ${formatMoney(s.previous_cost)}` : undefined}
        />
        <StatCard label="Entries" value={s ? s.entries : "..."} />
      </div>

      <Panel
        title="Restaurant comparison"
        subtitle="Always shows all restaurants, whichever one is selected above."
        state={comparisonData}
      >
        {(rows) => <RestaurantChart rows={rows} colorOf={colorOf} />}
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