export type OperatorLocalDepthOutcome = "completed" | "not_available" | "denied" | "error";

export interface OperatorLocalDepthEstimate {
  candidateId: string;
  depthStatus: string;
  estimatedDepthMinM: number | null;
  estimatedDepthBestM: number | null;
  estimatedDepthMaxM: number | null;
  depthQuality: string;
  warnings: string[];
}

export interface OperatorLocalDepthResult {
  outcome: OperatorLocalDepthOutcome;
  runId: string;
  status: string;
  siteId: string;
  methodKind: string;
  methodVersion: string;
  calibrationDatasetVersion: string;
  runQualityStatus: string;
  anchorCount: number;
  candidateCount: number;
  estimatedCount: number;
  insufficientDataCount: number;
  notAvailableCount: number;
  estimates: OperatorLocalDepthEstimate[];
  warnings: string[];
  filesystemOnly: boolean;
  httpServable: boolean;
  geometryReturned: boolean;
  localOnly: boolean;
  transferable: boolean;
  appDepthEnabledByDefault: boolean;
  automaticFindingCandidates: boolean;
  resultsAttachedToFindings: boolean;
  message?: string;
  requestId?: string;
  supportReference?: string;
}

export interface OperatorLocalDepthInput {
  geojson: Record<string, unknown>;
  siteId: string;
  calibrationDatasetVersion: string;
  methodVersion?: string;
  inputCrs?: string;
  erosionPixels?: number;
  minimumValidPixels?: number;
  allowRunQualityWarning?: boolean;
  force?: boolean;
  operatorConfirmedReview: boolean;
}

export async function fetchOperatorLocalDepthResult(
  runId: string,
  options?: { accessToken?: string | null },
): Promise<OperatorLocalDepthResult> {
  const headers = authorizationHeaders(options?.accessToken);
  try {
    const response = await fetch(`/runs/${encodeURIComponent(runId)}/operator/local-depth`, {
      headers,
    });
    const payload = await readJson(response);
    if (response.status === 403) {
      return mapResult(payload, runId, "denied");
    }
    if (!response.ok) {
      return mapResult(payload, runId, "error");
    }
    return mapResult(payload, runId);
  } catch (_error) {
    return errorResult(runId, "Finding-depth results are temporarily unavailable.");
  }
}

export async function runOperatorLocalDepth(
  runId: string,
  input: OperatorLocalDepthInput,
  options?: { accessToken?: string | null },
): Promise<OperatorLocalDepthResult> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...authorizationHeaders(options?.accessToken),
  };

  try {
    const response = await fetch(`/runs/${encodeURIComponent(runId)}/operator/local-depth`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        geojson: input.geojson,
        site_id: input.siteId,
        calibration_dataset_version: input.calibrationDatasetVersion,
        method_version: input.methodVersion ?? "operator_local_depth_app_v2",
        input_crs: input.inputCrs ?? "EPSG:4326",
        erosion_pixels: input.erosionPixels ?? 2,
        minimum_valid_pixels: input.minimumValidPixels ?? 20,
        allow_run_quality_warning: input.allowRunQualityWarning === true,
        force: input.force === true,
        operator_confirmed_review: input.operatorConfirmedReview,
      }),
    });
    const payload = await readJson(response);
    if (response.status === 403) {
      return mapResult(payload, runId, "denied");
    }
    if (!response.ok) {
      return mapResult(payload, runId, "error");
    }
    return mapResult(payload, runId, "completed");
  } catch (_error) {
    return errorResult(runId, "Finding-depth processing is temporarily unavailable.");
  }
}

export function mapResult(
  payload: unknown,
  fallbackRunId: string,
  forcedOutcome?: OperatorLocalDepthOutcome,
): OperatorLocalDepthResult {
  const dto = asRecord(payload);
  const estimates = Array.isArray(dto.estimates)
    ? dto.estimates.map(mapEstimate).filter((value): value is OperatorLocalDepthEstimate => value !== null)
    : [];
  const outcome = forcedOutcome ?? mapOutcome(dto.outcome);
  return {
    outcome,
    runId: asString(dto.run_id) || fallbackRunId,
    status: asString(dto.status) || (outcome === "completed" ? "completed" : "unavailable"),
    siteId: asString(dto.site_id) || "",
    methodKind: asString(dto.method_kind) || "",
    methodVersion: asString(dto.method_version) || "",
    calibrationDatasetVersion: asString(dto.calibration_dataset_version) || "",
    runQualityStatus: asString(dto.run_quality_status) || "",
    anchorCount: asNumber(dto.anchor_count),
    candidateCount: asNumber(dto.candidate_count),
    estimatedCount: asNumber(dto.estimated_count),
    insufficientDataCount: asNumber(dto.insufficient_data_count),
    notAvailableCount: asNumber(dto.not_available_count),
    estimates,
    warnings: asStringArray(dto.warnings),
    filesystemOnly: dto.filesystem_only === true,
    httpServable: dto.http_servable === true,
    geometryReturned: dto.geometry_returned === true,
    localOnly: dto.local_only === true,
    transferable: dto.transferable === true,
    appDepthEnabledByDefault: dto.app_depth_enabled_by_default === true,
    automaticFindingCandidates: dto.automatic_finding_candidates === true,
    resultsAttachedToFindings: dto.results_attached_to_findings === true,
    message: asString(dto.message) || undefined,
    requestId: asString(dto.request_id) || undefined,
    supportReference: asString(dto.support_reference) || undefined,
  };
}

function mapEstimate(value: unknown): OperatorLocalDepthEstimate | null {
  const dto = asRecord(value);
  const candidateId = asString(dto.candidate_id);
  if (!candidateId) {
    return null;
  }
  return {
    candidateId,
    depthStatus: asString(dto.depth_status) || "not_available",
    estimatedDepthMinM: asNullableNumber(dto.estimated_depth_min_m),
    estimatedDepthBestM: asNullableNumber(dto.estimated_depth_best_m),
    estimatedDepthMaxM: asNullableNumber(dto.estimated_depth_max_m),
    depthQuality: asString(dto.depth_quality) || "",
    warnings: asStringArray(dto.warnings),
  };
}

function authorizationHeaders(accessToken?: string | null): Record<string, string> {
  const token = (accessToken ?? "").trim();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function errorResult(runId: string, message: string): OperatorLocalDepthResult {
  return {
    outcome: "error",
    runId,
    status: "local_depth_processing_failed",
    siteId: "",
    methodKind: "",
    methodVersion: "",
    calibrationDatasetVersion: "",
    runQualityStatus: "",
    anchorCount: 0,
    candidateCount: 0,
    estimatedCount: 0,
    insufficientDataCount: 0,
    notAvailableCount: 0,
    estimates: [],
    warnings: [],
    filesystemOnly: true,
    httpServable: false,
    geometryReturned: false,
    localOnly: true,
    transferable: false,
    appDepthEnabledByDefault: false,
    automaticFindingCandidates: true,
    resultsAttachedToFindings: true,
    message,
  };
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch (_error) {
    return null;
  }
}

function mapOutcome(value: unknown): OperatorLocalDepthOutcome {
  return value === "completed" ||
    value === "not_available" ||
    value === "denied" ||
    value === "error"
    ? value
    : "error";
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
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
