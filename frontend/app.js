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

  const state = {
    currentRunId: null,
    currentRunStatus: null,
    pollTimerId: null,
    pollFailed: false,
    recentRuns: [],
    currentOutputTreeRunId: null,
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
    if (relativePath.startsWith("REPORT_640_")) {
      return "Reports";
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
    if (relativePath.startsWith("QA/sar/intermediates/")) {
      return "QA/sar/intermediates";
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
    return "App-only extras";
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
  }

  function renderOutputTreeMessage(message) {
    const outputTreeList = document.getElementById("output-tree-list");
    const outputTreeCount = document.getElementById("output-tree-count");
    if (!outputTreeList || !outputTreeCount) {
      return;
    }
    outputTreeList.innerHTML = "";
    outputTreeCount.textContent = "0 files";
    const item = document.createElement("li");
    item.className = "output-tree-empty";
    item.textContent = message;
    outputTreeList.appendChild(item);
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
      status.textContent = "Not implemented in current app output set.";

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

    const outputs = Array.isArray(payload && payload.outputs) ? payload.outputs : [];
    const grouped = new Map();
    for (const output of outputs) {
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

    if (outputs.length === 0) {
      renderOutputTreeMessage("No output files found for this run.");
      renderNotImplementedList(payload && payload.not_implemented);
      return;
    }

    for (const [groupLabel, groupOutputs] of grouped.entries()) {
      const groupItem = document.createElement("li");
      groupItem.className = "output-group";

      const head = document.createElement("div");
      head.className = "output-group-head";

      const title = document.createElement("span");
      title.className = "output-group-title";
      title.textContent = groupLabel;

      const count = document.createElement("span");
      count.className = "output-group-count";
      count.textContent = `${groupOutputs.length} file${groupOutputs.length === 1 ? "" : "s"}`;

      head.appendChild(title);
      head.appendChild(count);

      const fileList = document.createElement("ul");
      fileList.className = "output-file-list";

      for (const output of groupOutputs) {
        const fileItem = document.createElement("li");
        fileItem.className = "output-file-card";

        const fileHead = document.createElement("div");
        fileHead.className = "output-file-head";

        const name = document.createElement("span");
        name.className = "output-file-name";
        name.textContent = output.filename;

        const type = document.createElement("span");
        type.className = "output-file-type";
        type.textContent = output.extension || output.file_type || "file";

        fileHead.appendChild(name);
        fileHead.appendChild(type);

        const path = document.createElement("span");
        path.className = "output-file-path";
        path.textContent = output.relative_path;

        const meta = document.createElement("div");
        meta.className = "output-file-meta";

        const size = document.createElement("span");
        size.className = "output-file-size";
        size.textContent = formatFileSize(Number(output.size_bytes));

        const directory = document.createElement("span");
        directory.className = "output-file-size";
        directory.textContent = typeof output.directory === "string" && output.directory ? output.directory : "run root";

        meta.appendChild(size);
        meta.appendChild(directory);

        fileItem.appendChild(fileHead);
        fileItem.appendChild(path);
        fileItem.appendChild(meta);

        if (typeof output.download_url === "string" && output.download_url) {
          const link = document.createElement("a");
          link.className = "output-file-link";
          link.href = output.download_url;
          link.download = output.filename;
          link.textContent = "Download";
          fileItem.appendChild(link);
        }

        fileList.appendChild(fileItem);
      }

      groupItem.appendChild(head);
      groupItem.appendChild(fileList);
      outputTreeList.appendChild(groupItem);
    }

    renderNotImplementedList(payload && payload.not_implemented);
  }

  async function loadOutputTree(runId) {
    state.currentOutputTreeRunId = runId;
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
      item.className = "stage-progress-item";

      const label = document.createElement("span");
      label.className = "stage-progress-label";
      label.textContent = stage.label;

      const status = document.createElement("span");
      status.className = "stage-progress-status";
      status.textContent = stage.status;

      item.appendChild(label);
      item.appendChild(status);
      list.appendChild(item);
    }
  }

  function renderStatusHistory(runDetail) {
    const list = document.getElementById("status-history-list");
    if (!list) {
      return;
    }

    const history = Array.isArray(runDetail && runDetail.history) ? runDetail.history : [];
    list.innerHTML = "";

    if (history.length === 0) {
      const item = document.createElement("li");
      item.className = "status-history-item status-history-empty";
      item.textContent = "No detailed status history is available for this run.";
      list.appendChild(item);
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

  function renderRunHistory(runs) {
    const list = document.getElementById("run-history-list");
    if (!list) {
      return;
    }

    list.innerHTML = "";
    if (!Array.isArray(runs) || runs.length === 0) {
      setHistoryStatus("No recent runs found.");
      return;
    }

    setHistoryStatus(`${runs.length} recent run${runs.length === 1 ? "" : "s"} available.`);
    for (const run of runs) {
      if (!run || typeof run.id !== "string") {
        continue;
      }

      const item = document.createElement("li");
      item.className = "run-history-item";

      const meta = document.createElement("span");
      meta.className = "run-history-meta";

      const id = document.createElement("span");
      id.className = "run-history-id";
      id.textContent = run.id;

      const name = document.createElement("span");
      name.className = "run-history-name";
      name.textContent = typeof run.name === "string" && run.name.trim() ? run.name : "Unnamed run";

      const status = document.createElement("span");
      status.className = "run-history-status";
      status.textContent = describeRunStatus(run.status);

      const button = document.createElement("button");
      button.className = "refresh-button";
      button.type = "button";
      button.textContent = "Load";
      button.addEventListener("click", function () {
        void selectRun(run.id);
      });

      meta.appendChild(id);
      meta.appendChild(name);
      item.appendChild(meta);
      item.appendChild(status);
      item.appendChild(button);
      list.appendChild(item);
    }
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
    if (!form || !latInput || !lonInput || !refreshButton || !lookupForm || !lookupInput || !recentRunsRefresh) {
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
    renderOutputTreeMessage("Full output tree is available after a completed run.");
    renderNotImplementedList([]);
    renderArtifactMessage("Artifacts will appear after a run completes.");
    void loadRecentRuns();
  }

  initializePinWorkspace();
})();
