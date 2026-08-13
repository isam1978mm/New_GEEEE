import { ClassifierOnlyResultsPanel } from "./ClassifierOnlyResultsPanel";

interface ClassifierResultsPanelProps {
  runId: string;
}

export function ClassifierResultsPanel({ runId }: ClassifierResultsPanelProps) {
  return <ClassifierOnlyResultsPanel runId={runId} />;
}
