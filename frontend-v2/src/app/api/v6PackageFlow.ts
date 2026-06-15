export type V6PackageOutcome = "generated" | "available" | "not_available" | "denied" | "invalid_package_inputs" | "error";

export interface V6PackageStatus {
  outcome: V6PackageOutcome;
  runId: string;
  requestId?: string;
  packageReady: boolean;
  validationStatus?: string;
  payloadCount?: number;
  zipEntryCount?: number;
  categoryCounts?: Record<string, number>;
  issueCount?: number;
  warningCount?: number;
  zipFilename?: string;
  inventoryFilename?: string;
  validationReportFilename?: string;
  message?: string;
  supportReference?: string;
}

export interface V6PackageRetrieveResult {
  status: V6PackageStatus;
  blob?: Blob;
  filename?: string;
}

export async function generateV6Package(runId: string, options?: { accessToken?: string | null }): Promise<V6PackageStatus> {
  return requestV6PackageStatus(`/runs/${encodeURIComponent(runId)}/operator/v6/package/generate`, runId, {
    method: "POST",
    ...operatorFetchOptions(options),
  });
}

export async function reviewV6Package(runId: string, options?: { accessToken?: string | null }): Promise<V6PackageStatus> {
  return requestV6PackageStatus(
    `/runs/${encodeURIComponent(runId)}/operator/v6/package/review`,
    runId,
    operatorFetchOptions(options),
  );
}

export async function retrieveV6Package(
  runId: string,
  options?: { accessToken?: string | null },
): Promise<V6PackageRetrieveResult> {
  try {
    const response = await fetch(`/runs/${encodeURIComponent(runId)}/operator/v6/package/download`, operatorFetchOptions(options));
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const payload = await readJson(response);
      return { status: mapV6PackageStatus(payload, runId, response.status === 403 ? "denied" : undefined) };
    }
    if (!response.ok) {
      return { status: errorStatus(runId, "Paid Imagery Request Package is temporarily unavailable.") };
    }
    const blob = await response.blob();
    const filename = filenameFromContentDisposition(response.headers.get("content-disposition")) || "V6_REAL_GENERATED.zip";
    return {
      status: {
        outcome: "available",
        runId,
        packageReady: true,
        zipFilename: filename,
      },
      blob,
      filename,
    };
  } catch (_error) {
    return { status: errorStatus(runId, "Paid Imagery Request Package is temporarily unavailable.") };
  }
}

export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function requestV6PackageStatus(url: string, fallbackRunId: string, init?: RequestInit): Promise<V6PackageStatus> {
  try {
    const response = await fetch(url, init);
    const payload = await readJson(response);
    if (response.status === 403) {
      return mapV6PackageStatus(payload, fallbackRunId, "denied");
    }
    if (!response.ok) {
      const mapped = mapV6PackageStatus(payload, fallbackRunId);
      if (mapped.outcome === "invalid_package_inputs") {
        return mapped;
      }
      return errorStatus(fallbackRunId, "Paid Imagery Request Package status is temporarily unavailable.");
    }
    return mapV6PackageStatus(payload, fallbackRunId);
  } catch (_error) {
    return errorStatus(fallbackRunId, "Paid Imagery Request Package status is temporarily unavailable.");
  }
}

function operatorFetchOptions(options?: { accessToken?: string | null }): RequestInit {
  const trimmedToken = (options?.accessToken ?? "").trim();
  return trimmedToken ? { headers: { Authorization: `Bearer ${trimmedToken}` } } : {};
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch (_error) {
    return null;
  }
}

function mapV6PackageStatus(payload: unknown, fallbackRunId: string, forcedOutcome?: V6PackageOutcome): V6PackageStatus {
  const dto = asRecord(payload);
  const outcome = forcedOutcome ?? mapOutcome(dto.outcome);
  return {
    outcome,
    runId: asString(dto.run_id) || fallbackRunId,
    requestId: asString(dto.request_id) || undefined,
    packageReady: asBoolean(dto.package_ready),
    validationStatus: asString(dto.validation_status) || undefined,
    payloadCount: asNullableNumber(dto.payload_count) ?? undefined,
    zipEntryCount: asNullableNumber(dto.zip_entry_count) ?? undefined,
    categoryCounts: asNumberRecord(dto.category_counts),
    issueCount: asNullableNumber(dto.issue_count) ?? undefined,
    warningCount: asNullableNumber(dto.warning_count) ?? undefined,
    zipFilename: asString(dto.zip_filename) || undefined,
    inventoryFilename: asString(dto.inventory_filename) || undefined,
    validationReportFilename: asString(dto.validation_report_filename) || undefined,
    message: asString(dto.message) || undefined,
    supportReference: asString(dto.support_reference) || undefined,
  };
}

function errorStatus(runId: string, message: string): V6PackageStatus {
  return {
    outcome: "error",
    runId,
    packageReady: false,
    message,
  };
}

function mapOutcome(value: unknown): V6PackageOutcome {
  if (
    value === "generated" ||
    value === "available" ||
    value === "not_available" ||
    value === "denied" ||
    value === "invalid_package_inputs" ||
    value === "error"
  ) {
    return value;
  }
  return "error";
}

function filenameFromContentDisposition(value: string | null): string | null {
  if (!value) {
    return null;
  }
  const match = /filename="?([^";]+)"?/i.exec(value);
  return match?.[1] || null;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function asNullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asBoolean(value: unknown): boolean {
  return value === true;
}

function asNumberRecord(value: unknown): Record<string, number> | undefined {
  const dto = asRecord(value);
  const mapped: Record<string, number> = {};
  for (const [key, item] of Object.entries(dto)) {
    if (typeof item === "number" && Number.isFinite(item)) {
      mapped[key] = item;
    }
  }
  return Object.keys(mapped).length > 0 ? mapped : undefined;
}
