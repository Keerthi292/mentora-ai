import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import BotAvatar from "../components/BotAvatar";

// Links shown in the navbar
const NAV_LINKS = [
  { to: "/", label: "Dashboard", icon: "bi-grid-1x2" },
  { to: "/skills", label: "Skills", icon: "bi-stars" },
  { to: "/goals", label: "Goals", icon: "bi-bullseye" },
  { to: "/career", label: "Career", icon: "bi-briefcase" },
  { to: "/projects", label: "Projects", icon: "bi-kanban" },
  { to: "/mentor", label: "Mentor", icon: "bi-robot" },
];

const THEME_KEY = "mentora.theme"; // also read in index.html, before the page draws

// Dark by default; the choice is remembered in this browser
function useTheme() {
  const [theme, setTheme] = useState(() => document.documentElement.getAttribute("data-bs-theme") || "dark");

  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-bs-theme", next);
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      // storage blocked: the theme still changes for this visit
    }
    setTheme(next);
  };

  return [theme, toggle];
}

function MainLayout() {
  const [theme, toggleTheme] = useTheme();
  // The menu on small screens (hamburger button). Controlled by React rather than
  // Bootstrap's JS, so it closes when a link is tapped or the page changes.
  const [menuOpen, setMenuOpen] = useState(false);
  const navRef = useRef(null);
  const location = useLocation();

  useEffect(() => setMenuOpen(false), [location.pathname]);

  // Close on a tap outside the navbar, or Escape
  useEffect(() => {
    if (!menuOpen) return;
    const onPointer = (event) => !navRef.current?.contains(event.target) && setMenuOpen(false);
    const onKey = (event) => event.key === "Escape" && setMenuOpen(false);
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [menuOpen]);

  return (
    <>
      <nav className="navbar navbar-expand-lg sticky-top app-navbar" ref={navRef}>
        <div className="container">
          <NavLink className="navbar-brand d-flex align-items-center gap-2 fw-bold" to="/">
            <BotAvatar size={42} className="brand-bot" />
            <span className="brand-text">Mentora AI</span>
          </NavLink>

          <div className="d-flex align-items-center gap-2 order-lg-last ms-auto ms-lg-3">
            <button
              type="button"
              className="btn btn-sm btn-outline-secondary rounded-circle theme-toggle"
              onClick={toggleTheme}
              aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
              title={theme === "dark" ? "Light theme" : "Dark theme"}
            >
              <i className={`bi ${theme === "dark" ? "bi-sun" : "bi-moon-stars"}`} />
            </button>

            {/* Hamburger button on small screens */}
            <button
              className="navbar-toggler"
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-controls="mainNavbar"
              aria-expanded={menuOpen}
              aria-label="Toggle navigation"
            >
              <span className="navbar-toggler-icon"></span>
            </button>
          </div>

          <div className={`collapse navbar-collapse ${menuOpen ? "show" : ""}`} id="mainNavbar">
            <ul className="navbar-nav ms-auto gap-lg-1">
              {NAV_LINKS.map((link) => (
                <li className="nav-item" key={link.to}>
                  {/* NavLink adds the "active" class to the link for the current page.
                      `end` stops "/" from matching every page. */}
                  <NavLink
                    className="nav-link d-flex align-items-center gap-2 rounded-3 px-lg-3"
                    to={link.to}
                    end={link.to === "/"}
                    onClick={() => setMenuOpen(false)}
                  >
                    <i className={`bi ${link.icon}`} aria-hidden="true" />
                    {link.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </nav>

      <main className="container py-4">
        {/* The current page renders here */}
        <Outlet />
      </main>
    </>
  );
}

export default MainLayout;
