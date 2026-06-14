import { expect, test, type Page, type Route } from "@playwright/test";

const RUN_ID = "e2e-v6-package-flow";
const CREATED_AT = "2026-06-14T12:00:00Z";
const OPERATOR_TOKEN = "local-e2e-operator-token";
const ZIP_FILENAME = "V6_REAL_GENERATED.zip";

const runSummary = {
  id: RUN_ID,
  name: "V6 E2E frozen package flow",
  status: "done",
  created_at: CREATED_AT,
  disk_usage_bytes: 4096,
  output_file_count: 12,
  last_disk_scan_at: CREATED_AT,
};

const runDetail = {
  ...runSummary,
  detail: "Frozen V6 package flow smoke run.",
  current_stage: "done",
  stages: [
    { name: "done", label: "Completed", status: "done" },
  ],
  history: [
    {
      timestamp: CREATED_AT,
      event_type: "done",
      label: "Completed",
      message: "Run completed.",
      stage_name: "done",
    },
  ],
  artifacts: [],
};

const emptyOutputTree = {
  run_id: RUN_ID,
  outputs: [],
  not_implemented: [],
};

const privateOverlayPreviewUnavailable = {
  outcome: "not_available",
  run_id: RUN_ID,
  artifact_family: "phase_d1_private_geojson",
  access_mode: "operator_only_preview",
  preview_type: "operator_private_overlay_preview",
  item_count: null,
  preview_payload: null,
  filesystem_only: true,
  http_servable: false,
  downloadable_via_api: false,
  frontend_visible: "operator_only",
};

const packageStatusDenied = {
  outcome: "denied",
  run_id: RUN_ID,
  package_ready: false,
  message: "Operator token required.",
  support_reference: "v6-e2e-denied-before-session",
};

const packageStatusAvailable = {
  outcome: "available",
  run_id: RUN_ID,
  request_id: "v6-e2e-safe-request",
  package_ready: true,
  validation_status: "passed",
  payload_count: 12,
  zip_entry_count: 12,
  category_counts: {
    csv: 6,
    geojson: 3,
    report: 2,
    html: 1,
  },
  issue_count: 0,
  warning_count: 0,
  zip_filename: ZIP_FILENAME,
  inventory_filename: "v6_inventory.json",
  validation_report_filename: "v6_validation_report.json",
};

const packageStatusGenerated = {
  ...packageStatusAvailable,
  outcome: "generated",
};

const forbiddenUiText = [
  "candidate rows",
  "feature rows",
  "private package input body",
  "spatial payload body",
  "coordinates",
  "geometry",
  "bbox",
  "source_path",
  "package_path",
];

test("operator can review, generate, and retrieve the frozen V6 package without exposing private rows", async ({ page }) => {
  await mockFrozenV6PackageFlow(page);
  await enablePrivateOperatorUi(page);

  await page.goto("/");

  await page.getByPlaceholder("Paste local bearer value").fill(OPERATOR_TOKEN);
  await page.getByRole("button", { name: "Start session" }).click();

  await expect(page.getByText("V6 real package flow (operator-only)")).toBeVisible();
  await expect(page.getByText("Package metadata")).toBeVisible();
  await expect(page.getByText("Validation")).toBeVisible();
  await expect(page.getByText("passed")).toBeVisible();
  await expect(page.getByText("Payloads")).toBeVisible();
  await expect(page.getByText("12").first()).toBeVisible();
  await expect(page.getByText("ZIP entries")).toBeVisible();
  await expect(page.getByText(ZIP_FILENAME)).toBeVisible();

  await expectNoForbiddenPrivatePayloadText(page);

  await page.getByRole("button", { name: "Generate package" }).click();
  await expect(page.getByText("Package generated.")).toBeVisible();
  await expect(page.getByText("generated")).toBeVisible();
  await expectNoForbiddenPrivatePayloadText(page);

  await page.getByRole("button", { name: "Review metadata" }).click();
  await expect(page.getByText("available")).toBeVisible();
  await expectNoForbiddenPrivatePayloadText(page);

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Retrieve ZIP" }).click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toBe(ZIP_FILENAME);
  await expect(page.getByText("Package retrieval started.")).toBeVisible();
  await expectNoForbiddenPrivatePayloadText(page);
});

async function enablePrivateOperatorUi(page: Page): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "gs_operator_ui_settings_v1",
      JSON.stringify({
        externalTilesEnabled: false,
        tileUrlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        showAdvancedUnavailableOutputs: false,
        operatorPrivateOverlayEnabled: true,
      }),
    );
  });
}

async function mockFrozenV6PackageFlow(page: Page): Promise<void> {
  await page.route(/\/runs\/deletion-audit$/, async (route) => {
    await route.fulfill({ json: { total_freed_bytes: 0, records: [] } });
  });

  await page.route(/\/runs\/cleanup-summary$/, async (route) => {
    await route.fulfill({
      json: {
        total_runs: 1,
        total_disk_usage_bytes: 4096,
        terminal_runs_count: 1,
        active_runs_count: 0,
        deleted_runs_count: 0,
        total_freed_bytes: 0,
        largest_runs: [runSummary],
        oldest_terminal_runs: [runSummary],
        stale_failed_runs: [],
        cleanup_recommended: false,
        warning_reason: "No cleanup needed.",
        threshold_bytes: 10737418240,
      },
    });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}/operator/private-overlays.*$`), async (route) => {
    if (!(await requireBearer(route))) {
      return;
    }
    await route.fulfill({ json: privateOverlayPreviewUnavailable });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}/operator/v6/package/review$`), async (route) => {
    if (!(await requireBearer(route))) {
      return;
    }
    await route.fulfill({ json: packageStatusAvailable });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}/operator/v6/package/generate$`), async (route) => {
    if (!(await requireBearer(route))) {
      return;
    }
    await route.fulfill({ json: packageStatusGenerated });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}/operator/v6/package/download$`), async (route) => {
    if (!(await requireBearer(route))) {
      return;
    }
    await route.fulfill({
      status: 200,
      headers: {
        "content-type": "application/zip",
        "content-disposition": `attachment; filename="${ZIP_FILENAME}"`,
      },
      body: "safe mocked zip bytes",
    });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}/outputs$`), async (route) => {
    await route.fulfill({ json: emptyOutputTree });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}$`), async (route) => {
    await route.fulfill({ json: runDetail });
  });

  await page.route(/\/runs(\?.*)?$/, async (route) => {
    await route.fulfill({ json: [runSummary] });
  });
}

async function requireBearer(route: Route): Promise<boolean> {
  const auth = route.request().headers()["authorization"] || "";
  if (auth !== `Bearer ${OPERATOR_TOKEN}`) {
    await route.fulfill({ status: 403, json: packageStatusDenied });
    return false;
  }
  return true;
}

async function expectNoForbiddenPrivatePayloadText(page: Page): Promise<void> {
  for (const text of forbiddenUiText) {
    await expect(page.getByText(text, { exact: false })).toHaveCount(0);
  }
}
