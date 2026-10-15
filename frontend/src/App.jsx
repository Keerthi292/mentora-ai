import { Route, Routes } from "react-router-dom";

import MainLayout from "./layouts/MainLayout";
import CareerGoals from "./pages/CareerGoals";
import Dashboard from "./pages/Dashboard";
import LearningGoals from "./pages/LearningGoals";
import MentorChat from "./pages/MentorChat";
import Projects from "./pages/Projects";
import Skills from "./pages/Skills";

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
        <Route path="/mentor" element={<MentorChat />} />
        <Route path="*" element={<p className="text-body-secondary">Page not found.</p>} />
      </Route>
    </Routes>
  );
}

export default App;
