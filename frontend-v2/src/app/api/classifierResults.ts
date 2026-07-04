export interface ClassifierSummary {
  objectCount: number;
  clusterCount: number;
  classifierVersion: string;
  classCounts: Record<string, number>;
}

export interface ClassifierDownloadLink {
  artifactName: string;
  filename: string;
  label: string;
  downloadUrl: string;
}

const CLASSIFIER_ARTIFACTS = [
  {
    artifactName: "experimental_classifications",
    filename: "classifications.csv",
    label: "Download classifications CSV",
  },
  {
    artifactName: "experimental_summary",
    filename: "summary.json",
    label: "Download summary JSON",
  },
  {
    artifactName: "experimental_neutral_labels",
    filename: "neutral_target_labels.json",
    label: "Download neutral target labels JSON",
  },
] as const;

interface ClassifierSummaryDto {
  object_count?: unknown;
  cluster_count?: unknown;
  classifier_version?: unknown;
  class_counts?: unknown;
}

export async function fetchClassifierSummary(runId: string): Promise<ClassifierSummary> {
  const response = await fetch(classifierArtifactUrl(runId, "experimental_summary"));
  if (!response.ok) {
    throw new Error("Classifier results are unavailable.");
  }
  const payload = (await response.json()) as ClassifierSummaryDto;
  return mapClassifierSummary(payload);
}

export function classifierDownloadLinks(runId: string): ClassifierDownloadLink[] {
  return CLASSIFIER_ARTIFACTS.map((artifact) => ({
    ...artifact,
    downloadUrl: classifierDownloadUrl(runId, artifact.artifactName, artifact.filename),
  }));
}

function classifierArtifactUrl(runId: string, artifactName: string): string {
  return `/runs/${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(artifactName)}`;
}

function classifierDownloadUrl(runId: string, artifactName: string, filename: string): string {
  return `${classifierArtifactUrl(runId, artifactName)}/download/${encodeURIComponent(filename)}`;
}

function mapClassifierSummary(payload: ClassifierSummaryDto): ClassifierSummary {
  return {
    objectCount: requiredNumber(payload.object_count),
    clusterCount: requiredNumber(payload.cluster_count),
    classifierVersion: requiredString(payload.classifier_version),
    classCounts: mapClassCounts(payload.class_counts),
  };
}

function mapClassCounts(value: unknown): Record<string, number> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("Classifier summary is unavailable.");
  }
  const counts: Record<string, number> = {};
  for (const [key, count] of Object.entries(value)) {
    if (typeof key === "string" && key.startsWith("Class_") && typeof count === "number" && Number.isFinite(count)) {
      counts[key] = count;
    }
  }
  return counts;
}

function requiredNumber(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error("Classifier summary is unavailable.");
  }
  return value;
}

function requiredString(value: unknown): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error("Classifier summary is unavailable.");
  }
  return value;
}
