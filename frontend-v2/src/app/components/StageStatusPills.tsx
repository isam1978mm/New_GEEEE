import { CheckCircle2, Loader2, XCircle, Circle } from "lucide-react";
import type { Stage } from "../data/mockData";

const statusCfg = {
  done: {
    icon: <CheckCircle2 size={9} />,
    color: "var(--gs-green)",
    bg: "var(--gs-green-bg)",
    border: "var(--gs-green-border)",
  },
  running: {
    icon: <Loader2 size={9} className="animate-spin" />,
    color: "var(--gs-blue)",
    bg: "var(--gs-blue-bg)",
    border: "var(--gs-blue-border)",
  },
  failed: {
    icon: <XCircle size={9} />,
    color: "var(--gs-red)",
    bg: "var(--gs-red-bg)",
    border: "var(--gs-red-border)",
  },
  pending: {
    icon: <Circle size={9} />,
    color: "rgba(100,116,139,0.5)",
    bg: "transparent",
    border: "rgba(100,116,139,0.18)",
  },
  skipped: {
    icon: <Circle size={9} />,
    color: "rgba(100,116,139,0.4)",
    bg: "transparent",
    border: "rgba(100,116,139,0.12)",
  },
};

interface StageStatusPillsProps {
  stages: Stage[];
}

export function StageStatusPills({ stages }: StageStatusPillsProps) {
  return (
    <div className="flex flex-wrap gap-1">
      {stages.map((stage) => {
        const cfg = statusCfg[stage.status];
        return (
          <div
            key={stage.key}
            className="flex items-center gap-1 px-1.5 rounded"
            style={{
              backgroundColor: cfg.bg,
              border: `1px solid ${cfg.border}`,
              color: cfg.color,
              height: "20px",
            }}
            title={`${stage.label}: ${stage.status}`}
          >
            <span style={{ color: cfg.color, display: "flex", alignItems: "center" }}>
              {cfg.icon}
            </span>
            <span
              className="font-mono"
              style={{ fontSize: "9.5px", fontWeight: 600, color: cfg.color, whiteSpace: "nowrap" }}
            >
              {stage.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
