export interface RankedAreaFinding {
  findingLabel: string;
  findingScore: number;
  scoreType: string;
  supportingCandidateCount: number;
}

export interface FinalAreaFindingsSummary {
  summaryVersion: string;
  runId: string;
  resultStatus: string;
  bestFinding: string | null;
  bestFindingScore: number | null;
  scoreType: string;
  rankedFindings: RankedAreaFinding[];
  dataQualityStatus: string;
  summaryTextEasyEnglish: string;
  depthStatus: string;
}

export interface ClassifierSummary {
  objectCount: number;
  clusterCount: number;
  classifierVersion: string;
  classCounts: Record<string, number>;
  finalAreaFindings: FinalAreaFindingsSummary | null;
}

export interface ClassifierObjectRow {
  objectId: string;
  clusterId: string;
  score: number;
  scoreLevel: string;
  findingLabel: string;
  findingReason: string;
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
  final_area_findings?: unknown;
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
    finalAreaFindings: mapFinalAreaFindings(payload.final_area_findings),
  };
}

function mapFinalAreaFindings(value: unknown): FinalAreaFindingsSummary | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  const payload = value as Record<string, unknown>;
  const rankedValue = payload.ranked_findings;
  const rankedFindings = Array.isArray(rankedValue)
    ? rankedValue
        .map(mapRankedFinding)
        .filter((item): item is RankedAreaFinding => item !== null)
    : [];

  return {
    summaryVersion: optionalString(payload.summary_version, "legacy_frontend_fallback"),
    runId: optionalString(payload.run_id, ""),
    resultStatus: optionalString(payload.result_status, "unclear_result"),
    bestFinding: nullableString(payload.best_finding),
    bestFindingScore: nullableNumber(payload.best_finding_score),
    scoreType: optionalString(payload.score_type, "app_score"),
    rankedFindings,
    dataQualityStatus: optionalString(payload.data_quality_status, "unknown"),
    summaryTextEasyEnglish: optionalString(
      payload.summary_text_easy_english,
      "The final area findings summary is unavailable for this run.",
    ),
    depthStatus: optionalString(payload.depth_status, "not_available"),
  };
}

function mapRankedFinding(value: unknown): RankedAreaFinding | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  const item = value as Record<string, unknown>;
  const findingLabel = nullableString(item.finding_label);
  const findingScore = nullableNumber(item.finding_score);
  const supportingCandidateCount = nullableNumber(item.supporting_candidate_count);
  if (!findingLabel || findingScore === null || supportingCandidateCount === null) {
    return null;
  }
  return {
    findingLabel,
    findingScore,
    scoreType: optionalString(item.score_type, "app_score"),
    supportingCandidateCount,
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
  const score = asNumber(firstValue(row, ["finding_score", "class_score"]));
  const rowStart = firstValue(row, ["row_min", "row_start"]);
  const rowEnd = firstValue(row, ["row_max", "row_end"]);
  const columnStart = firstValue(row, ["col_min", "column_start", "col_start"]);
  const columnEnd = firstValue(row, ["col_max", "column_end", "col_end"]);
  const fallback = deriveAreaFinding(score, rowStart, rowEnd, columnStart, columnEnd);
  return {
    objectId: firstValue(row, ["object_id", "object"]),
    clusterId: firstValue(row, ["cluster_id", "cluster"]),
    score,
    scoreLevel: scoreLevel(row.class_id),
    findingLabel: firstValue(row, ["finding_label"]) || fallback.findingLabel,
    findingReason: firstValue(row, ["finding_reason"]) || fallback.findingReason,
    reviewOrder: firstValue(row, ["review_order"]) || fallback.reviewOrder,
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

interface DerivedAreaFinding {
  findingLabel: string;
  findingReason: string;
  reviewOrder: string;
}

function deriveAreaFinding(
  score: number,
  rowStart: string,
  rowEnd: string,
  columnStart: string,
  columnEnd: string,
): DerivedAreaFinding {
  const height = Math.max(1, asInteger(rowEnd) - asInteger(rowStart) + 1);
  const width = Math.max(1, asInteger(columnEnd) - asInteger(columnStart) + 1);
  const longSide = Math.max(height, width);
  const shortSide = Math.max(1, Math.min(height, width));
  const elongated = longSide / shortSide >= 3;
  const compact = longSide <= 3;

  if (score >= 0.7 && elongated) {
    return {
      findingLabel: "ENTRANCE_SHAFT_TRACE",
      findingReason: `app_score=${score.toFixed(3)}; shape=${height}x${width}; elongated`,
      reviewOrder: "01_CORE_REVIEW",
    };
  }
  if (score >= 0.7 && compact) {
    return {
      findingLabel: "COMPACT_CHAMBER_POINT",
      findingReason: `app_score=${score.toFixed(3)}; shape=${height}x${width}; compact`,
      reviewOrder: "01_CORE_REVIEW",
    };
  }
  if (score >= 0.7) {
    return {
      findingLabel: "CHAMBER_VOID_AREA",
      findingReason: `app_score=${score.toFixed(3)}; shape=${height}x${width}; area-like`,
      reviewOrder: "01_CORE_REVIEW",
    };
  }
  if (score >= 0.6 && elongated) {
    return {
      findingLabel: "POSSIBLE_ENTRANCE_SHAFT",
      findingReason: `app_score=${score.toFixed(3)}; shape=${height}x${width}; elongated`,
      reviewOrder: "02_SECOND_REVIEW",
    };
  }
  if (score >= 0.6) {
    return {
      findingLabel: "POSSIBLE_CHAMBER_STRUCTURE_AREA",
      findingReason: `app_score=${score.toFixed(3)}; shape=${height}x${width}; area-like`,
      reviewOrder: "02_SECOND_REVIEW",
    };
  }
  if (score >= 0.5) {
    return {
      findingLabel: "RING_CONTEXT_AREA",
      findingReason: `app_score=${score.toFixed(3)}; compare cluster context`,
      reviewOrder: "03_CONTEXT_REVIEW",
    };
  }
  if (score >= 0.4) {
    return {
      findingLabel: "WEAK_CONTEXT_AREA",
      findingReason: `app_score=${score.toFixed(3)}; use only near stronger objects`,
      reviewOrder: "04_LATE_REVIEW",
    };
  }
  return {
    findingLabel: "BACKGROUND_AREA",
    findingReason: `app_score=${score.toFixed(3)}`,
    reviewOrder: "05_BACKGROUND",
  };
}

export function buildLegacyFinalAreaFindings(
  objects: ClassifierObjectRow[],
  runId: string,
): FinalAreaFindingsSummary | null {
  if (objects.length === 0) {
    return null;
  }
  const grouped = new Map<string, RankedAreaFinding>();
  for (const row of objects) {
    const existing = grouped.get(row.findingLabel);
    if (existing) {
      existing.findingScore = Math.max(existing.findingScore, row.score);
      existing.supportingCandidateCount += 1;
    } else {
      grouped.set(row.findingLabel, {
        findingLabel: row.findingLabel,
        findingScore: row.score,
        scoreType: "app_score",
        supportingCandidateCount: 1,
      });
    }
  }
  const rankedFindings = [...grouped.values()].sort(
    (left, right) =>
      right.findingScore - left.findingScore ||
      right.supportingCandidateCount - left.supportingCandidateCount ||
      left.findingLabel.localeCompare(right.findingLabel),
  );
  const top = rankedFindings[0];
  const topPercent = Math.round(top.findingScore * 100);
  const tiedTopFindings = rankedFindings.filter(
    (finding) => Math.abs(finding.findingScore - top.findingScore) <= 1e-9,
  );
  let resultStatus = "result_available";
  let bestFinding: string | null = top.findingLabel;
  let bestFindingScore: number | null = top.findingScore;
  let summaryTextEasyEnglish: string;

  if (top.findingScore < 0.4) {
    resultStatus = "no_strong_result";
    bestFinding = null;
    bestFindingScore = null;
    summaryTextEasyEnglish =
      `No strong result was found. The highest app score was ${topPercent}%, which is in the background range.`;
  } else if (top.findingScore < 0.6) {
    resultStatus = "unclear_result";
    summaryTextEasyEnglish =
      `The result is unclear. The strongest pattern was ${easyFindingName(top.findingLabel)} ` +
      `with an app score of ${topPercent}%, but it is only a context-level result.`;
  } else if (tiedTopFindings.length > 1) {
    resultStatus = "tied_top_result";
    const bestName = easyFindingName(top.findingLabel);
    const sentenceBestName = bestName.charAt(0).toUpperCase() + bestName.slice(1);
    summaryTextEasyEnglish =
      `The top findings are tied for the highest app score at ${topPercent}%. ` +
      `${sentenceBestName} ranks first because ${top.supportingCandidateCount} ` +
      `${top.supportingCandidateCount === 1 ? "object supports" : "objects support"} it, ` +
      "the highest support count among the tied findings. Review all tied top findings.";
  } else {
    summaryTextEasyEnglish =
      `The strongest result is ${easyFindingName(top.findingLabel)} with an app score of ${topPercent}%. ` +
      `${top.supportingCandidateCount} ${top.supportingCandidateCount === 1 ? "object supports" : "objects support"} this finding.`;
    if (rankedFindings.length > 1) {
      const second = rankedFindings[1];
      summaryTextEasyEnglish +=
        ` The next result is ${easyFindingName(second.findingLabel)} ` +
        `with an app score of ${Math.round(second.findingScore * 100)}%.`;
    }
    summaryTextEasyEnglish += " The strongest result is the first one to review.";
  }

  return {
    summaryVersion: "legacy_frontend_fallback",
    runId,
    resultStatus,
    bestFinding,
    bestFindingScore,
    scoreType: "app_score",
    rankedFindings,
    dataQualityStatus: "legacy_output_derived",
    summaryTextEasyEnglish,
    depthStatus: "not_available",
  };
}

export function easyFindingName(label: string): string {
  const names: Record<string, string> = {
    ENTRANCE_SHAFT_TRACE: "an entrance or shaft-like trace",
    COMPACT_CHAMBER_POINT: "a compact chamber-like point",
    CHAMBER_VOID_AREA: "a chamber or void-like area",
    POSSIBLE_ENTRANCE_SHAFT: "a possible entrance or shaft-like trace",
    POSSIBLE_CHAMBER_STRUCTURE_AREA: "a possible chamber or structure-like area",
    RING_CONTEXT_AREA: "a ring or context area",
    WEAK_CONTEXT_AREA: "a weak context area",
    BACKGROUND_AREA: "background variation",
  };
  return names[label] || label.replaceAll("_", " ").toLowerCase();
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

function optionalString(value: unknown, fallback: string): string {
  return typeof value === "string" && value ? value : fallback;
}

function nullableString(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}

function nullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
