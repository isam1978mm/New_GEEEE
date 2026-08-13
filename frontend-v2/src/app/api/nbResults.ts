export interface NBObjectResult {
  objectId: number;
  nbMetalSignature: number | null;
  nbVoidSignature: number | null;
  nbCeramicSignature: number | null;
  nbMassSignature: number | null;
  nbFalseSignatureScore: number | null;
  nbBestObjectInterpretation: string | null;
  nbBestObjectScore: number | null;
  nanoDepthPenetration: number | null;
  nbDepthM: number | null;
  nbDepthAvailable: boolean;
}

export interface NBResults {
  status: string;
  method: string;
  objectCount: number;
  reason: string | null;
  unavailableSupport: string[];
  objects: NBObjectResult[];
}

interface NBObjectDto {
  object_id?: unknown;
  nb_metal_signature?: unknown;
  nb_void_signature?: unknown;
  nb_ceramic_signature?: unknown;
  nb_mass_signature?: unknown;
  nb_false_signature_score?: unknown;
  nb_best_object_interpretation?: unknown;
  nb_best_object_score?: unknown;
  nano_depth_penetration?: unknown;
  nb_depth_m?: unknown;
  nb_depth_available?: unknown;
}

interface NBResultsDto {
  status?: unknown;
  method?: unknown;
  object_count?: unknown;
  reason?: unknown;
  unavailable_support?: unknown;
  objects?: unknown;
}

function asNumber(value: unknown, fallback = 0): number {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function asNullableNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function asNullableString(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null;
  return String(value);
}

export async function fetchNBResults(runId: string): Promise<NBResults> {
  const response = await fetch(`/runs/${encodeURIComponent(runId)}/nb-results`);
  if (!response.ok) {
    throw new Error("NB results are unavailable.");
  }
  const payload = (await response.json()) as NBResultsDto;
  const objectRows = Array.isArray(payload.objects) ? (payload.objects as NBObjectDto[]) : [];
  const unavailableSupport = Array.isArray(payload.unavailable_support)
    ? payload.unavailable_support.map((item) => String(item))
    : [];
  return {
    status: String(payload.status ?? "not_available"),
    method: String(payload.method ?? ""),
    objectCount: asNumber(payload.object_count),
    reason: payload.reason === null || payload.reason === undefined ? null : String(payload.reason),
    unavailableSupport,
    objects: objectRows.map((row) => ({
      objectId: asNumber(row.object_id),
      nbMetalSignature: asNullableNumber(row.nb_metal_signature),
      nbVoidSignature: asNullableNumber(row.nb_void_signature),
      nbCeramicSignature: asNullableNumber(row.nb_ceramic_signature),
      nbMassSignature: asNullableNumber(row.nb_mass_signature),
      nbFalseSignatureScore: asNullableNumber(row.nb_false_signature_score),
      nbBestObjectInterpretation: asNullableString(row.nb_best_object_interpretation),
      nbBestObjectScore: asNullableNumber(row.nb_best_object_score),
      nanoDepthPenetration: asNullableNumber(row.nano_depth_penetration),
      nbDepthM: asNullableNumber(row.nb_depth_m),
      nbDepthAvailable: Boolean(row.nb_depth_available),
    })),
  };
}
