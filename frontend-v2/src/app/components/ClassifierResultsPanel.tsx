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

    async function checkRunState() {
      try {
        const run = await getRunDetail(runId);
        if (cancelled) {
          return;
        }

        if (run.state === "queued" || run.state === "running") {
          retryTimer = window.setTimeout(() => {
            void checkRunState();
          }, RESULTS_COMPLETION_POLL_MS);
          return;
        }

        // A completed run must force one fresh Results mount even when this
        // component's first lifecycle check already sees `done`. The previous
        // implementation required observing queued/running first, which left
        // stale "not available" results visible until a manual refresh.
        if (run.state === "done") {
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
