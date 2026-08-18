import { useEffect, useMemo, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Download,
  Folder,
  FolderOpen,
  Search,
  AlertTriangle,
  Lock,
} from "lucide-react";
import { formatFileSize, type ExportFile, type ExportGroup, type UnavailableOutput } from "../api/client";

interface ExportsTabProps {
  groups: ExportGroup[];
  unavailable: UnavailableOutput[];
  loading?: boolean;
  error?: string | null;
  showAdvancedByDefault?: boolean;
}

type ExportCategoryKey =
  | "result-classifier"
  | "user-focus"
  | "candidate-focus"
  | "location-field"
  | "paid-imagery"
  | "technical-advanced";

const EXPORT_CATEGORIES: Array<{ key: ExportCategoryKey; label: string; description: string }> = [
  {
    key: "result-classifier",
    label: "Result & Classifier",
    description: "Preferred classifier result files; legacy classifier copies are used here only when preferred files are absent.",
  },
  {
    key: "user-focus",
    label: "User Focus",
    description: "Detailed Focus outputs centered on the original coordinate entered for the run.",
  },
  {
    key: "candidate-focus",
    label: "Candidate Focus",
    description: "Detailed Focus outputs for the highest-ranked candidates found automatically in the full scene.",
  },
  {
    key: "location-field",
    label: "Location & Field",
    description: "Guarded location, navigation, GPS and field-operation files when returned by the output API.",
  },
  {
    key: "paid-imagery",
    label: "Paid Imagery",
    description: "Manual paid-imagery request and vendor-package files when returned by the output API.",
  },
  {
    key: "technical-advanced",
    label: "Technical / Advanced Outputs",
    description: "DEMs, rasters, hypercubes, arrays, manifests, QA/support files and compatibility copies.",
  },
];

const PREFERRED_CLASSIFIER_PATHS = new Set([
  "classifier/summary.json",
  "classifier/classifications.csv",
]);

const LEGACY_CLASSIFIER_RESULT_PATHS = new Set([
  "experimental/summary.json",
  "experimental/classifications.csv",
]);

function normalizePath(path: string): string {
  return path.replace(/\\/g, "/").replace(/^\.\//, "").toLowerCase();
}

function exportCategoryForPath(path: string, preferredClassifierAvailable: boolean): ExportCategoryKey {
  const normalized = normalizePath(path);

  if (normalized.startsWith("full_job/candidate_focus/")) {
    return "candidate-focus";
  }
  if (normalized.startsWith("full_job/focus/")) {
    return "user-focus";
  }
  if (PREFERRED_CLASSIFIER_PATHS.has(normalized)) {
    return "result-classifier";
  }
  if (LEGACY_CLASSIFIER_RESULT_PATHS.has(normalized)) {
    return preferredClassifierAvailable ? "technical-advanced" : "result-classifier";
  }

  if (
    normalized.startsWith("full_job/location/") ||
    normalized.startsWith("full_job/field_ops/") ||
    normalized.startsWith("kmz/") ||
    normalized.includes("site_location") ||
    normalized.includes("field_ops") ||
    normalized.includes("gps_compare") ||
    normalized.includes("gps_comparison")
  ) {
    return "location-field";
  }

  if (
    normalized.startsWith("paid_imagery/") ||
    normalized.startsWith("paid-imagery/") ||
    normalized.includes("/paid_imagery/") ||
    normalized.includes("/paid-imagery/") ||
    normalized.includes("paid_imagery_") ||
    normalized.includes("imagery_request") ||
    normalized.includes("quote_request") ||
    normalized.includes("vendor_request")
  ) {
    return "paid-imagery";
  }

  return "technical-advanced";
}

function buildExportCategories(groups: ExportGroup[]): ExportGroup[] {
  const filesByPath = new Map<string, ExportFile>();
  for (const group of groups) {
    for (const file of group.files) {
      filesByPath.set(file.path, file);
    }
  }
  const files = Array.from(filesByPath.values());
  const preferredClassifierAvailable = files.some((file) => PREFERRED_CLASSIFIER_PATHS.has(normalizePath(file.path)));
  const buckets = new Map<ExportCategoryKey, ExportFile[]>(EXPORT_CATEGORIES.map((category) => [category.key, []]));

  for (const file of files) {
    const category = exportCategoryForPath(file.path, preferredClassifierAvailable);
    buckets.get(category)?.push(file);
  }

  return EXPORT_CATEGORIES.map((category) => {
    const categoryFiles = (buckets.get(category.key) ?? []).slice().sort((left, right) => left.path.localeCompare(right.path));
    const totalBytes = categoryFiles.reduce((sum, file) => sum + file.sizeBytes, 0);
    return {
      key: category.key,
      label: category.label,
      fileCount: categoryFiles.length,
      totalSize: formatFileSize(totalBytes),
      files: categoryFiles,
      hasDownloads: categoryFiles.some((file) => Boolean(file.downloadUrl)),
    };
  });
}

function categoryDescription(key: string): string {
  return EXPORT_CATEGORIES.find((category) => category.key === key)?.description ?? "Guarded run outputs.";
}

export function ExportsTab({
  groups,
  unavailable,
  loading = false,
  error = null,
  showAdvancedByDefault = false,
}: ExportsTabProps) {
  const [search, setSearch] = useState("");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [showAdvanced, setShowAdvanced] = useState(showAdvancedByDefault);
  const categorizedGroups = useMemo(() => buildExportCategories(groups), [groups]);

  useEffect(() => {
    setShowAdvanced(showAdvancedByDefault);
  }, [showAdvancedByDefault]);

  const totalFiles = categorizedGroups.reduce((sum, group) => sum + group.fileCount, 0);
  const totalSizeBytes = categorizedGroups.reduce(
    (sum, group) => sum + group.files.reduce((groupSum, file) => groupSum + file.sizeBytes, 0),
    0,
  );
  const totalSizeLabel = totalFiles === 0 ? "0 files" : formatFileSize(totalSizeBytes);

  function toggleGroup(key: string) {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  const filteredGroups = categorizedGroups
    .map((group) => ({
      ...group,
      files: group.files.filter(
        (file) =>
          file.name.toLowerCase().includes(search.toLowerCase()) ||
          file.path.toLowerCase().includes(search.toLowerCase()),
      ),
    }))
    .filter((group) => search === "" || group.files.length > 0);

  return (
    <div className="flex flex-col gap-3">
      {/* Search + stats bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search
            size={12}
            className="absolute left-2.5 top-1/2 -translate-y-1/2"
            style={{ color: "var(--gs-slate)", opacity: 0.5 }}
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter files…"
            className="rounded px-2.5 py-1.5 pl-7 w-full outline-none"
            style={{
              fontSize: "12px",
              backgroundColor: "var(--card)",
              border: "1px solid var(--border)",
              color: "var(--gs-navy)",
            }}
          />
        </div>
        <div
          className="flex items-center gap-3 px-3 py-1.5 rounded shrink-0"
          style={{ backgroundColor: "var(--card)", border: "1px solid var(--border)" }}
        >
          <span style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
            <span className="font-mono" style={{ fontWeight: 700, color: "var(--gs-navy)" }}>
              {totalFiles}
            </span>{" "}
            files
          </span>
          <span style={{ fontSize: "11.5px", color: "var(--gs-slate)" }}>
            <span className="font-mono" style={{ fontWeight: 700, color: "var(--gs-navy)" }}>
              {totalSizeLabel}
            </span>{" "}
            total
          </span>
          {search && (
            <span style={{ fontSize: "11px", color: "var(--gs-blue)" }}>
              {filteredGroups.length} categories match
            </span>
          )}
        </div>
      </div>

      <div
        className="rounded px-3 py-2"
        style={{
          fontSize: "11px",
          color: "var(--gs-slate)",
          backgroundColor: "var(--accent)",
          border: "1px solid rgba(28,43,94,0.12)",
          lineHeight: "1.5",
        }}
      >
        Downloads keep their existing guarded URLs and artifact paths. User Focus keeps the original run coordinate; Candidate Focus contains the strongest automatically ranked scene candidates. Candidate/anomaly scores are screening evidence, not physical confirmation.
      </div>

      {/* Purpose-based export browser */}
      <div
        className="rounded-lg bg-card overflow-hidden"
        style={{ border: "1px solid var(--border)", boxShadow: "0 1px 3px rgba(28,43,94,0.05)" }}
      >
        <div
          className="flex items-center gap-2 px-4 py-2"
          style={{ borderBottom: "1px solid var(--border)", backgroundColor: "var(--accent)" }}
        >
          <span
            className="font-mono"
            style={{ fontSize: "10px", fontWeight: 700, color: "var(--gs-navy)", textTransform: "uppercase", letterSpacing: "0.07em" }}
          >
            Export Categories
          </span>
          <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
            · {EXPORT_CATEGORIES.length} categories · collapsed by default
          </span>
        </div>

        <div className="overflow-y-auto" style={{ maxHeight: "520px" }}>
          {loading && (
            <div className="px-4 py-8 text-center" style={{ fontSize: "12px", color: "var(--gs-slate)" }}>
              Loading exports from the run output API...
            </div>
          )}
          {!loading && error && (
            <div className="px-4 py-8 text-center" style={{ fontSize: "12px", color: "var(--gs-red)" }}>
              {error}
            </div>
          )}
          {!loading && !error && filteredGroups.length === 0 && (
            <div className="px-4 py-8 text-center" style={{ fontSize: "12px", color: "var(--gs-slate)" }}>
              {search
                ? "No exports match the current filter."
                : "No guarded exports are available for this run yet. Select a completed run or inspect unavailable/status metadata below."}
            </div>
          )}
          {!loading && !error && filteredGroups.map((group, groupIndex) => {
            const isExpanded = expandedGroups.has(group.key) || (search !== "" && group.files.length > 0);
            return (
              <div
                key={group.key}
                style={{ borderBottom: groupIndex < filteredGroups.length - 1 ? "1px solid var(--border)" : "none" }}
              >
                <button
                  onClick={() => toggleGroup(group.key)}
                  className="flex items-center gap-2 px-4 py-2 w-full hover:bg-accent/30 transition-colors"
                  style={{ background: "none", border: "none", cursor: "pointer" }}
                >
                  {isExpanded
                    ? <ChevronDown size={12} style={{ color: "var(--gs-slate)", flexShrink: 0 }} />
                    : <ChevronRight size={12} style={{ color: "var(--gs-slate)", flexShrink: 0 }} />
                  }
                  {isExpanded
                    ? <FolderOpen size={13} style={{ color: "var(--gs-amber)", flexShrink: 0 }} />
                    : <Folder size={13} style={{ color: "var(--gs-amber)", flexShrink: 0 }} />
                  }
                  <div className="flex-1 min-w-0 text-left">
                    <div
                      className="font-mono"
                      style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-navy)" }}
                    >
                      {group.label}
                    </div>
                    <div style={{ fontSize: "10px", color: "var(--gs-slate)", marginTop: "1px" }}>
                      {categoryDescription(group.key)}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 ml-auto shrink-0">
                    <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                      {group.fileCount} files
                    </span>
                    <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-slate)", opacity: 0.65 }}>
                      {group.totalSize}
                    </span>
                    {group.hasDownloads ? (
                      <span
                        className="font-mono"
                        style={{
                          fontSize: "8.5px",
                          fontWeight: 700,
                          color: "var(--gs-blue)",
                          backgroundColor: "var(--gs-blue-bg)",
                          border: "1px solid var(--gs-blue-border)",
                          padding: "1px 4px",
                          borderRadius: "2px",
                        }}
                      >
                        READY
                      </span>
                    ) : (
                      <Lock size={10} style={{ color: "var(--gs-slate)", opacity: 0.4 }} />
                    )}
                  </div>
                </button>

                {isExpanded && (
                  <div style={{ backgroundColor: "var(--accent)" }}>
                    {group.files.length > 0 ? (
                      <>
                        <div
                          className="grid px-4 py-1"
                          style={{
                            gridTemplateColumns: "minmax(0,2fr) minmax(0,3fr) 70px 100px",
                            gap: "8px",
                            borderTop: "1px solid var(--border)",
                            borderBottom: "1px solid var(--border)",
                          }}
                        >
                          {["Filename", "Path", "Size", ""].map((heading) => (
                            <span
                              key={heading}
                              className="font-mono"
                              style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.06em" }}
                            >
                              {heading}
                            </span>
                          ))}
                        </div>

                        {group.files.map((file, fileIndex) => (
                          <div
                            key={file.path}
                            className="grid px-4 py-1.5 hover:bg-card/50 transition-colors items-center"
                            style={{
                              gridTemplateColumns: "minmax(0,2fr) minmax(0,3fr) 70px 100px",
                              gap: "8px",
                              borderBottom: fileIndex < group.files.length - 1 ? "1px solid rgba(28,43,94,0.05)" : "none",
                            }}
                          >
                            <span
                              className="font-mono truncate"
                              style={{ fontSize: "11.5px", fontWeight: 600, color: "var(--gs-navy)" }}
                            >
                              {file.name}
                            </span>
                            <span
                              className="font-mono truncate"
                              style={{ fontSize: "10px", color: "var(--gs-slate)", opacity: 0.6 }}
                            >
                              {file.path}
                            </span>
                            <span
                              className="font-mono"
                              style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}
                            >
                              {file.size}
                            </span>
                            {file.downloadUrl ? (
                              <a
                                href={file.downloadUrl}
                                download={file.name}
                                className="flex items-center gap-1 px-2 py-0.5 rounded hover:bg-card transition-colors"
                                style={{
                                  fontSize: "11px",
                                  fontWeight: 500,
                                  color: "var(--gs-navy)",
                                  backgroundColor: "var(--card)",
                                  border: "1px solid rgba(28,43,94,0.15)",
                                  cursor: "pointer",
                                  textDecoration: "none",
                                }}
                              >
                                <Download size={9} />
                                Download
                              </a>
                            ) : (
                              <span style={{ fontSize: "11px", color: "var(--gs-slate)" }}>Unavailable</span>
                            )}
                          </div>
                        ))}
                      </>
                    ) : (
                      <div
                        className="px-4 py-3"
                        style={{ borderTop: "1px solid var(--border)", fontSize: "11px", color: "var(--gs-slate)" }}
                      >
                        No files in this category for the selected run.
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Unavailable output status metadata remains separate from downloadable technical files. */}
      <div
        className="rounded-lg overflow-hidden"
        style={{ border: "1px solid var(--border)", backgroundColor: "var(--card)" }}
      >
        <button
          onClick={() => setShowAdvanced((previous) => !previous)}
          className="flex items-center gap-2 px-4 py-2.5 w-full hover:bg-accent/20 transition-colors"
          style={{ background: "none", border: "none", cursor: "pointer" }}
        >
          {showAdvanced
            ? <ChevronDown size={12} style={{ color: "var(--gs-slate)" }} />
            : <ChevronRight size={12} style={{ color: "var(--gs-slate)" }} />
          }
          <AlertTriangle size={12} style={{ color: "var(--gs-amber)" }} />
          <span style={{ fontSize: "11.5px", fontWeight: 500, color: "var(--gs-slate)" }}>
            Unavailable / status metadata
          </span>
        </button>
        {showAdvanced && (
          <div
            className="px-4 pb-3 pt-0"
            style={{ borderTop: "1px solid var(--border)", backgroundColor: "var(--gs-amber-bg)" }}
          >
            <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.6", paddingTop: "10px" }}>
              {unavailable.length === 0
                ? "No unavailable outputs are reported for this run. If the run is still queued or running, exports may appear after completion."
                : `${unavailable.length} outputs are unavailable for this run. Detailed source status is retained by the guarded output API.`}
            </p>
            {unavailable.length > 0 && (
              <div className="flex flex-col gap-1.5 mt-2">
                {unavailable.map((item) => (
                  <div
                    key={`${item.group}-${item.path}`}
                    className="rounded px-2 py-1.5"
                    style={{ backgroundColor: "rgba(255,255,255,0.55)", border: "1px solid rgba(28,43,94,0.08)" }}
                  >
                    <div className="font-mono" style={{ fontSize: "11px", color: "var(--gs-navy)", fontWeight: 700 }}>
                      {item.group} · {item.filename}
                    </div>
                    <div className="font-mono" style={{ fontSize: "10px", color: "var(--gs-slate)", marginTop: "2px" }}>
                      {item.path}
                    </div>
                    <div style={{ fontSize: "10.5px", color: "var(--gs-slate)", marginTop: "2px" }}>
                      {item.status} · source: {item.source}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
