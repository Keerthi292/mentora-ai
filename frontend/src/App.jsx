import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import MainLayout from "./layouts/MainLayout";
import CareerGoals from "./pages/CareerGoals";
import Dashboard from "./pages/Dashboard";
import LearningGoals from "./pages/LearningGoals";
import Projects from "./pages/Projects";
import Skills from "./pages/Skills";

// Loaded only when opened: it brings the Markdown renderer, which other pages don't need
const MentorChat = lazy(() => import("./pages/MentorChat"));
// Brings the rich-text editor
const ProjectDetail = lazy(() => import("./pages/ProjectDetail"));

// No login/register or protected routes: the backend uses a single demo user.
function App() {
  return (
    <Routes>
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
