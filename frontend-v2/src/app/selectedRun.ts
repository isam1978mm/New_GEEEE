const SELECTED_RUN_STORAGE_KEY = "gs_selected_run_id_v1";

export function rememberSelectedRunId(runId: string): void {
  if (typeof window === "undefined") {
    return;
  }
  const value = runId.trim();
  if (!value) {
    window.sessionStorage.removeItem(SELECTED_RUN_STORAGE_KEY);
    return;
  }
  window.sessionStorage.setItem(SELECTED_RUN_STORAGE_KEY, value);
}

export function readSelectedRunId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const value = window.sessionStorage.getItem(SELECTED_RUN_STORAGE_KEY)?.trim() ?? "";
  return value || null;
}
