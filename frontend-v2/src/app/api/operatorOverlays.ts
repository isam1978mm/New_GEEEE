export type OperatorPrivateOverlayArtifactFamily =
  | "phase_d1_private_geojson"
  | "phase_d2_private_kmz"
  | "phase_d3_private_heatmap_json";

export type OperatorPrivateOverlayOutcome = "allowed" | "not_available" | "denied" | "error";

export interface OperatorPrivateOverlayWeightSummary {
  min: number;
  max: number;
  mean: number;
}

export interface OperatorPrivateOverlayPreviewPayload {
  featureCount?: number;
  featureKinds?: string[];
  placemarkCount?: number;
  pointCount?: number;
  weightSummary?: OperatorPrivateOverlayWeightSummary | null;
}

export interface OperatorPrivateOverlayPreview {
  outcome: OperatorPrivateOverlayOutcome;
  runId: string;
  artifactFamily: OperatorPrivateOverlayArtifactFamily;
  accessMode: "operator_only_preview";
  previewType: string;
  itemCount: number | null;
  previewPayload: OperatorPrivateOverlayPreviewPayload | null;
  filesystemOnly: boolean;
  httpServable: boolean;
  downloadableViaApi: boolean;
  frontendVisible: string;
  status?: string;
  reasonCode?: string;
  requestId?: string;
  message?: string;
  retryAllowed?: boolean;
  supportReference?: string;
}

const OPERATOR_ONLY_ACCESS_MODE = "operator_only_preview";

export async function getOperatorPrivateOverlayPreview(
  runId: string,
  artifactFamily: OperatorPrivateOverlayArtifactFamily,
  options?: { accessToken?: string | null },
): Promise<OperatorPrivateOverlayPreview> {
  const query = new URLSearchParams({
    artifact_family: artifactFamily,
    access_mode: OPERATOR_ONLY_ACCESS_MODE,
  });

  const fetchOptions: RequestInit = {};
  const trimmedToken = (options?.accessToken ?? "").trim();
  if (trimmedToken) {
    fetchOptions.headers = { Authorization: `Bearer ${trimmedToken}` };
  }

  try {
    const response = await fetch(
      `/runs/${encodeURIComponent(runId)}/operator/private-overlays?${query.toString()}`,
      fetchOptions,
    );
    const payload = await readJson(response);

    if (response.status === 403) {
      return mapOperatorPrivateOverlayPreview(payload, runId, artifactFamily, "denied");
    }

    if (!response.ok) {
      return errorPreview(runId, artifactFamily, "Operator private overlay preview is temporarily unavailable.");
    }

    return mapOperatorPrivateOverlayPreview(payload, runId, artifactFamily);
  } catch (_error) {
    return errorPreview(runId, artifactFamily, "Operator private overlay preview is temporarily unavailable.");
  }
}

export function mapOperatorPrivateOverlayPreview(
  payload: unknown,
  fallbackRunId: string,
  fallbackArtifactFamily: OperatorPrivateOverlayArtifactFamily,
  forcedOutcome?: OperatorPrivateOverlayOutcome,
): OperatorPrivateOverlayPreview {
  const dto = asRecord(payload);
  const outcome = forcedOutcome ?? mapOutcome(dto.outcome);
  const artifactFamily = mapArtifactFamily(dto.artifact_family) ?? fallbackArtifactFamily;
  const previewPayload = mapPreviewPayload(dto.preview_payload);

  return {
    outcome,
    runId: asString(dto.run_id) || fallbackRunId,
    artifactFamily,
    accessMode: "operator_only_preview",
    previewType: asString(dto.preview_type) || "operator_private_overlay_preview",
    itemCount: outcome === "allowed" ? asNullableNumber(dto.item_count) : null,
    previewPayload: outcome === "allowed" ? previewPayload : null,
    filesystemOnly: asBoolean(dto.filesystem_only),
    httpServable: asBoolean(dto.http_servable),
    downloadableViaApi: asBoolean(dto.downloadable_via_api),
    frontendVisible: asString(dto.frontend_visible) || "operator_only",
    status: asString(dto.status) || undefined,
    reasonCode: asString(dto.reason_code) || undefined,
    requestId: asString(dto.request_id) || undefined,
    message: asString(dto.message) || undefined,
    retryAllowed: typeof dto.retry_allowed === "boolean" ? dto.retry_allowed : undefined,
    supportReference: asString(dto.support_reference) || undefined,
  };
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch (_error) {
    return null;
  }
}

function errorPreview(
  runId: string,
  artifactFamily: OperatorPrivateOverlayArtifactFamily,
  message: string,
): OperatorPrivateOverlayPreview {
  return {
    outcome: "error",
    runId,
    artifactFamily,
    accessMode: "operator_only_preview",
    previewType: "operator_private_overlay_preview",
    itemCount: null,
    previewPayload: null,
    filesystemOnly: true,
    httpServable: false,
    downloadableViaApi: false,
    frontendVisible: "operator_only",
    message,
  };
}

function mapOutcome(value: unknown): OperatorPrivateOverlayOutcome {
  if (value === "allowed" || value === "not_available" || value === "denied" || value === "error") {
    return value;
  }
  return "error";
}

function mapArtifactFamily(value: unknown): OperatorPrivateOverlayArtifactFamily | null {
  if (
    value === "phase_d1_private_geojson" ||
    value === "phase_d2_private_kmz" ||
    value === "phase_d3_private_heatmap_json"
  ) {
    return value;
  }
  return null;
}

function mapPreviewPayload(value: unknown): OperatorPrivateOverlayPreviewPayload | null {
  const dto = asRecord(value);
  if (Object.keys(dto).length === 0) {
    return null;
  }

  const weightSummary = asRecord(dto.weight_summary);
  return {
    featureCount: asNullableNumber(dto.feature_count) ?? undefined,
    featureKinds: Array.isArray(dto.feature_kinds) ? dto.feature_kinds.map(asString).filter(Boolean) : undefined,
    placemarkCount: asNullableNumber(dto.placemark_count) ?? undefined,
    pointCount: asNullableNumber(dto.point_count) ?? undefined,
    weightSummary:
      Object.keys(weightSummary).length > 0
        ? {
            min: asNumber(weightSummary.min),
            max: asNumber(weightSummary.max),
            mean: asNumber(weightSummary.mean),
          }
        : null,
  };
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
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
