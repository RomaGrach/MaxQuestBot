import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { buttonSecondaryClass, cx, getErrorMessage, panelClass } from "./utils";
import { pingHealth } from "./api";
import LandingPage from "./pages/LandingPage";
import AdminPage from "./pages/AdminPage";
import WebAppPage from "./pages/WebAppPage";

function NotFoundPage() {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-4xl items-center justify-center px-4 py-6">
      <div className={cx(panelClass, "grid gap-4 p-8 text-center")}>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[color:var(--muted)]">
          404
        </p>
        <h1 className="text-2xl font-semibold text-[color:var(--ink)]">Страница не найдена</h1>
        <p className="text-sm text-[color:var(--muted)]">
          Перейдите на главную, в админку или в WebApp.
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          <Link className={buttonSecondaryClass} to="/">
            Главная
          </Link>
          <Link className={buttonSecondaryClass} to="/admin">
            Админка
          </Link>
          <Link className={buttonSecondaryClass} to="/app">
            WebApp
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [health, setHealth] = useState({ state: "loading" });

  useEffect(() => {
    let cancelled = false;

    pingHealth()
      .then(() => {
        if (!cancelled) {
          setHealth({ state: "online" });
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setHealth({ state: "offline", error: getErrorMessage(error) });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Routes>
      <Route element={<LandingPage health={health} />} path="/" />
      <Route element={<AdminPage health={health} />} path="/admin" />
      <Route element={<WebAppPage health={health} />} path="/app" />
      <Route element={<NotFoundPage />} path="*" />
    </Routes>
  );
}
