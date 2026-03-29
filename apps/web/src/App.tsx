import { Navigate, Route, Routes } from "react-router-dom";
import AppPage from "./pages/AppPage";
import LandingPageFrame from "./pages/LandingPageFrame";
import SignInPage from "./pages/SignInPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPageFrame />} />
      <Route path="/sign-in/*" element={<SignInPage />} />
      <Route path="/app/*" element={<AppPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
