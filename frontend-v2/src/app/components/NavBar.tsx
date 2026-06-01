type NavTab = "dashboard" | "archive" | "exports" | "settings";

interface NavBarProps {
  activeTab: NavTab;
  onTabChange: (tab: NavTab) => void;
}

const tabs: { key: NavTab; label: string }[] = [
  { key: "dashboard", label: "Dashboard" },
  { key: "archive", label: "Run Archive" },
  { key: "exports", label: "Exports" },
  { key: "settings", label: "Settings" },
];

export function NavBar({ activeTab, onTabChange }: NavBarProps) {
  return (
    <header
      style={{ backgroundColor: "var(--gs-navy)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      className="flex items-center px-5 h-11 shrink-0 gap-0"
    >
      {/* GS logo + brand */}
      <div className="flex items-center gap-2.5 mr-8 shrink-0">
        <div
          className="flex items-center justify-center rounded-full shrink-0"
          style={{
            width: "26px",
            height: "26px",
            backgroundColor: "rgba(255,255,255,0.13)",
            border: "1px solid rgba(255,255,255,0.22)",
          }}
        >
          <span
            className="font-mono select-none"
            style={{ fontSize: "10px", fontWeight: 700, color: "white", letterSpacing: "-0.02em" }}
          >
            GS
          </span>
        </div>
        <span
          style={{ fontSize: "13px", fontWeight: 500, color: "white", letterSpacing: "-0.01em" }}
        >
          GEE Screening
        </span>
      </div>

      {/* Nav tabs */}
      <nav className="flex items-stretch h-full gap-0">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => onTabChange(tab.key)}
            className="relative px-4 h-full transition-all"
            style={{
              fontSize: "12px",
              fontWeight: activeTab === tab.key ? 500 : 400,
              color: activeTab === tab.key ? "white" : "rgba(255,255,255,0.5)",
              background: "none",
              border: "none",
              cursor: "pointer",
              borderBottom: activeTab === tab.key
                ? "2px solid rgba(255,255,255,0.8)"
                : "2px solid transparent",
            }}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Right: local access marker */}
      <div className="ml-auto flex items-center gap-1.5">
        <span
          style={{ fontSize: "10px", color: "rgba(255,255,255,0.45)", marginRight: "4px" }}
          className="font-mono"
        >
          local access
        </span>
      </div>
    </header>
  );
}
