import { useState } from "react";

export interface OperatorSessionState {
  accessToken: string;
  actorId: string;
  roles: string[];
}

interface OperatorSessionShellProps {
  session: OperatorSessionState | null;
  onStartSession: (session: OperatorSessionState) => void;
  onEndSession: () => void;
}

function parseRoles(value: string): string[] {
  const roles = value.split(",").map((role) => role.trim()).filter(Boolean);
  return roles.length > 0 ? roles : ["operator"];
}

export function OperatorSessionShell({ session, onStartSession, onEndSession }: OperatorSessionShellProps) {
  const [draftAccessToken, setDraftAccessToken] = useState("");
  const [draftActorId, setDraftActorId] = useState("local-operator");
  const [draftRoles, setDraftRoles] = useState("operator");
  const [error, setError] = useState<string | null>(null);

  function handleStartSession() {
    const accessToken = draftAccessToken.trim();
    if (!accessToken) {
      setError("Paste a local development bearer value before starting the operator session.");
      return;
    }

    onStartSession({
      accessToken,
      actorId: draftActorId.trim() || "local-operator",
      roles: parseRoles(draftRoles),
    });
    setDraftAccessToken("");
    setError(null);
  }

  function handleEndSession() {
    setDraftAccessToken("");
    setError(null);
    onEndSession();
  }

  return (
    <section
      className="mx-5 mt-3 rounded-lg bg-card overflow-hidden"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <div className="px-4 py-2" style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}>
        <span className="font-mono" style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}>
          Local operator session
        </span>
      </div>

      <div className="px-4 py-3 flex flex-col gap-3">
        <div style={{ fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
          Local development shell. The bearer value is kept in page memory and forwarded only through the existing operatorAccessToken handoff path. No provider SDK or persistence is added.
        </div>

        {session ? (
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-navy)" }}>
                Operator: <span className="font-mono">{session.actorId}</span>
              </div>
              <div style={{ fontSize: "11px", color: "var(--gs-slate)", marginTop: "2px" }}>
                Roles: <span className="font-mono">{session.roles.join(", ")}</span> · in-memory session
              </div>
            </div>
            <button type="button" onClick={handleEndSession} className="rounded px-3 py-1.5" style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--gs-navy)", backgroundColor: "transparent", border: "1px solid rgba(28,43,94,0.18)", cursor: "pointer" }}>
              End session
            </button>
          </div>
        ) : (
          <div className="grid gap-2" style={{ gridTemplateColumns: "minmax(180px, 1fr) minmax(150px, 0.6fr) minmax(120px, 0.4fr) auto" }}>
            <label className="flex flex-col gap-1">
              <span style={{ fontSize: "10.5px", fontWeight: 700, color: "var(--gs-navy)" }}>Bearer value</span>
              <input type="password" value={draftAccessToken} onChange={(event) => setDraftAccessToken(event.target.value)} placeholder="Paste local bearer value" autoComplete="off" className="font-mono rounded outline-none" style={{ fontSize: "11px", padding: "7px 10px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" }} />
            </label>
            <label className="flex flex-col gap-1">
              <span style={{ fontSize: "10.5px", fontWeight: 700, color: "var(--gs-navy)" }}>Actor</span>
              <input type="text" value={draftActorId} onChange={(event) => setDraftActorId(event.target.value)} placeholder="local-operator" className="font-mono rounded outline-none" style={{ fontSize: "11px", padding: "7px 10px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" }} />
            </label>
            <label className="flex flex-col gap-1">
              <span style={{ fontSize: "10.5px", fontWeight: 700, color: "var(--gs-navy)" }}>Roles</span>
              <input type="text" value={draftRoles} onChange={(event) => setDraftRoles(event.target.value)} placeholder="operator" className="font-mono rounded outline-none" style={{ fontSize: "11px", padding: "7px 10px", backgroundColor: "var(--input-background)", border: "1px solid var(--border)", color: "var(--gs-navy)" }} />
            </label>
            <button type="button" onClick={handleStartSession} className="rounded px-3 py-1.5 self-end" style={{ fontSize: "11.5px", fontWeight: 700, color: "white", backgroundColor: "var(--gs-navy)", border: "1px solid var(--gs-navy)", cursor: "pointer" }}>
              Start session
            </button>
          </div>
        )}

        {error && (
          <div className="rounded px-3 py-2" style={{ fontSize: "11px", color: "var(--gs-red)", backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)" }}>
            {error}
          </div>
        )}
      </div>
    </section>
  );
}
