import { useEffect, useState } from "react";
import { api } from "../api";

const money = (n) => "Rs. " + Number(n || 0).toLocaleString("en-IN");
const currentMonth = () => {
  const d = new Date();
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
};

export default function Budgets() {
  const [month, setMonth] = useState(currentMonth());
  const [categories, setCategories] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [form, setForm] = useState({ category_id: "", limit_amount: "" });
  const [version, setVersion] = useState(0);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const reload = () => setVersion((v) => v + 1);

  useEffect(() => {
    api.categories().then(setCategories).catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    api.budgets(month).then(setBudgets).catch((e) => setError(e.message));
  }, [month, version]);
  useEffect(() => {
    api.alertsAll().then(setAlerts).catch((e) => setError(e.message));
  }, [version]);

  const catId = form.category_id || (categories[0] ? categories[0].id : "");

  async function save(e) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      await api.setBudget({ category_id: Number(catId), month_year: month,
        limit_amount: Number(form.limit_amount) });
      setForm({ ...form, limit_amount: "" });
      setMsg("Budget saved");
      reload();
    } catch (err) { setError(err.message); }
  }

  async function read(id) {
    try { await api.markRead(id); reload(); }
    catch (err) { setError(err.message); }
  }

  return (
    <>
      {error && <div className="error">{error}</div>}
      {msg && <div className="success">{msg}</div>}

      <div className="controls">
        <label>Month: <input type="month" value={month}
          onChange={(e) => e.target.value && setMonth(e.target.value)} /></label>
      </div>

      <form className="card" onSubmit={save}>
        <h3>Set a budget for {month}</h3>
        <div className="form-row">
          <select value={catId} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <input type="number" step="0.01" min="1" placeholder="Monthly limit (Rs.)"
                 value={form.limit_amount} onChange={(e) => setForm({ ...form, limit_amount: e.target.value })} required />
          <button className="primary">Save budget</button>
        </div>
        <p className="muted">Setting a budget again for the same category and month changes its limit.</p>
      </form>

      <div className="card">
        <h3>Budget progress</h3>
        {budgets.length === 0 ? <p className="muted">No budgets for this month.</p> :
          budgets.map((b) => (
            <div key={b.id} className="budget">
              <div className="row"><span>{b.category}</span>
                <span className="muted">{money(b.spent)} / {money(b.limit_amount)} ({b.percent}%)</span></div>
              <div className="bar"><div className={"fill " + b.status}
                   style={{ width: Math.min(b.percent, 100) + "%" }} /></div>
            </div>
          ))}
      </div>

      <div className="card">
        <h3>Alerts</h3>
        {alerts.length === 0 ? <p className="muted">No alerts yet.</p> :
          alerts.map((a) => (
            <div key={a.id} className={"banner " + (a.level >= 100 ? "danger" : "warn")}>
              <div className="row">
                <span>{a.category} ({a.month_year}): {a.level}% of budget reached</span>
                {a.is_read ? <span className="muted">read</span> :
                  <button onClick={() => read(a.id)}>Mark read</button>}
              </div>
            </div>
          ))}
      </div>
    </>
  );
}