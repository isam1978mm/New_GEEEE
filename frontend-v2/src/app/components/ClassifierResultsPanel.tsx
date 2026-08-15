import { useEffect, useState } from "react";

import { getRunDetail } from "../api/client";
import { fetchClassifierSummary } from "../api/classifierResults";
import { fetchNBResults } from "../api/nbResults";
import { ClassifierOnlyResultsPanel } from "./ClassifierOnlyResultsPanel";
import { NBResultsPanel } from "./NBResultsPanel";

interface ClassifierResultsPanelProps {
  runId: string;
}

const RESULTS_COMPLETION_POLL_MS = 2000;
const RESULTS_READY_POLL_MS = 1000;
const RESULTS_READY_MAX_ATTEMPTS = 12;

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
    let lastReadyMask = 0;

    function schedule(callback: () => void, delayMs: number) {
      if (cancelled) {
        return;
      }
      retryTimer = window.setTimeout(callback, delayMs);
    }

    async function checkResultReadiness(attempt: number) {
      const [classifierReady, nbReady] = await Promise.all([
        fetchClassifierSummary(runId).then(() => true).catch(() => false),
        fetchNBResults(runId)
          .then((results) => results.status !== "not_available")
          .catch(() => false),
      ]);
      if (cancelled) {
        return;
      }

      const readyMask = (classifierReady ? 1 : 0) | (nbReady ? 2 : 0);
      if (readyMask !== 0 && readyMask !== lastReadyMask) {
        lastReadyMask = readyMask;
        setRevision((current) => current + 1);
      }

      if (readyMask === 3 || attempt >= RESULTS_READY_MAX_ATTEMPTS) {
        return;
      }

      schedule(() => {
        void checkResultReadiness(attempt + 1);
      }, RESULTS_READY_POLL_MS);
    }

    async function checkRunState() {
      try {
        const run = await getRunDetail(runId);
        if (cancelled) {
          return;
        }

        if (run.state === "queued" || run.state === "running") {
          schedule(() => {
            void checkRunState();
          }, RESULTS_COMPLETION_POLL_MS);
          return;
        }

        if (run.state === "done") {
          // Do not trust run-state timing alone. A run can be marked done before
          // the classifier/NB read paths are visible to the browser. Poll the
          // actual result read APIs and refresh the existing panels only when
          // those outputs are demonstrably ready.
          void checkResultReadiness(0);
        }
      } catch (_error) {
        schedule(() => {
          void checkRunState();
        }, RESULTS_COMPLETION_POLL_MS);
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
