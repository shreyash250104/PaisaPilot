const BASE = "http://127.0.0.1:8000";

export const getToken = () => localStorage.getItem("token");
export const logout = () => localStorage.removeItem("token");

const qs = (o) =>
  new URLSearchParams(
    Object.entries(o).filter(([, v]) => v !== "" && v != null)
  ).toString();

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(BASE + path, { ...options, headers });
  if (res.status === 401 && token && path !== "/login") {
    logout();
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) {
    const d = data && data.detail;
    throw new Error(
      typeof d === "string" ? d
      : Array.isArray(d) ? d.map((e) => e.msg).join(", ")
      : "Request failed"
    );
  }
  return data;
}

const json = (method, body) => ({ method, body: JSON.stringify(body) });

export const api = {
  login: (email, password) => request("/login", json("POST", { email, password })),
  register: (name, email, password) => request("/register", json("POST", { name, email, password })),
  me: () => request("/me"),
  summary: (month) => request(`/reports/summary?month=${month}`),
  trend: () => request("/reports/trend?months=6"),
  budgets: (month) => request(`/budgets?month=${month}`),
  setBudget: (b) => request("/budgets", json("POST", b)),
  alerts: () => request("/alerts?unread_only=true"),
  alertsAll: () => request("/alerts"),
  markRead: (id) => request(`/alerts/${id}/read`, { method: "PUT" }),
  accounts: () => request("/accounts"),
  createAccount: (a) => request("/accounts", json("POST", a)),
  categories: () => request("/categories"),
  transactions: (p) => request("/transactions?" + qs({ limit: 100, ...p })),
  addTxn: (t) => request("/transactions", json("POST", t)),
  deleteTxn: (id) => request(`/transactions/${id}`, { method: "DELETE" }),
  importCsv: (accountId, save, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return request(`/import/csv?account_id=${accountId}&save=${save}`, { method: "POST", body: fd });
  },
};