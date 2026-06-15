import { expect, test, type Page, type Route } from "@playwright/test";

const RUN_ID = "e2e-v6-package-flow";
const CREATED_AT = "2026-06-14T12:00:00Z";
const OPERATOR_TOKEN = "local-e2e-operator-token";
const WRONG_ROLE_TOKEN = "local-e2e-wrong-role-token";
const UNAUTHORIZED_RUN_TOKEN = "local-e2e-unauthorized-run-token";
const ZIP_FILENAME = "V6_REAL_GENERATED.zip";

type MockDownloadMode = "success" | "failure" | "json-not-available";

interface MockFrozenV6PackageFlowOptions {
  acceptedToken?: string;
  deniedStatus?: Record<string, unknown>;
  forcedDeniedStatus?: Record<string, unknown>;
  reviewStatus?: Record<string, unknown>;
  generateStatus?: Record<string, unknown>;
  downloadMode?: MockDownloadMode;
}

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
  message: "Access to requested resource not available.",
  support_reference: "v6-e2e-denied-before-session",
};

const packageStatusDisabledDenied = {
  ...packageStatusDenied,
  support_reference: "v6-e2e-disabled-rollback",
};

const packageStatusWrongRoleDenied = {
  ...packageStatusDenied,
  support_reference: "v6-e2e-wrong-role",
};

const packageStatusRunUnauthorizedDenied = {
  ...packageStatusDenied,
  support_reference: "v6-e2e-run-not-authorized",
};

const packageStatusUnavailable = {
  outcome: "not_available",
  run_id: RUN_ID,
  request_id: "v6-e2e-unavailable",
  package_ready: false,
};

const packageStatusInvalidInputs = {
  outcome: "invalid_package_inputs",
  run_id: RUN_ID,
  request_id: "v6-e2e-invalid-input",
  package_ready: false,
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
  "source_path",
  "package_path",
  "coordinates",
  "bounds",
  "west",
  "south",
  "east",
  "north",
];

test("operator can review, generate, and retrieve the frozen V6 package without exposing private rows", async ({ page }) => {
  await mockFrozenV6PackageFlow(page);
  await openFrozenRun(page, OPERATOR_TOKEN);

  await expect(page.getByText("Package metadata", { exact: true })).toBeVisible();
  await expect(page.getByText("Validation", { exact: true })).toBeVisible();
  await expect(page.getByText("passed", { exact: true })).toBeVisible();
  await expect(page.getByText("Payloads", { exact: true })).toBeVisible();
  await expect(page.getByText("12", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("ZIP entries", { exact: true })).toBeVisible();
  await expect(page.getByText(ZIP_FILENAME, { exact: true })).toBeVisible();

  await expectNoForbiddenPrivatePayloadText(page);

  await page.getByRole("button", { name: "Generate package" }).click();
  await expect(page.getByText("Package generated.", { exact: true })).toBeVisible();
  await expect(page.getByText("generated", { exact: true })).toBeVisible();
  await expectNoForbiddenPrivatePayloadText(page);

  await page.getByRole("button", { name: "Review metadata" }).click();
  await expect(page.getByText("available", { exact: true })).toBeVisible();
  await expectNoForbiddenPrivatePayloadText(page);

  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Retrieve ZIP" }).click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toBe(ZIP_FILENAME);
  await expect(page.getByText("Package retrieval started.", { exact: true })).toBeVisible();
  await expectNoForbiddenPrivatePayloadText(page);
});

test.describe("expanded V6 package flow states", () => {
  test("shows disabled rollback denial safely", async ({ page }) => {
    await mockFrozenV6PackageFlow(page, { forcedDeniedStatus: packageStatusDisabledDenied });
    await openFrozenRun(page, OPERATOR_TOKEN);

    await expect(page.getByText("Access to requested resource not available.", { exact: true })).toBeVisible();
    await expect(page.getByText("Support reference: v6-e2e-disabled-rollback", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Retrieve ZIP" })).toBeDisabled();
    await expectNoForbiddenPrivatePayloadText(page);
  });

  test("shows unauthenticated denial safely before an operator session", async ({ page }) => {
    await mockFrozenV6PackageFlow(page);
    await openFrozenRun(page, null);

    await expect(page.getByText("Access to requested resource not available.", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Support reference: v6-e2e-denied-before-session", { exact: true }).first()).toBeVisible();
    await expect(page.getByPlaceholder("Paste local bearer value")).toBeVisible();
    await expectNoForbiddenPrivatePayloadText(page);
  });

  test("shows wrong-role denial safely", async ({ page }) => {
    await mockFrozenV6PackageFlow(page, { deniedStatus: packageStatusWrongRoleDenied });
    await openFrozenRun(page, WRONG_ROLE_TOKEN);

    await expect(page.getByText("Access to requested resource not available.", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Support reference: v6-e2e-wrong-role", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Retrieve ZIP" })).toBeDisabled();
    await expectNoForbiddenPrivatePayloadText(page);
  });

  test("shows run-not-authorized denial safely", async ({ page }) => {
    await mockFrozenV6PackageFlow(page, { deniedStatus: packageStatusRunUnauthorizedDenied });
    await openFrozenRun(page, UNAUTHORIZED_RUN_TOKEN);

    await expect(page.getByText("Access to requested resource not available.", { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Support reference: v6-e2e-run-not-authorized", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Retrieve ZIP" })).toBeDisabled();
    await expectNoForbiddenPrivatePayloadText(page);
  });

  test("shows unavailable package state safely", async ({ page }) => {
    await mockFrozenV6PackageFlow(page, {
      reviewStatus: packageStatusUnavailable,
      generateStatus: packageStatusUnavailable,
      downloadMode: "json-not-available",
    });
    await openFrozenRun(page, OPERATOR_TOKEN);

    await expect(page.getByText("No V6 package is available for this run yet.", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Retrieve ZIP" })).toBeDisabled();
    await page.getByRole("button", { name: "Generate package" }).click();
    await expect(page.getByText("Package generation did not complete.", { exact: true })).toBeVisible();
    await expectNoForbiddenPrivatePayloadText(page);
  });

  test("shows invalid package input state without leaking input content", async ({ page }) => {
    await mockFrozenV6PackageFlow(page, {
      reviewStatus: packageStatusUnavailable,
      generateStatus: packageStatusInvalidInputs,
    });
    await openFrozenRun(page, OPERATOR_TOKEN);

    await page.getByRole("button", { name: "Generate package" }).click();
    await expect(page.getByText("The run-local V6 package inputs are invalid.", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Retrieve ZIP" })).toBeDisabled();
    await expectNoForbiddenPrivatePayloadText(page);
  });

  test("shows retrieval failure after metadata review", async ({ page }) => {
    await mockFrozenV6PackageFlow(page, { downloadMode: "failure" });
    await openFrozenRun(page, OPERATOR_TOKEN);

    await expect(page.getByText(ZIP_FILENAME, { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Retrieve ZIP" }).click();
    await expect(page.getByText("V6 package is temporarily unavailable.", { exact: true }).first()).toBeVisible();
    await expectNoForbiddenPrivatePayloadText(page);
  });

  test("keeps expanded mock assertions metadata-only", async ({ page }) => {
    await mockFrozenV6PackageFlow(page, { reviewStatus: packageStatusGenerated });
    await openFrozenRun(page, OPERATOR_TOKEN);

    await expect(page.getByText("Package metadata", { exact: true })).toBeVisible();
    await expect(page.getByText("Categories: csv 6 · geojson 3 · report 2 · html 1", { exact: true })).toBeVisible();
    await expect(page.getByText(ZIP_FILENAME, { exact: true })).toBeVisible();
    await expectNoForbiddenPrivatePayloadText(page);
  });
});

async function openFrozenRun(page: Page, operatorToken: string | null): Promise<void> {
  await enablePrivateOperatorUi(page);
  await page.goto("/");
  if (operatorToken) {
    await startOperatorSession(page, operatorToken);
  }
  await expect(page.getByText("V6 real package flow (operator-only)")).toBeVisible();
}

async function startOperatorSession(page: Page, operatorToken: string): Promise<void> {
  await page.getByPlaceholder("Paste local bearer value").fill(operatorToken);
  await page.getByRole("button", { name: "Start session" }).click();
}

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

async function mockFrozenV6PackageFlow(page: Page, options: MockFrozenV6PackageFlowOptions = {}): Promise<void> {
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
    if (!(await requireBearer(route, options))) {
      return;
    }
    await route.fulfill({ json: privateOverlayPreviewUnavailable });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}/operator/v6/package/review$`), async (route) => {
    if (await fulfillForcedDenied(route, options)) {
      return;
    }
    if (!(await requireBearer(route, options))) {
      return;
    }
    await route.fulfill({ json: options.reviewStatus ?? packageStatusAvailable });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}/operator/v6/package/generate$`), async (route) => {
    if (await fulfillForcedDenied(route, options)) {
      return;
    }
    if (!(await requireBearer(route, options))) {
      return;
    }
    const status = options.generateStatus ?? packageStatusGenerated;
    const outcome = typeof status.outcome === "string" ? status.outcome : "";
    await route.fulfill({ status: outcome === "invalid_package_inputs" ? 400 : 200, json: status });
  });

  await page.route(new RegExp(`/runs/${RUN_ID}/operator/v6/package/download$`), async (route) => {
    if (await fulfillForcedDenied(route, options)) {
      return;
    }
    if (!(await requireBearer(route, options))) {
      return;
    }
    if (options.downloadMode === "failure") {
      await route.fulfill({ status: 500, body: "safe mocked retrieval failure" });
      return;
    }
    if (options.downloadMode === "json-not-available") {
      await route.fulfill({ json: packageStatusUnavailable });
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

async function fulfillForcedDenied(route: Route, options: MockFrozenV6PackageFlowOptions): Promise<boolean> {
  if (!options.forcedDeniedStatus) {
    return false;
  }
  await route.fulfill({ status: 403, json: options.forcedDeniedStatus });
  return true;
}

async function requireBearer(route: Route, options: MockFrozenV6PackageFlowOptions = {}): Promise<boolean> {
  const auth = route.request().headers()["authorization"] || "";
  const acceptedToken = options.acceptedToken ?? OPERATOR_TOKEN;
  if (auth !== `Bearer ${acceptedToken}`) {
    await route.fulfill({ status: 403, json: options.deniedStatus ?? packageStatusDenied });
    return false;
  }
  return true;
}

async function expectNoForbiddenPrivatePayloadText(page: Page): Promise<void> {
  for (const text of forbiddenUiText) {
    await expect(page.getByText(text, { exact: false })).toHaveCount(0);
  }
}
