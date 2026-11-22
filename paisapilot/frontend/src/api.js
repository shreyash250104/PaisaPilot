const BASE = "http://127.0.0.1:8000";

export const getToken = () => localStorage.getItem("token");
export const logout = () => localStorage.removeItem("token");

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
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

export const api = {
  login: (email, password) =>
    request("/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (name, email, password) =>
    request("/register", { method: "POST", body: JSON.stringify({ name, email, password }) }),
  me: () => request("/me"),
  summary: (month) => request(`/reports/summary?month=${month}`),
  trend: () => request("/reports/trend?months=6"),
  budgets: (month) => request(`/budgets?month=${month}`),
  alerts: () => request("/alerts?unread_only=true"),
};