export interface AnomalyObjectRow {
  objectId: string;
  clusterId: string;
  areaPixels: number;
  meanAnomaly: number;
  peakAnomaly: number;
}

export interface AnomalySummary {
  objectCount: number;
  totalAreaPixels: number;
  medianObjectMean: number | null;
  strongestPeak: number | null;
}

const OBJECTS_ARTIFACT_NAME = "objects_index";
const OBJECTS_FILENAME = "objects_index.csv";

export async function fetchAnomalyObjects(runId: string): Promise<AnomalyObjectRow[]> {
  const response = await fetch(anomalyDownloadUrl(runId));
  if (!response.ok) {
    throw new Error("Radar anomaly results are unavailable.");
  }

  return parseCsv(await response.text())
    .map(mapAnomalyObjectRow)
    .filter((row): row is AnomalyObjectRow => row !== null)
    .sort((left, right) => right.peakAnomaly - left.peakAnomaly || left.objectId.localeCompare(right.objectId));
}

export function summarizeAnomalyObjects(rows: AnomalyObjectRow[]): AnomalySummary {
  if (rows.length === 0) {
    return {
      objectCount: 0,
      totalAreaPixels: 0,
      medianObjectMean: null,
      strongestPeak: null,
    };
  }

  const means = rows.map((row) => row.meanAnomaly).sort((left, right) => left - right);
  const middle = Math.floor(means.length / 2);
  const medianObjectMean = means.length % 2 === 0
    ? (means[middle - 1] + means[middle]) / 2
    : means[middle];

  return {
    objectCount: rows.length,
    totalAreaPixels: rows.reduce((total, row) => total + row.areaPixels, 0),
    medianObjectMean,
    strongestPeak: Math.max(...rows.map((row) => row.peakAnomaly)),
  };
}

export function anomalyDownloadUrl(runId: string): string {
  return `/runs/${encodeURIComponent(runId)}/artifacts/${OBJECTS_ARTIFACT_NAME}/download/${OBJECTS_FILENAME}`;
}

function mapAnomalyObjectRow(row: Record<string, string>): AnomalyObjectRow | null {
  const meanAnomaly = finiteNumber(row.mean_anomaly);
  const peakAnomaly = finiteNumber(row.max_anomaly);
  const areaPixels = finiteNumber(row.area_px);
  if (meanAnomaly === null || peakAnomaly === null || areaPixels === null) {
    return null;
  }

  return {
    objectId: row.object_id || "",
    clusterId: row.cluster_id || "",
    areaPixels: Math.max(0, Math.trunc(areaPixels)),
    meanAnomaly,
    peakAnomaly,
  };
}

function finiteNumber(value: string | undefined): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseCsv(text: string): Record<string, string>[] {
  const lines = text.trim().split(/\r?\n/).filter((line) => line.length > 0);
  if (lines.length < 2) {
    return [];
  }

  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
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
