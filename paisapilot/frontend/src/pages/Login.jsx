import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Login() {
  const nav = useNavigate();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") await api.register(form.name, form.email, form.password);
      const t = await api.login(form.email, form.password);
      localStorage.setItem("token", t.access_token);
      nav("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <form className="card auth" onSubmit={submit}>
        <h1>PaisaPilot</h1>
        <p className="muted">Know where every rupee goes.</p>
        {mode === "register" && (
          <input placeholder="Name" value={form.name} onChange={set("name")} required />
        )}
        <input type="email" placeholder="Email" value={form.email} onChange={set("email")} required />
        <input type="password" placeholder="Password (6+ characters)" minLength={6}
               value={form.password} onChange={set("password")} required />
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>
          {busy ? "Please wait..." : mode === "login" ? "Login" : "Create account"}
        </button>
        <button type="button" className="link"
                onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
          {mode === "login" ? "New user? Create an account" : "Already registered? Login"}
        </button>
      </form>
    </div>
  );
}