(function () {
  "use strict";

  const SPA_CONFIG = {
    externalTilesEnabled: false,
    guardedArtifactPrefix: "/runs/",
  };

  const sampleArtifacts = [
    {
      run_id: "demo-run",
      name: "objects_index.csv",
      artifact_class: "REDACTED_PUBLIC",
      relative_path: "objects_index.csv",
      display_label: "Object table",
    },
    {
      run_id: "demo-run",
      name: "alignment_qa.json",
      artifact_class: "REDACTED_PUBLIC",
      relative_path: "alignment_qa.json",
      display_label: "Alignment QA",
    },
    {
      run_id: "demo-run",
      name: "experimental_summary",
      artifact_class: "FILESYSTEM_ONLY",
      relative_path: "experimental/summary.json",
      display_label: "Hidden experimental summary",
    },
  ];

  function isVisibleArtifact(artifact) {
    if (!artifact || artifact.artifact_class === "FILESYSTEM_ONLY") {
      return false;
    }
    if (typeof artifact.relative_path === "string" && artifact.relative_path.startsWith("experimental/")) {
      return false;
    }
    if (typeof artifact.name === "string" && artifact.name.startsWith("experimental_")) {
      return false;
    }
    return true;
  }

  function buildArtifactHref(artifact) {
    return `${SPA_CONFIG.guardedArtifactPrefix}${encodeURIComponent(artifact.run_id)}/artifacts/${encodeURIComponent(artifact.name)}`;
  }

  function renderArtifacts(artifacts) {
    const visibleArtifacts = artifacts.filter(isVisibleArtifact);
    const list = document.getElementById("artifact-list");
    const count = document.getElementById("artifact-count");
    const tileMode = document.getElementById("tile-mode");

    tileMode.textContent = SPA_CONFIG.externalTilesEnabled ? "External tiles enabled" : "External tiles disabled";
    count.textContent = `${visibleArtifacts.length} visible`;

    list.innerHTML = "";
    for (const artifact of visibleArtifacts) {
      const item = document.createElement("li");
      item.className = "artifact-card";

      const title = document.createElement("span");
      title.className = "artifact-label";
      title.textContent = artifact.display_label;

      const link = document.createElement("a");
      link.className = "artifact-link";
      link.href = buildArtifactHref(artifact);
      link.textContent = "Download";

      const meta = document.createElement("span");
      meta.className = "artifact-meta";
      meta.textContent = artifact.artifact_class;

      item.appendChild(title);
      item.appendChild(meta);
      item.appendChild(link);
      list.appendChild(item);
    }
  }

  renderArtifacts(sampleArtifacts);
})();
