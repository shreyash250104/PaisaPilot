import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale,
  LinearScale, PointElement, LineElement,
} from "chart.js";
import { Doughnut, Line } from "react-chartjs-2";
import { api, logout } from "../api";

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, PointElement, LineElement);

const COLORS = ["#4A7FB5", "#E0A030", "#6AA84F", "#C0504D", "#9E9E9E", "#8E6BB5", "#2BA3A3"];
const money = (n) => "Rs. " + Number(n || 0).toLocaleString("en-IN");
const currentMonth = () => {
  const d = new Date();
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
};

export default function Dashboard() {
  const nav = useNavigate();
  const [month, setMonth] = useState(currentMonth());
  const [user, setUser] = useState(null);
  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.me().then(setUser).catch((e) => setError(e.message));
  }, []);

    useEffect(() => {
    Promise.all([api.summary(month), api.trend(), api.budgets(month), api.alerts()])
      .then(([s, t, b, a]) => {
        setError("");
        setSummary(s);
        setTrend(t);
        setBudgets(b);
        setAlerts(a);
      })
      .catch((e) => setError(e.message));
  }, [month]);
  const doLogout = () => { logout(); nav("/login"); };
  const cats = summary ? summary.categories : [];

  return (
    <div className="page">
      <header className="top">
        <h2>PaisaPilot</h2>
        <div className="right">
          <span className="muted">{user ? user.name : ""}</span>
          <button onClick={doLogout}>Logout</button>
        </div>
      </header>

      <div className="controls">
        <label>Month: <input type="month" value={month} onChange={(e) => e.target.value && setMonth(e.target.value)} /></label>
      </div>

      {error && <div className="error">{error}</div>}

      {alerts.map((a) => (
        <div key={a.id} className={"banner " + (a.level >= 100 ? "danger" : "warn")}>
          {a.category} budget for {a.month_year}: {a.level}% reached
        </div>
      ))}

      <div className="cards">
        <div className="card"><span className="muted">Income</span><b>{money(summary?.income)}</b></div>
        <div className="card"><span className="muted">Expenses</span><b>{money(summary?.expense)}</b></div>
        <div className="card"><span className="muted">Savings</span><b>{money(summary?.savings)}</b></div>
      </div>

      <div className="grid">
        <div className="card">
          <h3>Spending by category</h3>
          {cats.length === 0 ? <p className="muted">No expenses in this month.</p> : (
            <Doughnut data={{
              labels: cats.map((c) => c.category),
              datasets: [{ data: cats.map((c) => c.total), backgroundColor: COLORS }],
            }} options={{ plugins: { legend: { position: "bottom" } } }} />
          )}
        </div>
        <div className="card">
          <h3>Monthly trend</h3>
          {trend.length === 0 ? <p className="muted">No data yet.</p> : (
            <Line data={{
              labels: trend.map((t) => t.month),
              datasets: [
                { label: "Expenses", data: trend.map((t) => t.expense), borderColor: "#C0504D", backgroundColor: "#C0504D" },
                { label: "Income", data: trend.map((t) => t.income), borderColor: "#6AA84F", backgroundColor: "#6AA84F" },
              ],
            }} options={{ plugins: { legend: { position: "bottom" } } }} />
          )}
        </div>
      </div>

      <div className="card">
        <h3>Budgets for {month}</h3>
        {budgets.length === 0 ? <p className="muted">No budgets set for this month.</p> :
          budgets.map((b) => (
            <div key={b.id} className="budget">
              <div className="row"><span>{b.category}</span>
                <span className="muted">{money(b.spent)} / {money(b.limit_amount)} ({b.percent}%)</span></div>
              <div className="bar"><div className={"fill " + b.status}
                   style={{ width: Math.min(b.percent, 100) + "%" }} /></div>
            </div>
          ))}
      </div>
    </div>
  );
}