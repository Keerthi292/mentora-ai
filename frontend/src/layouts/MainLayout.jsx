import { NavLink, Outlet } from "react-router-dom";

// Links shown in the navbar. Only the Dashboard page exists so far.
const NAV_LINKS = [
  { to: "/", label: "Dashboard" },
  { to: "/skills", label: "Skills" },
  { to: "/goals", label: "Goals" },
  { to: "/career", label: "Career" },
  { to: "/projects", label: "Projects" },
  { to: "/mentor", label: "Mentor" },
];

function MainLayout() {
  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
        <div className="container">
          <NavLink className="navbar-brand fw-semibold" to="/">
            Mentora AI
          </NavLink>

          {/* Hamburger button on small screens (needs Bootstrap's JS, loaded in main.jsx) */}
          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#mainNavbar"
            aria-controls="mainNavbar"
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <span className="navbar-toggler-icon"></span>
          </button>

          <div className="collapse navbar-collapse" id="mainNavbar">
            <ul className="navbar-nav ms-auto">
              {NAV_LINKS.map((link) => (
                <li className="nav-item" key={link.to}>
                  {/* NavLink adds the "active" class to the link for the current page.
                      `end` stops "/" from matching every page. */}
                  <NavLink className="nav-link" to={link.to} end={link.to === "/"}>
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
