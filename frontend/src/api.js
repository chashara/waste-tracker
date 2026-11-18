const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

function errorMessage(data) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    // Validation errors: [{ loc: [...], msg: "..." }]
    return detail.map((d) => d.msg).join(". ");
  }
  return "Something went wrong. Please try again.";
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("Couldn't reach the server. It may be waking up, so please try again in a moment.");
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(errorMessage(data));
  return data;
}

// Turns { a: 1, b: "", c: undefined } into "a=1", skipping empty values
function toQuery(params = {}) {
  return new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== "")
  ).toString();
}

export const getRestaurants = () => request("/api/restaurants");
export const getIngredients = () => request("/api/ingredients");
export const getReasons = () => request("/api/reasons");

export const createWaste = (payload) =>
  request("/api/waste", { method: "POST", body: JSON.stringify(payload) });

export const deleteWaste = (id) => request(`/api/waste/${id}`, { method: "DELETE" });

export const getWaste = (params) => request(`/api/waste?${toQuery(params)}`);

// Dashboard
export const getSummary = (params) => request(`/api/stats/summary?${toQuery(params)}`);
export const getRestaurantStats = (params) => request(`/api/stats/restaurants?${toQuery(params)}`);
export const getIngredientStats = (params) => request(`/api/stats/ingredients?${toQuery(params)}`);
export const getReasonStats = (params) => request(`/api/stats/reasons?${toQuery(params)}`);
export const getTrend = (params) => request(`/api/stats/trend?${toQuery(params)}`);