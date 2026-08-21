export type OperatorReviewedZoneDepthOutcome = "completed" | "denied" | "error";

export interface OperatorReviewedZoneDepthEstimate {
  candidateId: string;
  zoneId: string;
  depthStatus: string;
  estimatedDepthMinM: number | null;
  estimatedDepthBestM: number | null;
  estimatedDepthMaxM: number | null;
  depthQuality: string;
  warnings: string[];
}

export interface OperatorReviewedZoneDepthResult {
  outcome: OperatorReviewedZoneDepthOutcome;
  runId: string;
  status: string;
  siteId: string;
  methodKind: string;
  methodVersion: string;
  calibrationDatasetVersion: string;
  validationStatus: string;
  runQualityStatus: string;
  candidateCount: number;
  spatialMatchCount: number;
  estimatedCount: number;
  notAvailableCount: number;
  insufficientDataCount: number;
  estimates: OperatorReviewedZoneDepthEstimate[];
  warnings: string[];
  message?: string;
}

export async function runOperatorReviewedZoneDepth(
  runId: string,
  input: { operatorConfirmedReview: boolean },
  options?: { accessToken?: string | null },
): Promise<OperatorReviewedZoneDepthResult> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = (options?.accessToken ?? "").trim();
  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    const response = await fetch(`/runs/${encodeURIComponent(runId)}/operator/reviewed-zone-depth`, {
      method: "POST",
      headers,
      body: JSON.stringify({ operator_confirmed_review: input.operatorConfirmedReview }),
    });
    const payload = await readJson(response);
    if (response.status === 403) return mapResult(payload, runId, "denied");
    if (!response.ok) return mapResult(payload, runId, "error");
    return mapResult(payload, runId, "completed");
  } catch (_error) {
    return errorResult(runId, "Reviewed-zone depth processing is temporarily unavailable.");
  }
}

function mapResult(
  payload: unknown,
  fallbackRunId: string,
  forcedOutcome?: OperatorReviewedZoneDepthOutcome,
): OperatorReviewedZoneDepthResult {
  const dto = asRecord(payload);
  const estimates = Array.isArray(dto.estimates)
    ? dto.estimates.map(mapEstimate).filter((value): value is OperatorReviewedZoneDepthEstimate => value !== null)
    : [];
  return {
    outcome: forcedOutcome ?? mapOutcome(dto.outcome),
    runId: asString(dto.run_id) || fallbackRunId,
    status: asString(dto.status) || "not_available",
    siteId: asString(dto.site_id) || "",
    methodKind: asString(dto.method_kind) || "",
    methodVersion: asString(dto.method_version) || "",
    calibrationDatasetVersion: asString(dto.calibration_dataset_version) || "",
    validationStatus: asString(dto.validation_status) || "provisional",
    runQualityStatus: asString(dto.run_quality_status) || "UNKNOWN",
    candidateCount: asNumber(dto.candidate_count),
    spatialMatchCount: asNumber(dto.spatial_match_count),
    estimatedCount: asNumber(dto.estimated_count),
    notAvailableCount: asNumber(dto.not_available_count),
    insufficientDataCount: asNumber(dto.insufficient_data_count),
    estimates,
    warnings: asStringArray(dto.warnings),
    message: asString(dto.message) || undefined,
  };
}

function mapEstimate(value: unknown): OperatorReviewedZoneDepthEstimate | null {
  const dto = asRecord(value);
  const candidateId = asString(dto.candidate_id);
  if (!candidateId) return null;
  return {
    candidateId,
    zoneId: asString(dto.zone_id) || "",
    depthStatus: asString(dto.depth_status) || "not_available",
    estimatedDepthMinM: asNullableNumber(dto.estimated_depth_min_m),
    estimatedDepthBestM: asNullableNumber(dto.estimated_depth_best_m),
    estimatedDepthMaxM: asNullableNumber(dto.estimated_depth_max_m),
    depthQuality: asString(dto.depth_quality) || "not_available",
    warnings: asStringArray(dto.warnings),
  };
}

function errorResult(runId: string, message: string): OperatorReviewedZoneDepthResult {
  return {
    outcome: "error",
    runId,
    status: "reviewed_zone_depth_processing_failed",
    siteId: "",
    methodKind: "",
    methodVersion: "",
    calibrationDatasetVersion: "",
    validationStatus: "provisional",
    runQualityStatus: "UNKNOWN",
    candidateCount: 0,
    spatialMatchCount: 0,
    estimatedCount: 0,
    notAvailableCount: 0,
    insufficientDataCount: 0,
    estimates: [],
    warnings: [],
    message,
  };
}

async function readJson(response: Response): Promise<unknown> {
  try { return await response.json(); } catch (_error) { return null; }
}
function mapOutcome(value: unknown): OperatorReviewedZoneDepthOutcome {
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
