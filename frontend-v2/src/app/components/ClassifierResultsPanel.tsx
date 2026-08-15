import { useEffect, useState } from "react";

import { getRunDetail } from "../api/client";
import { ClassifierOnlyResultsPanel } from "./ClassifierOnlyResultsPanel";
import { NBResultsPanel } from "./NBResultsPanel";

interface ClassifierResultsPanelProps {
  runId: string;
}

const RESULTS_COMPLETION_POLL_MS = 2000;

export function ClassifierResultsPanel({ runId }: ClassifierResultsPanelProps) {
  const completionRevision = useCompletionRevision(runId);

  return <ResultsPanels key={`${runId}:${completionRevision}`} runId={runId} />;
}

function ResultsPanels({ runId }: ClassifierResultsPanelProps) {
  return (
    <>
      <ClassifierOnlyResultsPanel runId={runId} />
      <NBResultsPanel runId={runId} />
    </>
  );
}

function useCompletionRevision(runId: string) {
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let retryTimer: number | null = null;
    let sawActiveRun = false;

    async function checkRunState() {
      try {
        const run = await getRunDetail(runId);
        if (cancelled) {
          return;
        }

        if (run.state === "queued" || run.state === "running") {
          sawActiveRun = true;
          retryTimer = window.setTimeout(() => {
            void checkRunState();
          }, RESULTS_COMPLETION_POLL_MS);
          return;
        }

        if (run.state === "done" && sawActiveRun) {
          setRevision((current) => current + 1);
        }
      } catch (_error) {
        if (!cancelled) {
          retryTimer = window.setTimeout(() => {
            void checkRunState();
          }, RESULTS_COMPLETION_POLL_MS);
        }
      }
    }

    void checkRunState();
    return () => {
      cancelled = true;
      if (retryTimer !== null) {
        window.clearTimeout(retryTimer);
      }
    };
  }, [runId]);

  return revision;
}
