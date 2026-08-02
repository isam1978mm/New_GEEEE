import { ClassifierOnlyResultsPanel } from "./ClassifierOnlyResultsPanel";
import { Option5ResultsPanel } from "./Option5ResultsPanel";

interface ClassifierResultsPanelProps {
  runId: string;
}

export function ClassifierResultsPanel({ runId }: ClassifierResultsPanelProps) {
  return (
    <>
      <ClassifierOnlyResultsPanel runId={runId} />
      <Option5ResultsPanel runId={runId} />
    </>
  );
}
