from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_frontend_spa_shell_is_served_locally_without_external_assets() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "GEE Screening Workspace" in response.text
    assert 'src="/app.js"' in response.text
    assert 'href="/style.css"' in response.text
    assert "Target Input" in response.text
    assert "External tiles disabled" in response.text
    assert "Queue run" in response.text
    assert 'id="target-lat"' in response.text
    assert 'id="target-lon"' in response.text
    assert "Run lifecycle" in response.text
    assert "Current stage" in response.text
    assert "stage-progress-list" in response.text
    assert "Status history" in response.text
    assert "status-history-list" in response.text
    assert "What outputs will I get?" in response.text
    assert "Output Browser" in response.text
    assert "Full operator output tree" in response.text
    assert response.text.index("Full operator output tree") < response.text.index("Run outputs")
    assert "Full operator output tree appears here after a completed run." in response.text
    assert "Key Downloads" in response.text
    assert "key-downloads-list" in response.text
    assert "output-filter" in response.text
    assert "Filter outputs" in response.text
    assert "Expand all" in response.text
    assert "Collapse all" in response.text
    assert "Grouped output browser" in response.text
    assert "output-tree-list" in response.text
    assert "not-implemented-list" in response.text
    assert "Run outputs" in response.text
    assert "Public-safe artifacts appear here when a run completes." in response.text
    assert "public-safe artifacts" in response.text
    assert "data/runs/&lt;run_id&gt;/" in response.text
    assert "guarded links" in response.text
    assert "FILESYSTEM_ONLY" in response.text
    assert "GRID/DEM" in response.text
    assert "SAR" in response.text
    assert "Sentinel-2 indices" in response.text
    assert "DEM derivatives" in response.text
    assert "thermal" in response.text
    assert "hypercube/PCA" in response.text
    assert "object extraction" in response.text
    assert "alignment QA" in response.text
    assert "docs/RUN_OUTPUTS.md" in response.text
    assert 'href="docs/RUN_OUTPUTS.md"' not in response.text
    assert "Run lookup" in response.text
    assert "Refresh runs" in response.text
    assert "Load run" in response.text
    assert "Recent runs will load automatically." in response.text
    assert "Manual Pin Workspace" not in response.text
    assert "Stage a local point" not in response.text
    assert "pin-map" not in response.text
    assert "geojson" not in response.text.casefold()
    assert "wkt" not in response.text.casefold()
    assert "cdn" not in response.text.casefold()
    assert "fonts.googleapis" not in response.text.casefold()
    assert "googletagmanager" not in response.text.casefold()
    assert "experimental/" not in response.text


def test_frontend_assets_are_served_and_guarded_artifact_path_is_used() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)

    js_response = client.get("/app.js")
    css_response = client.get("/style.css")

    assert js_response.status_code == 200
    assert "application/javascript" in js_response.headers["content-type"] or "text/javascript" in js_response.headers["content-type"]
    assert 'externalTilesEnabled: false' in js_response.text
    assert 'fetch("/runs"' in js_response.text
    assert 'fetch("/runs")' in js_response.text
    assert "fetch(`/runs/${encodeURIComponent(runId)}`)" in js_response.text
    assert "fetch(`/runs/${encodeURIComponent(runId)}/outputs`)" in js_response.text
    assert 'method: "POST"' in js_response.text
    assert "loadRecentRuns" in js_response.text
    assert "selectRun" in js_response.text
    assert "loadOutputTree" in js_response.text
    assert "renderOutputTree" in js_response.text
    assert "KEY_DOWNLOAD_PATHS" in js_response.text
    assert "OUTPUT_GROUP_ORDER" in js_response.text
    assert "renderKeyDownloads" in js_response.text
    assert "outputMatchesFilter" in js_response.text
    assert "sortOutputGroups" in js_response.text
    assert "outputGroupsExpanded" in js_response.text
    assert "outputFilter" in js_response.text
    assert "output-file-table" in js_response.text
    assert "stage-status-" in js_response.text
    assert "run-lookup-form" in js_response.text
    assert "run-history-list" in js_response.text
    assert "target-lat" in js_response.text
    assert "target-lon" in js_response.text
    assert "renderStageProgress" in js_response.text
    assert "renderStatusHistory" in js_response.text
    assert "syncRecentRunFromDetail" in js_response.text
    assert "describeOutputGroup" in js_response.text
    assert "describeArtifact" in js_response.text
    assert "displayArtifactName" in js_response.text
    assert "objects_index.csv" in js_response.text
    assert "clusters_summary.csv" in js_response.text
    assert "alignment_qa.json" in js_response.text
    assert "alignment_audit.json" in js_response.text
    assert "alignment_mask_selection.json" in js_response.text
    assert "detailed detected object table" in js_response.text
    assert "grouped cluster summary" in js_response.text
    assert "safe alignment health summary" in js_response.text
    assert "alignment audit details" in js_response.text
    assert "selected masks used for alignment QA" in js_response.text
    assert "public-safe run artifact" in js_response.text
    assert "current_stage" in js_response.text
    assert "history" in js_response.text
    assert "Completed" in js_response.text
    assert "Waiting for first stage" in js_response.text
    assert "Historical run; detailed stage progress is unavailable." in js_response.text
    assert "Detailed stage progress is unavailable for this failed run." in js_response.text
    assert "Waiting for first stage update." in js_response.text
    assert "No detailed status history is available for this run." in js_response.text
    assert "Run completed." in js_response.text
    assert "Run ended in a failed state." in js_response.text
    assert "Stage progress is not available yet." not in js_response.text
    assert "Status history is not available yet." not in js_response.text
    assert "stage-progress-list" in js_response.text
    assert "status-history-list" in js_response.text
    assert "selectedPoint" not in js_response.text
    assert "pin-map" not in js_response.text
    assert "stagePointFromNormalized" not in js_response.text
    assert '/artifacts/' in js_response.text
    assert '/download/' in js_response.text
    assert 'artifacts/${encodeURIComponent(artifact.name)}/download/${encodeURIComponent(downloadFilename)}' in js_response.text
    assert 'output.download_url' in js_response.text
    assert "link.download = displayArtifactName(artifact);" in js_response.text
    assert 'FILESYSTEM_ONLY' in js_response.text
    assert "experimental_" in js_response.text
    assert "Outputs are loading..." in js_response.text
    assert "No output files found for this run." in js_response.text
    assert "Could not load full output tree." in js_response.text
    assert "Not implemented in current app output set." in js_response.text
    assert "QA/RUN_MANIFEST.json" in js_response.text
    assert "DEM_GEO8_TIFS/DEM_640.tif" in js_response.text
    assert "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.tif" in js_response.text
    assert "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE.npy" in js_response.text
    assert "NPY_STACKS/FINAL_TESLA_V7_2_HYPERCUBE_PATCHED_14B.tif" in js_response.text
    assert "REPORT_640_Pottery_Report.tif" in js_response.text
    assert "sampleArtifacts" not in js_response.text
    assert "demo-run" not in js_response.text
    assert "Artifacts will appear after a run completes." in js_response.text
    assert "No UI-downloadable artifacts are available for this run." in js_response.text
    assert "Full local outputs are stored under data/runs/<" in js_response.text
    assert "Run completed with no public artifacts." not in js_response.text
    assert 'GeoJSON' not in js_response.text
    assert 'WKT' not in js_response.text
    assert "relative_path" in js_response.text
    assert "display_label" not in js_response.text
    assert "run_id" not in js_response.text
    assert 'https://' not in js_response.text
    assert 'http://' not in js_response.text

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert "key-downloads-panel" in css_response.text
    assert "output-browser-scroll" in css_response.text
    assert "output-file-table" in css_response.text
    assert "stage-status-done" in css_response.text
    assert "@import" not in css_response.text
    assert "fonts.googleapis" not in css_response.text
