import { useState } from "react";
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
import type { ExportGroup, UnavailableOutput } from "../api/client";

interface ExportsTabProps {
  groups: ExportGroup[];
  unavailable: UnavailableOutput[];
  loading?: boolean;
  error?: string | null;
}

export function ExportsTab({ groups, unavailable, loading = false, error = null }: ExportsTabProps) {
  const [search, setSearch] = useState("");
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [showAdvanced, setShowAdvanced] = useState(false);

  const totalFiles = groups.reduce((sum, g) => sum + g.fileCount, 0);
  const totalSize = groups.length === 0 ? "0 files" : groups.reduce((sum, g) => sum + g.files.reduce((groupSum, file) => groupSum + file.sizeBytes, 0), 0);
  const totalSizeLabel =
    typeof totalSize === "number" && totalSize > 1024 * 1024 * 1024
      ? `${(totalSize / (1024 * 1024 * 1024)).toFixed(1)} GB`
      : typeof totalSize === "number" && totalSize > 1024 * 1024
        ? `${(totalSize / (1024 * 1024)).toFixed(1)} MB`
        : "0 files";

  function toggleGroup(key: string) {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  const filteredGroups = groups.map((group) => ({
    ...group,
    files: group.files.filter(
      (f) =>
        f.name.toLowerCase().includes(search.toLowerCase()) ||
        f.path.toLowerCase().includes(search.toLowerCase())
    ),
  })).filter((group) => search === "" || group.files.length > 0);

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
              {filteredGroups.length} groups match
            </span>
          )}
        </div>
      </div>

      {/* Folder browser */}
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
            Export Tree
          </span>
          <span style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
            · {groups.length} groups · collapsed by default
          </span>
        </div>

        <div className="overflow-y-auto" style={{ maxHeight: "440px" }}>
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
              {search ? "No exports match the current filter." : "No guarded exports are available for this run."}
            </div>
          )}
          {!loading && !error && filteredGroups.map((group, gi) => {
            const isExpanded = expandedGroups.has(group.key) || (search !== "" && group.files.length > 0);
            return (
              <div
                key={group.key}
                style={{ borderBottom: gi < filteredGroups.length - 1 ? "1px solid var(--border)" : "none" }}
              >
                {/* Group header */}
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
                  <span
                    className="font-mono flex-1 text-left"
                    style={{ fontSize: "12px", fontWeight: 700, color: "var(--gs-navy)" }}
                  >
                    {group.label}
                  </span>
                  <div className="flex items-center gap-3 ml-auto shrink-0">
                    <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                      {group.fileCount} files
                    </span>
                    <span className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-slate)", opacity: 0.65 }}>
                      {group.totalSize}
                    </span>
                    {group.isPublicSafe ? (
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
                        PUB
                      </span>
                    ) : (
                      <Lock size={10} style={{ color: "var(--gs-slate)", opacity: 0.4 }} />
                    )}
                  </div>
                </button>

                {/* Expanded file table */}
                {isExpanded && (
                  <div style={{ backgroundColor: "var(--accent)" }}>
                    {/* Table head */}
                    <div
                      className="grid px-4 py-1"
                      style={{
                        gridTemplateColumns: "minmax(0,2fr) minmax(0,3fr) 70px 100px",
                        gap: "8px",
                        borderTop: "1px solid var(--border)",
                        borderBottom: "1px solid var(--border)",
                      }}
                    >
                      {["Filename", "Path", "Size", ""].map((h) => (
                        <span
                          key={h}
                          className="font-mono"
                          style={{ fontSize: "9.5px", fontWeight: 700, color: "var(--gs-slate)", textTransform: "uppercase", letterSpacing: "0.06em" }}
                        >
                          {h}
                        </span>
                      ))}
                    </div>

                    {/* File rows */}
                    {group.files.map((file, fi) => (
                      <div
                        key={file.path}
                        className="grid px-4 py-1.5 hover:bg-card/50 transition-colors items-center"
                        style={{
                          gridTemplateColumns: "minmax(0,2fr) minmax(0,3fr) 70px 100px",
                          gap: "8px",
                          borderBottom: fi < group.files.length - 1 ? "1px solid rgba(28,43,94,0.05)" : "none",
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

                    {group.files.length < group.fileCount && (
                      <div className="px-4 py-1.5" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                        +{group.fileCount - group.files.length} more files (not shown in preview)
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Advanced / unavailable outputs */}
      <div
        className="rounded-lg overflow-hidden"
        style={{ border: "1px solid var(--border)", backgroundColor: "var(--card)" }}
      >
        <button
          onClick={() => setShowAdvanced((p) => !p)}
          className="flex items-center gap-2 px-4 py-2.5 w-full hover:bg-accent/20 transition-colors"
          style={{ background: "none", border: "none", cursor: "pointer" }}
        >
          {showAdvanced
            ? <ChevronDown size={12} style={{ color: "var(--gs-slate)" }} />
            : <ChevronRight size={12} style={{ color: "var(--gs-slate)" }} />
          }
          <AlertTriangle size={12} style={{ color: "var(--gs-amber)" }} />
          <span style={{ fontSize: "11.5px", fontWeight: 500, color: "var(--gs-slate)" }}>
            Advanced / unavailable outputs
          </span>
        </button>
        {showAdvanced && (
          <div
            className="px-4 pb-3 pt-0"
            style={{ borderTop: "1px solid var(--border)", backgroundColor: "var(--gs-amber-bg)" }}
          >
            <p style={{ fontSize: "11.5px", color: "var(--gs-slate)", lineHeight: "1.6", paddingTop: "10px" }}>
              {unavailable.length === 0
                ? "No unavailable outputs are reported for this run."
                : `${unavailable.length} outputs are unavailable for this run. Detailed source status is retained by the guarded operator output API.`}
            </p>
            {unavailable.length > 0 && (
              <div className="mt-2 flex flex-col gap-1">
                {unavailable.slice(0, 20).map((item) => (
                  <div key={item.path} className="font-mono" style={{ fontSize: "10.5px", color: "var(--gs-slate)" }}>
                    {item.path} · {item.status}
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
