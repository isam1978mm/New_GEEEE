export type H5OperatorSummaryOutcome = "allowed" | "denied" | "not_available" | "error";

export interface H5OperatorAggregateSummary {
  status: string;
  pipelineStage: string;
  featureSetType: string;
  trainingType: string;
  totalRowCount: number;
  featureMatrixRows: number;
  featureColumnCount: number;
  scoreMin: number | null;
  scoreMax: number | null;
  scoreMean: number | null;
  rowsBySource: Record<string, number>;
  rowsBySplit: Record<string, number>;
  scoreBandCounts: Record<string, number>;
  scoreBandCountsStatus: string;
  predictionFilesWritten: boolean;
  apiFrontendChanged: boolean;
  overlaysCreated: boolean;
  rowLevelOutputIncluded: boolean;
  privatePathsIncluded: boolean;
}

export interface H5OperatorSummaryResponse {
  outcome: H5OperatorSummaryOutcome;
  accessMode: string;
  summary: H5OperatorAggregateSummary | null;
  httpServable: boolean;
  downloadableViaApi: boolean;
  rowLevelOutputIncluded: boolean;
  apiFrontendChanged: boolean;
  overlaysCreated: boolean;
  status?: string;
  reasonCode?: string;
  requestId?: string;
  message?: string;
}

export async function getH5OperatorAggregateSummary(options?: { accessToken?: string | null }): Promise<H5OperatorSummaryResponse> {
  const fetchOptions: RequestInit = {};
  const trimmedToken = (options?.accessToken ?? "").trim();
  if (trimmedToken) {
    fetchOptions.headers = { Authorization: `Bearer ${trimmedToken}` };
  }

  try {
    const response = await fetch("/operator/h5/aggregate-summary", fetchOptions);
    const payload = await readJson(response);
    if (response.status === 403) {
      return mapH5OperatorSummaryResponse(payload, "denied");
    }
    if (!response.ok) {
      return errorResponse("Operator aggregate summary is temporarily unavailable.");
    }
    return mapH5OperatorSummaryResponse(payload);
  } catch (_error) {
    return errorResponse("Operator aggregate summary is temporarily unavailable.");
  }
}

function mapH5OperatorSummaryResponse(payload: unknown, forcedOutcome?: H5OperatorSummaryOutcome): H5OperatorSummaryResponse {
  const dto = asRecord(payload);
  const outcome = forcedOutcome ?? mapOutcome(dto.outcome);
  return {
    outcome,
    accessMode: asString(dto.access_mode) || "operator_only_aggregate",
    summary: outcome === "allowed" ? mapAggregateSummary(dto.summary) : null,
    httpServable: asBoolean(dto.http_servable),
    downloadableViaApi: asBoolean(dto.downloadable_via_api),
    rowLevelOutputIncluded: asBoolean(dto.row_level_output_included),
    apiFrontendChanged: asBoolean(dto.api_frontend_changed),
    overlaysCreated: asBoolean(dto.overlays_created),
    status: asString(dto.status) || undefined,
    reasonCode: asString(dto.reason_code) || undefined,
    requestId: asString(dto.request_id) || undefined,
    message: asString(dto.message) || undefined,
  };
}

function mapAggregateSummary(value: unknown): H5OperatorAggregateSummary {
  const dto = asRecord(value);
  return {
    status: asString(dto.status) || "unknown",
    pipelineStage: asString(dto.pipeline_stage) || "h5_operator_aggregate_summary",
    featureSetType: asString(dto.feature_set_type) || "unknown",
    trainingType: asString(dto.training_type) || "unknown",
    totalRowCount: asNumber(dto.total_row_count),
    featureMatrixRows: asNumber(dto.feature_matrix_rows),
    featureColumnCount: asNumber(dto.feature_column_count),
    scoreMin: asNullableNumber(dto.score_min),
    scoreMax: asNullableNumber(dto.score_max),
    scoreMean: asNullableNumber(dto.score_mean),
    rowsBySource: asNumberRecord(dto.rows_by_source),
    rowsBySplit: asNumberRecord(dto.rows_by_split),
    scoreBandCounts: asNumberRecord(dto.score_band_counts),
    scoreBandCountsStatus: asString(dto.score_band_counts_status) || "not_available_from_aggregate_summary",
    predictionFilesWritten: asBoolean(dto.prediction_files_written),
    apiFrontendChanged: asBoolean(dto.api_frontend_changed),
    overlaysCreated: asBoolean(dto.overlays_created),
    rowLevelOutputIncluded: asBoolean(dto.row_level_output_included),
    privatePathsIncluded: asBoolean(dto.private_paths_included),
  };
}

function errorResponse(message: string): H5OperatorSummaryResponse {
  return {
    outcome: "error",
    accessMode: "operator_only_aggregate",
    summary: null,
    httpServable: false,
    downloadableViaApi: false,
    rowLevelOutputIncluded: false,
    apiFrontendChanged: false,
    overlaysCreated: false,
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

function mapOutcome(value: unknown): H5OperatorSummaryOutcome {
  if (value === "allowed" || value === "denied" || value === "not_available" || value === "error") {
    return value;
  }
  return "error";
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asNumberRecord(value: unknown): Record<string, number> {
  const record = asRecord(value);
  const output: Record<string, number> = {};
  for (const [key, item] of Object.entries(record)) {
    output[key] = asNumber(item);
  }
  return output;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function asNumber(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function asNullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asBoolean(value: unknown): boolean {
  return value === true;
}
