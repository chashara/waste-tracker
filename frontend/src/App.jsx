import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import EntryPage from "./pages/EntryPage";

const todayLabel = new Date().toLocaleDateString("en-GB", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
});

export default function App() {
  return (
    <BrowserRouter>
      <div className="site-strip">
        <div className="wrap">
          <span>Food waste tracking</span>
          <span>{todayLabel}</span>
        </div>
      </div>

      <header className="site-header">
        <div className="wrap">
          <span className="brand">Waste Tracker</span>
        </div>
      </header>

      <nav className="site-nav">
        <div className="wrap">
          <NavLink to="/" end>
            Enter waste
          </NavLink>
          <NavLink to="/dashboard">Dashboard</NavLink>
        </div>
      </nav>

      <main className="container">
        <Routes>
          <Route path="/" element={<EntryPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}