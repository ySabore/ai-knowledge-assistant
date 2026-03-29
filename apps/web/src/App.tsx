import { Link, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700 bg-slate-900/80 px-4 py-3">
        <nav className="mx-auto flex max-w-3xl items-center gap-4">
          <Link to="/" className="font-semibold text-teal-400">
            AI Knowledge Assistant
          </Link>
          <span className="text-xs text-slate-500">recovery UI</span>
        </nav>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-8">
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      </main>
    </div>
  );
}
