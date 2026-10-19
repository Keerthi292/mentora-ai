import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import BotAvatar from "./components/BotAvatar";
import useMe from "./hooks/useMe";
import MainLayout from "./layouts/MainLayout";
import AuthPage from "./pages/AuthPage";
import CareerGoals from "./pages/CareerGoals";
import Dashboard from "./pages/Dashboard";
import LearningGoals from "./pages/LearningGoals";
import Projects from "./pages/Projects";
import Skills from "./pages/Skills";

// Loaded only when opened: it brings the Markdown renderer, which other pages don't need
const MentorChat = lazy(() => import("./pages/MentorChat"));
// Brings the rich-text editor
const ProjectDetail = lazy(() => import("./pages/ProjectDetail"));

// Logged out: the login / sign-up pages at every address. Logged in: the app.
function App() {
  const { status, error, retry } = useMe();

  if (status === "loading") {
    return (
      <div className="auth-page d-flex align-items-center justify-content-center">
        <BotAvatar size={64} thinking />
      </div>
    );
  }

  if (status === "offline") {
    return (
      <div className="auth-page d-flex flex-column align-items-center justify-content-center text-center px-3">
        <BotAvatar size={64} />
        <p className="mt-3 mb-1 fw-semibold">Mentora can't reach the backend.</p>
        <p className="text-body-secondary small">{error}</p>
        <button type="button" className="btn btn-gradient" onClick={retry}>
          Try again
        </button>
      </div>
    );
  }

  if (status === "out") {
    return (
      <Routes>
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route path="*" element={<AuthPage mode="login" />} />
      </Routes>
    );
  }

  return (
    <Routes>
      {/* Just logged in from one of these: go to the dashboard */}
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route path="/register" element={<Navigate to="/" replace />} />
      {/* Every page inside MainLayout gets the navbar */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/skills" element={<Skills />} />
        <Route path="/goals" element={<LearningGoals />} />
        <Route path="/career" element={<CareerGoals />} />
        <Route path="/projects" element={<Projects />} />
        <Route
          path="/projects/:id"
          element={
            <Suspense fallback={<div className="text-body-secondary">Loading project...</div>}>
              <ProjectDetail />
            </Suspense>
          }
        />
        <Route
          path="/mentor"
          element={
            <Suspense fallback={<div className="text-body-secondary">Loading mentor...</div>}>
              <MentorChat />
            </Suspense>
          }
        />
        <Route path="*" element={<p className="text-body-secondary">Page not found.</p>} />
      </Route>
    </Routes>
  );
}

export default App;
