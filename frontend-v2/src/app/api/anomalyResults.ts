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

export type RelativeDisturbanceReviewLevel = "higher" | "medium" | "lower" | "only zone";

export interface AnomalyZoneSummary {
  zoneId: string;
  objectCount: number;
  totalAreaPixels: number;
  areaShare: number;
  areaWeightedMeanAnomaly: number;
  strongestPeak: number;
  relativeDisturbanceReview: RelativeDisturbanceReviewLevel;
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

export function summarizeAnomalyZones(rows: AnomalyObjectRow[]): AnomalyZoneSummary[] {
  if (rows.length === 0) {
    return [];
  }

  const grouped = new Map<string, {
    objectCount: number;
    totalAreaPixels: number;
    weightedMeanTotal: number;
    unweightedMeanTotal: number;
    strongestPeak: number;
  }>();

  for (const row of rows) {
    const zoneId = row.clusterId.trim() || "unclustered";
    const current = grouped.get(zoneId) ?? {
      objectCount: 0,
      totalAreaPixels: 0,
      weightedMeanTotal: 0,
      unweightedMeanTotal: 0,
      strongestPeak: Number.NEGATIVE_INFINITY,
    };

    current.objectCount += 1;
    current.totalAreaPixels += row.areaPixels;
    current.weightedMeanTotal += row.meanAnomaly * row.areaPixels;
    current.unweightedMeanTotal += row.meanAnomaly;
    current.strongestPeak = Math.max(current.strongestPeak, row.peakAnomaly);
    grouped.set(zoneId, current);
  }

  const totalAreaPixels = Array.from(grouped.values())
    .reduce((total, zone) => total + zone.totalAreaPixels, 0);

  const ranked = Array.from(grouped.entries())
    .map(([zoneId, zone]) => ({
      zoneId,
      objectCount: zone.objectCount,
      totalAreaPixels: zone.totalAreaPixels,
      areaShare: totalAreaPixels > 0 ? zone.totalAreaPixels / totalAreaPixels : 0,
      areaWeightedMeanAnomaly: zone.totalAreaPixels > 0
        ? zone.weightedMeanTotal / zone.totalAreaPixels
        : zone.unweightedMeanTotal / zone.objectCount,
      strongestPeak: zone.strongestPeak,
    }))
    .sort((left, right) => (
      right.strongestPeak - left.strongestPeak
      || right.areaWeightedMeanAnomaly - left.areaWeightedMeanAnomaly
      || right.totalAreaPixels - left.totalAreaPixels
      || left.zoneId.localeCompare(right.zoneId)
    ));

  return ranked.map((zone, index) => ({
    ...zone,
    relativeDisturbanceReview: relativeReviewLevel(index, ranked.length),
  }));
}

export function anomalyDownloadUrl(runId: string): string {
  return `/runs/${encodeURIComponent(runId)}/artifacts/${OBJECTS_ARTIFACT_NAME}/download/${OBJECTS_FILENAME}`;
}

function relativeReviewLevel(index: number, zoneCount: number): RelativeDisturbanceReviewLevel {
  if (zoneCount <= 1) {
    return "only zone";
  }

  const percentile = index / (zoneCount - 1);
  if (percentile <= 0.25) {
    return "higher";
  }
  if (percentile <= 0.75) {
    return "medium";
  }
  return "lower";
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
