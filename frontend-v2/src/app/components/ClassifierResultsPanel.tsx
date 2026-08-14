import { ClassifierOnlyResultsPanel } from "./ClassifierOnlyResultsPanel";
import { NBResultsPanel } from "./NBResultsPanel";

interface ClassifierResultsPanelProps {
  runId: string;
}

export function ClassifierResultsPanel({ runId }: ClassifierResultsPanelProps) {
  return (
    <>
      <ClassifierOnlyResultsPanel runId={runId} />
      <NBResultsPanel runId={runId} />
    </>
  );
}
