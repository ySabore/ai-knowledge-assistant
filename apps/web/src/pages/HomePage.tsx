import { useEffect, useState } from "react";

const defaultBearer = import.meta.env.VITE_DEV_BEARER_TOKEN ?? "dev-local-token";
const storageKey = "aka.auth.bearer";

const api = (path: string, bearer: string, init?: RequestInit) =>
  fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${bearer}`,
      ...(init?.headers || {}),
    },
  });

export default function HomePage() {
  const [bearer, setBearer] = useState<string>(() => localStorage.getItem(storageKey) || defaultBearer);
  const [tokenDraft, setTokenDraft] = useState<string>(bearer);
  const [health, setHealth] = useState<string>("…");
  const [orgs, setOrgs] = useState<unknown[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const h = await api("/health", bearer);
        const hj = await h.json();
        if (!cancelled) setHealth(hj.status === "ok" ? "ok" : JSON.stringify(hj));
        const o = await api("/me/organizations", bearer);
        if (!o.ok) throw new Error(`${o.status} ${await o.text()}`);
        const oj = await o.json();
        if (!cancelled) setOrgs(oj.organizations || []);
      } catch (e) {
        if (!cancelled) setErr(String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [bearer]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Status</h1>
      <p className="text-slate-400">
        This UI was regenerated after filesystem damage on the original project copy. The API
        talks to your existing <code className="text-teal-300">app.db</code>.
      </p>
      {err && (
        <div className="rounded border border-red-800 bg-red-950/50 p-3 text-sm text-red-200">
          {err}
        </div>
      )}
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        <div className="text-sm text-slate-400">GET /health</div>
        <div className="text-lg font-mono text-teal-300">{health}</div>
      </div>
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        <div className="text-sm text-slate-400">Authorization bearer token</div>
        <p className="mb-2 mt-1 text-xs text-slate-500">
          Use <code>dev-local-token</code> for local dev auth, or paste a Clerk JWT when
          <code>AUTH_MODE=clerk</code> on the backend.
        </p>
        <div className="flex gap-2">
          <input
            className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-sm text-slate-200"
            value={tokenDraft}
            onChange={(e) => setTokenDraft(e.target.value)}
            placeholder="Paste bearer token"
          />
          <button
            className="rounded bg-teal-600 px-3 py-1 text-sm text-white hover:bg-teal-500"
            onClick={() => {
              const next = tokenDraft.trim() || defaultBearer;
              setBearer(next);
              localStorage.setItem(storageKey, next);
              setErr(null);
            }}
            type="button"
          >
            Apply
          </button>
        </div>
      </div>
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
        <div className="text-sm text-slate-400">GET /me/organizations</div>
        <ul className="mt-2 list-inside list-disc text-slate-200">
          {orgs.map((o: any) => (
            <li key={o.organization_id}>
              {o.organization_name}{" "}
              <span className="text-slate-500">({o.organization_id})</span>
            </li>
          ))}
        </ul>
      </div>
      <p className="text-xs text-slate-500">
        Backend: <code>cd backend && uvicorn ai_knowledge_assistant.main:app --reload</code>
        <br />
        Browser sends <code>Authorization: Bearer ...</code>. Default comes from{" "}
        <code>VITE_DEV_BEARER_TOKEN</code>, and you can override it in-page for Clerk JWT testing.
      </p>
    </div>
  );
}
