import { useEffect, useState } from "react";
import { api } from "../api";

const money = (n) => "Rs. " + Number(n || 0).toLocaleString("en-IN");
const today = () => {
  const d = new Date();
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") +
    "-" + String(d.getDate()).padStart(2, "0");
};

export default function Groups() {
  const [me, setMe] = useState(null);
  const [groups, setGroups] = useState([]);
  const [sel, setSel] = useState(null);
  const [detail, setDetail] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [bal, setBal] = useState(null);
  const [version, setVersion] = useState(0);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [gname, setGname] = useState("");
  const [email, setEmail] = useState("");
  const [form, setForm] = useState({ description: "", amount: "", paid_by: "",
    split_type: "equal", expense_date: today(), shares: {} });
  const reload = () => setVersion((v) => v + 1);

  useEffect(() => {
    api.me().then(setMe).catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    api.groups().then(setGroups).catch((e) => setError(e.message));
  }, [version]);

  const activeId = sel || (groups[0] ? groups[0].id : null);

  useEffect(() => {
    if (!activeId) return;
    Promise.all([api.groupDetail(activeId), api.groupExpenses(activeId), api.balances(activeId)])
      .then(([d, e, b]) => { setDetail(d); setExpenses(e); setBal(b); })
      .catch((e) => setError(e.message));
  }, [activeId, version]);

  const d = detail && detail.id === activeId ? detail : null;
  const names = d ? Object.fromEntries(d.members.map((m) => [m.user_id, m.name])) : {};
  const payer = form.paid_by || (me ? me.id : "");
  const shareSum = Object.values(form.shares).reduce((s, v) => s + Number(v || 0), 0);

  async function createGroup(e) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      const g = await api.createGroup(gname);
      setGname(""); setSel(g.id); setMsg("Group created"); reload();
    } catch (err) { setError(err.message); }
  }

  async function addMember(e) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      await api.addMember(activeId, email);
      setEmail(""); setMsg("Member added"); reload();
    } catch (err) { setError(err.message); }
  }

  async function addExpense(e) {
    e.preventDefault();
    setError(""); setMsg("");
    const body = {
      description: form.description,
      amount: Number(form.amount),
      paid_by: Number(payer),
      split_type: form.split_type,
      expense_date: form.expense_date,
    };
    if (form.split_type === "custom") {
      body.splits = Object.entries(form.shares)
        .filter(([, v]) => Number(v) > 0)
        .map(([id, v]) => ({ user_id: Number(id), share: Number(v) }));
    }
    try {
      await api.addGroupExpense(activeId, body);
      setForm({ ...form, description: "", amount: "", shares: {} });
      setMsg("Expense added"); reload();
    } catch (err) { setError(err.message); }
  }

  async function settle(p) {
    setError(""); setMsg("");
    try {
      await api.settle(activeId, { from_user: p.from_user, to_user: p.to_user,
        amount: p.amount, settled_on: today() });
      setMsg("Settlement recorded"); reload();
    } catch (err) { setError(err.message); }
  }

  return (
    <>
      {error && <div className="error">{error}</div>}
      {msg && <div className="success">{msg}</div>}

      <div className="layout2">
        <div className="card">
          <h3>My groups</h3>
          <div className="glist">
            {groups.length === 0 && <p className="muted">No groups yet.</p>}
            {groups.map((g) => (
              <button key={g.id} className={g.id === activeId ? "active" : ""}
                      onClick={() => setSel(g.id)}>{g.name}</button>
            ))}
          </div>
          <form onSubmit={createGroup} className="form-row">
            <input placeholder="New group name" value={gname}
                   onChange={(e) => setGname(e.target.value)} required />
            <button className="primary">Create</button>
          </form>
        </div>

        <div>
          {!d ? <div className="card"><p className="muted">Create or select a group.</p></div> : (
            <>
              <div className="card">
                <h3>{d.name}</h3>
                <div className="chips">
                  {d.members.map((m) => <span key={m.user_id} className="chip">{m.name}</span>)}
                </div>
                <form onSubmit={addMember} className="form-row">
                  <input type="email" placeholder="Member e-mail (must be registered)"
                         value={email} onChange={(e) => setEmail(e.target.value)} required />
                  <button>Add member</button>
                </form>
              </div>

              <form className="card" onSubmit={addExpense}>
                <h3>Add shared expense</h3>
                <div className="form-grid">
                  <input placeholder="Description" value={form.description}
                         onChange={(e) => setForm({ ...form, description: e.target.value })} required />
                  <input type="number" step="0.01" min="0.01" placeholder="Amount" value={form.amount}
                         onChange={(e) => setForm({ ...form, amount: e.target.value })} required />
                  <select value={payer} onChange={(e) => setForm({ ...form, paid_by: e.target.value })}>
                    {d.members.map((m) => <option key={m.user_id} value={m.user_id}>Paid by {m.name}</option>)}
                  </select>
                  <select value={form.split_type}
                          onChange={(e) => setForm({ ...form, split_type: e.target.value })}>
                    <option value="equal">Split equally</option>
                    <option value="custom">Custom split</option>
                  </select>
                  <input type="date" value={form.expense_date}
                         onChange={(e) => setForm({ ...form, expense_date: e.target.value })} required />
                </div>
                {form.split_type === "custom" && (
                  <div className="form-grid">
                    {d.members.map((m) => (
                      <input key={m.user_id} type="number" step="0.01" min="0"
                             placeholder={m.name + "'s share"} value={form.shares[m.user_id] || ""}
                             onChange={(e) => setForm({ ...form,
                               shares: { ...form.shares, [m.user_id]: e.target.value } })} />
                    ))}
                    <span className="muted">Shares total {money(shareSum)} of {money(form.amount)}</span>
                  </div>
                )}
                <button className="primary">Save expense</button>
              </form>

              <div className="grid">
                <div className="card">
                  <h3>Balances</h3>
                  <table>
                    <thead><tr><th>Member</th><th>Net</th></tr></thead>
                    <tbody>
                      {bal && bal.balances.map((b) => (
                        <tr key={b.user_id}>
                          <td>{b.name}</td>
                          <td className={b.net >= 0 ? "pos" : "neg"}>
                            {b.net >= 0 ? "gets " : "owes "}{money(Math.abs(b.net))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="card">
                  <h3>Settle up (minimum payments)</h3>
                  {bal && bal.payments.length === 0 && <p className="muted">All settled.</p>}
                  {bal && bal.payments.map((p, i) => (
                    <div key={i} className="suggest">
                      <span>{p.from_name} pays {p.to_name} <b>{money(p.amount)}</b></span>
                      <button onClick={() => settle(p)}>Mark paid</button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card">
                <h3>Expenses</h3>
                {expenses.length === 0 ? <p className="muted">No expenses yet.</p> : (
                  <div className="scroll">
                    <table>
                      <thead><tr><th>Date</th><th>Description</th><th>Paid by</th><th>Amount</th><th>Split</th></tr></thead>
                      <tbody>
                        {expenses.map((x) => (
                          <tr key={x.id}>
                            <td>{x.expense_date}</td><td>{x.description}</td>
                            <td>{names[x.paid_by]}</td><td>{money(x.amount)}</td><td>{x.split_type}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}