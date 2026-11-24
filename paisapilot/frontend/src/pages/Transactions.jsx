import { useEffect, useState } from "react";
import { api } from "../api";

const money = (n) => "Rs. " + Number(n || 0).toLocaleString("en-IN");
const today = () => {
  const d = new Date();
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") +
    "-" + String(d.getDate()).padStart(2, "0");
};

export default function Transactions() {
  const [accounts, setAccounts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [txns, setTxns] = useState([]);
  const [filters, setFilters] = useState({ account_id: "", category_id: "", type: "" });
  const [version, setVersion] = useState(0);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [form, setForm] = useState({ account_id: "", category_id: "", type: "expense",
    amount: "", txn_date: today(), description: "" });
  const [acc, setAcc] = useState({ name: "", type: "cash", balance: "0" });
  const [csv, setCsv] = useState({ account_id: "", file: null });
  const [preview, setPreview] = useState(null);

  const reload = () => setVersion((v) => v + 1);

  useEffect(() => {
    api.categories().then(setCategories).catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    api.accounts().then(setAccounts).catch((e) => setError(e.message));
  }, [version]);
  useEffect(() => {
    api.transactions(filters).then(setTxns).catch((e) => setError(e.message));
  }, [filters, version]);

  const first = accounts[0] ? accounts[0].id : "";
  const formAcc = form.account_id || first;
  const csvAcc = csv.account_id || first;
  const catName = Object.fromEntries(categories.map((c) => [c.id, c.name]));
  const accName = Object.fromEntries(accounts.map((a) => [a.id, a.name]));
  const setF = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function addAccount(e) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      await api.createAccount({ name: acc.name, type: acc.type, balance: Number(acc.balance || 0) });
      setAcc({ name: "", type: "cash", balance: "0" });
      setMsg("Account created");
      reload();
    } catch (err) { setError(err.message); }
  }

  async function addTxn(e) {
    e.preventDefault();
    setError(""); setMsg("");
    if (!formAcc) { setError("Create an account first"); return; }
    try {
      await api.addTxn({
        account_id: Number(formAcc),
        category_id: form.category_id ? Number(form.category_id) : null,
        amount: Number(form.amount),
        type: form.type,
        description: form.description || null,
        txn_date: form.txn_date,
      });
      setForm({ ...form, amount: "", description: "" });
      setMsg("Transaction added");
      reload();
    } catch (err) { setError(err.message); }
  }

  async function del(id) {
    if (!window.confirm("Delete this transaction?")) return;
    setError(""); setMsg("");
    try { await api.deleteTxn(id); setMsg("Transaction deleted"); reload(); }
    catch (err) { setError(err.message); }
  }

  async function runImport(save) {
    setError(""); setMsg("");
    if (!csvAcc) { setError("Create an account first"); return; }
    if (!csv.file) { setError("Choose a CSV file first"); return; }
    try {
      const r = await api.importCsv(csvAcc, save, csv.file);
      if (save) {
        setMsg(`Imported ${r.new} rows, skipped ${r.duplicates} duplicates`);
        setPreview(null);
        reload();
      } else {
        setPreview(r);
      }
    } catch (err) { setError(err.message); }
  }

  return (
    <>
      {error && <div className="error">{error}</div>}
      {msg && <div className="success">{msg}</div>}

      <div className="card">
        <h3>Accounts</h3>
        <div className="chips">
          {accounts.length === 0 && <span className="muted">No accounts yet. Create one below.</span>}
          {accounts.map((a) => (
            <span key={a.id} className="chip">{a.name} ({a.type}): <b>{money(a.balance)}</b></span>
          ))}
        </div>
        <form className="form-row" onSubmit={addAccount}>
          <input placeholder="Account name" value={acc.name}
                 onChange={(e) => setAcc({ ...acc, name: e.target.value })} required />
          <select value={acc.type} onChange={(e) => setAcc({ ...acc, type: e.target.value })}>
            <option value="cash">Cash</option><option value="bank">Bank</option><option value="upi">UPI</option>
          </select>
          <input type="number" step="0.01" placeholder="Opening balance" value={acc.balance}
                 onChange={(e) => setAcc({ ...acc, balance: e.target.value })} />
          <button className="primary">Add account</button>
        </form>
      </div>

      <div className="grid">
        <form className="card" onSubmit={addTxn}>
          <h3>Add transaction</h3>
          <div className="form-grid">
            <select value={formAcc} onChange={setF("account_id")}>
              {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <select value={form.category_id} onChange={setF("category_id")}>
              <option value="">No category</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <select value={form.type} onChange={setF("type")}>
              <option value="expense">Expense</option><option value="income">Income</option>
            </select>
            <input type="number" step="0.01" min="0.01" placeholder="Amount" value={form.amount}
                   onChange={setF("amount")} required />
            <input type="date" value={form.txn_date} onChange={setF("txn_date")} required />
            <input placeholder="Description" value={form.description} onChange={setF("description")} />
          </div>
          <button className="primary">Save transaction</button>
        </form>

        <div className="card">
          <h3>Upload bank statement (CSV)</h3>
          <p className="muted">Columns: date, description, amount (negative = expense).</p>
          <div className="form-grid">
            <select value={csvAcc} onChange={(e) => setCsv({ ...csv, account_id: e.target.value })}>
              {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
            <input type="file" accept=".csv"
                   onChange={(e) => { setCsv({ ...csv, file: e.target.files[0] || null }); setPreview(null); }} />
          </div>
          <div className="form-row">
            <button type="button" onClick={() => runImport(false)}>Preview</button>
            {preview && preview.new > 0 &&
              <button type="button" className="primary" onClick={() => runImport(true)}>
                Import {preview.new} rows
              </button>}
          </div>
        </div>
      </div>

      {preview && (
        <div className="card">
          <h3>Preview: {preview.new} new, {preview.duplicates} duplicates, {preview.errors} errors</h3>
          <div className="scroll">
            <table>
              <thead><tr><th>Row</th><th>Date</th><th>Description</th><th>Amount</th><th>Category</th><th>Status</th></tr></thead>
              <tbody>
                {preview.rows.map((r) => (
                  <tr key={r.row}>
                    <td>{r.row}</td><td>{r.date}</td><td>{r.description}</td>
                    <td className={r.type}>{r.amount ? money(r.amount) : ""}</td>
                    <td>{r.category}</td>
                    <td><span className={"tag " + r.status}>{r.status === "error" ? r.reason : r.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card">
        <h3>Transactions</h3>
        <div className="form-row">
          <select value={filters.account_id} onChange={(e) => setFilters({ ...filters, account_id: e.target.value })}>
            <option value="">All accounts</option>
            {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
          <select value={filters.category_id} onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}>
            <option value="">All categories</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select value={filters.type} onChange={(e) => setFilters({ ...filters, type: e.target.value })}>
            <option value="">Income and expense</option>
            <option value="expense">Expense</option><option value="income">Income</option>
          </select>
        </div>
        {txns.length === 0 ? <p className="muted">No transactions found.</p> : (
          <div className="scroll">
            <table>
              <thead><tr><th>Date</th><th>Description</th><th>Category</th><th>Account</th><th>Amount</th><th></th></tr></thead>
              <tbody>
                {txns.map((t) => (
                  <tr key={t.id}>
                    <td>{t.txn_date}</td><td>{t.description}</td>
                    <td>{catName[t.category_id] || "-"}</td><td>{accName[t.account_id]}</td>
                    <td className={t.type}>{t.type === "expense" ? "-" : "+"}{money(t.amount)}</td>
                    <td><button onClick={() => del(t.id)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}