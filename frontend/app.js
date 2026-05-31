(function () {
  "use strict";

  const SPA_CONFIG = {
    externalTilesEnabled: false,
    guardedArtifactPrefix: "/runs/",
  };

  const ARTIFACT_DESCRIPTIONS = {
    objects_index: "detailed detected object table",
    clusters_summary: "grouped cluster summary",
    alignment_qa: "safe alignment health summary",
    alignment_audit: "alignment audit details",
    alignment_mask_selection: "selected masks used for alignment QA",
  };

  const ARTIFACT_DISPLAY_FILENAMES = {
    objects_index: "objects_index.csv",
    clusters_summary: "clusters_summary.csv",
    alignment_qa: "alignment_qa.json",
    alignment_audit: "alignment_audit.json",
    alignment_mask_selection: "alignment_mask_selection.json",
  };

  const KEY_DOWNLOAD_PATHS = [
    "QA/RUN_MANIFEST.json",
    "DEM_GEO8_TIFS/DEM_640.tif",
    "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif",
    "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy",
    "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif",
    "REPORT_640_FINAL_Zero_Point_Targets.tif",
    "REPORT_640_Mass_Report.tif",
    "REPORT_640_Pottery_Report.tif",
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
    "Root files / app science outputs",
  ];

  const DASHBOARD_TABS = ["overview", "exports", "status-history", "diagnostics"];

  const STAGE_LABEL_SHORT_NAMES = {
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
  };

  const STATUS_ICON_BY_STATE = {
    done: "ok",
    pending: "o",
    queued: "o",
    running: ">",
    failed: "!",
    stale_failed: "!",
    skipped: "-",
    cancelled: "-",
  };

  const state = {
    currentRunId: null,
    currentRunStatus: null,
    pollTimerId: null,
    pollFailed: false,
    recentRuns: [],
    currentOutputTreeRunId: null,
    currentOutputTreePayload: null,
    outputFilter: "",
    outputGroupsExpanded: false,
    activeDashboardTab: "overview",
    archiveFilter: "",
  };

  function isVisibleArtifact(artifact) {
    if (!artifact || artifact.artifact_class === "FILESYSTEM_ONLY") {
      return false;
    }
    if (typeof artifact.name === "string" && artifact.name.startsWith("experimental_")) {
      return false;
    }
    return true;
  }

  function buildArtifactHref(runId, artifact) {
    const downloadFilename = displayArtifactName(artifact);
    return `${SPA_CONFIG.guardedArtifactPrefix}${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(artifact.name)}/download/${encodeURIComponent(downloadFilename)}`;
  }

  function describeArtifact(artifact) {
    if (!artifact || typeof artifact.name !== "string") {
      return "public-safe run artifact";
    }
    const artifactName = artifact.name;
    const artifactStem = artifactName.replace(/\.[^.]+$/, "");
    return ARTIFACT_DESCRIPTIONS[artifactName] || ARTIFACT_DESCRIPTIONS[artifactStem] || "public-safe run artifact";
  }

  function displayArtifactName(artifact) {
    if (!artifact || typeof artifact.name !== "string") {
      return "run artifact";
    }
    return ARTIFACT_DISPLAY_FILENAMES[artifact.name] || artifact.name;
  }

  function describeOutputGroup(item) {
    if (!item || typeof item.relative_path !== "string") {
      return "App-only extras";
    }

    const relativePath = item.relative_path;
    if (relativePath.startsWith("AI_READY_640/")) {
      return "AI_READY_640";
    }
    if (relativePath.startsWith("REPORT_640_")) {
      return "REPORT_640";
    }
    if (relativePath.startsWith("DEM_GEO8_TIFS/")) {
      return "DEM_GEO8_TIFS";
    }
    if (relativePath.startsWith("GEOTIFF_RADAR_BANDS/")) {
      return "GEOTIFF_RADAR_BANDS";
    }
    if (relativePath.startsWith("NPY_RADAR_BANDS/")) {
      return "NPY_RADAR_BANDS";
    }
    if (relativePath.startsWith("NPY_STACKS/")) {
      return "NPY_STACKS";
    }
    if (relativePath.startsWith("QA/")) {
      return "QA";
    }
    if (relativePath.startsWith("objects/") || relativePath === "objects_index.csv" || relativePath === "clusters_summary.csv") {
      return "Object extraction";
    }
    if (relativePath.includes("manifest")) {
      return "Manifests";
    }
    if (!relativePath.includes("/")) {
      return "Root files / app science outputs";
    }
    return relativePath.split("/")[0] || "Other";
  }

  function formatFileSize(sizeBytes) {
    if (!Number.isFinite(sizeBytes) || sizeBytes < 0) {
      return "size unavailable";
    }
    if (sizeBytes < 1024) {
      return `${sizeBytes} B`;
    }
    if (sizeBytes < 1024 * 1024) {
      return `${(sizeBytes / 1024).toFixed(1)} KB`;
    }
    return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function clearOutputTree() {
    const outputTreeList = document.getElementById("output-tree-list");
    const notImplementedList = document.getElementById("not-implemented-list");
    const outputTreeCount = document.getElementById("output-tree-count");
    if (!outputTreeList || !notImplementedList || !outputTreeCount) {
      return;
    }
    outputTreeList.innerHTML = "";
    notImplementedList.innerHTML = "";
    outputTreeCount.textContent = "0 files";
    state.currentOutputTreePayload = null;
    renderKeyDownloads([]);
  }

  function renderOutputTreeMessage(message) {
    const outputTreeList = document.getElementById("output-tree-list");
    const outputTreeCount = document.getElementById("output-tree-count");
    if (!outputTreeList || !outputTreeCount) {
      return;
    }
    outputTreeList.innerHTML = "";
    outputTreeCount.textContent = "0 files";
    state.currentOutputTreePayload = null;
    renderKeyDownloads([]);
    const item = document.createElement("li");
    item.className = "output-tree-empty";
    item.textContent = message;
    outputTreeList.appendChild(item);
  }

  function outputMatchesFilter(output, query) {
    if (!query) {
      return true;
    }
    const haystack = `${output.filename || ""} ${output.relative_path || ""} ${output.directory || ""}`.toLowerCase();
    return haystack.includes(query);
  }

  function sortOutputGroups(left, right) {
    const leftIndex = OUTPUT_GROUP_ORDER.indexOf(left);
    const rightIndex = OUTPUT_GROUP_ORDER.indexOf(right);
    if (leftIndex !== -1 || rightIndex !== -1) {
      if (leftIndex === -1) {
        return 1;
      }
      if (rightIndex === -1) {
        return -1;
      }
      return leftIndex - rightIndex;
    }
    return left.localeCompare(right);
  }

  function renderKeyDownloads(outputs) {
    const list = document.getElementById("key-downloads-list");
    if (!list) {
      return;
    }
    list.innerHTML = "";

    const byPath = new Map();
    for (const output of Array.isArray(outputs) ? outputs : []) {
      if (output && typeof output.relative_path === "string") {
        byPath.set(output.relative_path, output);
      }
    }

    const keyOutputs = KEY_DOWNLOAD_PATHS.map(function (relativePath) {
      return byPath.get(relativePath);
    }).filter(Boolean);

    if (keyOutputs.length === 0) {
      const item = document.createElement("li");
      item.className = "key-download-empty";
      item.textContent = "Key artifacts appear here when available for this run.";
      list.appendChild(item);
      return;
    }

    for (const output of keyOutputs) {
      const item = document.createElement("li");
      item.className = "key-download-item";

      const label = document.createElement("span");
      label.className = "key-download-label";
      label.textContent = output.filename;

      const path = document.createElement("span");
      path.className = "key-download-path";
      path.textContent = output.relative_path;

      item.appendChild(label);
      item.appendChild(path);

      if (typeof output.download_url === "string" && output.download_url) {
        const link = document.createElement("a");
        link.className = "key-download-link";
        link.href = output.download_url;
        link.download = output.filename;
        link.textContent = "Download";
        item.appendChild(link);
      }

      list.appendChild(item);
    }
  }

  function renderNotImplementedList(notImplemented) {
    const list = document.getElementById("not-implemented-list");
    if (!list) {
      return;
    }
    list.innerHTML = "";

    const entries = Array.isArray(notImplemented) ? notImplemented : [];
    if (entries.length === 0) {
      const item = document.createElement("li");
      item.className = "output-tree-empty";
      item.textContent = "No not-implemented outputs are reported for this run.";
      list.appendChild(item);
      return;
    }

    for (const entry of entries) {
      if (!entry || typeof entry.filename !== "string" || typeof entry.relative_path !== "string") {
        continue;
      }
      const item = document.createElement("li");
      item.className = "not-implemented-card";

      const head = document.createElement("div");
      head.className = "not-implemented-head";

      const name = document.createElement("span");
      name.className = "not-implemented-name";
      name.textContent = entry.filename;

      const status = document.createElement("span");
      status.className = "not-implemented-status";
      status.textContent = "Unavailable in this run.";

      head.appendChild(name);
      head.appendChild(status);

      const path = document.createElement("span");
      path.className = "not-implemented-path";
      path.textContent = entry.relative_path;

      const meta = document.createElement("div");
      meta.className = "not-implemented-meta";

      const group = document.createElement("span");
      group.className = "not-implemented-source";
      group.textContent = describeOutputGroup(entry);

      const source = document.createElement("span");
      source.className = "not-implemented-source";
      source.textContent = typeof entry.source === "string" ? `Source: ${entry.source}` : "";

      meta.appendChild(group);
      meta.appendChild(source);

      item.appendChild(head);
      item.appendChild(path);
      item.appendChild(meta);
      list.appendChild(item);
    }
  }

  function renderOutputTree(payload) {
    const outputTreeList = document.getElementById("output-tree-list");
    const outputTreeCount = document.getElementById("output-tree-count");
    if (!outputTreeList || !outputTreeCount) {
      return;
    }

    state.currentOutputTreePayload = payload || null;
    const outputs = Array.isArray(payload && payload.outputs) ? payload.outputs : [];
    const query = state.outputFilter.trim().toLowerCase();
    const filteredOutputs = outputs.filter(function (output) {
      return outputMatchesFilter(output, query);
    });
    const grouped = new Map();
    for (const output of filteredOutputs) {
      if (!output || typeof output.relative_path !== "string" || typeof output.filename !== "string") {
        continue;
      }
      const groupLabel = describeOutputGroup(output);
      if (!grouped.has(groupLabel)) {
        grouped.set(groupLabel, []);
      }
      grouped.get(groupLabel).push(output);
    }

    outputTreeList.innerHTML = "";
    outputTreeCount.textContent = `${outputs.length} file${outputs.length === 1 ? "" : "s"}`;
    renderKeyDownloads(outputs);

    if (outputs.length === 0) {
      renderOutputTreeMessage("No output files found for this run.");
      renderNotImplementedList(payload && payload.not_implemented);
      return;
    }
    if (filteredOutputs.length === 0) {
      const item = document.createElement("li");
      item.className = "output-tree-empty";
      item.textContent = "No output files match the current filter.";
      outputTreeList.appendChild(item);
      renderNotImplementedList(payload && payload.not_implemented);
      return;
    }

    const groupLabels = Array.from(grouped.keys()).sort(sortOutputGroups);
    for (const groupLabel of groupLabels) {
      const groupOutputs = grouped.get(groupLabel).slice().sort(function (left, right) {
        return left.relative_path.localeCompare(right.relative_path);
      });
      const groupItem = document.createElement("li");
      groupItem.className = "output-group";

      const details = document.createElement("details");
      details.className = "output-group-details";
      details.open = state.outputGroupsExpanded;

      const head = document.createElement("summary");
      head.className = "output-group-head";

      const title = document.createElement("span");
      title.className = "output-group-title";
      title.textContent = groupLabel;

      const count = document.createElement("span");
      count.className = "output-group-count";
      const totalSize = groupOutputs.reduce(function (sum, output) {
        const size = Number(output.size_bytes);
        return Number.isFinite(size) && size > 0 ? sum + size : sum;
      }, 0);
      count.textContent = `${groupOutputs.length} file${groupOutputs.length === 1 ? "" : "s"} · ${formatFileSize(totalSize)}`;

      head.appendChild(title);
      head.appendChild(count);

      const table = document.createElement("table");
      table.className = "output-file-table";
      const thead = document.createElement("thead");
      thead.innerHTML = "<tr><th>Filename</th><th>Path</th><th>Size</th><th>Action</th></tr>";
      const tbody = document.createElement("tbody");

      for (const output of groupOutputs) {
        const row = document.createElement("tr");

        const nameCell = document.createElement("td");
        nameCell.className = "output-file-name";
        nameCell.textContent = output.filename;

        const pathCell = document.createElement("td");
        pathCell.className = "output-file-path";
        pathCell.textContent = output.relative_path;

        const sizeCell = document.createElement("td");
        sizeCell.className = "output-file-size";
        sizeCell.textContent = formatFileSize(Number(output.size_bytes));

        const actionCell = document.createElement("td");

        if (typeof output.download_url === "string" && output.download_url) {
          const link = document.createElement("a");
          link.className = "output-file-link";
          link.href = output.download_url;
          link.download = output.filename;
          link.textContent = "Download";
          actionCell.appendChild(link);
        } else {
          actionCell.textContent = "Unavailable";
        }

        row.appendChild(nameCell);
        row.appendChild(pathCell);
        row.appendChild(sizeCell);
        row.appendChild(actionCell);
        tbody.appendChild(row);
      }

      table.appendChild(thead);
      table.appendChild(tbody);
      const tableWrap = document.createElement("div");
      tableWrap.className = "output-file-table-wrap";
      tableWrap.appendChild(table);
      details.appendChild(head);
      details.appendChild(tableWrap);
      groupItem.appendChild(details);
      outputTreeList.appendChild(groupItem);
    }

    renderNotImplementedList(payload && payload.not_implemented);
  }

  async function loadOutputTree(runId) {
    state.currentOutputTreeRunId = runId;
    state.outputFilter = "";
    state.outputGroupsExpanded = false;
    const outputFilter = document.getElementById("output-filter");
    if (outputFilter) {
      outputFilter.value = "";
    }
    renderOutputTreeMessage("Outputs are loading...");
    renderNotImplementedList([]);

    const response = await fetch(`/runs/${encodeURIComponent(runId)}/outputs`);
    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }
    if (!response.ok) {
      const message = payload && typeof payload.message === "string" ? payload.message : "Could not load full output tree.";
      throw new Error(message);
    }
    if (state.currentOutputTreeRunId !== runId) {
      return null;
    }
    renderOutputTree(payload);
    return payload;
  }

  function parseTargetInput() {
    const latInput = document.getElementById("target-lat");
    const lonInput = document.getElementById("target-lon");
    if (!latInput || !lonInput) {
      return { isValid: false, lat: null, lon: null, message: "Target input is unavailable." };
    }

    const lat = Number.parseFloat(latInput.value);
    const lon = Number.parseFloat(lonInput.value);
    if (!Number.isFinite(lat)) {
      return { isValid: false, lat: null, lon: null, message: "Target point is incomplete." };
    }
    if (lat < -90 || lat > 90) {
      return { isValid: false, lat: null, lon: null, message: "Target point is outside the accepted range." };
    }
    if (!Number.isFinite(lon)) {
      return { isValid: false, lat: null, lon: null, message: "Target point is incomplete." };
    }
    if (lon < -180 || lon > 180) {
      return { isValid: false, lat: null, lon: null, message: "Target point is outside the accepted range." };
    }
    return { isValid: true, lat, lon, message: "Target point is valid." };
  }

  function renderTargetValidation() {
    const status = document.getElementById("selection-status");
    const submitButton = document.getElementById("submit-run");
    const feedback = document.getElementById("run-feedback");
    if (!status || !submitButton || !feedback) {
      return;
    }

    const target = parseTargetInput();
    submitButton.disabled = !target.isValid;
    status.textContent = target.message;
    if (!target.isValid && !state.currentRunId) {
      feedback.textContent = "";
    }
  }

  function isTerminalRunStatus(status) {
    return status === "done" || status === "failed" || status === "stale_failed" || status === "cancelled";
  }

  function describeRunStatus(status) {
    if (status === "queued") {
      return "Queued";
    }
    if (status === "running") {
      return "Running";
    }
    if (status === "done") {
      return "Done";
    }
    if (status === "failed" || status === "stale_failed") {
      return "Failed";
    }
    if (status === "cancelled") {
      return "Cancelled";
    }
    return "Idle";
  }

  function shortStageLabel(label) {
    return STAGE_LABEL_SHORT_NAMES[label] || label;
  }

  function statusIcon(status) {
    return STATUS_ICON_BY_STATE[status] || "o";
  }

  function shouldExpandStatusHistory(status) {
    return status === "running" || status === "failed" || status === "stale_failed";
  }

  function setActiveDashboardTab(tabName) {
    const nextTab = DASHBOARD_TABS.includes(tabName) ? tabName : "overview";
    state.activeDashboardTab = nextTab;

    for (const button of document.querySelectorAll(".tab-button[data-tab]")) {
      const isActive = button.getAttribute("data-tab") === nextTab;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-selected", isActive ? "true" : "false");
    }

    for (const panel of document.querySelectorAll(".tab-panel[data-panel]")) {
      const isActive = panel.getAttribute("data-panel") === nextTab;
      panel.classList.toggle("is-active", isActive);
      panel.hidden = !isActive;
    }
  }

  function formatRunTimestamp(run) {
    if (!run) {
      return "";
    }
    return run.updated_at || run.created_at || "";
  }

  function syncRecentRunFromDetail(runDetail) {
    if (!runDetail || typeof runDetail.id !== "string" || typeof runDetail.status !== "string") {
      return;
    }

    let changed = false;
    state.recentRuns = state.recentRuns.map(function (run) {
      if (!run || run.id !== runDetail.id) {
        return run;
      }
      changed = true;
      return {
        ...run,
        name: Object.prototype.hasOwnProperty.call(runDetail, "name") ? runDetail.name : run.name,
        status: runDetail.status,
        created_at: runDetail.created_at || run.created_at,
      };
    });

    if (changed) {
      renderRunHistory(state.recentRuns);
    }
  }

  function setRunLifecycleView(detail) {
    const runIdValue = document.getElementById("run-id-value");
    const runStateValue = document.getElementById("run-state-value");
    const runDetailValue = document.getElementById("run-detail-value");
    const refreshButton = document.getElementById("run-refresh");
    if (!runIdValue || !runStateValue || !runDetailValue || !refreshButton) {
      return;
    }

    runIdValue.textContent = detail.runId || "Not started";
    runStateValue.textContent = detail.stateLabel;
    runDetailValue.textContent = detail.detail;
    refreshButton.classList.toggle("is-hidden", !detail.showManualRefresh);
  }

  function renderStageProgress(runDetail) {
    const currentStageValue = document.getElementById("current-stage-value");
    const list = document.getElementById("stage-progress-list");
    if (!currentStageValue || !list) {
      return;
    }

    const stages = Array.isArray(runDetail && runDetail.stages) ? runDetail.stages : [];
    const runStatus = typeof runDetail.status === "string" ? runDetail.status : null;
    const currentStageName = typeof runDetail.current_stage === "string" ? runDetail.current_stage : null;
    const currentStage = stages.find(function (stage) {
      return stage && stage.name === currentStageName;
    });

    if (currentStage) {
      currentStageValue.textContent = currentStage.label;
    } else if (runStatus === "done") {
      currentStageValue.textContent = "Completed";
    } else if (runStatus === "failed" || runStatus === "stale_failed") {
      currentStageValue.textContent = "Failed";
    } else if (runStatus === "queued" || runStatus === "running") {
      currentStageValue.textContent = "Waiting for first stage";
    } else {
      currentStageValue.textContent = "Not active";
    }
    list.innerHTML = "";

    if (stages.length === 0) {
      const item = document.createElement("li");
      item.className = "stage-progress-item stage-progress-empty";
      if (runStatus === "done") {
        item.textContent = "Historical run; detailed stage progress is unavailable.";
      } else if (runStatus === "failed" || runStatus === "stale_failed") {
        item.textContent = "Detailed stage progress is unavailable for this failed run.";
      } else if (runStatus === "queued" || runStatus === "running") {
        item.textContent = "Waiting for first stage update.";
      } else {
        item.textContent = "Detailed stage progress is unavailable.";
      }
      list.appendChild(item);
      return;
    }

    for (const stage of stages) {
      if (!stage || typeof stage.label !== "string" || typeof stage.status !== "string") {
        continue;
      }
      const item = document.createElement("li");
      item.className = `stage-progress-item stage-status-${stage.status}`;
      item.title = `${stage.label}: ${stage.status}`;
      item.setAttribute("aria-label", `${stage.label}: ${stage.status}`);

      const icon = document.createElement("span");
      icon.className = "stage-progress-icon";
      icon.setAttribute("aria-hidden", "true");
      icon.textContent = statusIcon(stage.status);

      const label = document.createElement("span");
      label.className = "stage-progress-label";
      label.textContent = shortStageLabel(stage.label);

      item.appendChild(icon);
      item.appendChild(label);
      list.appendChild(item);
    }
  }

  function renderStatusHistory(runDetail) {
    const list = document.getElementById("status-history-list");
    const details = document.getElementById("status-history-details");
    const summary = document.getElementById("status-history-summary-label");
    if (!list) {
      return;
    }

    const history = Array.isArray(runDetail && runDetail.history) ? runDetail.history : [];
    const runStatus = typeof (runDetail && runDetail.status) === "string" ? runDetail.status : null;
    list.innerHTML = "";
    if (summary) {
      summary.textContent = `Status history (${history.length} event${history.length === 1 ? "" : "s"})`;
    }
    if (details) {
      details.open = shouldExpandStatusHistory(runStatus);
    }

    if (history.length === 0) {
      const item = document.createElement("li");
      item.className = "status-history-item status-history-empty";
      item.textContent = "No detailed status history is available for this run.";
      list.appendChild(item);
      renderStatusHistorySummary(history);
      return;
    }

    for (const event of history) {
      if (!event || typeof event.label !== "string" || typeof event.message !== "string") {
        continue;
      }
      const item = document.createElement("li");
      item.className = "status-history-item";

      const label = document.createElement("span");
      label.className = "status-history-label";
      label.textContent = event.label;

      const message = document.createElement("span");
      message.className = "status-history-message";
      message.textContent = event.message;

      item.appendChild(label);
      item.appendChild(message);
      list.appendChild(item);
    }
    renderStatusHistorySummary(history);
  }

  function renderStatusHistorySummary(history) {
    const list = document.getElementById("status-history-summary-list");
    const count = document.getElementById("status-history-count");
    const events = Array.isArray(history) ? history : [];
    if (!list) {
      return;
    }
    list.innerHTML = "";
    if (count) {
      count.textContent = `${events.length} event${events.length === 1 ? "" : "s"}`;
    }
    if (events.length === 0) {
      const item = document.createElement("li");
      item.className = "status-history-item status-history-empty";
      item.textContent = "No status history summary is available yet.";
      list.appendChild(item);
      return;
    }
    for (const event of events.slice(-3)) {
      if (!event || typeof event.label !== "string" || typeof event.message !== "string") {
        continue;
      }
      const item = document.createElement("li");
      item.className = "status-history-item status-history-summary-item";

      const label = document.createElement("span");
      label.className = "status-history-label";
      label.textContent = event.label;

      const message = document.createElement("span");
      message.className = "status-history-message";
      message.textContent = event.message;

      item.appendChild(label);
      item.appendChild(message);
      list.appendChild(item);
    }
  }

  function renderArtifactMessage(message, detailMessage) {
    const list = document.getElementById("artifact-list");
    const count = document.getElementById("artifact-count");
    const tileMode = document.getElementById("tile-mode");
    if (!list || !count || !tileMode) {
      return;
    }

    tileMode.textContent = SPA_CONFIG.externalTilesEnabled ? "External tiles enabled" : "External tiles disabled";
    count.textContent = "0 artifacts";
    list.innerHTML = "";

    const item = document.createElement("li");
    item.className = "artifact-card artifact-card-empty";
    const primary = document.createElement("span");
    primary.className = "artifact-message";
    primary.textContent = message;
    item.appendChild(primary);
    if (detailMessage) {
      const detail = document.createElement("span");
      detail.className = "artifact-meta artifact-message-detail";
      detail.textContent = detailMessage;
      item.appendChild(detail);
    }
    list.appendChild(item);
  }

  function renderArtifacts(runId, artifacts) {
    const list = document.getElementById("artifact-list");
    const count = document.getElementById("artifact-count");
    const tileMode = document.getElementById("tile-mode");
    if (!list || !count || !tileMode) {
      return;
    }

    const visibleArtifacts = Array.isArray(artifacts) ? artifacts.filter(isVisibleArtifact) : [];
    tileMode.textContent = SPA_CONFIG.externalTilesEnabled ? "External tiles enabled" : "External tiles disabled";
    count.textContent = `${visibleArtifacts.length} artifact${visibleArtifacts.length === 1 ? "" : "s"}`;

    list.innerHTML = "";
    if (visibleArtifacts.length === 0) {
      renderArtifactMessage(
        "No UI-downloadable artifacts are available for this run.",
        "Full local outputs are stored under data/runs/<" + "run" + "_id>/."
      );
      return;
    }

    for (const artifact of visibleArtifacts) {
      const item = document.createElement("li");
      item.className = "artifact-card";

      const title = document.createElement("span");
      title.className = "artifact-title";

      const label = document.createElement("span");
      label.className = "artifact-label";
      label.textContent = displayArtifactName(artifact);

      const description = document.createElement("span");
      description.className = "artifact-description";
      description.textContent = describeArtifact(artifact);

      title.appendChild(label);
      title.appendChild(description);

      const link = document.createElement("a");
      link.className = "artifact-link";
      link.href = buildArtifactHref(runId, artifact);
      link.download = displayArtifactName(artifact);
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

  function setHistoryStatus(message) {
    const status = document.getElementById("history-status");
    if (status) {
      status.textContent = message;
    }
  }

  function createRunHistoryItem(run) {
    const item = document.createElement("li");
    item.className = "run-history-item";

    const meta = document.createElement("span");
    meta.className = "run-history-meta";

    const name = document.createElement("span");
    name.className = "run-history-name";
    name.textContent = typeof run.name === "string" && run.name.trim() ? run.name : "Unnamed run";

    const id = document.createElement("span");
    id.className = "run-history-id";
    id.textContent = run.id;

    const time = document.createElement("span");
    time.className = "run-history-time";
    time.textContent = formatRunTimestamp(run);

    const status = document.createElement("span");
    status.className = "run-history-status";
    status.textContent = describeRunStatus(run.status);

    const button = document.createElement("button");
    button.className = "refresh-button";
    button.type = "button";
    button.textContent = "Open";
    button.addEventListener("click", function () {
      void selectRun(run.id);
    });

    meta.appendChild(name);
    meta.appendChild(id);
    if (time.textContent) {
      meta.appendChild(time);
    }
    item.appendChild(meta);
    item.appendChild(status);
    item.appendChild(button);
    return item;
  }

  function renderRunArchive(runs) {
    const list = document.getElementById("run-archive-list");
    if (!list) {
      return;
    }

    list.innerHTML = "";
    const entries = Array.isArray(runs) ? runs.slice(3) : [];
    const query = state.archiveFilter.trim().toLowerCase();
    const filteredEntries = entries.filter(function (run) {
      const haystack = `${run.id || ""} ${run.name || ""} ${run.status || ""} ${formatRunTimestamp(run)}`.toLowerCase();
      return !query || haystack.includes(query);
    });
    if (entries.length === 0) {
      const item = document.createElement("li");
      item.className = "status-history-item status-history-empty";
      item.textContent = "No older loaded runs are available from the current API response.";
      list.appendChild(item);
      return;
    }
    if (filteredEntries.length === 0) {
      const item = document.createElement("li");
      item.className = "status-history-item status-history-empty";
      item.textContent = "No archived runs match the current filter.";
      list.appendChild(item);
      return;
    }

    for (const run of filteredEntries) {
      if (!run || typeof run.id !== "string") {
        continue;
      }
      list.appendChild(createRunHistoryItem(run));
    }
  }

  function renderRunHistory(runs) {
    const list = document.getElementById("run-history-list");
    if (!list) {
      return;
    }

    list.innerHTML = "";
    if (!Array.isArray(runs) || runs.length === 0) {
      setHistoryStatus("No recent runs found.");
      renderRunArchive([]);
      return;
    }

    setHistoryStatus(`${runs.length} loaded run${runs.length === 1 ? "" : "s"} available. Showing the latest 3.`);
    for (const run of runs.slice(0, 3)) {
      if (!run || typeof run.id !== "string") {
        continue;
      }
      list.appendChild(createRunHistoryItem(run));
    }
    renderRunArchive(runs);
  }

  async function loadRecentRuns() {
    setHistoryStatus("Loading recent runs...");
    try {
      const response = await fetch("/runs");
      let payload = null;
      try {
        payload = await response.json();
      } catch (_error) {
        payload = null;
      }
      if (!response.ok) {
        const message =
          payload && typeof payload.message === "string" ? payload.message : "Recent runs are temporarily unavailable.";
        throw new Error(message);
      }
      state.recentRuns = Array.isArray(payload) ? payload : [];
      renderRunHistory(state.recentRuns);
    } catch (error) {
      state.recentRuns = [];
      renderRunHistory([]);
      setHistoryStatus(error instanceof Error ? error.message : "Recent runs are temporarily unavailable.");
    }
  }

  async function selectRun(runId) {
    const feedback = document.getElementById("run-feedback");
    clearRunPolling();
    state.currentRunId = runId;
    setRunLifecycleView({
      runId,
      stateLabel: "Loading",
      detail: "Loading selected run.",
      showManualRefresh: false,
    });
    renderOutputTreeMessage("Outputs are loading...");
    renderNotImplementedList([]);
    renderArtifactMessage("Loading artifact status for the selected run.");
    if (feedback) {
      feedback.textContent = `Loading run: ${runId}`;
    }

    try {
      await fetchRunStatus(runId);
      await loadRecentRuns();
    } catch (error) {
      state.pollFailed = true;
      setRunLifecycleView({
        runId,
        stateLabel: describeRunStatus(state.currentRunStatus),
        detail: "Selected run could not be loaded. Use manual refresh to retry.",
        showManualRefresh: true,
      });
      renderArtifactMessage("Artifact status is unavailable. Use manual refresh to retry.");
      renderOutputTreeMessage("Could not load full output tree.");
      renderNotImplementedList([]);
      if (feedback) {
        feedback.textContent = error instanceof Error ? error.message : "Run lookup failed.";
      }
    }
  }

  function clearRunPolling() {
    if (state.pollTimerId !== null) {
      window.clearTimeout(state.pollTimerId);
      state.pollTimerId = null;
    }
  }

  async function fetchRunStatus(runId, options) {
    const response = await fetch(`/runs/${encodeURIComponent(runId)}`);
    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }
    if (!response.ok) {
      const message =
        payload && typeof payload.message === "string" ? payload.message : "Run status is temporarily unavailable.";
      throw new Error(message);
    }

    const status = typeof payload.status === "string" ? payload.status : "queued";
    state.currentRunId = runId;
    state.currentRunStatus = status;
    state.pollFailed = false;
    syncRecentRunFromDetail(payload);

    const detail =
      status === "queued"
        ? "Run accepted. Polling every 2 seconds."
        : status === "running"
          ? "Run is in progress. Polling every 2 seconds."
          : status === "done"
            ? "Run completed."
            : "Run ended in a failed state.";

    setRunLifecycleView({
      runId,
      stateLabel: describeRunStatus(status),
      detail,
      showManualRefresh: false,
    });
    renderStageProgress(payload);
    renderStatusHistory(payload);

    if (!options || options.updateFeedback !== false) {
      const feedback = document.getElementById("run-feedback");
      if (feedback) {
        feedback.textContent =
          status === "done" ? `Run completed: ${runId}` : status === "failed" || status === "stale_failed" ? `Run failed: ${runId}` : `Run active: ${runId}`;
      }
    }

    if (!isTerminalRunStatus(status)) {
      renderArtifactMessage("Artifacts are not ready while the run is queued or running.");
      renderOutputTreeMessage("Full output tree is available after a completed run.");
      renderNotImplementedList([]);
      clearRunPolling();
      state.pollTimerId = window.setTimeout(function () {
        void pollRunStatus(runId);
      }, 2000);
    } else {
      clearRunPolling();
      if (status === "done") {
        renderArtifacts(runId, payload.artifacts);
        try {
          await loadOutputTree(runId);
        } catch (_error) {
          renderOutputTreeMessage("Could not load full output tree.");
          renderNotImplementedList([]);
        }
      } else {
        renderArtifactMessage("Artifacts are unavailable for this run state.");
        renderOutputTreeMessage("Full output tree is unavailable for this run state.");
        renderNotImplementedList([]);
      }
    }

    return payload;
  }

  async function pollRunStatus(runId) {
    try {
      await fetchRunStatus(runId);
    } catch (error) {
      clearRunPolling();
      state.pollFailed = true;
      setRunLifecycleView({
        runId,
        stateLabel: describeRunStatus(state.currentRunStatus),
        detail: "Polling paused. Use manual refresh to retry.",
        showManualRefresh: true,
      });
      renderArtifactMessage("Artifact status is unavailable. Use manual refresh to retry.");
      renderOutputTreeMessage("Could not load full output tree.");
      renderNotImplementedList([]);
      const feedback = document.getElementById("run-feedback");
      if (feedback) {
        feedback.textContent = error instanceof Error ? error.message : "Polling failed.";
      }
    }
  }

  async function submitRun(event) {
    event.preventDefault();
    const target = parseTargetInput();
    if (!target.isValid) {
      renderTargetValidation();
      return;
    }

    const submitButton = document.getElementById("submit-run");
    const runNameInput = document.getElementById("run-name");
    const feedback = document.getElementById("run-feedback");
    if (!submitButton || !feedback || !runNameInput) {
      return;
    }

    submitButton.disabled = true;
    feedback.textContent = "Queueing local run...";
    clearRunPolling();
    renderOutputTreeMessage("Full output tree is available after a completed run.");
    renderNotImplementedList([]);
    renderArtifactMessage("Artifacts are not ready while the run is queued or running.");
    setRunLifecycleView({
      runId: state.currentRunId || "Pending",
      stateLabel: "Submitting",
      detail: "Submitting run request.",
      showManualRefresh: false,
    });

    try {
      const response = await fetch("/runs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          lat: target.lat,
          lon: target.lon,
          name: runNameInput.value.trim() || null,
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(typeof payload.message === "string" ? payload.message : "Run request failed.");
      }

      state.currentRunId = payload.id;
      state.currentRunStatus = payload.status;
      renderArtifactMessage("Artifacts are not ready while the run is queued or running.");
      setRunLifecycleView({
        runId: payload.id,
        stateLabel: describeRunStatus(payload.status),
        detail: "Run accepted. Polling every 2 seconds.",
        showManualRefresh: false,
      });
      feedback.textContent = `Run queued: ${payload.id}`;
      await fetchRunStatus(payload.id, { updateFeedback: false });
      await loadRecentRuns();
    } catch (error) {
      clearRunPolling();
      state.currentRunStatus = "failed";
      renderOutputTreeMessage("Full output tree is unavailable because the run request failed.");
      renderNotImplementedList([]);
      renderArtifactMessage("Artifacts are unavailable because the run request failed.");
      setRunLifecycleView({
        runId: state.currentRunId || "Not started",
        stateLabel: "Failed",
        detail: "Run request did not complete. Check the safe message below.",
        showManualRefresh: false,
      });
      feedback.textContent = error instanceof Error ? error.message : "Run request failed.";
    } finally {
      submitButton.disabled = false;
    }
  }

  function initializePinWorkspace() {
    const form = document.getElementById("run-form");
    const latInput = document.getElementById("target-lat");
    const lonInput = document.getElementById("target-lon");
    const refreshButton = document.getElementById("run-refresh");
    const lookupForm = document.getElementById("run-lookup-form");
    const lookupInput = document.getElementById("run-lookup-id");
    const recentRunsRefresh = document.getElementById("recent-runs-refresh");
    const outputFilter = document.getElementById("output-filter");
    const archiveFilter = document.getElementById("archive-filter");
    const expandOutputGroups = document.getElementById("expand-output-groups");
    const collapseOutputGroups = document.getElementById("collapse-output-groups");
    if (
      !form ||
      !latInput ||
      !lonInput ||
      !refreshButton ||
      !lookupForm ||
      !lookupInput ||
      !recentRunsRefresh ||
      !outputFilter ||
      !archiveFilter ||
      !expandOutputGroups ||
      !collapseOutputGroups
    ) {
      return;
    }

    latInput.addEventListener("input", renderTargetValidation);
    lonInput.addEventListener("input", renderTargetValidation);
    form.addEventListener("submit", submitRun);
    lookupForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const runId = lookupInput.value.trim();
      if (!runId) {
        setHistoryStatus("Enter a run ID to load a run.");
        return;
      }
      void selectRun(runId);
    });
    recentRunsRefresh.addEventListener("click", function () {
      void loadRecentRuns();
    });
    outputFilter.addEventListener("input", function () {
      state.outputFilter = outputFilter.value.trim();
      if (state.currentOutputTreePayload) {
        renderOutputTree(state.currentOutputTreePayload);
      }
    });
    archiveFilter.addEventListener("input", function () {
      state.archiveFilter = archiveFilter.value.trim();
      renderRunArchive(state.recentRuns);
    });
    for (const button of document.querySelectorAll(".tab-button[data-tab]")) {
      button.addEventListener("click", function () {
        setActiveDashboardTab(button.getAttribute("data-tab"));
      });
    }
    expandOutputGroups.addEventListener("click", function () {
      state.outputGroupsExpanded = true;
      if (state.currentOutputTreePayload) {
        renderOutputTree(state.currentOutputTreePayload);
      }
    });
    collapseOutputGroups.addEventListener("click", function () {
      state.outputGroupsExpanded = false;
      if (state.currentOutputTreePayload) {
        renderOutputTree(state.currentOutputTreePayload);
      }
    });
    refreshButton.addEventListener("click", function () {
      if (!state.currentRunId) {
        return;
      }
      setRunLifecycleView({
        runId: state.currentRunId,
        stateLabel: describeRunStatus(state.currentRunStatus),
        detail: "Refreshing run state.",
        showManualRefresh: false,
      });
      void fetchRunStatus(state.currentRunId);
    });
    renderTargetValidation();
    setRunLifecycleView({
      runId: "Not started",
      stateLabel: "Idle",
      detail: "Submit a run to begin polling.",
      showManualRefresh: false,
    });
    renderStageProgress({ current_stage: null, stages: [] });
    renderStatusHistory({ history: [] });
    setActiveDashboardTab("overview");
    renderOutputTreeMessage("Full output tree is available after a completed run.");
    renderNotImplementedList([]);
    renderArtifactMessage("Artifacts will appear after a run completes.");
    void loadRecentRuns();
  }

  initializePinWorkspace();
})();
