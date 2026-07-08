import { NavLink, Outlet } from "react-router-dom";

import { useTheme } from "../hooks/useTheme";
import "./Layout.css";

const NAV_ITEMS = [
  { to: "/memories", label: "Memories" },
  { to: "/search", label: "Search" },
  { to: "/intelligence", label: "Intelligence" },
  { to: "/settings", label: "Settings" },
];

/** App shell: left nav + routed content. Graph search is a mode on the
 * Search page (not its own nav item — ADR-0006); Consolidate/Learn/Export/
 * Import live on the Intelligence page. A global Events feed is still not in
 * this nav — there is no backing API for it (per-memory version history
 * lives in the detail pane's History tab instead; see 29-session-handoff.md).
 */
export function Layout() {
  const [themePreference, setThemePreference] = useTheme();

  return (
    <div className="layout">
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      <header className="layout__topbar">
        <span className="layout__brand">MIP Console</span>
        <label className="layout__theme">
          <span className="visually-hidden">Theme</span>
          <select
            aria-label="Theme"
            value={themePreference}
            onChange={(event) => setThemePreference(event.target.value as typeof themePreference)}
          >
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </label>
      </header>
      <div className="layout__body">
        <nav className="layout__nav" aria-label="Primary">
          <ul>
            {NAV_ITEMS.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} className={({ isActive }) => (isActive ? "active" : "")}>
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main id="main-content" className="layout__content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
