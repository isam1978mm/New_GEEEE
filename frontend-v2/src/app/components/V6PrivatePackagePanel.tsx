import { useEffect, useState } from "react";
import {
  generateV6Package,
  retrieveV6Package,
  reviewV6Package,
  saveBlob,
  type V6PackageStatus,
} from "../api/v6PackageFlow";
import { useOperatorAccessToken } from "./OperatorSessionContext";

interface V6PrivatePackagePanelProps {
  runId: string;
  operatorAccessToken?: string | null;
}

type ActionState = "idle" | "generating" | "reviewing" | "retrieving";

const PACKAGE_TITLE = "Paid Imagery Export Package";

export function V6PrivatePackagePanel({ runId, operatorAccessToken }: V6PrivatePackagePanelProps) {
  const contextOperatorAccessToken = useOperatorAccessToken();
  const resolvedOperatorAccessToken = operatorAccessToken ?? contextOperatorAccessToken;
  const [status, setStatus] = useState<V6PackageStatus | null>(null);
  const [actionState, setActionState] = useState<ActionState>("idle");
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadReview() {
      setActionState("reviewing");
      const nextStatus = await reviewV6Package(runId, { accessToken: resolvedOperatorAccessToken });
      if (!cancelled) {
        setStatus(nextStatus);
        setActionState("idle");
      }
    }
    void loadReview();
    return () => {
      cancelled = true;
    };
  }, [runId, resolvedOperatorAccessToken]);

  async function handleGenerate() {
    setActionState("generating");
    setFeedback(null);
    const nextStatus = await generateV6Package(runId, { accessToken: resolvedOperatorAccessToken });
    setStatus(nextStatus);
    setFeedback(nextStatus.outcome === "generated" ? "Export package generated." : nextStatus.message || "Export package generation did not complete.");
    setActionState("idle");
  }

  async function handleReview() {
    setActionState("reviewing");
    setFeedback(null);
    const nextStatus = await reviewV6Package(runId, { accessToken: resolvedOperatorAccessToken });
    setStatus(nextStatus);
    setActionState("idle");
  }

  async function handleRetrieve() {
    setActionState("retrieving");
    setFeedback(null);
    const result = await retrieveV6Package(runId, { accessToken: resolvedOperatorAccessToken });
    setStatus(result.status);
    if (result.blob && result.filename) {
      saveBlob(result.blob, result.filename);
      setFeedback("Export package retrieval started.");
    } else {
      setFeedback(result.status.message || "Export package is not available for retrieval.");
    }
    setActionState("idle");
  }

  return (
    <section
      className="rounded-lg bg-card overflow-hidden mt-4"
      style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
    >
      <details open>
        <summary
          className="px-4 py-2"
          style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)", cursor: "pointer" }}
        >
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            {PACKAGE_TITLE}
          </span>
        </summary>

        <div className="px-4 py-3 flex flex-col gap-3">
          <div style={{ fontSize: "11px", color: "var(--gs-slate)", lineHeight: "1.5" }}>
            Generates, reviews, and retrieves a ZIP export package for requesting/reviewing paid imagery over the best candidate zones. The panel shows metadata only and never displays rows or spatial payloads.
          </div>

          <div className="flex flex-wrap gap-2">
            <ActionButton label="Generate export package" disabled={actionState !== "idle"} onClick={() => { void handleGenerate(); }} />
            <ActionButton label="Review package metadata" disabled={actionState !== "idle"} onClick={() => { void handleReview(); }} />
            <ActionButton label="Retrieve export package ZIP" disabled={actionState !== "idle" || status?.packageReady !== true} onClick={() => { void handleRetrieve(); }} />
          </div>

          {actionState !== "idle" && <StatusBox tone="neutral" message={loadingMessage(actionState)} />}
          {feedback && actionState === "idle" && <StatusBox tone="neutral" message={feedback} />}
          {status && actionState === "idle" && <PackageStatusBody status={status} />}
        </div>
      </details>
    </section>
  );
}

function PackageStatusBody({ status }: { status: V6PackageStatus }) {
  if (status.outcome === "denied") {
    return (
      <StatusBox
        tone="warning"
        message={status.message || "Paid Imagery Export Package is not available for this operator session."}
        detail={status.supportReference ? `Support reference: ${status.supportReference}` : undefined}
      />
    );
  }

  if (status.outcome === "not_available") {
    return <StatusBox tone="neutral" message="No export package is available for this run yet." />;
  }

  if (status.outcome === "invalid_package_inputs") {
    return <StatusBox tone="error" message="The run-local export package inputs are invalid." />;
  }

  if (status.outcome === "error") {
    return <StatusBox tone="error" message={status.message || "Paid Imagery Export Package is temporarily unavailable."} />;
  }

  return (
    <div className="rounded px-3 py-2" style={{ backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)" }}>
      <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--gs-navy)", marginBottom: "6px" }}>
        Export package metadata
      </div>
      <dl className="grid gap-2" style={{ gridTemplateColumns: "max-content 1fr", fontSize: "11px", color: "var(--gs-slate)" }}>
        <dt style={termStyle}>Run</dt>
        <dd className="font-mono">{status.runId}</dd>
        <dt style={termStyle}>Outcome</dt>
        <dd>{status.outcome}</dd>
        <dt style={termStyle}>Ready</dt>
        <dd>{status.packageReady ? "yes" : "no"}</dd>
        {status.validationStatus && (
          <>
            <dt style={termStyle}>Validation</dt>
            <dd>{status.validationStatus}</dd>
          </>
        )}
        {typeof status.payloadCount === "number" && (
          <>
            <dt style={termStyle}>Payloads</dt>
            <dd>{status.payloadCount}</dd>
          </>
        )}
        {typeof status.zipEntryCount === "number" && (
          <>
            <dt style={termStyle}>ZIP entries</dt>
            <dd>{status.zipEntryCount}</dd>
          </>
        )}
        {typeof status.issueCount === "number" && (
          <>
            <dt style={termStyle}>Issues</dt>
            <dd>{status.issueCount}</dd>
          </>
        )}
        {typeof status.warningCount === "number" && (
          <>
            <dt style={termStyle}>Warnings</dt>
            <dd>{status.warningCount}</dd>
          </>
        )}
        {status.zipFilename && (
          <>
            <dt style={termStyle}>ZIP package</dt>
            <dd className="font-mono">{status.zipFilename}</dd>
          </>
        )}
      </dl>
      {status.categoryCounts && (
        <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginTop: "8px" }}>
          Categories: {Object.entries(status.categoryCounts).map(([key, value]) => `${key} ${value}`).join(" · ")}
        </div>
      )}
    </div>
  );
}

function ActionButton({ label, disabled, onClick }: { label: string; disabled: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="rounded px-2.5 py-1"
      style={{
        fontSize: "11px",
        fontWeight: 700,
        color: disabled ? "var(--gs-slate)" : "white",
        backgroundColor: disabled ? "transparent" : "var(--gs-navy)",
        border: "1px solid rgba(28,43,94,0.18)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.65 : 1,
      }}
    >
      {label}
    </button>
  );
}

function StatusBox({ tone, message, detail }: { tone: "neutral" | "warning" | "error"; message: string; detail?: string }) {
  const styles = {
    neutral: { backgroundColor: "var(--accent)", border: "1px solid rgba(28,43,94,0.12)", color: "var(--gs-slate)" },
    warning: { backgroundColor: "var(--gs-amber-bg)", border: "1px solid var(--gs-amber-border)", color: "var(--gs-slate)" },
    error: { backgroundColor: "var(--gs-red-bg)", border: "1px solid var(--gs-red-border)", color: "var(--gs-red)" },
  }[tone];

  return (
    <div className="rounded px-3 py-2" style={{ ...styles, fontSize: "11px", lineHeight: "1.5" }}>
      <div>{message}</div>
      {detail && <div className="font-mono" style={{ marginTop: "4px", fontSize: "10.5px" }}>{detail}</div>}
    </div>
  );
}

function loadingMessage(actionState: ActionState): string {
  if (actionState === "generating") {
    return "Generating export package...";
  }
  if (actionState === "retrieving") {
    return "Retrieving export package ZIP...";
  }
  return "Reviewing export package metadata...";
}

const termStyle = { fontWeight: 600, color: "var(--gs-navy)" } as const;
