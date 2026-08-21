export type OperatorRecordedDepthOutcome = "completed" | "denied" | "error";

export interface OperatorRecordedDepthRecord {
  plotId: string;
  zoneId: string;
  depthStatus: string;
  recordedDepthMeanM: number | null;
  recordedDepthCi95LowM: number | null;
  recordedDepthCi95HighM: number | null;
  recordedSampleMinM: number | null;
  recordedSampleMaxM: number | null;
  recordedSampleCount: number;
  reportedDesignDepthM: number | null;
  measurementSource: string;
  measurementDate: string;
  measurementMethod: string;
  measurementTiming: string;
  depthQuality: string;
  warnings: string[];
}

export interface OperatorRecordedDepthResult {
  outcome: OperatorRecordedDepthOutcome;
  runId: string;
  status: string;
  siteId: string;
  methodKind: string;
  methodVersion: string;
  recordDatasetVersion: string;
  reviewStatus: string;
  recordedMeasurementCount: number;
  records: OperatorRecordedDepthRecord[];
  warnings: string[];
  prediction: boolean;
  interpolation: boolean;
  extrapolation: boolean;
  transferable: boolean;
  geometryReturned: boolean;
  message?: string;
}

export async function runOperatorRecordedDepth(
  runId: string,
  options?: { accessToken?: string | null },
): Promise<OperatorRecordedDepthResult> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = (options?.accessToken ?? "").trim();
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    const response = await fetch(`/runs/${encodeURIComponent(runId)}/operator/recorded-depth`, {
      method: "POST",
      headers,
      body: JSON.stringify({ operator_confirmed_review: true }),
    });
    const payload = await readJson(response);
    if (response.status === 403) return mapResult(payload, runId, "denied");
    if (!response.ok) return mapResult(payload, runId, "error");
    return mapResult(payload, runId, "completed");
  } catch (_error) {
    return errorResult(runId, "Recorded measurement lookup is temporarily unavailable.");
  }
}

export function mapResult(
  payload: unknown,
  fallbackRunId: string,
  forcedOutcome?: OperatorRecordedDepthOutcome,
): OperatorRecordedDepthResult {
  const dto = asRecord(payload);
  const outcome = forcedOutcome ?? mapOutcome(dto.outcome);
  const records = Array.isArray(dto.records)
    ? dto.records.map(mapRecord).filter((value): value is OperatorRecordedDepthRecord => value !== null)
    : [];
  return {
    outcome,
    runId: asString(dto.run_id) || fallbackRunId,
    status: asString(dto.status) || "not_available",
    siteId: asString(dto.site_id) || "",
    methodKind: asString(dto.method_kind) || "",
    methodVersion: asString(dto.method_version) || "",
    recordDatasetVersion: asString(dto.record_dataset_version) || "",
    reviewStatus: asString(dto.review_status) || "",
    recordedMeasurementCount: asNumber(dto.recorded_measurement_count),
    records,
    warnings: asStringArray(dto.warnings),
    prediction: dto.prediction === true,
    interpolation: dto.interpolation === true,
    extrapolation: dto.extrapolation === true,
    transferable: dto.transferable === true,
    geometryReturned: dto.geometry_returned === true,
    message: asString(dto.message) || undefined,
  };
}

function mapRecord(value: unknown): OperatorRecordedDepthRecord | null {
  const dto = asRecord(value);
  const plotId = asString(dto.plot_id);
  const zoneId = asString(dto.zone_id);
  if (!plotId || !zoneId) return null;
  return {
    plotId,
    zoneId,
    depthStatus: asString(dto.depth_status) || "not_available",
    recordedDepthMeanM: asNullableNumber(dto.recorded_depth_mean_m),
    recordedDepthCi95LowM: asNullableNumber(dto.recorded_depth_ci95_low_m),
    recordedDepthCi95HighM: asNullableNumber(dto.recorded_depth_ci95_high_m),
    recordedSampleMinM: asNullableNumber(dto.recorded_sample_min_m),
    recordedSampleMaxM: asNullableNumber(dto.recorded_sample_max_m),
    recordedSampleCount: asNumber(dto.recorded_sample_count),
    reportedDesignDepthM: asNullableNumber(dto.reported_design_depth_m),
    measurementSource: asString(dto.measurement_source) || "",
    measurementDate: asString(dto.measurement_date) || "",
    measurementMethod: asString(dto.measurement_method) || "",
    measurementTiming: asString(dto.measurement_timing) || "",
    depthQuality: asString(dto.depth_quality) || "",
    warnings: asStringArray(dto.warnings),
  };
}

function errorResult(runId: string, message: string): OperatorRecordedDepthResult {
  return {
    outcome: "error",
    runId,
    status: "recorded_depth_processing_failed",
    siteId: "",
    methodKind: "",
    methodVersion: "",
    recordDatasetVersion: "",
    reviewStatus: "",
    recordedMeasurementCount: 0,
    records: [],
    warnings: [],
    prediction: false,
    interpolation: false,
    extrapolation: false,
    transferable: false,
    geometryReturned: false,
    message,
  };
}

async function readJson(response: Response): Promise<unknown> {
  try { return await response.json(); } catch (_error) { return null; }
}

function mapOutcome(value: unknown): OperatorRecordedDepthOutcome {
  return value === "completed" || value === "denied" || value === "error" ? value : "error";
}
function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}
function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}
function asNumber(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}
function asNullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}
function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.length > 0) : [];
}
