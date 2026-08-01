export interface SurfaceChangeWindow {
  start: string;
  end: string;
}

export interface SurfaceChangeSummary {
  schema: string;
  status: "available" | "not_available";
  reason?: string;
  method?: string;
  before_window?: SurfaceChangeWindow;
  after_window?: SurfaceChangeWindow;
  window_days?: number;
  before_pair_count?: number | null;
  after_pair_count?: number | null;
  valid_pixel_count?: number;
  valid_pixel_fraction?: number;
  change_review_pixel_count?: number;
  change_review_pixel_fraction?: number;
  median_logratio_delta_db?: number;
  p95_absolute_centered_delta_db?: number;
  robust_scale_db?: number;
  review_threshold_db?: number;
  maximum_incidence_delta_degrees?: number;
  indicator_interpretation?: string;
  warnings?: string[];
}

const ARTIFACT_NAME = "option5_surface_change_summary";
const FILENAME = "option5_surface_change_summary.json";

export async function fetchSurfaceChangeSummary(runId: string): Promise<SurfaceChangeSummary> {
  const response = await fetch(surfaceChangeSummaryUrl(runId));
  if (!response.ok) {
    throw new Error("Surface-change summary is unavailable.");
  }

  const payload = await response.json() as SurfaceChangeSummary;
  if (payload.status !== "available" && payload.status !== "not_available") {
    throw new Error("Surface-change summary has an unsupported status.");
  }
  return payload;
}

export function surfaceChangeSummaryUrl(runId: string): string {
  return `/runs/${encodeURIComponent(runId)}/artifacts/${ARTIFACT_NAME}/download/${FILENAME}`;
}
