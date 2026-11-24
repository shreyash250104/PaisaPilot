import { useEffect, useState } from "react";
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend } from "chart.js";
import { Bar } from "react-chartjs-2";
import { api } from "../api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const money = (n) => "Rs. " + Number(n || 0).toLocaleString("en-IN");
const currentMonth = () => {
  const d = new Date();
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
};

export default function Reports() {
  const [month, setMonth] = useState(currentMonth());
  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [top, setTop] = useState([]);
  const [fc, setFc] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.summary(month), api.trend(), api.topExpenses(month), api.forecast()])
      .then(([s, t, tp, f]) => {
        setError("");
        setSummary(s); setTrend(t); setTop(tp.top); setFc(f);
      })
      .catch((e) => setError(e.message));
  }, [month]);

  function exportCsv() {
    const lines = ["Category,Total,Percent"];
    summary.categories.forEach((c) => lines.push(`${c.category},${c.total},${c.percent}`));
    lines.push("", "Month,Income,Expense,Savings,Change vs previous month %");
    trend.forEach((t) => lines.push(
      `${t.month},${t.income},${t.expense},${t.savings},${t.change_vs_previous_month_percent ?? ""}`));
    const url = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `paisapilot-report-${month}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const cats = summary ? summary.categories : [];

  return (
    <>
      <div className="controls form-row no-print">
        <label>Month: <input type="month" value={month}
          onChange={(e) => e.target.value && setMonth(e.target.value)} /></label>
        <button onClick={exportCsv} disabled={!summary}>Export CSV</button>
        <button onClick={() => window.print()}>Print / Save as PDF</button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="cards">
        <div className="card"><span className="muted">Income</span><b>{money(summary?.income)}</b></div>
        <div className="card"><span className="muted">Expenses</span><b>{money(summary?.expense)}</b></div>
        <div className="card"><span className="muted">Savings</span><b>{money(summary?.savings)}</b></div>
      </div>

      <div className="grid">
        <div className="card">
          <h3>Spending by category</h3>
          {cats.length === 0 ? <p className="muted">No expenses this month.</p> : cats.map((c) => (
            <div key={c.category} className="budget">
              <div className="row"><span>{c.category}</span>
                <span className="muted">{money(c.total)} ({c.percent}%)</span></div>
              <div className="bar"><div className="fill ok" style={{ width: c.percent + "%" }} /></div>
            </div>
          ))}
        </div>
        <div className="card">
          <h3>Top 5 expenses</h3>
          {top.length === 0 ? <p className="muted">Nothing to show.</p> : (
            <table>
              <tbody>
                {top.map((t) => (
                  <tr key={t.id}><td>{t.date}</td><td>{t.description}</td>
                    <td>{t.category}</td><td className="expense">{money(t.amount)}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="card">
        <h3>Month-over-month comparison</h3>
        {trend.length === 0 ? <p className="muted">No data yet.</p> : (
          <>
            <Bar data={{
              labels: trend.map((t) => t.month),
              datasets: [
                { label: "Income", data: trend.map((t) => t.income), backgroundColor: "#6AA84F" },
                { label: "Expenses", data: trend.map((t) => t.expense), backgroundColor: "#C0504D" },
              ],
            }} options={{ plugins: { legend: { position: "bottom" } } }} />
            <div className="scroll">
              <table>
                <thead><tr><th>Month</th><th>Income</th><th>Expenses</th><th>Savings</th><th>Expense change</th></tr></thead>
                <tbody>
                  {trend.map((t) => {
                    const ch = t.change_vs_previous_month_percent;
                    return (
                      <tr key={t.month}>
                        <td>{t.month}</td><td>{money(t.income)}</td><td>{money(t.expense)}</td>
                        <td>{money(t.savings)}</td>
                        <td className={ch == null ? "" : ch > 0 ? "neg" : "pos"}>
                          {ch == null ? "-" : (ch > 0 ? "+" : "") + ch + "%"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      <div className="grid">
        <div className="card">
          <h3>Forecast</h3>
          {!fc || fc.forecast.based_on_months.length === 0
            ? <p className="muted">Not enough earlier months of data yet.</p>
            : <>
                <p>Expected spending in <b>{fc.forecast.for_month}</b>:</p>
                <p><b style={{ fontSize: "1.4rem" }}>{money(fc.forecast.predicted_expense)}</b></p>
                <p className="muted">Average of: {fc.forecast.based_on_months.join(", ")}</p>
              </>}
        </div>
        <div className="card">
          <h3>Unusual spending this month</h3>
          {!fc || fc.unusual_spending.length === 0
            ? <p className="muted">Nothing unusual found.</p>
            : fc.unusual_spending.map((u) => (
                <div key={u.category} className="banner warn">
                  {u.category}: {money(u.this_month)} is {u.times_usual}x the usual {money(u.usual_average)}
                </div>
              ))}
        </div>
      </div>
    </>
  );
}