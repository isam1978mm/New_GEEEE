export interface ClassifierSummary {
  objectCount: number;
  clusterCount: number;
  classifierVersion: string;
  classCounts: Record<string, number>;
}

export interface ClassifierObjectRow {
  objectId: string;
  clusterId: string;
  score: number;
  scoreLevel: string;
  notebookLabel: string;
  ruleReason: string;
  reviewOrder: string;
  rowStart: string;
  rowEnd: string;
  columnStart: string;
  columnEnd: string;
}

export interface ClassifierDownloadLink {
  artifactName: string;
  filename: string;
  label: string;
  downloadUrl: string;
}

const SUMMARY_ARTIFACT_NAME = "classifier_summary";
const LEGACY_SUMMARY_ARTIFACT_NAME = "experimental_summary";
const SUMMARY_FILENAME = "summary.json";
const CLASSIFICATIONS_ARTIFACT_NAME = "classifier_classifications";
const LEGACY_CLASSIFICATIONS_ARTIFACT_NAME = "experimental_classifications";
const CLASSIFICATIONS_FILENAME = "classifications.csv";

const CLASSIFIER_ARTIFACTS = [
  {
    artifactName: CLASSIFICATIONS_ARTIFACT_NAME,
    filename: CLASSIFICATIONS_FILENAME,
    label: "Download classifier CSV",
  },
  {
    artifactName: SUMMARY_ARTIFACT_NAME,
    filename: SUMMARY_FILENAME,
    label: "Download classifier summary JSON",
  },
  {
    artifactName: "classifier_neutral_labels",
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
  const response = await fetchWithFallbacks([
    classifierDownloadUrl(runId, SUMMARY_ARTIFACT_NAME, SUMMARY_FILENAME),
    classifierDownloadUrl(runId, LEGACY_SUMMARY_ARTIFACT_NAME, SUMMARY_FILENAME),
    outputDownloadUrl(runId, `experimental/${SUMMARY_FILENAME}`),
  ]);
  if (!response.ok) {
    throw new Error("Classifier results are unavailable.");
  }
  const payload = (await response.json()) as ClassifierSummaryDto;
  return mapClassifierSummary(payload);
}

export async function fetchClassifierObjects(runId: string): Promise<ClassifierObjectRow[]> {
  const response = await fetchWithFallbacks([
    classifierDownloadUrl(runId, CLASSIFICATIONS_ARTIFACT_NAME, CLASSIFICATIONS_FILENAME),
    classifierDownloadUrl(runId, LEGACY_CLASSIFICATIONS_ARTIFACT_NAME, CLASSIFICATIONS_FILENAME),
    outputDownloadUrl(runId, `experimental/${CLASSIFICATIONS_FILENAME}`),
  ]);
  if (!response.ok) {
    throw new Error("Classifier object rows are unavailable.");
  }
  const rows = parseCsv(await response.text());
  return rows.map(mapClassifierObjectRow).sort((left, right) => right.score - left.score);
}

export function classifierDownloadLinks(runId: string): ClassifierDownloadLink[] {
  return [
    {
      artifactName: LEGACY_CLASSIFICATIONS_ARTIFACT_NAME,
      filename: CLASSIFICATIONS_FILENAME,
      label: "Download classifier CSV",
      downloadUrl: outputDownloadUrl(runId, `experimental/${CLASSIFICATIONS_FILENAME}`),
    },
    {
      artifactName: LEGACY_SUMMARY_ARTIFACT_NAME,
      filename: SUMMARY_FILENAME,
      label: "Download classifier summary JSON",
      downloadUrl: outputDownloadUrl(runId, `experimental/${SUMMARY_FILENAME}`),
    },
    {
      artifactName: "experimental_neutral_labels",
      filename: "neutral_target_labels.json",
      label: "Download neutral target labels JSON",
      downloadUrl: outputDownloadUrl(runId, "experimental/neutral_target_labels.json"),
    },
  ];
}

function classifierArtifactUrl(runId: string, artifactName: string): string {
  return `/runs/${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(artifactName)}`;
}

function classifierDownloadUrl(runId: string, artifactName: string, filename: string): string {
  return `${classifierArtifactUrl(runId, artifactName)}/download/${encodeURIComponent(filename)}`;
}

function outputDownloadUrl(runId: string, relativePath: string): string {
  return `/runs/${encodeURIComponent(runId)}/outputs/download/${relativePath
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/")}`;
}

async function fetchWithFallbacks(urls: string[]): Promise<Response> {
  let lastResponse: Response | null = null;
  for (const url of urls) {
    const response = await fetch(url);
    if (response.ok || response.status !== 404) {
      return response;
    }
    lastResponse = response;
  }
  return lastResponse || fetch(urls[0]);
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

function mapClassifierObjectRow(row: Record<string, string>): ClassifierObjectRow {
  const score = asNumber(row.class_score);
  const rowStart = firstValue(row, ["row_min", "row_start"]);
  const rowEnd = firstValue(row, ["row_max", "row_end"]);
  const columnStart = firstValue(row, ["col_min", "column_start", "col_start"]);
  const columnEnd = firstValue(row, ["col_max", "column_end", "col_end"]);
  return {
    objectId: firstValue(row, ["object_id", "object"]),
    clusterId: firstValue(row, ["cluster_id", "cluster"]),
    score,
    scoreLevel: scoreLevel(row.class_id),
    notebookLabel: notebookLabel(row.class_id),
    ruleReason: ruleReason(score, rowStart, rowEnd, columnStart, columnEnd),
    reviewOrder: reviewOrder(score),
    rowStart,
    rowEnd,
    columnStart,
    columnEnd,
  };
}

function scoreLevel(classId: string | undefined): string {
  const labels: Record<string, string> = {
    Class_A: "Very high (Class_A)",
    Class_B: "High (Class_B)",
    Class_C: "Strong (Class_C)",
    Class_D: "Medium-high (Class_D)",
    Class_E: "Medium (Class_E)",
    Class_F: "Lower-medium (Class_F)",
    Class_G: "Background (Class_G)",
  };
  return labels[classId || ""] || (classId || "Unlabeled");
}

function notebookLabel(classId: string | undefined): string {
  const labels: Record<string, string> = {
    Class_A: "ENTRANCE_SHAFT_TRACE",
    Class_B: "CHAMBER_VOID_AREA",
    Class_C: "COMPACT_CHAMBER_POINT",
    Class_D: "RING_CONTEXT_AREA",
    Class_E: "WEAK_CONTEXT_AREA",
    Class_F: "BACKGROUND_AREA",
    Class_G: "BACKGROUND_AREA",
  };
  return labels[classId || ""] || "BACKGROUND_AREA";
}

function reviewOrder(score: number): string {
  if (score >= 0.75) {
    return "01_CORE_REVIEW";
  }
  if (score >= 0.5) {
    return "02_SECONDARY_REVIEW";
  }
  return "03_BACKGROUND_REVIEW";
}

function ruleReason(score: number, rowStart: string, rowEnd: string, columnStart: string, columnEnd: string): string {
  const height = Math.max(1, asInteger(rowEnd) - asInteger(rowStart) + 1);
  const width = Math.max(1, asInteger(columnEnd) - asInteger(columnStart) + 1);
  const shape = height <= 3 && width <= 3 ? "compact" : "area-like";
  return `score=${score.toFixed(3)}; shape=${height}x${width}; ${shape}`;
}

function parseCsv(text: string): Record<string, string>[] {
  const rows = text.trim().split(/\r?\n/);
  if (rows.length < 2) {
    return [];
  }
  const headers = splitCsvLine(rows[0]);
  return rows.slice(1).map((line) => {
    const values = splitCsvLine(line);
    const mapped: Record<string, string> = {};
    headers.forEach((header, index) => {
      mapped[header] = values[index] || "";
    });
    return mapped;
  });
}

function splitCsvLine(line: string): string[] {
  const values: string[] = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"' && line[index + 1] === '"') {
      current += '"';
      index += 1;
      continue;
    }
    if (char === '"') {
      quoted = !quoted;
      continue;
    }
    if (char === "," && !quoted) {
      values.push(current);
      current = "";
      continue;
    }
    current += char;
  }
  values.push(current);
  return values;
}

function firstValue(row: Record<string, string>, keys: string[]): string {
  for (const key of keys) {
    const value = row[key];
    if (value !== undefined && value !== "") {
      return value;
    }
  }
  return "";
}

function asNumber(value: string | undefined): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function asInteger(value: string): number {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : 0;
}

function requiredNumber(value: unknown): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error("Classifier summary is unavailable.");
  }
  return value;
}

function requiredString(value: unknown): string {
  if (typeof value !== "string" || !value) {
    throw new Error("Classifier summary is unavailable.");
  }
  return value;
}
