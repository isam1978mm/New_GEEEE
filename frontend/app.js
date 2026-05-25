(function () {
  "use strict";

  const SPA_CONFIG = {
    externalTilesEnabled: false,
    guardedArtifactPrefix: "/runs/",
  };

  const state = {
    selectedPoint: null,
    currentRunId: null,
    currentRunStatus: null,
    pollTimerId: null,
    pollFailed: false,
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
    return `${SPA_CONFIG.guardedArtifactPrefix}${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(artifact.name)}`;
  }

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function describeSelection(point) {
    if (!point) {
      return "No point staged yet.";
    }

    const verticalLabel = point.lat > 8 ? "northern" : point.lat < -8 ? "southern" : "equatorial";
    const horizontalLabel = point.lon > 12 ? "eastern" : point.lon < -12 ? "western" : "central";
    return `Point staged in the ${verticalLabel} ${horizontalLabel} sector.`;
  }

  function renderSelection() {
    const marker = document.getElementById("pin-marker");
    const status = document.getElementById("selection-status");
    const submitButton = document.getElementById("submit-run");
    const feedback = document.getElementById("run-feedback");

    if (!marker || !status || !submitButton || !feedback) {
      return;
    }

    if (!state.selectedPoint) {
      marker.classList.add("is-hidden");
      submitButton.disabled = true;
      status.textContent = "No point staged yet.";
      feedback.textContent = "";
      return;
    }

    marker.classList.remove("is-hidden");
    marker.style.left = `${state.selectedPoint.x * 100}%`;
    marker.style.top = `${state.selectedPoint.y * 100}%`;
    submitButton.disabled = false;
    status.textContent = describeSelection(state.selectedPoint);
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

  function renderArtifactMessage(message) {
    const list = document.getElementById("artifact-list");
    const count = document.getElementById("artifact-count");
    const tileMode = document.getElementById("tile-mode");
    if (!list || !count || !tileMode) {
      return;
    }

    tileMode.textContent = SPA_CONFIG.externalTilesEnabled ? "External tiles enabled" : "External tiles disabled";
    count.textContent = "0 visible";
    list.innerHTML = "";

    const item = document.createElement("li");
    item.className = "artifact-card artifact-card-empty";
    item.textContent = message;
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
    count.textContent = `${visibleArtifacts.length} visible`;

    list.innerHTML = "";
    if (visibleArtifacts.length === 0) {
      renderArtifactMessage("Run completed with no public artifacts.");
      return;
    }

    for (const artifact of visibleArtifacts) {
      const item = document.createElement("li");
      item.className = "artifact-card";

      const title = document.createElement("span");
      title.className = "artifact-label";
      title.textContent = artifact.name;

      const link = document.createElement("a");
      link.className = "artifact-link";
      link.href = buildArtifactHref(runId, artifact);
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

    if (!options || options.updateFeedback !== false) {
      const feedback = document.getElementById("run-feedback");
      if (feedback) {
        feedback.textContent =
          status === "done" ? `Run completed: ${runId}` : status === "failed" || status === "stale_failed" ? `Run failed: ${runId}` : `Run active: ${runId}`;
      }
    }

    if (!isTerminalRunStatus(status)) {
      renderArtifactMessage("Artifacts are not ready while the run is queued or running.");
      clearRunPolling();
      state.pollTimerId = window.setTimeout(function () {
        void pollRunStatus(runId);
      }, 2000);
    } else {
      clearRunPolling();
      if (status === "done") {
        renderArtifacts(runId, payload.artifacts);
      } else {
        renderArtifactMessage("Artifacts are unavailable for this run state.");
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
      const feedback = document.getElementById("run-feedback");
      if (feedback) {
        feedback.textContent = error instanceof Error ? error.message : "Polling failed.";
      }
    }
  }

  function stagePointFromNormalized(x, y) {
    const boundedX = clamp(x, 0, 1);
    const boundedY = clamp(y, 0, 1);
    state.selectedPoint = {
      x: boundedX,
      y: boundedY,
      lon: boundedX * 360 - 180,
      lat: 90 - boundedY * 180,
    };
    renderSelection();
  }

  async function submitRun(event) {
    event.preventDefault();
    if (!state.selectedPoint) {
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
          lat: state.selectedPoint.lat,
          lon: state.selectedPoint.lon,
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
    } catch (error) {
      clearRunPolling();
      state.currentRunStatus = "failed";
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
    const map = document.getElementById("pin-map");
    const form = document.getElementById("run-form");
    const refreshButton = document.getElementById("run-refresh");
    if (!map || !form || !refreshButton) {
      return;
    }

    map.addEventListener("click", function (event) {
      const rect = map.getBoundingClientRect();
      if (!rect.width || !rect.height) {
        return;
      }
      const x = (event.clientX - rect.left) / rect.width;
      const y = (event.clientY - rect.top) / rect.height;
      stagePointFromNormalized(x, y);
    });

    map.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" && event.key !== " ") {
        return;
      }
      event.preventDefault();
      stagePointFromNormalized(0.5, 0.5);
    });

    form.addEventListener("submit", submitRun);
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
    renderSelection();
    setRunLifecycleView({
      runId: "Not started",
      stateLabel: "Idle",
      detail: "Submit a run to begin polling.",
      showManualRefresh: false,
    });
    renderArtifactMessage("Artifacts will appear after a run completes.");
  }

  initializePinWorkspace();
})();
