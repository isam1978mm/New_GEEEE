export type RunState = "done" | "running" | "failed" | "stale_failed" | "queued" | "cancelled";
export type StageStatus = "done" | "running" | "failed" | "pending" | "skipped";

export interface Run {
  id: string;
  name: string;
  state: RunState;
  stage: string;
  updated: string;
  created: string;
  diskUsageBytes: number | null;
  outputFileCount: number | null;
  lastDiskScanAt: string | null;
}

export interface Stage {
  key: string;
  label: string;
  status: StageStatus;
}

export interface StatusEvent {
  id: string;
  time: string;
  state: RunState;
  stage: string;
  message: string;
}

export interface ActivityEvent {
  id: string;
  type: "done" | "running" | "info" | "failed";
  message: string;
  detail?: string;
  time: string;
}

export interface ExportFile {
  name: string;
  path: string;
  size: string;
  sizeBytes: number;
  tag?: string;
  downloadUrl?: string;
}

export interface ExportGroup {
  key: string;
  label: string;
  fileCount: number;
  totalSize: string;
  files: ExportFile[];
  hasDownloads?: boolean;
}

export interface KeyDownload {
  label: string;
  path: string;
  size: string;
  tag?: string;
  downloadUrl?: string;
}

export interface UnavailableOutput {
  filename: string;
  path: string;
  group: string;
  status: string;
  source: string;
}

export interface RunDetail extends Run {
  detail?: string | null;
  stages: Stage[];
  history: StatusEvent[];
  artifacts: PublicArtifact[];
}

export interface PublicArtifact {
  name: string;
  artifactClass: string;
  downloadUrl: string;
}

export interface OperatorOutputTree {
  runId: string;
  outputs: ExportFile[];
  groups: ExportGroup[];
  keyDownloads: KeyDownload[];
  unavailable: UnavailableOutput[];
}

export interface CreateRunInput {
  lat: number;
  lon: number;
  name: string | null;
}

export interface RoiPreviewInput {
  lat: number;
  lon: number;
}

export interface RoiPreview {
  mode: string;
  selectedPointPreview: {
    northSouthDegrees: number;
    eastWestDegrees: number;
  };
  roiWindowPreview: {
    westMeters: number;
    southMeters: number;
    eastMeters: number;
    northMeters: number;
    widthMeters: number;
    heightMeters: number;
  };
  gridPreview: {
    referenceSystemLabel: string;
    referenceCodeValue: number;
    zoneNumber: number;
    hemisphere: string;
    widthCells: number;
    heightCells: number;
    cellSizeMeters: number;
    affineCoefficients: number[];
  };
  warnings: string[];
}

export interface EarthEnginePlanInput {
  lat: number;
  lon: number;
  acquisition_start: string;
  acquisition_end: string;
  cloud_percent_max?: number | null;
  sar_orbit?: "any" | "ascending" | "descending";
  sar_polarization?: "VV" | "VH" | "VV_VH";
  dry_run?: boolean;
}

export interface EarthEnginePlan {
  planId: string;
  mode: string;
  dryRun: boolean;
  executionStatus: string;
  authReadiness: {
    status: string;
    backendAuthConfigured: boolean;
    keyFilePresent: boolean;
    realExecutionEnabled: boolean;
  };
  acquisitionWindow: {
    start: string;
    end: string;
  };
  plannedProviderFamilies: string[];
  plannedQueryFilters: Record<string, string | number | null>;
  warnings: string[];
}

export interface DeleteRunResult {
  runId: string;
  deleted: boolean;
  deletedFilesCount: number;
  deletedDirsCount: number;
  freedBytes: number;
  status: string;
  message: string;
}

export interface DeletionAuditRecord {
  runId: string;
  runName: string | null;
  deletedAt: string;
  deletedFilesCount: number;
  deletedDirsCount: number;
  freedBytes: number;
  status: string;
  message: string;
}

export interface DeletionAuditSummary {
  totalFreedBytes: number;
  records: DeletionAuditRecord[];
}

export interface CleanupRunSuggestion {
  id: string;
  name: string;
  state: RunState;
  created: string;
  diskUsageBytes: number | null;
  outputFileCount: number | null;
  lastDiskScanAt: string | null;
}

export interface CleanupSummary {
  totalRuns: number;
  totalDiskUsageBytes: number;
  terminalRunsCount: number;
  activeRunsCount: number;
  deletedRunsCount: number;
  totalFreedBytes: number;
  largestRuns: CleanupRunSuggestion[];
  oldestTerminalRuns: CleanupRunSuggestion[];
  staleFailedRuns: CleanupRunSuggestion[];
  cleanupRecommended: boolean;
  warningReason: string;
  thresholdBytes: number;
}

export type RunListSortField = "created_at" | "updated_at" | "disk_usage_bytes" | "output_file_count" | "name" | "status";
export type RunListOrder = "asc" | "desc";
export type RunListStatusFilter = "done" | "running" | "failed" | "stale_failed" | "queued";

export interface RunListParams {
  q?: string;
  status?: RunListStatusFilter;
  sort?: RunListSortField;
  order?: RunListOrder;
  limit?: number;
  offset?: number;
}

interface RunPublicDto {
  id?: unknown;
  name?: unknown;
  status?: unknown;
  created_at?: unknown;
  detail?: unknown;
  disk_usage_bytes?: unknown;
  output_file_count?: unknown;
  last_disk_scan_at?: unknown;
}

interface RunStageDto {
  name?: unknown;
  label?: unknown;
  status?: unknown;
}

interface RunHistoryDto {
  timestamp?: unknown;
  event_type?: unknown;
  label?: unknown;
  message?: unknown;
  stage_name?: unknown;
}

interface RunDetailDto extends RunPublicDto {
  current_stage?: unknown;
  stages?: unknown;
  history?: unknown;
  artifacts?: unknown;
}

interface ArtifactDto {
  name?: unknown;
  artifact_class?: unknown;
}

interface OperatorOutputDto {
  relative_path?: unknown;
  filename?: unknown;
  directory?: unknown;
  group?: unknown;
  size_bytes?: unknown;
  status?: unknown;
  download_url?: unknown;
}

interface OperatorUnavailableDto {
  relative_path?: unknown;
  filename?: unknown;
  group?: unknown;
  status?: unknown;
  source?: unknown;
}

interface OperatorOutputTreeDto {
  run_id?: unknown;
  outputs?: unknown;
  not_implemented?: unknown;
}

interface DeleteRunDto {
  run_id?: unknown;
  deleted?: unknown;
  deleted_files_count?: unknown;
  deleted_dirs_count?: unknown;
  freed_bytes?: unknown;
  status?: unknown;
  message?: unknown;
}

interface DeletionAuditRecordDto {
  run_id?: unknown;
  run_name?: unknown;
  deleted_at?: unknown;
  deleted_files_count?: unknown;
  deleted_dirs_count?: unknown;
  freed_bytes?: unknown;
  status?: unknown;
  message?: unknown;
}

interface DeletionAuditDto {
  total_freed_bytes?: unknown;
  records?: unknown;
}

interface CleanupRunSuggestionDto extends RunPublicDto {}

interface CleanupSummaryDto {
  total_runs?: unknown;
  total_disk_usage_bytes?: unknown;
  terminal_runs_count?: unknown;
  active_runs_count?: unknown;
  deleted_runs_count?: unknown;
  total_freed_bytes?: unknown;
  largest_runs?: unknown;
  oldest_terminal_runs?: unknown;
  stale_failed_runs?: unknown;
  cleanup_recommended?: unknown;
  warning_reason?: unknown;
  threshold_bytes?: unknown;
}

interface RoiPreviewDto {
  mode?: unknown;
  selected_point_preview?: unknown;
  roi_window_preview?: unknown;
  grid_preview?: unknown;
  warnings?: unknown;
}

interface SelectedPointPreviewDto {
  north_south_degrees?: unknown;
  east_west_degrees?: unknown;
}

interface RoiWindowPreviewDto {
  west_meters?: unknown;
  south_meters?: unknown;
  east_meters?: unknown;
  north_meters?: unknown;
  width_meters?: unknown;
  height_meters?: unknown;
}

interface GridPreviewDto {
  reference_system_label?: unknown;
  reference_code_value?: unknown;
  zone_number?: unknown;
  hemisphere?: unknown;
  width_cells?: unknown;
  height_cells?: unknown;
  cell_size_meters?: unknown;
  affine_coefficients?: unknown;
}

interface EarthEnginePlanDto {
  plan_id?: unknown;
  mode?: unknown;
  dry_run?: unknown;
  execution_status?: unknown;
  auth_readiness?: unknown;
  acquisition_window?: unknown;
  planned_provider_families?: unknown;
  planned_query_filters?: unknown;
  warnings?: unknown;
}

interface EarthEngineAuthReadinessDto {
  status?: unknown;
  backend_auth_configured?: unknown;
  key_file_present?: unknown;
  real_execution_enabled?: unknown;
}

const KEY_DOWNLOAD_PATHS = [
  "QA/RUN_MANIFEST.json",
  "DEM_GEO8_TIFS/DEM_640.tif",
  "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
  "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
  "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
  "REPORT_640_FINAL_Zero_Point_Targets.tif",
  "REPORT_640_Mass_Report.tif",
  "REPORT_640_Pottery_Report.tif",
  "experimental/classifications.csv",
  "experimental/summary.json",
  "experimental/neutral_target_labels.json",
  "QA/sar/intermediates/post_rtc/final_VV_dB.npy",
];

const OUTPUT_GROUP_ORDER = [
  "AI_READY_640",
  "DEM_GEO8_TIFS",
  "GEOTIFF_RADAR_BANDS",
  "NPY_RADAR_BANDS",
  "NPY_STACKS",
  "QA",
  "REPORT_640",
  "experimental",
  "Root files",
];

export async function listRuns(params: RunListParams = {}): Promise<Run[]> {
  const query = new URLSearchParams();
  if (params.q && params.q.trim()) {
    query.set("q", params.q.trim());
  }
  if (params.status) {
    query.set("status", params.status);
  }
  if (params.sort) {
    query.set("sort", params.sort);
  }
  if (params.order) {
    query.set("order", params.order);
  }
  if (typeof params.limit === "number") {
    query.set("limit", String(params.limit));
  }
  if (typeof params.offset === "number") {
    query.set("offset", String(params.offset));
  }
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  const payload = await fetchJson<unknown>(`/runs${suffix}`);
  return Array.isArray(payload) ? payload.map(mapRunPublic).filter(Boolean) : [];
}

export async function getRunDetail(runId: string): Promise<RunDetail> {
  return mapRunDetail(await fetchJson<RunDetailDto>(`/runs/${encodeURIComponent(runId)}`));
}

export async function getOperatorOutputs(runId: string): Promise<OperatorOutputTree> {
  return mapOperatorOutputTree(await fetchJson<OperatorOutputTreeDto>(`/runs/${encodeURIComponent(runId)}/outputs`));
}

export async function createRun(input: CreateRunInput): Promise<Run> {
  const payload = await fetchJson<RunPublicDto>("/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  return mapRunPublic(payload) ?? emptyRun();
}

export async function previewRoi(input: RoiPreviewInput): Promise<RoiPreview> {
  return mapRoiPreview(
    await fetchJson<RoiPreviewDto>("/roi/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),
  );
}

export async function planEarthEngineRun(input: EarthEnginePlanInput): Promise<EarthEnginePlan> {
  return mapEarthEnginePlan(
    await fetchJson<EarthEnginePlanDto>("/earth-engine/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    }),
  );
}

export async function deleteRun(runId: string): Promise<DeleteRunResult> {
  return mapDeleteRunResult(await fetchJson<DeleteRunDto>(`/runs/${encodeURIComponent(runId)}`, { method: "DELETE" }));
}

export async function getDeletionAudit(): Promise<DeletionAuditSummary> {
  return mapDeletionAudit(await fetchJson<DeletionAuditDto>("/runs/deletion-audit"));
}

export async function getCleanupSummary(): Promise<CleanupSummary> {
  return mapCleanupSummary(await fetchJson<CleanupSummaryDto>("/runs/cleanup-summary"));
}

export function buildActivityEvents(detail: RunDetail | null): ActivityEvent[] {
  if (!detail || detail.history.length === 0) {
    return [];
  }
  return detail.history.slice(-10).reverse().map((event) => ({
    id: event.id,
    type:
      event.state === "done"
        ? "done"
        : event.state === "failed" || event.state === "stale_failed"
          ? "failed"
          : event.state === "running"
            ? "running"
            : "info",
    message: event.stage,
    detail: event.message,
    time: formatShortTime(event.time),
  }));
}

export function formatFileSize(sizeBytes: number): string {
  if (!Number.isFinite(sizeBytes) || sizeBytes < 0) {
    return "size unavailable";
  }
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }
  if (sizeBytes < 1024 * 1024) {
    return `${(sizeBytes / 1024).toFixed(1)} KB`;
  }
  if (sizeBytes < 1024 * 1024 * 1024) {
    return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(sizeBytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  let payload: unknown = null;
  try {
    payload = await response.json();
  } catch (_error) {
    payload = null;
  }
  if (!response.ok) {
    const message =
      payload && typeof payload === "object" && "message" in payload && typeof payload.message === "string"
        ? payload.message
        : "Request failed.";
    throw new Error(message);
  }
  return payload as T;
}

function mapRunPublic(payload: unknown): Run | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const dto = payload as RunPublicDto;
  const id = asString(dto.id);
  if (!id) {
    return null;
  }
  const created = asString(dto.created_at) || new Date(0).toISOString();
  const state = mapRunState(dto.status);
  return {
    id,
    name: asString(dto.name) || "Unnamed run",
    state,
    stage:
      state === "done"
        ? "Completed"
        : state === "running"
          ? "Running"
          : state === "failed"
            ? "Failed"
            : state === "stale_failed"
              ? "Stale failed"
              : state === "cancelled"
                ? "Cancelled"
                : "Queued",
    updated: created,
    created,
    diskUsageBytes: asNullableNumber(dto.disk_usage_bytes),
    outputFileCount: asNullableNumber(dto.output_file_count),
    lastDiskScanAt: asString(dto.last_disk_scan_at),
  };
}

function mapRunDetail(payload: RunDetailDto): RunDetail {
  const base = mapRunPublic(payload) ?? emptyRun();
  const stages = Array.isArray(payload.stages) ? payload.stages.map(mapStage).filter(Boolean) : [];
  const currentStage = asString(payload.current_stage);
  const history = Array.isArray(payload.history) ? payload.history.map(mapHistoryEvent).filter(Boolean) : [];
  const artifacts = Array.isArray(payload.artifacts) ? payload.artifacts.map((item) => mapArtifact(base.id, item)).filter(Boolean) : [];
  return {
    ...base,
    stage: currentStage ? stageLabelFromKey(currentStage, stages) : base.stage,
    detail: asString(payload.detail),
    stages,
    history,
    artifacts,
  };
}

function mapCleanupRunSuggestion(payload: unknown): CleanupRunSuggestion | null {
  const run = mapRunPublic(payload);
  if (!run) {
    return null;
  }
  return {
    id: run.id,
    name: run.name,
    state: run.state,
    created: run.created,
    diskUsageBytes: run.diskUsageBytes,
    outputFileCount: run.outputFileCount,
    lastDiskScanAt: run.lastDiskScanAt,
  };
}

function mapStage(payload: unknown): Stage | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const dto = payload as RunStageDto;
  const key = asString(dto.name);
  const label = asString(dto.label);
  if (!key || !label) {
    return null;
  }
  return { key, label: shortStageLabel(label), status: mapStageStatus(dto.status) };
}

function mapHistoryEvent(payload: unknown, index: number): StatusEvent | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const dto = payload as RunHistoryDto;
  const timestamp = asString(dto.timestamp) || new Date(0).toISOString();
  const label = asString(dto.label) || asString(dto.event_type) || "Status update";
  const message = asString(dto.message) || label;
  return {
    id: `${timestamp}-${index}`,
    time: timestamp,
    state: stateFromEventType(asString(dto.event_type)),
    stage: asString(dto.stage_name) || label,
    message,
  };
}

function mapArtifact(runId: string, payload: unknown): PublicArtifact | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const dto = payload as ArtifactDto;
  const name = asString(dto.name);
  if (!name) {
    return null;
  }
  const downloadName = artifactDownloadName(name);
  return {
    name: downloadName,
    artifactClass: asString(dto.artifact_class) || "REDACTED_PUBLIC",
    downloadUrl: `/runs/${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(name)}/download/${encodeURIComponent(downloadName)}`,
  };
}

function mapOperatorOutputTree(payload: OperatorOutputTreeDto): OperatorOutputTree {
  const runId = asString(payload.run_id) || "";
  const outputs = Array.isArray(payload.outputs) ? payload.outputs.map(mapOperatorOutput).filter(Boolean) : [];
  const unavailable = Array.isArray(payload.not_implemented)
    ? payload.not_implemented.map(mapUnavailableOutput).filter(Boolean)
    : [];
  const groups = groupOutputs(outputs);
  const byPath = new Map(outputs.map((output) => [output.path, output]));
  const keyDownloads = KEY_DOWNLOAD_PATHS.map((path) => byPath.get(path))
    .filter(Boolean)
    .map((output) => ({
      label: output.name,
      path: output.path,
      size: output.size,
      tag: output.tag,
      downloadUrl: output.downloadUrl,
    }));
  return { runId, outputs, groups, keyDownloads, unavailable };
}

function mapDeleteRunResult(payload: DeleteRunDto): DeleteRunResult {
  return {
    runId: asString(payload.run_id) || "",
    deleted: payload.deleted === true,
    deletedFilesCount: asNumber(payload.deleted_files_count),
    deletedDirsCount: asNumber(payload.deleted_dirs_count),
    freedBytes: asNumber(payload.freed_bytes),
    status: asString(payload.status) || "unknown",
    message: asString(payload.message) || "Run deleted.",
  };
}

function mapDeletionAudit(payload: DeletionAuditDto): DeletionAuditSummary {
  const records = Array.isArray(payload.records) ? payload.records.map(mapDeletionAuditRecord).filter(Boolean) : [];
  return {
    totalFreedBytes: asNumber(payload.total_freed_bytes),
    records,
  };
}

function mapCleanupSummary(payload: CleanupSummaryDto): CleanupSummary {
  return {
    totalRuns: asNullableNumber(payload.total_runs) ?? 0,
    totalDiskUsageBytes: asNullableNumber(payload.total_disk_usage_bytes) ?? 0,
    terminalRunsCount: asNullableNumber(payload.terminal_runs_count) ?? 0,
    activeRunsCount: asNullableNumber(payload.active_runs_count) ?? 0,
    deletedRunsCount: asNullableNumber(payload.deleted_runs_count) ?? 0,
    totalFreedBytes: asNullableNumber(payload.total_freed_bytes) ?? 0,
    largestRuns: Array.isArray(payload.largest_runs) ? payload.largest_runs.map(mapCleanupRunSuggestion).filter(Boolean) : [],
    oldestTerminalRuns: Array.isArray(payload.oldest_terminal_runs) ? payload.oldest_terminal_runs.map(mapCleanupRunSuggestion).filter(Boolean) : [],
    staleFailedRuns: Array.isArray(payload.stale_failed_runs) ? payload.stale_failed_runs.map(mapCleanupRunSuggestion).filter(Boolean) : [],
    cleanupRecommended: payload.cleanup_recommended === true,
    warningReason: asString(payload.warning_reason) || "Storage healthy.",
    thresholdBytes: asNullableNumber(payload.threshold_bytes) ?? 0,
  };
}

function mapRoiPreview(payload: RoiPreviewDto): RoiPreview {
  const selected = asObject<SelectedPointPreviewDto>(payload.selected_point_preview);
  const roiWindow = asObject<RoiWindowPreviewDto>(payload.roi_window_preview);
  const grid = asObject<GridPreviewDto>(payload.grid_preview);
  return {
    mode: asString(payload.mode) || "point",
    selectedPointPreview: {
      northSouthDegrees: asNumber(selected.north_south_degrees),
      eastWestDegrees: asNumber(selected.east_west_degrees),
    },
    roiWindowPreview: {
      westMeters: asNumber(roiWindow.west_meters),
      southMeters: asNumber(roiWindow.south_meters),
      eastMeters: asNumber(roiWindow.east_meters),
      northMeters: asNumber(roiWindow.north_meters),
      widthMeters: asNumber(roiWindow.width_meters),
      heightMeters: asNumber(roiWindow.height_meters),
    },
    gridPreview: {
      referenceSystemLabel: asString(grid.reference_system_label) || "unavailable",
      referenceCodeValue: asNumber(grid.reference_code_value),
      zoneNumber: asNumber(grid.zone_number),
      hemisphere: asString(grid.hemisphere) || "unknown",
      widthCells: asNumber(grid.width_cells),
      heightCells: asNumber(grid.height_cells),
      cellSizeMeters: asNumber(grid.cell_size_meters),
      affineCoefficients: Array.isArray(grid.affine_coefficients)
        ? grid.affine_coefficients.map(asNumber)
        : [],
    },
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(asString).filter(Boolean) : [],
  };
}

function mapEarthEnginePlan(payload: EarthEnginePlanDto): EarthEnginePlan {
  const auth = asObject<EarthEngineAuthReadinessDto>(payload.auth_readiness);
  const acquisitionWindow = asRecord(payload.acquisition_window);
  const plannedFilters = asRecord(payload.planned_query_filters);
  const filters: Record<string, string | number | null> = {};
  for (const [key, value] of Object.entries(plannedFilters)) {
    if (typeof value === "string" || typeof value === "number" || value === null) {
      filters[key] = value;
    }
  }
  return {
    planId: asString(payload.plan_id) || "",
    mode: asString(payload.mode) || "controlled_earth_engine_planning",
    dryRun: payload.dry_run !== false,
    executionStatus: asString(payload.execution_status) || "auth_not_configured",
    authReadiness: {
      status: asString(auth.status) || "auth_not_configured",
      backendAuthConfigured: auth.backend_auth_configured === true,
      keyFilePresent: auth.key_file_present === true,
      realExecutionEnabled: auth.real_execution_enabled === true,
    },
    acquisitionWindow: {
      start: asString(acquisitionWindow.start) || "",
      end: asString(acquisitionWindow.end) || "",
    },
    plannedProviderFamilies: Array.isArray(payload.planned_provider_families)
      ? payload.planned_provider_families.map(asString).filter(Boolean)
      : [],
    plannedQueryFilters: filters,
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(asString).filter(Boolean) : [],
  };
}

function mapDeletionAuditRecord(payload: unknown): DeletionAuditRecord | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const dto = payload as DeletionAuditRecordDto;
  const runId = asString(dto.run_id);
  const deletedAt = asString(dto.deleted_at);
  if (!runId || !deletedAt) {
    return null;
  }
  return {
    runId,
    runName: asString(dto.run_name),
    deletedAt,
    deletedFilesCount: asNumber(dto.deleted_files_count),
    deletedDirsCount: asNumber(dto.deleted_dirs_count),
    freedBytes: asNumber(dto.freed_bytes),
    status: asString(dto.status) || "deleted",
    message: asString(dto.message) || "Run deleted.",
  };
}

function mapOperatorOutput(payload: unknown): ExportFile | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const dto = payload as OperatorOutputDto;
  const relativePath = asString(dto.relative_path);
  const filename = asString(dto.filename);
  const downloadUrl = asString(dto.download_url);
  if (!relativePath || !filename || !downloadUrl) {
    return null;
  }
  const sizeBytes = asNumber(dto.size_bytes);
  return {
    name: filename,
    path: relativePath,
    size: formatFileSize(sizeBytes),
    sizeBytes,
    tag: asString(dto.status) || "implemented",
    downloadUrl,
  };
}

function mapUnavailableOutput(payload: unknown): UnavailableOutput | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }
  const dto = payload as OperatorUnavailableDto;
  const path = asString(dto.relative_path);
  const filename = asString(dto.filename);
  if (!path || !filename) {
    return null;
  }
  return {
    filename,
    path,
    group: asString(dto.group) || groupForPath(path),
    status: asString(dto.status) || "unavailable",
    source: asString(dto.source) || "not reported",
  };
}

function groupOutputs(outputs: ExportFile[]): ExportGroup[] {
  const groups = new Map<string, ExportFile[]>();
  for (const output of outputs) {
    const label = groupForPath(output.path);
    groups.set(label, [...(groups.get(label) ?? []), output]);
  }
  return Array.from(groups.entries())
    .sort(([left], [right]) => sortGroups(left, right))
    .map(([label, files]) => {
      const sortedFiles = files.slice().sort((left, right) => left.path.localeCompare(right.path));
      const totalBytes = sortedFiles.reduce((sum, file) => sum + file.sizeBytes, 0);
      return {
        key: label,
        label,
        fileCount: sortedFiles.length,
        totalSize: formatFileSize(totalBytes),
        files: sortedFiles,
        hasDownloads: sortedFiles.some((file) => Boolean(file.downloadUrl)),
      };
    });
}

function groupForPath(path: string): string {
  if (path.startsWith("REPORT_640_")) {
    return "REPORT_640";
  }
  if (!path.includes("/")) {
    return "Root files";
  }
  return path.split("/")[0] || "Other";
}

function sortGroups(left: string, right: string): number {
  const leftIndex = OUTPUT_GROUP_ORDER.indexOf(left);
  const rightIndex = OUTPUT_GROUP_ORDER.indexOf(right);
  if (leftIndex !== -1 || rightIndex !== -1) {
    if (leftIndex === -1) return 1;
    if (rightIndex === -1) return -1;
    return leftIndex - rightIndex;
  }
  return left.localeCompare(right);
}

function mapRunState(value: unknown): RunState {
  if (value === "done" || value === "running" || value === "queued" || value === "cancelled" || value === "stale_failed") {
    return value;
  }
  if (value === "failed") {
    return "failed";
  }
  return "queued";
}

function mapStageStatus(value: unknown): StageStatus {
  if (value === "done" || value === "running" || value === "failed" || value === "skipped") {
    return value;
  }
  return "pending";
}

function stateFromEventType(eventType: string | null): RunState {
  if (!eventType) {
    return "queued";
  }
  if (eventType.includes("stale_failed")) {
    return "stale_failed";
  }
  if (eventType.includes("failed")) {
    return "failed";
  }
  if (eventType.includes("done")) {
    return "done";
  }
  if (eventType.includes("started")) {
    return "running";
  }
  return "queued";
}

function shortStageLabel(label: string): string {
  const map: Record<string, string> = {
    "GRID setup": "GRID",
    "Sentinel-2 indices": "S2",
    "DEM derivatives": "DEM deriv.",
    "Object extraction": "Objects",
    "Alignment QA": "Align QA",
    "Location exports": "Locations",
    "Field ops exports": "Field ops",
    "GPS comparison": "GPS",
    "PCA anomaly": "PCA",
    "Report 640": "Rpt640",
    "Feature stacks": "Stacks",
    "Focus mask": "Focus",
    "Zero shift": "Zero",
    "SAR RTC": "SAR",
    "Secret layers": "Secret",
  };
  return map[label] || label;
}

function stageLabelFromKey(key: string, stages: Stage[]): string {
  return stages.find((stage) => stage.key === key)?.label || key;
}

function artifactDownloadName(name: string): string {
  const map: Record<string, string> = {
    objects_index: "objects_index.csv",
    clusters_summary: "clusters_summary.csv",
    alignment_qa: "alignment_qa.json",
    alignment_audit: "alignment_audit.json",
    alignment_mask_selection: "alignment_mask_selection.json",
    experimental_classifications: "classifications.csv",
    experimental_summary: "summary.json",
    experimental_neutral_labels: "neutral_target_labels.json",
  };
  return map[name] || name;
}

function formatShortTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
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

function asObject<T extends object>(value: unknown): Partial<T> {
  return value && typeof value === "object" ? (value as Partial<T>) : {};
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function emptyRun(): Run {
  return {
    id: "Not started",
    name: "No run selected",
    state: "queued",
    stage: "Queued",
    updated: new Date(0).toISOString(),
    created: new Date(0).toISOString(),
    diskUsageBytes: null,
    outputFileCount: null,
    lastDiskScanAt: null,
  };
}
