import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api, logout } from "../api";

export default function Layout() {
  const nav = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.me().then(setUser).catch(() => {});
  }, []);

  const doLogout = () => { logout(); nav("/login"); };

  return (
    <div className="page">
      <header className="top">
        <h2>PaisaPilot</h2>
        <nav className="nav">
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/transactions">Transactions</NavLink>
          <NavLink to="/budgets">Budgets</NavLink>
        </nav>
        <div className="right">
          <span className="muted">{user ? user.name : ""}</span>
          <button onClick={doLogout}>Logout</button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}