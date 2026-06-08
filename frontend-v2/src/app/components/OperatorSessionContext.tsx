import { createContext, useContext, useState, type ReactNode } from "react";
import { OperatorSessionShell, type OperatorSessionState } from "./OperatorSessionShell";

const OperatorSessionContext = createContext<string | null>(null);

export function OperatorSessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<OperatorSessionState | null>(null);

  return (
    <OperatorSessionContext.Provider value={session?.accessToken ?? null}>
      <OperatorSessionShell
        session={session}
        onStartSession={setSession}
        onEndSession={() => setSession(null)}
      />
      {children}
    </OperatorSessionContext.Provider>
  );
}

export function useOperatorAccessToken(): string | null {
  return useContext(OperatorSessionContext);
}
